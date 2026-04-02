"""
Test script to debug each layer of the pricing pipeline independently.
Uses fake data so you don't need real API keys or a live database.

Run from inside the backend/ directory:
    python test_pipeline.py
"""

import sys
import json

# ============================================================
# COLOR HELPERS (makes terminal output readable)
# ============================================================
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

def warn(msg):
    print(f"  {YELLOW}[WARN]{RESET} — {msg}")


# ============================================================
# FAKE DATA (simulates what the scraper would return)
# ============================================================
FAKE_MY_PRODUCT_RAW = {
    "product_url": "https://mystore.com/products/cool-widget",
    "product_name": "Cool Widget",
    "current_price": "49.99",
    "old_price": "59.99",
    "currency": "USD",
    "stock_status": "in_stock",
    "image_url": "https://mystore.com/images/widget.jpg",
    "source": "json_ld",
    "scrape_confidence": "high",
    "scraped_at": "2026-04-02T12:00:00"
}

FAKE_COMPETITOR_PRODUCTS_RAW = [
    {
        "product_url": "https://competitor-a.com/products/cool-widget",
        "product_name": "Cool Widget",
        "current_price": "44.99",
        "currency": "USD",
        "stock_status": "in_stock",
        "source": "json_ld",
        "scrape_confidence": "high",
        "scraped_at": "2026-04-02T12:00:00"
    },
    {
        "product_url": "https://competitor-b.com/products/cool-widget",
        "product_name": "Cool Widget Pro",
        "current_price": "42.50",
        "currency": "USD",
        "stock_status": "in_stock",
        "source": "json_ld",
        "scrape_confidence": "high",
        "scraped_at": "2026-04-02T12:00:00"
    },
    {
        "product_url": "https://competitor-c.com/products/cool-widget",
        "product_name": "Cool Widget",
        "current_price": "47.00",
        "currency": "USD",
        "stock_status": "in_stock",
        "source": "json_ld",
        "scrape_confidence": "medium",
        "scraped_at": "2026-04-02T12:00:00"
    },
    {
        "product_url": "https://competitor-d.com/products/cool-widget",
        "product_name": "Cool Widget",
        "current_price": "46.00",
        "currency": "USD",
        "stock_status": "in_stock",
        "source": "json_ld",
        "scrape_confidence": "high",
        "scraped_at": "2026-04-02T12:00:00"
    },
    {
        "product_url": "https://competitor-e.com/products/cool-widget",
        "product_name": "Cool Widget",
        "current_price": "43.75",
        "currency": "USD",
        "stock_status": "out_of_stock",
        "source": "html",
        "scrape_confidence": "medium",
        "scraped_at": "2026-04-02T12:00:00"
    },
]

# Edge case: bad data that should be dropped
FAKE_BAD_PRODUCTS = [
    {"product_url": "https://bad.com/products/x", "current_price": None, "currency": "USD", "source": "html", "scrape_confidence": "low"},
    {"product_url": "https://bad.com/products/y", "current_price": "free", "currency": None, "source": "html", "scrape_confidence": "low"},
    {"product_url": "https://bad.com/products/z", "current_price": "-10", "currency": "USD", "source": "html", "scrape_confidence": "low"},
]


# ============================================================
# TEST 1: Normalizer
# ============================================================
def test_normalizer():
    header("Layer 2 — Normalizer")
    try:
        from normalizer.normalize_product import ProductNormalizer
        normalizer = ProductNormalizer()

        # Test single product
        norm, diag = normalizer.normalize_product(FAKE_MY_PRODUCT_RAW)
        if norm and norm.current_price == 49.99:
            passed(f"Single product normalized: price={norm.current_price}, currency={norm.currency}, id={norm.product_id}")
        else:
            failed(f"Single product normalization returned unexpected result: {norm}")

        # Test batch (good + bad)
        all_raw = FAKE_COMPETITOR_PRODUCTS_RAW + FAKE_BAD_PRODUCTS
        normalized_list, metrics = normalizer.normalize_batch(all_raw)

        passed(f"Batch normalized: {metrics['normalized_count']}/{metrics['raw_count']} kept, {metrics['dropped_count']} dropped")

        if metrics["dropped_count"] > 0:
            passed(f"Drop reasons: {metrics['drop_reasons']}")
        
        if metrics["dropped_count"] < len(FAKE_BAD_PRODUCTS):
            warn(f"Expected at least {len(FAKE_BAD_PRODUCTS)} drops but got {metrics['dropped_count']}")

        return normalized_list, metrics

    except Exception as e:
        failed(f"Normalizer crashed: {e}")
        import traceback; traceback.print_exc()
        return [], {}


# ============================================================
# TEST 2: Pricing Engine
# ============================================================
def test_pricing_engine(normalized_list):
    header("Layer 3 — Pricing Engine")
    try:
        from pricing.pricing_engine import PricingEngine

        engine = PricingEngine()
        competitor_dicts = [p.dict() for p in normalized_list]

        # First, test aggregate_competitors directly
        stats_map = engine.aggregate_competitors(competitor_dicts, merchant_currency="USD")
        
        if stats_map:
            for pid, stats in stats_map.items():
                passed(f"Product '{pid}': count={stats.count}, median={stats.median_price}, stddev={stats.stddev_price:.2f}")
        else:
            warn("No competitor stats generated. Check if product_ids match.")

        # Now test a full recommendation
        # Use "cool-widget" as the product_id (that's what the normalizer extracts from the URL path)
        recommendation = engine.recommend_for(
            product_id="cool-widget",
            my_price=49.99,
            competitors_products=competitor_dicts,
            merchant_currency="USD"
        )

        passed(f"Recommendation: action={recommendation.action}, reason={recommendation.reason}, confidence={recommendation.rec_confidence:.2f}")
        if recommendation.suggested_price:
            passed(f"Suggested price: ${recommendation.suggested_price}")

        return recommendation

    except Exception as e:
        failed(f"Pricing Engine crashed: {e}")
        import traceback; traceback.print_exc()
        return None


# ============================================================
# TEST 3: Rules Agent
# ============================================================
def test_rules_agent(recommendation):
    header("Layer 4 — Rules Agent")
    try:
        from pricing.rules_agent import RulesAgent

        rules = RulesAgent()
        final = rules.decide(recommendation)

        passed(f"Final action: {final.final_action}")
        passed(f"Policy reason: {final.policy_reason}")
        passed(f"Confidence: {final.confidence:.2f}")
        if final.suggested_price:
            passed(f"Suggested price: ${final.suggested_price}")

        return final

    except Exception as e:
        failed(f"Rules Agent crashed: {e}")
        import traceback; traceback.print_exc()
        return None


# ============================================================
# TEST 4: Clamp & Percentile helpers
# ============================================================
def test_helpers():
    header("Helper Functions (clamp, percentile)")
    try:
        from pricing.pricing_engine import clamp, percentile

        # clamp tests
        assert clamp(5.0, 0.0, 10.0) == 5.0, "clamp(5, 0, 10) should be 5"
        assert clamp(-1.0, 0.0, 10.0) == 0.0, "clamp(-1, 0, 10) should be 0"
        assert clamp(15.0, 0.0, 10.0) == 10.0, "clamp(15, 0, 10) should be 10"
        passed("clamp() works correctly")

        # percentile tests
        data = [10.0, 20.0, 30.0, 40.0, 50.0]
        p50 = percentile(data, 0.5)
        assert p50 == 30.0, f"percentile(data, 0.5) should be 30, got {p50}"
        passed(f"percentile(0.5) = {p50}")

        p_empty = percentile([], 0.5)
        assert p_empty is None, "percentile of empty list should be None"
        passed("percentile([]) = None")

    except AssertionError as e:
        failed(f"Assertion failed: {e}")
    except Exception as e:
        failed(f"Helper functions crashed: {e}")
        import traceback; traceback.print_exc()


# ============================================================
# TEST 5: Config Loader
# ============================================================
def test_config():
    header("Config Loader")
    try:
        from config import load_agents_config
        config = load_agents_config()

        if "ambiguity-agent" in config:
            passed(f"ambiguity-agent config loaded (role: {config['ambiguity-agent']['role'][:40]}...)")
        else:
            failed("ambiguity-agent key missing from config")

        if "explanation-agent" in config:
            passed(f"explanation-agent config loaded (role: {config['explanation-agent']['role'][:40]}...)")
        else:
            failed("explanation-agent key missing from config")

    except Exception as e:
        failed(f"Config loader crashed: {e}")
        import traceback; traceback.print_exc()


# ============================================================
# TEST 6: Database Models (no live DB required)
# ============================================================
def test_db_models():
    header("Database Models (import check only)")
    try:
        from db import MerchantProduct, CompetitorPrice, PricingDecision, Base

        tables = Base.metadata.tables
        passed(f"Tables defined: {list(tables.keys())}")

        # Verify all expected columns exist
        decision_cols = [c.name for c in PricingDecision.__table__.columns]
        expected = ["id", "product_id", "my_price", "action", "suggested_price", "confidence", "policy_reason", "ai_advice", "explanation", "created_at"]
        
        missing = [col for col in expected if col not in decision_cols]
        if not missing:
            passed(f"PricingDecision has all {len(expected)} expected columns")
        else:
            failed(f"PricingDecision missing columns: {missing}")

    except Exception as e:
        failed(f"DB models crashed: {e}")
        import traceback; traceback.print_exc()


# ============================================================
# TEST 7: FastAPI app (import check)
# ============================================================
def test_fastapi_import():
    header("FastAPI App (import check only)")
    try:
        # We can't fully boot the app without a real DB, but we can check the import
        from main import app, AnalyzeRequest

        routes = [r.path for r in app.routes]
        if "/analyze" in routes:
            passed(f"POST /analyze endpoint registered")
        else:
            failed(f"/analyze not found in routes: {routes}")

        # Test request model
        req = AnalyzeRequest(
            my_product_url="https://test.com/products/x",
            competitor_store_urls=["https://a.com", "https://b.com"]
        )
        passed(f"AnalyzeRequest model works: {req.my_product_url}")

    except Exception as e:
        failed(f"FastAPI import crashed: {e}")
        import traceback; traceback.print_exc()


# ============================================================
# MAIN: Run all tests
# ============================================================
if __name__ == "__main__":
    print(f"\n{CYAN}{'='*60}")
    print(f"  CMPT — Full Pipeline Debug Test")
    print(f"{'='*60}{RESET}")

    # Layer tests (no API keys needed)
    test_helpers()
    test_config()
    test_db_models()

    normalized_list, metrics = test_normalizer()
    
    if normalized_list:
        recommendation = test_pricing_engine(normalized_list)
    else:
        recommendation = None
        warn("Skipping Pricing Engine test (no normalized data)")
    
    if recommendation:
        final = test_rules_agent(recommendation)
    else:
        warn("Skipping Rules Agent test (no recommendation)")

    test_fastapi_import()

    # Summary
    print(f"\n{CYAN}{'='*60}")
    print(f"  ALL DETERMINISTIC TESTS COMPLETE")
    print(f"{'='*60}{RESET}")
    print(f"\n  {YELLOW}NOTE:{RESET} AI Agent tests (AmbiguityAgent, ExplanationAgent)")
    print(f"  require a valid GEMINI_API_KEY in your .env file.")
    print(f"  To test them, run:")
    print(f"    python test_ai_agents.py")
    print()
