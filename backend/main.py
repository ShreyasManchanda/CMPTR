from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List

# Import our custom modules
from orchestrator import PricingOrchestrator
from db import init_db, SessionLocal, MerchantProduct, CompetitorPrice, PricingDecision

# --- STEP 1: App Setup and Initialization ---
app = FastAPI(
    title="Competitive Pricing Intelligence API",
    description="API for scraping, normalizing, and returning AI-assisted pricing recommendations.",
    version="1.0.0"
)

# Initialize the orchestrator once when the app boots
orchestrator = PricingOrchestrator()

@app.on_event("startup")
def startup_event():
    # This automatically creates our PostgreSQL tables if they don't exist yet!
    init_db()

# --- STEP 2: Database Dependency ---
def get_db():
    """
    This is a FastAPI dependency. It opens a database session for each 
    request, and safely closes it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- STEP 3: API Models ---
class AnalyzeRequest(BaseModel):
    my_product_url: str
    competitor_store_urls: List[str]


# --- STEP 4: The Main Endpoint ---
@app.post("/analyze")
def analyze_pricing(request: AnalyzeRequest, db = Depends(get_db)):
    """
    Trigger an end-to-end pricing analysis for a specific product.
    """
    # 1. Run the massive orchestration pipeline we just built!
    result = orchestrator.run_pipeline(
        my_product_url=request.my_product_url, 
        competitor_store_urls=request.competitor_store_urls
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
    
    # Add to session and commit (save to PostgreSQL)
    db.add(db_decision)
    db.commit()
    
    # Optional: You could also loop through result["metrics"]["competitor_stats"] 
    # and save them into the `CompetitorPrice` table here!
    
    # 4. Return the massive JSON result to the frontend
    return result
