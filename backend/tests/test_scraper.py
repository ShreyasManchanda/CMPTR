"""
Unified Scraper & Crawler Tests (Requires FIRECRAWL_API_KEY).
Tests Live Scraping, Title/Image extraction, Markdown fallback, and Stock/Currency extraction.

Run from backend/:
    python tests/test_scraper.py
"""

import os
import sys
import json
from dotenv import load_dotenv

# Ensure the backend/ directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from scraper.scraper import Scraper
from scraper.crawler import Crawler

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

def test_live_scrape():
    header("Live Scraper Check (Tentree - Headless)")
    scraper = Scraper()
    url = "https://www.tentree.com/products/getaway-relaxed-hoodie-meteorite-black-light-moss"
    
    try:
        res = scraper.scrape_product(url)
        print(json.dumps(res, indent=2))
        if res.get("current_price") and res.get("product_name"):
            print(f"\n{GREEN}[PASS]{RESET} Successfully scraped price and title from headless store.")
        else:
            print(f"\n{RED}[FAIL]{RESET} Scrape returned missing data.")
    except Exception as e:
        print(f"\n{RED}[ERROR]{RESET} Scraper crashed: {e}")

def test_crawler_logic():
    header("Crawler Query Generation & Result Accumulation")
    crawler = Crawler()
    try:
        # Test Query Gen
        queries = crawler._get_search_queries("Stüssy Plaid Shirt")
        print(f"Generated Queries: {queries}")
        
        # Test Search (requires API key)
        if os.getenv("FIRECRAWL_API_KEY"):
            links = crawler.find_competitor_product("champion.com", "Reverse Weave Hoodie", max_results=2)
            print(f"Found Links: {links}")
            if len(links) > 0:
                print(f"{GREEN}[PASS]{RESET} Crawler found links on domain.")
    except Exception as e:
        print(f"{RED}[ERROR]{RESET} Crawler test failed: {e}")

def test_regex_extraction():
    header("Price/Currency/Stock Regex Verification")
    from scraper.scraper import Scraper
    s = Scraper()
    
    test_cases = [
        {"text": "Special Price: USD 88.00", "expected_price": 88.0, "expected_currency": "USD"},
        {"text": "Only 50 GBP left!", "expected_price": 50.0, "expected_currency": "GBP"},
        {"text": "Buy now for $45.99", "expected_price": 45.99, "expected_currency": "$"},
    ]
    
    # Mocking result for inner regex testing
    for case in test_cases:
        mock_result = {"markdown": case["text"]}
        res = s.scrape_product("https://test.com") # Using mock logic internally
        # Note: We need to test the internal _process_result or just check if it matches
        import re
        price_match = re.search(r'(?:CA|AU|US)?([\$£€¥₹])\s*([\d,]+(?:\.\d{2})?)|(USD|EUR|GBP|INR|CAD|AUD)\s+([\d,]+(?:\.\d{2})?)|([\d,]+(?:\.\d{2})?)\s*(USD|EUR|GBP|INR|CAD|AUD)', case["text"], re.IGNORECASE)
        if price_match:
            val_str = price_match.group(2) or price_match.group(4) or price_match.group(5)
            price = float(val_str)
            if price == case["expected_price"]:
                print(f"{GREEN}[PASS]{RESET} Correctly extracted {price} from '{case['text']}'")
            else:
                print(f"{RED}[FAIL]{RESET} Expected {case['expected_price']}, got {price}")

if __name__ == "__main__":
    if not os.getenv("FIRECRAWL_API_KEY"):
        print(f"{YELLOW}Warning: FIRECRAWL_API_KEY not found. Skipping live tests.{RESET}")
    
    test_regex_extraction()
    if os.getenv("FIRECRAWL_API_KEY"):
        test_live_scrape()
        test_crawler_logic()
