"""
Scraper & Crawler tests (requires FIRECRAWL_API_KEY).

Run from backend/:
    python tests/test_scraper.py
"""

import os
import re
import sys
import json

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from tests.helpers import header, passed, failed, GREEN, RED, YELLOW, RESET
from scraper.scraper import Scraper
from scraper.crawler import Crawler


def test_live_scrape():
    header("Live Scraper Check (Tentree - Headless)")
    scraper = Scraper()
    url = "https://www.tentree.com/products/getaway-relaxed-hoodie-meteorite-black-light-moss"

    try:
        res = scraper.scrape_product(url)
        print(json.dumps(res, indent=2))
        if res.get("current_price") and res.get("product_name"):
            passed("Successfully scraped price and title from headless store.")
        else:
            failed("Scrape returned missing data.")
    except Exception as e:
        failed(f"Scraper crashed: {e}")


def test_crawler_logic():
    header("Crawler Query Generation & Result Accumulation")
    crawler = Crawler()
    try:
        queries = crawler._get_search_queries("Stüssy Plaid Shirt")
        print(f"Generated Queries: {queries}")

        if os.getenv("FIRECRAWL_API_KEY"):
            links = crawler.find_competitor_product("champion.com", "Reverse Weave Hoodie", max_results=2)
            print(f"Found Links: {links}")
            if len(links) > 0:
                passed("Crawler found links on domain.")

            suggestions = crawler.discover_competitor_stores("Cool Widget", max_results=3)
            print(f"Discovered competitor stores: {suggestions}")
            if len(suggestions) > 0:
                passed("Discovery returned competitor store suggestions.")
    except Exception as e:
        failed(f"Crawler test failed: {e}")


def test_regex_extraction():
    header("Price/Currency/Stock Regex Verification")

    test_cases = [
        {"text": "Special Price: USD 88.00", "expected_price": 88.0},
        {"text": "Only 50 GBP left!", "expected_price": 50.0},
        {"text": "Buy now for $45.99", "expected_price": 45.99},
    ]

    for case in test_cases:
        price_match = re.search(
            r'(?:CA|AU|US)?([\$£€¥₹])\s*([\d,]+(?:\.\d{2})?)'
            r'|(USD|EUR|GBP|INR|CAD|AUD)\s+([\d,]+(?:\.\d{2})?)'
            r'|([\d,]+(?:\.\d{2})?)\s*(USD|EUR|GBP|INR|CAD|AUD)',
            case["text"],
            re.IGNORECASE,
        )
        if price_match:
            val_str = price_match.group(2) or price_match.group(4) or price_match.group(5)
            price = float(val_str)
            if price == case["expected_price"]:
                passed(f"Correctly extracted {price} from '{case['text']}'")
            else:
                failed(f"Expected {case['expected_price']}, got {price}")


if __name__ == "__main__":
    if not os.getenv("FIRECRAWL_API_KEY"):
        print(f"{YELLOW}Warning: FIRECRAWL_API_KEY not found. Skipping live tests.{RESET}")

    test_regex_extraction()
    if os.getenv("FIRECRAWL_API_KEY"):
        test_live_scrape()
        test_crawler_logic()
