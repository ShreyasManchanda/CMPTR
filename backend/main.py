import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import (
    CompetitorPrice,
    MerchantProduct,
    PricingDecision,
    init_db,
    verify_db_connection,
)
import db as db_mod
from jobs import create_job, get_job, update_job
from orchestrator import PricingOrchestrator
from utils.domain import brand_from_domain, clean_product_name, domain_from_url, product_name_from_url

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)

API_KEY = os.getenv("CMPT_API_KEY", "").strip()

_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
if _cors_raw.strip() == "*":
    CORS_ORIGINS = ["*"]
else:
    CORS_ORIGINS = [o.strip() for o in _cors_raw.split(",") if o.strip()]

RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "10"))

_rate_buckets: dict[str, deque] = defaultdict(deque)
orchestrator: Optional[PricingOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    init_db()
    verify_db_connection()
    orchestrator = PricingOrchestrator()
    logger.info("CMPT API ready")
    yield


app = FastAPI(
    title="Competitive Pricing Intelligence API",
    description="API for scraping, normalizing, and returning AI-assisted pricing recommendations.",
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False if CORS_ORIGINS == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    if db_mod.SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database is not initialized.")
    db = db_mod.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    if not API_KEY:
        return
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def enforce_rate_limit(request: Request):
    client = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _rate_buckets[client]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SEC:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
    bucket.append(now)


def _is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def _validate_analyze_inputs(product_url: str, competitor_urls: List[str]) -> None:
    if not product_url or not _is_http_url(product_url):
        raise HTTPException(status_code=422, detail="A valid http(s) product URL is required.")
    if not competitor_urls:
        raise HTTPException(status_code=422, detail="At least one competitor URL is required.")
    if any(not _is_http_url(u) for u in competitor_urls):
        raise HTTPException(status_code=422, detail="All competitor URLs must be valid http(s) URLs.")


def persist_analysis(db: Session, product_url: str, result: dict) -> int:
    """Save merchant snapshot, decision, and competitors. Returns decision id."""
    decision_data = result["decision"]
    ai_advice = result.get("ai_advice")
    ai_advice_text = (
        json.dumps(ai_advice) if isinstance(ai_advice, dict) else (str(ai_advice) if ai_advice else None)
    )

    merchant = (
        db.query(MerchantProduct)
        .filter(MerchantProduct.product_url == product_url)
        .one_or_none()
    )
    if merchant is None:
        db.add(
            MerchantProduct(
                product_url=product_url,
                product_id=result["product_id"],
                product_name=result.get("product_name"),
                current_price=result["my_price"],
                currency=result.get("currency"),
            )
        )
    else:
        merchant.product_id = result["product_id"]
        merchant.product_name = result.get("product_name")
        merchant.current_price = result["my_price"]
        merchant.currency = result.get("currency")
        merchant.updated_at = datetime.utcnow()

    db_decision = PricingDecision(
        product_id=result["product_id"],
        product_url=product_url,
        product_name=result.get("product_name"),
        my_price=result["my_price"],
        currency=result.get("currency"),
        action=decision_data.get("action"),
        suggested_price=decision_data.get("suggested_price"),
        confidence=decision_data.get("confidence"),
        policy_reason=decision_data.get("policy_reason"),
        ai_advice=ai_advice_text,
        explanation=result.get("explanation"),
    )
    db.add(db_decision)
    db.flush()

    for comp in result.get("metrics", {}).get("competitor_stats", []):
        scraped_at = datetime.utcnow()
        raw_ts = comp.get("scraped_at")
        if raw_ts:
            try:
                scraped_at = datetime.fromisoformat(raw_ts)
            except (TypeError, ValueError):
                pass
        db.add(
            CompetitorPrice(
                decision_id=db_decision.id,
                product_id=result["product_id"],
                competitor_url=comp.get("store") or comp.get("product_url"),
                price=comp.get("original_price"),
                currency=comp.get("original_currency"),
                confidence=comp.get("confidence"),
                scraped_at=scraped_at,
            )
        )

    db.commit()
    db.refresh(db_decision)
    return db_decision.id


def _run_analyze_job(job_id: str, product_url: str, competitor_urls: List[str]) -> None:
    """Background worker for async analysis jobs."""
    try:
        update_job(job_id, status="running", progress="pipeline")
        if orchestrator is None:
            raise RuntimeError("Orchestrator is not ready.")

        result = orchestrator.run_pipeline(
            my_product_url=product_url,
            competitor_store_urls=competitor_urls,
        )
        if result.get("status") == "error":
            # Demo-friendly fallback: if scraping is rate-limited / flaky, return the latest successful run.
            fallback_result = _try_load_latest_decision_from_history(product_url, result.get("message"))
            if fallback_result:
                update_job(job_id, status="completed", progress="done", result=fallback_result, error=None)
                return
            update_job(
                job_id,
                status="failed",
                progress="failed",
                error=result.get("message") or "Analysis failed.",
            )
            return

        update_job(job_id, progress="persisting")
        if db_mod.SessionLocal is None:
            raise RuntimeError("Database is not initialized.")

        db = db_mod.SessionLocal()
        try:
            decision_id = persist_analysis(db, product_url, result)
            result["decision_id"] = decision_id
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        update_job(job_id, status="completed", progress="done", result=result, error=None)
    except Exception as e:
        logger.exception("Async analyze job %s failed", job_id)
        fallback_result = _try_load_latest_decision_from_history(product_url, str(e))
        if fallback_result:
            update_job(job_id, status="completed", progress="done", result=fallback_result, error=None)
        else:
            update_job(job_id, status="failed", progress="failed", error=str(e))


def _try_load_latest_decision_from_history(product_url: str, error_context: str | None) -> dict | None:
    """
    If live scraping fails (commonly Firecrawl 429/rate-limit), we return the latest successful
    decision stored in the DB so the demo still looks complete.
    """
    try:
        if db_mod.SessionLocal is None:
            return None

        msg = (error_context or "").lower()
        should_fallback = any(x in msg for x in ("429", "rate limit", "scrape failed", "timeout", "could not parse"))
        if not should_fallback:
            # Avoid masking real logic issues.
            return None

        db = db_mod.SessionLocal()
        try:
            latest = (
                db.query(PricingDecision)
                .filter(PricingDecision.product_url == product_url)
                .order_by(PricingDecision.created_at.desc())
                .first()
            )
            if not latest:
                return None

            comps = (
                db.query(CompetitorPrice)
                .filter(CompetitorPrice.decision_id == latest.id)
                .order_by(CompetitorPrice.scraped_at.desc())
                .all()
            )

            # ai_advice is stored as a JSON string in persist_analysis; try to parse for UI panels.
            ai_advice = None
            try:
                if latest.ai_advice:
                    ai_advice = json.loads(latest.ai_advice)
            except Exception:
                ai_advice = latest.ai_advice

            competitor_stats = []
            for c in comps:
                host = (c.competitor_url or "").strip()
                scheme_url = host
                if host and not host.startswith("http"):
                    scheme_url = f"https://{host}"
                competitor_stats.append(
                    {
                        "store": host,
                        "product_name": host,
                        "price": c.price,
                        "stock_status": "unknown",
                        "confidence": c.confidence,
                        "scraped_at": c.scraped_at.isoformat() if c.scraped_at else None,
                        "url": scheme_url,
                    }
                )

            note = "Live scraping was rate-limited / unreliable. Showing the latest successful cached run."
            if error_context:
                note = f"{note} (reason: {error_context})"

            return {
                "status": "success",
                "from_history": True,
                "fallback": True,
                "fallback_reason": note,
                "product_id": latest.product_id,
                "product_name": latest.product_name,
                "product_url": product_url,
                "my_price": latest.my_price,
                "currency": latest.currency,
                "decision": {
                    "action": latest.action,
                    "suggested_price": latest.suggested_price,
                    "policy_reason": latest.policy_reason,
                    "confidence": latest.confidence,
                },
                "ai_advice": ai_advice,
                "explanation": f"{note}\n\n{latest.explanation or ''}".strip(),
                "decision_id": latest.id,
                "metrics": {
                    "scrape_stats": [],
                    "normalization": {},
                    "competitor_stats": competitor_stats,
                    "aggregated_stats": None,
                },
            }
        finally:
            db.close()
    except Exception:
        return None


class AnalyzeRequest(BaseModel):
    my_product_url: Optional[str] = None
    product_url: Optional[str] = None
    competitor_store_urls: Optional[List[str]] = None
    competitor_urls: Optional[List[str]] = None

    def get_product_url(self) -> str:
        return self.my_product_url or self.product_url or ""

    def get_competitor_urls(self) -> List[str]:
        return self.competitor_store_urls or self.competitor_urls or []


class DiscoverRequest(BaseModel):
    my_product_url: Optional[str] = None
    product_url: Optional[str] = None

    def get_product_url(self) -> str:
        return self.my_product_url or self.product_url or ""


@app.get("/health")
def health_check():
    try:
        verify_db_connection()
        return {"status": "ok", "service": "cmpt-api", "database": "ok"}
    except Exception as e:
        logger.warning("Health DB check failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "service": "cmpt-api", "database": "error"},
        )


@app.post("/analyze", dependencies=[Depends(require_api_key)])
def analyze_pricing(
    request: AnalyzeRequest,
    raw_request: Request,
    db: Session = Depends(get_db),
):
    """Synchronous analyze (kept for compatibility). Prefer /analyze/jobs for long runs."""
    enforce_rate_limit(raw_request)

    product_url = request.get_product_url().strip()
    competitor_urls = [u.strip() for u in request.get_competitor_urls() if u and u.strip()]
    _validate_analyze_inputs(product_url, competitor_urls)

    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator is not ready.")

    result = orchestrator.run_pipeline(
        my_product_url=product_url,
        competitor_store_urls=competitor_urls,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    try:
        decision_id = persist_analysis(db, product_url, result)
        result["decision_id"] = decision_id
    except Exception as e:
        db.rollback()
        logger.exception("Failed to persist analysis result")
        raise HTTPException(status_code=500, detail=f"Analysis succeeded but failed to save: {e}")

    return result


@app.post("/analyze/jobs", dependencies=[Depends(require_api_key)])
def start_analyze_job(request: AnalyzeRequest, raw_request: Request):
    """Start an async analysis job; poll GET /analyze/jobs/{id} for status/result."""
    enforce_rate_limit(raw_request)

    product_url = request.get_product_url().strip()
    competitor_urls = [u.strip() for u in request.get_competitor_urls() if u and u.strip()]
    _validate_analyze_inputs(product_url, competitor_urls)

    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator is not ready.")

    job_id = create_job()
    thread = threading.Thread(
        target=_run_analyze_job,
        args=(job_id, product_url, competitor_urls),
        daemon=True,
        name=f"analyze-{job_id[:8]}",
    )
    thread.start()

    return {
        "status": "queued",
        "job_id": job_id,
        "poll_url": f"/analyze/jobs/{job_id}",
    }


@app.get("/analyze/jobs/{job_id}", dependencies=[Depends(require_api_key)])
def get_analyze_job(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "status": job["status"],
        "job_id": job["id"],
        "progress": job.get("progress"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "error": job.get("error"),
        "result": job.get("result"),
    }


@app.post("/discover-competitors", dependencies=[Depends(require_api_key)])
def discover_competitors(request: DiscoverRequest, raw_request: Request):
    """Discover competitor stores using the shared orchestrator scraper/crawler."""
    enforce_rate_limit(raw_request)

    product_url = request.get_product_url().strip()
    if not product_url or not _is_http_url(product_url):
        raise HTTPException(status_code=422, detail="A valid http(s) product URL is required.")

    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator is not ready.")

    merchant_domain = domain_from_url(product_url)
    product_name = clean_product_name(product_name_from_url(product_url))
    merchant_price: float | None = None
    currency: str | None = None

    # Always scrape merchant on discover for accurate name + price tier context.
    raw_product = orchestrator.scraper.scrape_product(product_url)
    product_name = clean_product_name(raw_product.get("product_name") or product_name)
    price_raw = raw_product.get("current_price")
    if price_raw is not None:
        try:
            merchant_price = float(price_raw)
        except (TypeError, ValueError):
            merchant_price = None
    currency = raw_product.get("currency")

    product_name = clean_product_name(product_name)

    if not product_name:
        raise HTTPException(
            status_code=400,
            detail="Could not determine the product name from the provided URL.",
        )

    suggestions = orchestrator.crawler.discover_competitor_stores(
        product_name,
        max_results=6,
        exclude_domains=[merchant_domain] if merchant_domain else None,
        merchant_brand=brand_from_domain(merchant_domain),
        merchant_domain=merchant_domain,
        merchant_price=merchant_price,
        currency=currency,
        fast=True,
    )
    if not suggestions:
        raise HTTPException(
            status_code=404,
            detail="No competitor stores could be discovered for this product.",
        )

    return {
        "status": "success",
        "product_name": product_name,
        "merchant_price": merchant_price,
        "currency": currency,
        "suggestions": suggestions,
    }


@app.get("/decisions", dependencies=[Depends(require_api_key)])
def list_decisions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    product_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(PricingDecision).order_by(PricingDecision.created_at.desc())
    if product_id:
        q = q.filter(PricingDecision.product_id == product_id)
    rows = q.offset(offset).limit(limit).all()
    return {
        "status": "success",
        "count": len(rows),
        "decisions": [
            {
                "id": d.id,
                "product_id": d.product_id,
                "product_url": d.product_url,
                "product_name": d.product_name,
                "my_price": d.my_price,
                "currency": d.currency,
                "action": d.action,
                "suggested_price": d.suggested_price,
                "confidence": d.confidence,
                "policy_reason": d.policy_reason,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in rows
        ],
    }


@app.get("/decisions/{decision_id}", dependencies=[Depends(require_api_key)])
def get_decision(decision_id: int, db: Session = Depends(get_db)):
    decision = db.query(PricingDecision).filter(PricingDecision.id == decision_id).one_or_none()
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found.")

    competitors = (
        db.query(CompetitorPrice)
        .filter(CompetitorPrice.decision_id == decision_id)
        .all()
    )

    ai_advice = decision.ai_advice
    try:
        if ai_advice:
            ai_advice = json.loads(ai_advice)
    except (TypeError, json.JSONDecodeError):
        pass

    return {
        "status": "success",
        "decision": {
            "id": decision.id,
            "product_id": decision.product_id,
            "product_url": decision.product_url,
            "product_name": decision.product_name,
            "my_price": decision.my_price,
            "currency": decision.currency,
            "action": decision.action,
            "suggested_price": decision.suggested_price,
            "confidence": decision.confidence,
            "policy_reason": decision.policy_reason,
            "ai_advice": ai_advice,
            "explanation": decision.explanation,
            "created_at": decision.created_at.isoformat() if decision.created_at else None,
        },
        "competitors": [
            {
                "id": c.id,
                "competitor_url": c.competitor_url,
                "price": c.price,
                "currency": c.currency,
                "confidence": c.confidence,
                "scraped_at": c.scraped_at.isoformat() if c.scraped_at else None,
            }
            for c in competitors
        ],
    }
