from typing import List
import os
from firecrawl import Firecrawl
from urllib.parse import urlparse, urlunparse
from datetime import datetime


class Scraper():
    """
    scrapes from the shopify stores
    """
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL API KEY not set")

        self.firecrawl = Firecrawl(api_key)

    def scrape_product(self, product_url : str) -> dict:
        product = {
            "product_url" : product_url,
            "product_name" : None, 
            "current_price" : None,
            "old_price" : None,
            "currency" : None,
            "stock_status" : "unknown",
            "image_url": None,
            "source": "unknown",
            "scrape_confidence": "low",
            "scraped_at": datetime.utcnow().isoformat()
        }

        try:
            result = self.firecrawl.scrape(product_url)
        except Exception:
            return product
        
        if not result:
            return product

        # --- preferred path: structured data (JSON-LD) ---
        structured = result.get("structured_data")
        if structured:
            offers = structured.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            product["product_name"] = structured.get("name")
            product["scrape_confidence"] = "high"
            product["current_price"] = offers.get("price")
            if product["current_price"] is None:
                product["scrape_confidence"] = "medium"
            product["currency"] = offers.get("priceCurrency")
            product["image_url"] = structured.get("image")

            availability = offers.get("availability", "").lower()
            if "instock" in availability:
                product["stock_status"] = "in_stock"
            elif "outofstock" in availability:
                product["stock_status"] = "out_of_stock"

            product["source"] = "json_ld"
            return product

        # --- fallback path: weak HTML/text signals ---
        text = (result.get("text") or "").lower()

        if "out of stock" in text:
            product["stock_status"] = "out_of_stock"

        product["source"] = "html"
        product["scrape_confidence"] = "medium"

        return product

    def clean_product_urls(self, urls: list[str]) -> list[str]:
        clean_urls = set()
        for url in urls:
            if not url:
                continue
            if "/products/" not in url:
                continue
            if any(x in url for x in [".json", "/cart", "/search"]):
                continue
            parsed = urlparse(url)
            normalized = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, "", "", "")
            )
            clean_urls.add(normalized)
        return list(clean_urls)



    def batch_scrape_products(
        self,
        product_urls: List[str],
        batch_size: int = 5
    ) -> tuple[list[dict], dict]:
    
        cleaned_urls = self.clean_product_urls(product_urls)
        results = []
        stats = {
            "product_urls": len(product_urls),
            "valid_product_urls": len(cleaned_urls),
            "scraped": 0,
            "low_confidence": 0,
            "failed": 0
        }
    
        for i in range(0, len(cleaned_urls), batch_size):
            batch = cleaned_urls[i : i + batch_size]
    
            for url in batch:
                try:
                    product = self.scrape_product(url)
                    results.append(product)
                    stats["scraped"] += 1
    
                    if product.get("scrape_confidence") == "low":
                        stats["low_confidence"] += 1
    
                except Exception:
                    results.append({
                        "product_url": url,
                        "scrape_confidence": "low",
                        "source": "exception"
                    })
                    stats["failed"] += 1
    
        return results, stats










