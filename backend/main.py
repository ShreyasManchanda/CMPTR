from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime
import logging

# Import our custom modules
from orchestrator import PricingOrchestrator
import db as db_module
from db import PricingDecision, CompetitorPrice
from scraper.crawler import Crawler
from scraper.scraper import Scraper

logger = logging.getLogger(__name__)

# --- STEP 1: App Setup and Initialization ---
app = FastAPI(
    title="Competitive Pricing Intelligence API",
    description="API for scraping, normalizing, and returning AI-assisted pricing recommendations.",
    version="1.0.0"
)

# --- CORS Configuration ---
# Allow the frontend dev server and common deployment origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",       # Vite default dev server
        "http://localhost:3000",       # Alternate dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the orchestrator once when the app boots
orchestrator = PricingOrchestrator()

@app.on_event("startup")
def startup_event():
    # This automatically creates our PostgreSQL tables if they don't exist yet!
    db_module.init_db()
    db_module.verify_db_connection()


# --- STEP 2: Health Check ---
@app.get("/health")
def health_check():
    """Quick connectivity test for the frontend."""
    return {"status": "ok", "service": "cmpt-api"}


# --- STEP 3: Database Dependency ---
def get_db():
    """
    This is a FastAPI dependency. It opens a database session for each 
    request, and safely closes it when the request is done.
    """
    if db_module.SessionLocal is None:
        raise RuntimeError("SessionLocal is not initialized. Check DATABASE_URL and startup initialization.")

    db = db_module.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- STEP 4: API Models ---
class AnalyzeRequest(BaseModel):
    # Accept both naming conventions from various frontend versions
    my_product_url: str = None
    product_url: str = None
    competitor_store_urls: List[str] = None
    competitor_urls: List[str] = None

    def get_product_url(self) -> str:
        return self.my_product_url or self.product_url or ""

    def get_competitor_urls(self) -> List[str]:
        return self.competitor_store_urls or self.competitor_urls or []


class DiscoverRequest(BaseModel):
    my_product_url: str = None
    product_url: str = None

    def get_product_url(self) -> str:
        return self.my_product_url or self.product_url or ""


# --- STEP 5: The Main Endpoint ---
@app.post("/analyze")
def analyze_pricing(request: AnalyzeRequest, db = Depends(get_db)):
    """
    Trigger an end-to-end pricing analysis for a specific product.
    """
    product_url = request.get_product_url()
    competitor_urls = request.get_competitor_urls()

    if not product_url:
        raise HTTPException(status_code=422, detail="Product URL is required.")
    if not competitor_urls:
        raise HTTPException(status_code=422, detail="At least one competitor URL is required.")

    # 1. Run the massive orchestration pipeline we just built!
    result = orchestrator.run_pipeline(
        my_product_url=product_url, 
        competitor_store_urls=competitor_urls
    )
    
    # 2. Check for errors (like if it couldn't find your product)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
        
    # 3. Save the Decision to the Database! 
    # We unpack the dictionary elements returned from the orchestrator
    decision_data = result["decision"]
    
    db_decision = PricingDecision(
        product_id=result["product_id"],
        my_price=result["my_price"],
        action=decision_data.get("action"),
        suggested_price=decision_data.get("suggested_price"),
        confidence=decision_data.get("confidence"),
        policy_reason=decision_data.get("policy_reason"),
        ai_advice=result.get("ai_advice"),
        explanation=result.get("explanation")
    )
    
    # Save competitor data into the `CompetitorPrice` table
    competitor_stats = result.get("metrics", {}).get("competitor_stats", [])
    for comp in competitor_stats:
        db_comp = CompetitorPrice(
            product_id=result["product_id"],
            competitor_url=comp.get("store") or comp.get("product_url"),
            price=comp.get("original_price"),
            currency=comp.get("original_currency"),
            confidence=comp.get("confidence"),
            scraped_at=datetime.fromisoformat(comp.get("scraped_at")) if comp.get("scraped_at") else datetime.utcnow()
        )
        db.add(db_comp)
    
    # Commit all changes (decision + competitors)
    db.commit()
    
    # 4. Return the massive JSON result to the frontend
    return result


@app.post("/discover-competitors")
def discover_competitors(request: DiscoverRequest):
    """
    Discover competitor store domains for the provided product URL.
    """
    product_url = request.get_product_url()
    if not product_url:
        raise HTTPException(status_code=422, detail="Product URL is required.")
    logger.info(f"/discover-competitors called with product_url={product_url}")

    scraper = Scraper()
    raw_product = scraper.scrape_product(product_url)
    product_name = raw_product.get("product_name")
    logger.info(f"Derived product_name='{product_name}' from URL")

    if not product_name:
        raise HTTPException(status_code=400, detail="Could not determine the product name from the provided URL.")

    crawler = Crawler()
    suggestions = crawler.discover_competitor_stores(product_name, max_results=6)
    logger.info(f"Discovery returned {len(suggestions)} suggestions")

    if not suggestions:
        raise HTTPException(status_code=404, detail="No competitor stores could be discovered for this product.")

    return {
        "status": "success",
        "product_name": product_name,
        "suggestions": suggestions
    }


@app.post("/discover_competitors")
def discover_competitors_compat(request: DiscoverRequest):
    """Backward-compatible alias for clients using underscore route."""
    return discover_competitors(request)
