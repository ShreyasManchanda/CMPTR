import os
import re
import logging
import unicodedata
import time
from typing import List, Any
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)


CURRENCY_SYMBOL_MAP = {
    "$": "USD",
    "\u00a3": "GBP",
    "\u20ac": "EUR",
    "\u00a5": "JPY",
    "\u20b9": "INR",
}


class Scraper:
    """Scrapes product data from e-commerce pages via Firecrawl."""

    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL_API_KEY not set")
        self.firecrawl = FirecrawlApp(api_key=api_key)

    def _to_float(self, value: Any):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip().replace(",", "")
            cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
            if not cleaned:
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    def _extract_price_currency_from_text(self, text: str):
        if not text:
            return None, None

        # Normalize common mojibake and unicode variants before regex matching.
        text = (
            text.replace("\u00e2\u201a\u00b9", "\u20b9")
            .replace("\u00e2\u201a\u00ac", "\u20ac")
            .replace("\u00c2\u00a3", "\u00a3")
            .replace("\u00c2\u00a5", "\u00a5")
            .replace("\u00c2$", "$")
        )
        text = unicodedata.normalize("NFKC", text)

        price_match = re.search(
            r"(?:CA|AU|US)?([\$\u00a3\u20ac\u00a5\u20b9])\s*([\d,]+(?:\.\d{1,2})?)"
            r"|(USD|EUR|GBP|INR|CAD|AUD|JPY|CNY|CHF)\s*([\d,]+(?:\.\d{1,2})?)"
            r"|(?:RS|INR)\.?\s*([\d,]+(?:\.\d{1,2})?)"
            r"|([\d,]+(?:\.\d{1,2})?)\s*(USD|EUR|GBP|INR|CAD|AUD|JPY|CNY|CHF)",
            text,
            re.IGNORECASE,
        )

        if not price_match:
            return None, None

        # Group mapping:
        # 1/2 => symbol + value
        # 3/4 => code + value
        # 5   => RS/INR prefixed value
        # 6/7 => value + code
        symbol_or_code = price_match.group(1) or price_match.group(3) or price_match.group(7)
        value_str = price_match.group(2) or price_match.group(4) or price_match.group(5) or price_match.group(6)

        price = self._to_float(value_str)
        if price is None:
            return None, None

        if price_match.group(5) and not symbol_or_code:
            symbol_or_code = "INR"

        if symbol_or_code in CURRENCY_SYMBOL_MAP:
            currency = CURRENCY_SYMBOL_MAP[symbol_or_code]
        else:
            currency = str(symbol_or_code).upper() if symbol_or_code else None

        return price, currency

    def _fallback_name_from_url(self, product_url: str):
        path = (urlparse(product_url).path or "").strip("/")
        if not path:
            return None
        slug = path.split("/")[-1]
        slug = slug.replace("-", " ").replace("_", " ")
        slug = re.sub(r"\s+", " ", slug).strip()
        return slug.title() if slug else None

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

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                result = self.firecrawl.scrape_url(
                    product_url,
                    formats=["markdown", "extract"],
                    extract={
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "number"},
                                "currency": {"type": "string"},
                                "availability": {"type": "string"},
                                "image": {"type": "string"},
                            },
                        }
                    },
                )
                break
            except Exception as e:
                error_str = str(e).lower()
                is_transient = "502" in error_str or "503" in error_str or "504" in error_str or "timeout" in error_str or "gateway" in error_str
                
                if is_transient and attempt < max_retries - 1:
                    logger.warning(f"Firecrawl transient error for {product_url} (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"Firecrawl scrape failed for {product_url} after {attempt + 1} attempts: {e}")
                    return product

        if not result:
            return product

        if hasattr(result, "model_dump"):
            result = result.model_dump()
        elif not isinstance(result, dict):
            logger.warning(f"Unexpected Firecrawl result type: {type(result)}")
            return product

        # Firecrawl may return fields nested under `data`.
        if isinstance(result.get("data"), dict):
            nested = result["data"]
            if not result.get("markdown") and nested.get("markdown"):
                result["markdown"] = nested.get("markdown")
            if not result.get("text") and nested.get("text"):
                result["text"] = nested.get("text")
            if not result.get("metadata") and nested.get("metadata"):
                result["metadata"] = nested.get("metadata")
            if not result.get("structured_data") and nested.get("structured_data"):
                result["structured_data"] = nested.get("structured_data")

        markdown = result.get("markdown") or result.get("text") or ""
        metadata = result.get("metadata", {}) or {}

        structured = result.get("structured_data")
        if isinstance(structured, list):
            structured = next((x for x in structured if isinstance(x, dict)), None)

        if isinstance(structured, dict):
            offers = structured.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if not isinstance(offers, dict):
                offers = {}

            product["product_name"] = structured.get("name") or metadata.get("og:title")
            product["image_url"] = structured.get("image") or metadata.get("og:image")

            product["current_price"] = self._to_float(offers.get("price"))
            product["old_price"] = self._to_float(offers.get("highPrice"))
            product["currency"] = offers.get("priceCurrency") or metadata.get("og:price:currency")
            if isinstance(product["currency"], str):
                product["currency"] = product["currency"].upper().strip()

            availability = str(offers.get("availability", "")).lower()
            if "instock" in availability or "in_stock" in availability:
                product["stock_status"] = "in_stock"
            elif "outofstock" in availability or "out_of_stock" in availability:
                product["stock_status"] = "out_of_stock"

            if product["current_price"] is not None:
                product["source"] = "json_ld"
                product["scrape_confidence"] = "high"
                return product

        og_price = (
            metadata.get("og:price:amount")
            or metadata.get("product:price:amount")
            or metadata.get("twitter:data1")
        )
        if og_price is not None:
            product["product_name"] = product["product_name"] or metadata.get("og:title") or metadata.get("title")
            product["image_url"] = product["image_url"] or metadata.get("og:image") or metadata.get("image")
            product["current_price"] = self._to_float(og_price)
            product["currency"] = (
                metadata.get("og:price:currency")
                or metadata.get("product:price:currency")
                or metadata.get("twitter:label1")
            )
            if isinstance(product["currency"], str):
                product["currency"] = product["currency"].upper().strip()

            text_l = markdown.lower()
            if "add to cart" in text_l or "add to bag" in text_l or "in stock" in text_l:
                product["stock_status"] = "in_stock"
            elif "out of stock" in text_l or "sold out" in text_l:
                product["stock_status"] = "out_of_stock"

            if product["current_price"] is not None:
                product["source"] = "opengraph"
                product["scrape_confidence"] = "high"
                return product

        product["product_name"] = product["product_name"] or metadata.get("og:title") or metadata.get("title")
        product["image_url"] = product["image_url"] or metadata.get("og:image") or metadata.get("image")

        text_lower = markdown.lower()
        if "add to cart" in text_lower or "add to bag" in text_lower or "in stock" in text_lower:
            product["stock_status"] = "in_stock"
        elif "out of stock" in text_lower or "sold out" in text_lower:
            product["stock_status"] = "out_of_stock"

        if product["current_price"] is None and markdown:
            parsed_price, parsed_currency = self._extract_price_currency_from_text(markdown)
            product["current_price"] = parsed_price
            product["currency"] = product["currency"] or parsed_currency
        elif product["current_price"] is not None and not product["currency"]:
            _, parsed_currency = self._extract_price_currency_from_text(markdown)
            product["currency"] = parsed_currency

        if not product["product_name"]:
            product["product_name"] = self._fallback_name_from_url(product_url)

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