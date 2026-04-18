from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from orchestrator import PricingOrchestrator
from db import init_db, SessionLocal, PricingDecision, CompetitorPrice
from scraper.crawler import Crawler
from scraper.scraper import Scraper
from constants import CURRENCY_DISPLAY


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Competitive Pricing Intelligence API",
    description="API for scraping, normalizing, and returning AI-assisted pricing recommendations.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = PricingOrchestrator()


@app.get("/health")
def health_check():
    """Quick connectivity test for the frontend."""
    return {"status": "ok", "service": "cmpt-api"}


def get_db():
    """FastAPI dependency that yields a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AnalyzeRequest(BaseModel):
    my_product_url: str
    competitor_store_urls: List[str]


class DiscoverRequest(BaseModel):
    my_product_url: str


@app.post("/analyze")
def analyze_pricing(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """Trigger an end-to-end pricing analysis for a specific product."""
    if not request.my_product_url:
        raise HTTPException(status_code=422, detail="Product URL is required.")
    if not request.competitor_store_urls:
        raise HTTPException(status_code=422, detail="At least one competitor URL is required.")

    result = orchestrator.run_pipeline(
        my_product_url=request.my_product_url,
        competitor_store_urls=request.competitor_store_urls,
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    decision_data = result["decision"]

    db_decision = PricingDecision(
        product_id=result["product_id"],
        my_price=result["my_price"],
        action=decision_data.get("action"),
        suggested_price=decision_data.get("suggested_price"),
        confidence=decision_data.get("confidence"),
        policy_reason=decision_data.get("policy_reason"),
        ai_advice=result.get("ai_advice"),
        explanation=result.get("explanation"),
    )
    db.add(db_decision)

    for comp in result.get("metrics", {}).get("competitor_stats", []):
        db_comp = CompetitorPrice(
            product_id=result["product_id"],
            competitor_url=comp.get("store") or comp.get("product_url"),
            price=comp.get("original_price"),
            currency=comp.get("original_currency"),
            confidence=comp.get("confidence"),
            scraped_at=(
                datetime.fromisoformat(comp["scraped_at"])
                if comp.get("scraped_at")
                else datetime.utcnow()
            ),
        )
        db.add(db_comp)

    db.commit()
    return result


@app.post("/discover-competitors")
def discover_competitors(request: DiscoverRequest):
    """Discover competitor store domains for the provided product URL."""
    if not request.my_product_url:
        raise HTTPException(status_code=422, detail="Product URL is required.")

    scraper = Scraper()
    raw_product = scraper.scrape_product(request.my_product_url)
    product_name = raw_product.get("product_name")

    if not product_name:
        raise HTTPException(
            status_code=400,
            detail="Could not determine the product name from the provided URL.",
        )

    crawler = Crawler()
    suggestions = crawler.discover_competitor_stores(product_name, max_results=6)

    if not suggestions:
        raise HTTPException(
            status_code=404,
            detail="No competitor stores could be discovered for this product.",
        )

    return {
        "status": "success",
        "product_name": product_name,
        "suggestions": suggestions,
    }
