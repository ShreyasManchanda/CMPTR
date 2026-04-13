from __future__ import annotations
import math
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from urllib.parse import urlparse
from pydantic import BaseModel, Field 



class NormalizedProduct(BaseModel):
    product_url: str
    product_id: str
    product_name: Optional[str] = None
    current_price: Optional[float] = None
    old_price: Optional[float] = None
    discount_percent: Optional[float] = None
    currency: Optional[str] = None
    stock_status: str = "unknown"    # in_stock | out_of_stock | unknown
    image_url: Optional[str] = None
    source: str = "unknown"          # json_ld | html | inferred
    scrape_confidence: str = "low"   # high | medium | low
    scraped_at: Optional[datetime] = None
    normalized_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    raw: Optional[dict] = None  


class ProductNormalizer:
    def __init__(self):
        pass
    
    CURRENCY_SYMBOLS: Dict[str, str] = {
        "$": "USD",
        "₹": "INR",
        "Rs": "INR",
        "£": "GBP",
        "€": "EUR",
        "¥": "JPY",
        "RMB": "CNY",
        "元": "CNY",
        "CN¥": "CNY",
        "JP¥": "JPY",
        "A$": "AUD",
        "AUD$": "AUD",
        "C$": "CAD",
        "CAD$": "CAD",
        "CHF": "CHF"
    }
    
    _number_re = re.compile(r"[-+]?\d{1,3}(?:[,\d]*)(?:\.\d+)?")

    def extract_numbers_from_string(self, s: str) -> List[float]:
        if not s or not isinstance(s, str):
            return []
        matches = self._number_re.findall(s)
        nums: List[float] = []
        for m in matches:
            try:
                cleaned = m.replace(",", "")
                nums.append(float(cleaned))
            except Exception:
                continue
        return nums

    def coerce_price_to_float(self, raw_price) -> Optional[float]:
        """
        Conservative conversion:
         - numeric -> float
         - range -> min value
         - "From X" -> X
         - else -> None
        """

        if raw_price is None:
            return None

        if isinstance(raw_price, (int, float)) and not math.isnan(raw_price):
            try:
                return float(raw_price)
            except Exception:
                return None

        if isinstance(raw_price, str):
            s = raw_price.strip()
            nums = self.extract_numbers_from_string(s)

            if not nums:
                return None

            # presence of explicit range tokens
            if any(x in s for x in ["-", "to", "–"]):
                return(float(min(nums)))

            # "From 499" or "Starting at"
            if re.search(r"\bfrom\b|\bstarting\b|\bstarts\b", s, re.IGNORECASE):
                return float(nums[0])

            # default: take first number
            return float(nums[0])

        return None
    
    def parse_currency_from_price(self, raw_price_str: Optional[str], fallback: Optional[str]) -> Optional[str]:
        if fallback and isinstance(fallback, str):
            fallback_upper = fallback.upper()
            mapped = self.CURRENCY_SYMBOLS.get(fallback, self.CURRENCY_SYMBOLS.get(fallback_upper, fallback_upper))
            if len(mapped) <= 4:
                return mapped

        if not raw_price_str or not isinstance(raw_price_str, str):
            return None

        for sym, code in self.CURRENCY_SYMBOLS.items():
            if sym in raw_price_str:
                return code

        if re.search(r"\b(inr|rupees|rs\.?)\b", raw_price_str, re.IGNORECASE):
            return "INR"
        if re.search(r"\b(usd|dollars?)\b", raw_price_str, re.IGNORECASE):
            return "USD"
        if re.search(r"\b(eur|euros?)\b", raw_price_str, re.IGNORECASE):
            return "EUR"
        if re.search(r"\b(gbp|pounds?)\b", raw_price_str, re.IGNORECASE):
            return "GBP"
        if re.search(r"\b(jpy|yen)\b", raw_price_str, re.IGNORECASE):
            return "JPY"
        if re.search(r"\b(cny|rmb|yuan)\b", raw_price_str, re.IGNORECASE):
            return "CNY"

        return None

    def extract_product_id(self, product_url: Optional[str]) -> str:
        if not product_url:
            return ""

        try:
            parsed = urlparse(product_url)
            path = parsed.path.rstrip("/")
            return path.split("/")[-1] or path.replace("/","_")
        except Exception:
            return product_url or ""

    def compute_discount_pct(self, old_price: float, current_price: float) -> Optional[float]:
        try:
            if old_price and current_price and old_price > 0 and old_price > current_price:
                return round((old_price - current_price) / old_price * 100.0, 2)
        except Exception:
            pass
        return None

    def map_stock_status(self, raw_stock: Optional[str]) -> Optional[str]:
        if not raw_stock:
            return "unknown"
        s = raw_stock.lower()
        if "out of stock" in s or "outofstock" in s or "sold out" in s:
            return "out_of_stock"
        if "in stock" in s or "available" in s or "add to cart" in s:
            return "in_stock"
        return "unknown" 

    def assign_confidence(self, raw: dict, parsed: dict) -> Tuple[str, float]:
        """
        Combine raw scrape confidence with parsing signals to yield
        a label (high/medium/low) and numeric score [0,1].
        Tunable heuristics; conservative by default.
        """
        base_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
        raw_label = (raw.get("scrape_confidence") or "low").lower()
        score = base_map.get(raw_label, 0.3)

        # small positive signals
        if parsed.get("currency"):
            score += 0.05
        if parsed.get("image_url"):
            score += 0.03

        # negative signals
        if parsed.get("current_price") is None:
            score -= 0.25
        if (raw.get("source") or "").lower() == "html":
            score -= 0.10
        if parsed.get("price_was_range"):
            score -= 0.10

        # clamp
        score = max(0.0, min(1.0, score))

        if score >= 0.75:
            label = "high"
        elif score >= 0.45:
            label = "medium"
        else:
            label = "low"

        return label, score

    def should_drop(self, parsed: dict, confidence_label: str) -> Tuple[bool, Optional[str]]:
        """
        Conservative gating rules. Return (should_drop, reason)
        """
        price = parsed.get("current_price")
        currency = parsed.get("currency")

        if price is None:
            return True, "missing_price"
        if currency is None:
            return True, "missing_currency"
        if price <= 0:
            return True, "nonpositive_price"
        if confidence_label == "low":
            return True, "low_confidence"
        return False, None

    def normalize_product(self, raw:dict) -> Tuple[Optional[NormalizedProduct], Dict]:
        """
        Normalize one raw scraped product dict.
        Returns (NormalizedProduct or None, diagnostics).
        """
        
        diagnostics: Dict = {"notes": []}
        product_url = raw.get("product_url")
        diagnostics["product_url"] = product_url

        parsed: Dict = {}
        parsed["product_id"] = self.extract_product_id(product_url)
        parsed["product_name"] = (raw.get("product_name") or None)

        raw_current = raw.get("current_price")
        raw_old = raw.get("old_price")

        parsed_price = self.coerce_price_to_float(raw_current)
        parsed_old_price = self.coerce_price_to_float(raw_old)

        if parsed_price is None:
            diagnostics["notes"].append("could_not_parse_current_price")
        if parsed_old_price is None and raw_old is not None:
            diagnostics["notes"].append("could_not_parse_old_price")

        parsed["current_price"] = parsed_price
        parsed["old_price"] = parsed_old_price

        # detect if price string looked like a range
        if isinstance(raw_current, str) and ("-" in raw_current or " to " in raw_current or "–" in raw_current):
            parsed["price_was_range"] = True
            diagnostics["notes"].append("price_was_range_used_min_value")
        else:
            parsed["price_was_range"] = False

        # currency
        parsed["currency"] = self.parse_currency_from_price(
            raw_current if isinstance(raw_current, str) else None,
            raw.get("currency")
        )
        if parsed["currency"] is None:
            diagnostics["notes"].append("currency_unknown")

        raw_image_url = raw.get("image_url")
        if isinstance(raw_image_url, list):
            parsed["image_url"] = raw_image_url[0] if raw_image_url else None
        else:
            parsed["image_url"] = raw_image_url
        
        parsed["stock_status"] = self.map_stock_status(raw.get("stock_status"))
        parsed["source"] = raw.get("source") or "unknown"

        # scraped_at parse (best-effort)
        parsed["scraped_at"] = None
        try:
            sa = raw.get("scraped_at")
            if sa:
                # ISO format expected; guard with try/except
                parsed["scraped_at"] = datetime.fromisoformat(sa)
        except Exception:
            diagnostics["notes"].append("could_not_parse_scraped_at")

        # discount calculation
        if parsed["old_price"] and parsed["current_price"]:
            parsed["discount_percent"] = self.compute_discount_pct(parsed["old_price"], parsed["current_price"])
        else:
            parsed["discount_percent"] = None

        # confidence
        conf_label, conf_score = self.assign_confidence(raw, parsed)
        diagnostics["confidence_score"] = conf_score
        diagnostics["confidence_label"] = conf_label

        # gating decision
        drop, reason = self.should_drop(parsed, conf_label)
        if drop:
            diagnostics["drop_reason"] = reason
            return None, diagnostics

        # assemble normalized model
        normalized = NormalizedProduct(
            product_url=product_url,
            product_id=parsed["product_id"],
            product_name=parsed["product_name"],
            current_price=parsed["current_price"],
            old_price=parsed["old_price"],
            discount_percent=parsed["discount_percent"],
            currency=parsed["currency"],
            stock_status=parsed["stock_status"],
            image_url=parsed["image_url"],
            source=parsed["source"],
            scrape_confidence=conf_label,
            scraped_at=parsed["scraped_at"],
            raw={"product_url": product_url, "raw_price": raw_current}
        )

        return normalized, diagnostics

    def normalize_batch(self, raw_products: List[dict]) -> Tuple[List[NormalizedProduct], Dict]:
        normalized_list: List[NormalizedProduct] = []
        metrics = {
            "raw_count": len(raw_products),
            "normalized_count": 0,
            "dropped_count": 0,
            "drop_reasons": {},
            "avg_confidence": None,
            "low_confidence_pct": None,
            "missing_currency_count": 0
        }

        conf_scores: List[float] = []
        for raw in raw_products:
            norm, diag = self.normalize_product(raw)
            if norm:
                normalized_list.append(norm)
                metrics["normalized_count"] += 1
                conf_scores.append(diag.get("confidence_score", 0.0))
                if norm.currency is None:
                    metrics["missing_currency_count"] += 1
            else:
                metrics["dropped_count"] += 1
                reason = diag.get("drop_reason", "unknown")
                metrics["drop_reasons"][reason] = metrics["drop_reasons"].get(reason, 0) + 1

        if conf_scores:
            metrics["avg_confidence"] = sum(conf_scores) / len(conf_scores)
            metrics["low_confidence_pct"] = len([s for s in conf_scores if s < 0.45]) / len(conf_scores)
        else:
            metrics["avg_confidence"] = 0.0
            metrics["low_confidence_pct"] = 0.0

        return normalized_list, metrics

