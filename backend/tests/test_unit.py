"""
Assert-based unit tests for scraper extract parsing, matching, agent output,
normalizer, and pricing engine.

Run from backend/:
    pytest -q
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from normalizer.normalize_product import ProductNormalizer
from pricing.pricing_engine import PricingEngine, clamp, percentile
from pricing.rules_agent import RulesAgent
from scraper.scraper import Scraper
from utils.agent_output import parse_ambiguity_advice, parse_json_object
from utils.match import filter_matching_products, name_similarity


def _scraper_without_api():
    with patch.dict("os.environ", {"FIRECRAWL_API_KEY": "test-key"}):
        with patch("scraper.scraper.FirecrawlApp") as mock_app:
            mock_app.return_value = MagicMock()
            return Scraper()


def test_clamp_and_percentile():
    assert clamp(10, 0, 5) == 5
    assert percentile([10, 20, 30], 0.5) == 20


def test_extract_payload_preferred_over_markdown():
    scraper = _scraper_without_api()
    product = {
        "product_url": "https://shop.example/products/hoodie",
        "product_name": "Hoodie From Url",
        "current_price": None,
        "old_price": None,
        "currency": None,
        "stock_status": "unknown",
        "image_url": None,
        "source": "unknown",
        "scrape_confidence": "low",
        "scraped_at": datetime.utcnow().isoformat(),
    }
    result = {
        "extract": {
            "name": "Getaway Relaxed Hoodie",
            "price": 88,
            "currency": "USD",
            "availability": "Only 4 Left!",
            "image": "https://cdn.example/img.jpg",
        },
        "markdown": "Buy now for $1.00",
        "metadata": {"og:title": "Wrong Title"},
    }
    out = scraper._hydrate_from_result(product, result)
    assert out["source"] == "extract"
    assert out["scrape_confidence"] == "high"
    assert out["current_price"] == 88.0
    assert out["currency"] == "USD"
    assert out["product_name"] == "Getaway Relaxed Hoodie"
    assert out["stock_status"] == "in_stock"


def test_product_profile_preferred_over_json():
    scraper = _scraper_without_api()
    product = {
        "product_url": "https://shop.example/products/hoodie",
        "product_name": "Hoodie From Url",
        "current_price": None,
        "old_price": None,
        "currency": None,
        "stock_status": "unknown",
        "image_url": None,
        "source": "unknown",
        "scrape_confidence": "low",
        "scraped_at": datetime.utcnow().isoformat(),
    }
    result = {
        "product": {
            "title": "Getaway Relaxed Hoodie",
            "variants": [
                {
                    "price": {"amount": 88.0, "currency": "USD"},
                    "availability": {"in_stock": True, "text": "In stock"},
                    "images": [{"url": "https://cdn.example/img.jpg"}],
                }
            ],
        },
        "json": {"name": "Wrong", "price": 1, "currency": "USD"},
        "markdown": "Buy now for $1.00",
        "metadata": {},
    }
    out = scraper._hydrate_from_result(product, result)
    assert out["source"] == "product"
    assert out["current_price"] == 88.0
    assert out["currency"] == "USD"
    assert out["product_name"] == "Getaway Relaxed Hoodie"
    assert out["stock_status"] == "in_stock"


def test_name_similarity_and_filter():
    assert name_similarity("Cool Widget Hoodie", "Cool Widget Hoodie Black") >= 0.25
    assert name_similarity("Cool Widget", "Totally Unrelated Pants") < 0.25

    products = [
        {"product_name": "Cool Widget Hoodie"},
        {"product_name": "Kitchen Blender Pro"},
    ]
    matched, rejected = filter_matching_products("Cool Widget Hoodie", products, threshold=0.15)
    assert len(matched) == 1
    assert matched[0]["product_name"] == "Cool Widget Hoodie"
    assert len(rejected) == 1


def test_category_aware_match_keeps_hoodies():
    from utils.match import is_likely_match

    merchant = "Faded Graphic Zip Hoodie"
    assert is_likely_match(merchant, "Boohooman Oversized Washed Graphic Zip Through Hoodie")
    assert is_likely_match(merchant, "American Thrift Pullover Hoodie Washed Black")
    assert not is_likely_match(merchant, "Mens Renew Weekender Charcoal")
    assert not is_likely_match(merchant, "Babies Toddlers")


def test_product_url_ranking():
    from scraper.crawler import Crawler

    name = "Faded Graphic Zip Hoodie"
    good = Crawler.score_product_url(
        "https://shop.example.com/products/faded-graphic-zip-hoodie",
        name,
    )
    bad = Crawler.score_product_url(
        "https://shop.example.com/collections/hoodies",
        name,
    )
    assert good >= 3
    assert bad < 0


def test_merchant_slug_reconcile():
    scraper = _scraper_without_api()
    product = {
        "product_url": "https://www.allbirds.com/products/mens-tree-runners",
        "product_name": "Anytime No Show Sock",
        "current_price": 14.0,
        "currency": "USD",
        "source": "extract",
        "scrape_confidence": "high",
    }
    out = scraper._reconcile_merchant_with_slug(
        product,
        "https://www.allbirds.com/products/mens-tree-runners",
    )
    assert "Runner" in out["product_name"] or "Tree" in out["product_name"]
    assert out["scrape_confidence"] == "medium"

def test_parse_ambiguity_json_and_fallback():
    parsed = parse_json_object('```json\n{"recommended_action":"rescrape","reasoning":"thin data","confidence_in_advice":0.7}\n```')
    assert parsed["recommended_action"] == "rescrape"

    advice = parse_ambiguity_advice('{"recommended_action":"ignore_outliers","reasoning":"spike","confidence_in_advice":0.8}')
    assert advice["recommended_action"] == "ignore_outliers"
    assert advice["confidence_in_advice"] == 0.8

    fallback = parse_ambiguity_advice("not json at all")
    assert fallback["recommended_action"] == "manual_review"


def test_pipeline_reduce_and_rules():
    competitors = [
        {"product_url": "https://a.com/p/1", "product_name": "Cool Widget", "current_price": "44.99", "currency": "USD", "scrape_confidence": "high"},
        {"product_url": "https://b.com/p/2", "product_name": "Cool Widget", "current_price": "42.50", "currency": "USD", "scrape_confidence": "high"},
        {"product_url": "https://c.com/p/3", "product_name": "Cool Widget", "current_price": "47.00", "currency": "USD", "scrape_confidence": "medium"},
        {"product_url": "https://d.com/p/4", "product_name": "Cool Widget", "current_price": "46.00", "currency": "USD", "scrape_confidence": "high"},
    ]
    norm = ProductNormalizer()
    collapsed, metrics = norm.normalize_batch(competitors)
    assert metrics["normalized_count"] == 4

    eng = PricingEngine()
    comp_dicts = [c.model_dump() for c in collapsed]
    for c in comp_dicts:
        c["product_id"] = "cool-widget"

    recommendation = eng.recommend_for(
        product_id="cool-widget",
        my_price=55.0,
        competitors_products=comp_dicts,
        merchant_currency="USD",
    )
    assert recommendation.action == "reduce"
    assert recommendation.suggested_price is not None

    final = RulesAgent().decide(recommendation)
    assert final.final_action == "reduce"
    assert final.policy_reason == "requires_human_approval"


def test_insufficient_samples_with_min_two():
    eng = PricingEngine(min_sample_size=2)
    comps = [
        {"product_id": "w", "current_price": 45, "currency": "USD", "scrape_confidence": "high"},
    ]
    rec = eng.recommend_for("w", 50, comps, "USD")
    assert rec.action == "manual_review"
    assert rec.reason == "insufficient_samples"


def test_high_volatility_still_manual_review():
    competitors = [
        {"product_url": f"https://c.com/p/{i}", "product_name": "Cool Widget", "current_price": price, "currency": "USD", "scrape_confidence": "high"}
        for i, price in enumerate(["44.99", "42.50", "47.00", "46.00", "160.00"], start=1)
    ]
    norm = ProductNormalizer()
    collapsed, _ = norm.normalize_batch(competitors)
    eng = PricingEngine()
    comp_dicts = [c.model_dump() for c in collapsed]
    for c in comp_dicts:
        c["product_id"] = "cool-widget"
    recommendation = eng.recommend_for(
        product_id="cool-widget",
        my_price=49.99,
        competitors_products=comp_dicts,
        merchant_currency="USD",
    )
    assert recommendation.action == "manual_review"
    assert recommendation.reason == "high_volatility"


def test_discovery_domain_filters():
    from utils.domain import (
        brand_from_domain,
        brand_label_matches_domain,
        clean_product_name,
        domain_from_url,
        domains_match,
        is_blocked_discovery_domain,
        is_mall_fast_fashion_domain,
        is_tier_mismatch,
        product_name_from_url,
    )

    assert is_blocked_discovery_domain("www.reddit.com")
    assert is_blocked_discovery_domain("old.reddit.com")
    assert not is_blocked_discovery_domain("champion.com")
    assert domains_match("www.tentree.com", "tentree.com")
    assert domain_from_url("https://shop.tentree.com/products/foo") == "shop.tentree.com"
    assert "Hoodie" in product_name_from_url(
        "https://www.tentree.com/products/getaway-relaxed-hoodie-black"
    )
    assert clean_product_name("118553 Faded Graphic Zip Hoodie") == "Faded Graphic Zip Hoodie"
    assert is_blocked_discovery_domain("stockx.com")
    assert is_blocked_discovery_domain("www.grailed.com")
    assert brand_from_domain("www.stussy.com") == "Stussy"
    assert brand_from_domain("shop.stussy.com") == "Stussy"
    assert is_mall_fast_fashion_domain("www.hollisterco.com")
    assert is_tier_mismatch("stussy.com", "hollisterco.com")
    assert not is_tier_mismatch("hollisterco.com", "abercrombie.com")
    assert brand_label_matches_domain("Hollister", "www.hollisterco.com")
    assert brand_label_matches_domain("Represent", "representclo.com")


def test_peer_brand_context_parsing():
    from unittest.mock import MagicMock, patch

    with patch.dict("os.environ", {"FIRECRAWL_API_KEY": "test-key", "GEMINI_API_KEY": "test"}):
        with patch("scraper.crawler.FirecrawlApp") as mock_app:
            with patch("scraper.crawler.LLM") as mock_llm_cls:
                mock_app.return_value = MagicMock()
                mock_llm = MagicMock()
                mock_llm_cls.return_value = mock_llm
                mock_llm.call.return_value = """```json
{
  "positioning": "streetwear mid-premium",
  "peer_brands": ["Represent", "Carhartt WIP", "Obey"],
  "avoid_brands": ["Hollister", "Shein"],
  "search_queries": ["Represent official store buy"]
}
```"""
                from scraper.crawler import Crawler

                crawler = Crawler()
                ctx = crawler._get_peer_brand_context(
                    "Stussy",
                    "Faded Graphic Zip Hoodie",
                    merchant_price=150,
                    currency="USD",
                    merchant_domain="stussy.com",
                )
                assert ctx["positioning"] == "streetwear mid-premium"
                assert "Represent" in ctx["peer_brands"]
                assert "Hollister" in ctx["avoid_brands"]
                assert ctx["search_queries"][0] == "Represent official store buy"


def test_discover_skips_tier_mismatch():
    from unittest.mock import MagicMock, patch

    with patch.dict("os.environ", {"FIRECRAWL_API_KEY": "test-key", "GEMINI_API_KEY": "test"}):
        with patch("scraper.crawler.FirecrawlApp") as mock_app:
            with patch("scraper.crawler.LLM") as mock_llm_cls:
                mock_fc = MagicMock()
                mock_app.return_value = mock_fc
                mock_llm_cls.return_value = MagicMock()
                mock_fc.search.return_value = {
                    "data": [
                        {"url": "https://www.hollisterco.com/shop/us/p/hoodie"},
                        {"url": "https://representclo.com/products/essential-hoodie-black"},
                    ]
                }
                from scraper.crawler import Crawler

                crawler = Crawler()
                crawler._get_peer_brand_context = MagicMock(
                    return_value={
                        "positioning": "streetwear",
                        "peer_brands": ["Represent"],
                        "avoid_brands": ["Hollister"],
                        "search_queries": [],
                    }
                )
                results = crawler.discover_competitor_stores(
                    "Faded Graphic Zip Hoodie",
                    max_results=5,
                    merchant_brand="Stussy",
                    merchant_domain="stussy.com",
                    merchant_price=150,
                    currency="USD",
                    fast=False,
                )
                stores = {r["store"] for r in results}
                assert not any("hollister" in s.lower() for s in stores)
                assert any("represent" in s.lower() for s in stores)


def test_clean_urls_keeps_collection_products():
    scraper = _scraper_without_api()
    urls = scraper.clean_product_urls([
        "https://www.stussy.com/collections/sweats/products/118553-hoodie",
        "https://shop.com/collections/hoodies",
        "https://shop.com/products/ok",
        "https://shop.com/cart",
    ])
    assert any("118553-hoodie" in u for u in urls)
    assert any(u.endswith("/products/ok") for u in urls)
    assert not any(u.rstrip("/").endswith("/hoodies") for u in urls)
    assert not any("/cart" in u for u in urls)


def test_markdown_prefers_retail_price_over_order_total():
    scraper = _scraper_without_api()
    price, currency = scraper._extract_price_currency_from_text(
        "Order total $58,425.58  Buy now $149.00",
        "https://shop.example.com/products/hoodie",
    )
    assert price == 149.0
    assert currency == "USD"
    assert scraper._is_plausible_retail_price(149)
    assert not scraper._is_plausible_retail_price(58425.58)


def test_fixed_search_query_ladder():
    from unittest.mock import MagicMock, patch

    with patch.dict("os.environ", {"FIRECRAWL_API_KEY": "test-key", "GEMINI_API_KEY": "test"}):
        with patch("scraper.crawler.FirecrawlApp") as mock_app:
            with patch("scraper.crawler.LLM"):
                mock_app.return_value = MagicMock()
                from scraper.crawler import Crawler

                crawler = Crawler()
                queries = crawler._fixed_search_queries(
                    "118553 Faded Graphic Zip Hoodie Washed Olive"
                )
                assert queries[0] == "Faded Graphic Zip Hoodie Washed Olive"
                assert "Washed Olive" not in queries[1] or "Faded Graphic Zip Hoodie" in queries[1]
                assert any("hoodie" in q.lower() or "zip" in q.lower() for q in queries)
