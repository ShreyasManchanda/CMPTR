import os
import re
import math
import logging
import unicodedata
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Any, Optional
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from firecrawl import FirecrawlApp

from utils.domain import clean_product_name

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
            if not cleaned or cleaned.count(".") > 1:
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    def _currency_from_domain(self, product_url: str | None, symbol_or_code: str | None) -> str | None:
        """Disambiguate bare `$` using store domain (AU/CA often use $ for local currency)."""
        if not symbol_or_code:
            return None
        if symbol_or_code in CURRENCY_SYMBOL_MAP:
            mapped = CURRENCY_SYMBOL_MAP[symbol_or_code]
        else:
            mapped = str(symbol_or_code).upper().strip()

        if mapped != "USD" and symbol_or_code != "$":
            return mapped

        host = (urlparse(product_url or "").netloc or "").lower()
        if host.endswith(".com.au") or host.endswith(".au") or "culturekings" in host:
            return "AUD"
        if host.endswith(".ca") or host.startswith("ca."):
            return "CAD"
        if host.endswith(".co.uk") or host.endswith(".uk"):
            return "GBP"
        return mapped

    def _extract_price_currency_from_text(self, text: str, product_url: str | None = None):
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

        pattern = re.compile(
            r"(?:(CA|AU|US)\s*)?([\$\u00a3\u20ac\u00a5\u20b9])\s*([\d,]+(?:\.\d{1,2})?)"
            r"|(USD|EUR|GBP|INR|CAD|AUD|JPY|CNY|CHF)\s*([\d,]+(?:\.\d{1,2})?)"
            r"|(?:RS|INR)\.?\s*([\d,]+(?:\.\d{1,2})?)"
            r"|([\d,]+(?:\.\d{1,2})?)\s*(USD|EUR|GBP|INR|CAD|AUD|JPY|CNY|CHF)",
            re.IGNORECASE,
        )

        candidates: list[tuple[float, str | None]] = []
        for price_match in pattern.finditer(text):
            prefix = price_match.group(1)
            symbol = price_match.group(2)
            code = price_match.group(4) or price_match.group(8)
            value_str = (
                price_match.group(3)
                or price_match.group(5)
                or price_match.group(6)
                or price_match.group(7)
            )
            price = self._to_float(value_str)
            if price is None or price <= 0:
                continue

            if price_match.group(6) and not symbol and not code:
                symbol_or_code = "INR"
            elif prefix:
                symbol_or_code = {"CA": "CAD", "AU": "AUD", "US": "USD"}.get(prefix.upper(), symbol or code)
            else:
                symbol_or_code = symbol or code

            currency = self._currency_from_domain(product_url, symbol_or_code)
            candidates.append((price, currency))

        if not candidates:
            return None, None

        # Prefer realistic single-item retail prices over order totals / junk numbers.
        plausible = [c for c in candidates if 5 <= c[0] <= 2500]
        chosen = plausible[0] if plausible else min(candidates, key=lambda c: abs(math.log10(max(c[0], 1)) - 2))
        return chosen

    def _fallback_name_from_url(self, product_url: str):
        path = (urlparse(product_url).path or "").strip("/")
        if not path:
            return None
        slug = path.split("/")[-1]
        slug = slug.replace("-", " ").replace("_", " ")
        slug = re.sub(r"\s+", " ", slug).strip()
        return slug.title() if slug else None

    def _apply_availability(self, product: dict, availability: Any) -> None:
        """Map free-text or schema.org availability into stock_status."""
        if availability is None:
            return
        text = str(availability).lower()
        if any(x in text for x in ("outofstock", "out_of_stock", "out of stock", "sold out")):
            product["stock_status"] = "out_of_stock"
        elif any(
            x in text
            for x in (
                "instock",
                "in_stock",
                "in stock",
                "add to cart",
                "add to bag",
                "only",
                "left",
                "available",
            )
        ):
            product["stock_status"] = "in_stock"

    def _apply_flat_extract(self, product: dict, payload: dict, metadata: dict) -> None:
        """Apply Firecrawl extract/json flat schema fields onto product dict."""
        product["product_name"] = (
            payload.get("name")
            or payload.get("product_name")
            or product.get("product_name")
            or metadata.get("og:title")
        )
        image = payload.get("image") or payload.get("image_url")
        if isinstance(image, list):
            image = image[0] if image else None
        product["image_url"] = image or product.get("image_url") or metadata.get("og:image")

        product["current_price"] = self._to_float(
            payload.get("price") if payload.get("price") is not None else payload.get("current_price")
        )
        product["old_price"] = self._to_float(payload.get("old_price") or payload.get("highPrice"))

        currency = payload.get("currency") or payload.get("priceCurrency")
        if isinstance(currency, str):
            product["currency"] = currency.upper().strip()
        elif product.get("currency") is None:
            product["currency"] = None

        self._apply_availability(product, payload.get("availability") or payload.get("stock_status"))

    def _apply_product_profile(self, product: dict, profile: dict, metadata: dict) -> bool:
        """Apply Firecrawl v2 deterministic `product` format onto product dict."""
        if not isinstance(profile, dict):
            return False

        title = profile.get("title")
        if title:
            product["product_name"] = title

        variants = profile.get("variants") or []
        chosen = None
        for variant in variants:
            if not isinstance(variant, dict):
                continue
            availability = variant.get("availability") or {}
            in_stock = True
            if isinstance(availability, dict):
                if "in_stock" in availability:
                    in_stock = bool(availability.get("in_stock"))
                elif "inStock" in availability:
                    in_stock = bool(availability.get("inStock"))
            price_obj = variant.get("price") or {}
            amount = None
            if isinstance(price_obj, dict):
                amount = price_obj.get("amount")
            elif isinstance(price_obj, (int, float)):
                amount = price_obj
            if amount is None:
                continue
            if chosen is None or in_stock:
                chosen = variant
                if in_stock:
                    break

        if chosen:
            price_obj = chosen.get("price") or {}
            if isinstance(price_obj, dict):
                product["current_price"] = self._to_float(price_obj.get("amount"))
                currency = price_obj.get("currency")
                if isinstance(currency, str):
                    product["currency"] = currency.upper().strip()
            sale = chosen.get("sale") or {}
            if isinstance(sale, dict):
                original = sale.get("original_price") or sale.get("originalPrice") or {}
                if isinstance(original, dict):
                    product["old_price"] = self._to_float(original.get("amount"))
            availability = chosen.get("availability")
            if isinstance(availability, dict):
                if availability.get("in_stock") is True or availability.get("inStock") is True:
                    product["stock_status"] = "in_stock"
                elif availability.get("in_stock") is False or availability.get("inStock") is False:
                    product["stock_status"] = "out_of_stock"
                else:
                    self._apply_availability(product, availability.get("text"))
            images = chosen.get("images") or []
            if images and isinstance(images[0], dict):
                product["image_url"] = images[0].get("url") or product.get("image_url")
            elif images and isinstance(images[0], str):
                product["image_url"] = images[0]

        if not product.get("image_url"):
            product["image_url"] = product.get("image_url") or metadata.get("og:image")

        return product.get("current_price") is not None

    # Firecrawl v2: schema lives inside formats=[{type: json, schema: ...}]
    _JSON_EXTRACT_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"},
            "currency": {"type": "string"},
            "availability": {"type": "string"},
            "image": {"type": "string"},
        },
    }

    @staticmethod
    def _is_rate_limited(error: Exception) -> bool:
        text = str(error).lower()
        return "rate limit" in text or "429" in text

    @staticmethod
    def _retry_after_seconds(error: Exception, default: float = 5.0) -> float:
        match = re.search(r"retry after\s+(\d+(?:\.\d+)?)\s*s", str(error), re.IGNORECASE)
        if match:
            return max(float(match.group(1)), 1.0)
        return default

    def _firecrawl_scrape(self, product_url: str, *, with_extract: bool):
        """Call Firecrawl v2 scrape. Retries transient and rate-limit errors."""
        max_retries = 4
        retry_delay = 2.0
        result = None

        # v2: use deterministic "product" format + optional JSON schema extract.
        # Legacy v1 kwargs (formats=["extract"], extract=...) are rejected by SDK 4.x.
        if with_extract:
            formats = [
                "markdown",
                "product",
                {"type": "json", "schema": self._JSON_EXTRACT_SCHEMA},
            ]
        else:
            formats = ["markdown"]

        for attempt in range(max_retries):
            try:
                result = self.firecrawl.scrape(product_url, formats=formats)
                break
            except Exception as e:
                error_str = str(e).lower()
                is_transient = (
                    "502" in error_str
                    or "503" in error_str
                    or "504" in error_str
                    or "timeout" in error_str
                    or "gateway" in error_str
                )
                is_rate = self._is_rate_limited(e)
                if (is_transient or is_rate) and attempt < max_retries - 1:
                    wait = self._retry_after_seconds(e, retry_delay) if is_rate else retry_delay
                    logger.warning(
                        f"Firecrawl scrape retry for {product_url} "
                        f"(attempt {attempt + 1}/{max_retries}): {e}. Waiting {wait:.0f}s..."
                    )
                    time.sleep(wait)
                    retry_delay = min(retry_delay * 2, 60)
                    continue
                logger.error(
                    f"Firecrawl scrape failed for {product_url} after {attempt + 1} attempts: {e}"
                )
                return None

        return result

    def scrape_product(self, product_url: str, mode: str = "merchant") -> dict:
        """
        Scrape a product page.

        mode="merchant": markdown + LLM extract (higher quality for your price).
        mode="competitor": markdown first; extract only if price is still missing.
        """
        product = {
            "product_url": product_url,
            "product_name": self._fallback_name_from_url(product_url),
            "current_price": None,
            "old_price": None,
            "currency": None,
            "stock_status": "unknown",
            "image_url": None,
            "source": "unknown",
            "scrape_confidence": "low",
            "scraped_at": datetime.utcnow().isoformat(),
        }

        use_extract = mode != "competitor"
        result = self._firecrawl_scrape(product_url, with_extract=use_extract)
        if not result:
            return product

        product = self._hydrate_from_result(product, result)

        if mode == "merchant":
            product = self._reconcile_merchant_with_slug(product, product_url)

        # Competitor fast path: escalate to extract when price missing or implausible.
        if mode == "competitor":
            price = product.get("current_price")
            needs_extract = price is None or not self._is_plausible_retail_price(price)
            if needs_extract:
                logger.info(
                    f"Competitor scrape needs extract (price={price}): {product_url}"
                )
                extract_result = self._firecrawl_scrape(product_url, with_extract=True)
                if extract_result:
                    product = self._hydrate_from_result(product, extract_result)
                # Drop still-implausible junk so it cannot poison market stats.
                if not self._is_plausible_retail_price(product.get("current_price")):
                    logger.warning(
                        f"Dropping implausible competitor price "
                        f"{product.get('current_price')} from {product_url}"
                    )
                    product["current_price"] = None
                    product["scrape_confidence"] = "low"
                    product["source"] = "implausible_price"

        return product

    def _reconcile_merchant_with_slug(self, product: dict, product_url: str) -> dict:
        """If extract attaches the wrong product, prefer the URL slug name."""
        from utils.match import content_overlap, name_similarity

        slug_name = self._fallback_name_from_url(product_url) or ""
        scraped_name = product.get("product_name") or ""
        if not slug_name:
            return product

        sim = name_similarity(slug_name, scraped_name)
        overlap = content_overlap(slug_name, scraped_name)
        if sim >= 0.2 or overlap >= 2:
            return product

        logger.warning(
            "Merchant extract name mismatch vs URL slug "
            f"(scraped={scraped_name!r} slug={slug_name!r} sim={sim:.2f}); preferring slug"
        )
        product["product_name"] = clean_product_name(slug_name) or slug_name
        # Keep price if plausible; downgrade confidence because title was wrong.
        if product.get("current_price") is not None:
            product["scrape_confidence"] = "medium"
            product["source"] = f"{product.get('source') or 'extract'}_slug_name"
        return product

    @staticmethod
    def _is_plausible_retail_price(price: Any) -> bool:
        try:
            value = float(price)
        except (TypeError, ValueError):
            return False
        return 5.0 <= value <= 5000.0

    def _hydrate_from_result(self, product: dict, result) -> dict:
        """Parse a Firecrawl scrape response into the product dict. Public for tests."""
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        elif not isinstance(result, dict):
            logger.warning(f"Unexpected Firecrawl result type: {type(result)}")
            return product

        # Firecrawl may return fields nested under `data`.
        if isinstance(result.get("data"), dict):
            nested = result["data"]
            for key in ("markdown", "text", "metadata", "structured_data", "extract", "json"):
                if not result.get(key) and nested.get(key):
                    result[key] = nested.get(key)

        markdown = result.get("markdown") or result.get("text") or ""
        metadata = result.get("metadata", {}) or {}
        if hasattr(metadata, "model_dump"):
            metadata = metadata.model_dump()
        if not isinstance(metadata, dict):
            metadata = {}

        # Prefer Firecrawl v2 product profile, then JSON/extract schema, then JSON-LD.
        product_profile = result.get("product")
        if hasattr(product_profile, "model_dump"):
            product_profile = product_profile.model_dump()
        if isinstance(product_profile, dict) and self._apply_product_profile(
            product, product_profile, metadata
        ):
            product["source"] = "product"
            product["scrape_confidence"] = "high"
            return product

        extract_payload = result.get("extract") or result.get("json")
        if hasattr(extract_payload, "model_dump"):
            extract_payload = extract_payload.model_dump()
        if isinstance(extract_payload, list):
            extract_payload = next((x for x in extract_payload if isinstance(x, dict)), None)

        if isinstance(extract_payload, dict):
            self._apply_flat_extract(product, extract_payload, metadata)
            if product["current_price"] is not None:
                product["source"] = "extract"
                product["scrape_confidence"] = "high"
                return product

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

            self._apply_availability(product, offers.get("availability"))

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
            parsed_price, parsed_currency = self._extract_price_currency_from_text(
                markdown, product.get("product_url")
            )
            product["current_price"] = parsed_price
            product["currency"] = product["currency"] or parsed_currency
        elif product["current_price"] is not None and not product["currency"]:
            _, parsed_currency = self._extract_price_currency_from_text(
                markdown, product.get("product_url")
            )
            product["currency"] = parsed_currency

        # Disambiguate bare $ currencies from domain when still USD-looking.
        if product.get("currency") == "USD" and product.get("product_url"):
            inferred = self._currency_from_domain(product["product_url"], "$")
            if inferred and inferred != "USD":
                product["currency"] = inferred

        if not product["product_name"]:
            product["product_name"] = self._fallback_name_from_url(product["product_url"])

        if product.get("current_price") is not None:
            product["source"] = "markdown_fallback"
            product["scrape_confidence"] = "medium"
        else:
            product["source"] = "html"
            product["scrape_confidence"] = "low"

        return product

    def clean_product_urls(self, urls: list[str]) -> list[str]:
        from scraper.crawler import Crawler

        clean_urls = set()
        for url in urls:
            if not url:
                continue
            lower = url.lower()
            if any(x in lower for x in [".json", "/cart", "/checkout"]):
                continue
            if "/search?" in lower or "/search/" in lower or lower.rstrip("/").endswith("/search"):
                continue
            # Keep Shopify-style /collections/.../products/... ; drop bare collection listings.
            if "/collections/" in lower and "/products/" not in lower:
                continue
            if re.search(r"/category/[^/]+/?$", lower) and "/product" not in lower:
                continue
            if Crawler.score_product_url(url) < 0:
                continue
            parsed = urlparse(url)
            if not parsed.netloc:
                continue
            normalized = urlunparse((parsed.scheme or "https", parsed.netloc, parsed.path, "", "", ""))
            clean_urls.add(normalized)

        # Prefer higher-scored URLs when we have extras
        ranked = sorted(clean_urls, key=lambda u: Crawler.score_product_url(u), reverse=True)
        return ranked

    def batch_scrape_products(
        self,
        product_urls: List[str],
        batch_size: int = 5,
        mode: str = "competitor",
        max_workers: int = 4,
    ) -> tuple[list[dict], dict]:
        cleaned_urls = self.clean_product_urls(product_urls)
        stats = {
            "product_urls": len(product_urls),
            "valid_product_urls": len(cleaned_urls),
            "scraped": 0,
            "low_confidence": 0,
            "failed": 0,
        }
        if not cleaned_urls:
            return [], stats

        results: list[Optional[dict]] = [None] * len(cleaned_urls)
        workers = max(1, min(max_workers, len(cleaned_urls), batch_size))

        def _scrape_one(index: int, url: str) -> tuple[int, dict, bool]:
            try:
                product = self.scrape_product(url, mode=mode)
                return index, product, False
            except Exception as e:
                logger.error(f"Batch scrape failed for {url}: {e}")
                return index, {
                    "product_url": url,
                    "scrape_confidence": "low",
                    "source": "exception",
                }, True

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(_scrape_one, i, url)
                for i, url in enumerate(cleaned_urls)
            ]
            for future in as_completed(futures):
                index, product, failed = future.result()
                results[index] = product
                if failed:
                    stats["failed"] += 1
                else:
                    stats["scraped"] += 1
                    if product.get("scrape_confidence") == "low":
                        stats["low_confidence"] += 1

        return [r for r in results if r is not None], stats