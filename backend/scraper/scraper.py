import os
import re
import logging
from typing import List
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)


class Scraper:
    """Scrapes product data from any e-commerce store via Firecrawl."""

    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL_API_KEY not set")
        self.firecrawl = FirecrawlApp(api_key=api_key)

    def scrape_product(self, product_url: str) -> dict:
        product = {
            "product_url": product_url,
            "product_name": None,
            "current_price": None,
            "old_price": None,
            "currency": None,
            "stock_status": "unknown",
            "image_url": None,
            "source": "unknown",
            "scrape_confidence": "low",
            "scraped_at": datetime.utcnow().isoformat(),
        }

        try:
            result = self.firecrawl.scrape_url(product_url)
        except Exception as e:
            logger.error(f"Firecrawl scrape failed for {product_url}: {e}")
            return product

        if not result:
            return product

        # Firecrawl SDK returns a dict; normalize if needed
        if isinstance(result, dict):
            pass
        elif hasattr(result, "model_dump"):
            result = result.model_dump()
        else:
            logger.warning(f"Unexpected Firecrawl result type: {type(result)}")
            return product

        # Preferred path: structured data (JSON-LD)
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

        # Secondary path: OpenGraph metadata
        metadata = result.get("metadata", {})
        if metadata and metadata.get("og:price:amount"):
            product["product_name"] = metadata.get("og:title")
            product["scrape_confidence"] = "high"
            try:
                product["current_price"] = float(metadata.get("og:price:amount"))
            except (ValueError, TypeError):
                pass
            product["currency"] = metadata.get("og:price:currency")
            product["image_url"] = metadata.get("og:image")

            product["stock_status"] = "unknown"
            text = (result.get("markdown") or "").lower()
            if "add to cart" in text or "add to bag" in text or "in stock" in text:
                product["stock_status"] = "in_stock"
            elif "out of stock" in text or "sold out" in text:
                product["stock_status"] = "out_of_stock"

            product["source"] = "opengraph"
            return product

        # Fallback path: weak HTML/text signals
        text = result.get("markdown") or result.get("text") or ""
        metadata = result.get("metadata", {})

        if metadata:
            product["product_name"] = metadata.get("og:title") or metadata.get("title")
            product["image_url"] = metadata.get("og:image") or metadata.get("image")

        text_lower = text.lower()
        if "add to cart" in text_lower or "add to bag" in text_lower or "in stock" in text_lower:
            product["stock_status"] = "in_stock"
        elif "out of stock" in text_lower or "sold out" in text_lower:
            product["stock_status"] = "out_of_stock"

        if product["current_price"] is None and text:
            price_match = re.search(
                r'(?:CA|AU|US)?([\$£€¥₹])\s*([\d,]+(?:\.\d{2})?)'
                r'|(USD|EUR|GBP|INR|CAD|AUD)\s+([\d,]+(?:\.\d{2})?)'
                r'|([\d,]+(?:\.\d{2})?)\s*(USD|EUR|GBP|INR|CAD|AUD)',
                text,
                re.IGNORECASE,
            )
            if price_match:
                sym = price_match.group(1) or price_match.group(3) or price_match.group(6)
                val_str = price_match.group(2) or price_match.group(4) or price_match.group(5)
                if val_str:
                    val_str = val_str.replace(',', '')
                    try:
                        product["current_price"] = float(val_str)
                        if sym:
                            product["currency"] = sym.upper()
                    except ValueError:
                        pass

        if product.get("current_price") is not None:
            product["source"] = "markdown_fallback"
            product["scrape_confidence"] = "medium"
        else:
            product["source"] = "html"
            product["scrape_confidence"] = "low"

        return product

    def clean_product_urls(self, urls: list[str]) -> list[str]:
        clean_urls = set()
        for url in urls:
            if not url:
                continue
            if any(x in url for x in [".json", "/cart", "/search", "/collections/"]):
                continue
            parsed = urlparse(url)
            normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
            clean_urls.add(normalized)
        return list(clean_urls)

    def batch_scrape_products(
        self,
        product_urls: List[str],
        batch_size: int = 5,
    ) -> tuple[list[dict], dict]:
        cleaned_urls = self.clean_product_urls(product_urls)
        results = []
        stats = {
            "product_urls": len(product_urls),
            "valid_product_urls": len(cleaned_urls),
            "scraped": 0,
            "low_confidence": 0,
            "failed": 0,
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
                except Exception as e:
                    logger.error(f"Batch scrape failed for {url}: {e}")
                    results.append({
                        "product_url": url,
                        "scrape_confidence": "low",
                        "source": "exception",
                    })
                    stats["failed"] += 1

        return results, stats
