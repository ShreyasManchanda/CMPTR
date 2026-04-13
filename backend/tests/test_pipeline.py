"""
Unified Deterministic Pipeline Tests.
Tests Normalizer, Pricing Engine, and Rules Agent with reproducible mock data.

Run from backend/: 
    python tests/test_pipeline.py
"""

import sys
import os
import json
from dataclasses import asdict

# Ensure the backend/ directory is in the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# COLOR HELPERS
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def header(title):
    print(f"\n{'='*60}")
    print(f"{CYAN}  TESTING: {title}{RESET}")
    print(f"{'='*60}")

def passed(msg):
    print(f"  {GREEN}[PASS]{RESET} — {msg}")

def failed(msg):
    print(f"  {RED}[FAIL]{RESET} — {msg}")

# FAKE DATA
FAKE_MY_PRODUCT = {
    "product_url": "https://mystore.com/products/cool-widget",
    "product_name": "Cool Widget",
    "current_price": "49.99",
    "currency": "USD",
    "scrape_confidence": "high"
}

FAKE_COMPETITORS = [
    {"product_url": "https://comp-a.com/p/1", "product_name": "Cool Widget", "current_price": "44.99", "currency": "USD", "scrape_confidence": "high"},
    {"product_url": "https://comp-b.com/p/2", "product_name": "Cool Widget", "current_price": "42.50", "currency": "USD", "scrape_confidence": "high"},
    {"product_url": "https://comp-c.com/p/3", "product_name": "Cool Widget", "current_price": "47.00", "currency": "USD", "scrape_confidence": "medium"},
    {"product_url": "https://comp-d.com/p/4", "product_name": "Cool Widget", "current_price": "46.00", "currency": "USD", "scrape_confidence": "high"},
    {"product_url": "https://comp-e.com/p/5", "product_name": "Cool Widget", "current_price": "160.00", "currency": "USD", "scrape_confidence": "high"}, # Outlier
]

def test_full_pipeline():
    header("Full Deterministic Pipeline")
    try:
        from normalizer.normalize_product import ProductNormalizer
        from pricing.pricing_engine import PricingEngine
        from pricing.rules_agent import RulesAgent

        # 1. Normalization
        norm = ProductNormalizer()
        collapsed_comps, metrics = norm.normalize_batch(FAKE_COMPETITORS)
        passed(f"Normalized {metrics['normalized_count']} items")

        # 2. Engine Math
        engine = PricingEngine()
        comp_dicts = [c.dict() for c in collapsed_comps]
        # Align IDs
        for c in comp_dicts: c["product_id"] = "cool-widget"
        
        recommendation = engine.recommend_for(
            product_id="cool-widget",
            my_price=49.99,
            competitors_products=comp_dicts,
            merchant_currency="USD"
        )
        passed(f"Engine Recommendation: {recommendation.action} (Reason: {recommendation.reason})")

        # 3. Rules Policy
        rules = RulesAgent()
        final = rules.decide(recommendation)
        passed(f"Final Rule Action: {final.final_action} (Policy: {final.policy_reason})")

    except Exception as e:
        failed(f"Pipeline test crashed: {e}")
        import traceback; traceback.print_exc()

def test_helpers():
    header("Engine Helpers (Clamp/Percentile)")
    from pricing.pricing_engine import clamp, percentile
    try:
        assert clamp(10, 0, 5) == 5
        assert percentile([10, 20, 30], 0.5) == 20
        passed("Helpers working correctly")
    except AssertionError:
        failed("Helper check failed")

if __name__ == "__main__":
    test_helpers()
    test_full_pipeline()
