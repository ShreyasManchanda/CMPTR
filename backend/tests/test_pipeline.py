"""
Deterministic pipeline tests — Normalizer, Pricing Engine, and Rules Agent.

Run from backend/:
    python tests/test_pipeline.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import header, passed, failed

FAKE_COMPETITORS = [
    {"product_url": "https://comp-a.com/p/1", "product_name": "Cool Widget", "current_price": "44.99", "currency": "USD", "scrape_confidence": "high"},
    {"product_url": "https://comp-b.com/p/2", "product_name": "Cool Widget", "current_price": "42.50", "currency": "USD", "scrape_confidence": "high"},
    {"product_url": "https://comp-c.com/p/3", "product_name": "Cool Widget", "current_price": "47.00", "currency": "USD", "scrape_confidence": "medium"},
    {"product_url": "https://comp-d.com/p/4", "product_name": "Cool Widget", "current_price": "46.00", "currency": "USD", "scrape_confidence": "high"},
    {"product_url": "https://comp-e.com/p/5", "product_name": "Cool Widget", "current_price": "160.00", "currency": "USD", "scrape_confidence": "high"},
]


def test_full_pipeline():
    header("Full Deterministic Pipeline")
    try:
        from normalizer.normalize_product import ProductNormalizer
        from pricing.pricing_engine import PricingEngine
        from pricing.rules_agent import RulesAgent

        norm = ProductNormalizer()
        collapsed_comps, metrics = norm.normalize_batch(FAKE_COMPETITORS)
        passed(f"Normalized {metrics['normalized_count']} items")

        engine = PricingEngine()
        comp_dicts = [c.model_dump() for c in collapsed_comps]
        for c in comp_dicts:
            c["product_id"] = "cool-widget"

        recommendation = engine.recommend_for(
            product_id="cool-widget",
            my_price=49.99,
            competitors_products=comp_dicts,
            merchant_currency="USD",
        )
        passed(f"Engine Recommendation: {recommendation.action} (Reason: {recommendation.reason})")

        rules = RulesAgent()
        final = rules.decide(recommendation)
        passed(f"Final Rule Action: {final.final_action} (Policy: {final.policy_reason})")

    except Exception as e:
        failed(f"Pipeline test crashed: {e}")
        import traceback
        traceback.print_exc()


def test_helpers():
    header("Engine Helpers (Clamp/Percentile)")
    from pricing.pricing_engine import clamp, percentile
    assert clamp(10, 0, 5) == 5
    assert percentile([10, 20, 30], 0.5) == 20
    passed("Helpers working correctly")


if __name__ == "__main__":
    test_helpers()
    test_full_pipeline()
