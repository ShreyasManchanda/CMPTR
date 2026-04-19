import math
import time
import logging
from typing import List, Optional, Dict
from statistics import mean, median, stdev
from dataclasses import dataclass

import requests

from constants import CONFIDENCE_MAP

logger = logging.getLogger(__name__)


# ── Exchange rate cache with TTL ──────────────────────────────────────
_exchange_rate_cache: dict = {}
_exchange_rate_ts: float = 0.0
_EXCHANGE_RATE_TTL = 3600  # 1 hour


def fetch_live_exchange_rates() -> dict:
    global _exchange_rate_cache, _exchange_rate_ts

    if _exchange_rate_cache and (time.time() - _exchange_rate_ts) < _EXCHANGE_RATE_TTL:
        return _exchange_rate_cache

    fallback = {
        "USD": 1.0, "EUR": 0.90, "GBP": 0.75, "INR": 83.00,
        "CAD": 1.35, "AUD": 1.50, "JPY": 150.00, "CNY": 7.20,
    }
    try:
        response = requests.get("https://api.frankfurter.app/latest?from=USD", timeout=5)
        if response.status_code == 200:
            rates = response.json().get("rates", {})
            rates["USD"] = 1.0
            logger.info("Fetched live exchange rates from frankfurter.")
            _exchange_rate_cache = rates
            _exchange_rate_ts = time.time()
            return rates
    except requests.RequestException as e:
        logger.error(f"Failed to fetch exchange rates, using fallback: {e}")

    _exchange_rate_cache = fallback
    _exchange_rate_ts = time.time()
    return fallback


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def percentile(sorted_list: List[float], p: float) -> Optional[float]:
    if not sorted_list:
        return None
    n = len(sorted_list)
    idx = max(0, min(int(round(p * (n - 1))), n - 1))
    return sorted_list[idx]


@dataclass(frozen=True)
class CompetitorStats:
    product_id: str
    prices: List[float]
    count: int
    min_price: float
    median_price: float
    mean_price: float
    stddev_price: float
    p10: float
    p90: float
    avg_confidence: float


@dataclass(frozen=True)
class Recommendation:
    product_id: str
    my_price: float
    suggested_price: Optional[float]
    action: str
    reason: str
    rec_confidence: float
    stats: Optional[CompetitorStats]


class PricingEngine:
    def __init__(
        self,
        min_sample_size: int = 1,
        min_avg_confidence: float = 0.6,
        volatility_threshold: float = 0.80,
    ):
        self.min_sample_size = min_sample_size
        self.min_avg_confidence = min_avg_confidence
        self.volatility_threshold = volatility_threshold

    def _compute_recommendation_confidence(
        self, stats: CompetitorStats, volatility_ratio: float
    ) -> float:
        """Shared confidence scoring: penalizes volatility and rewards sample size."""
        vol_penalty = clamp(1.0 - (volatility_ratio * 0.4), 0.7, 1.0)
        sample_boost = clamp(0.55 + (stats.count * 0.15), 0.7, 1.0)
        return clamp(stats.avg_confidence * vol_penalty * sample_boost, 0.0, 1.0)

    def aggregate_competitors(
        self,
        normalized_products: List[dict],
        merchant_currency: Optional[str] = None,
    ) -> Dict[str, CompetitorStats]:
        exchange_rates = fetch_live_exchange_rates()

        groups: Dict[str, List[tuple]] = {}
        for item in normalized_products:
            pid = item.get("product_id")
            price = item.get("current_price")
            if price is None:
                continue
            try:
                price_val = float(price)
            except (ValueError, TypeError):
                continue
            if math.isnan(price_val) or price_val <= 0:
                continue

            item_currency = item.get("currency")
            if merchant_currency and item_currency and item_currency != merchant_currency:
                rate_from = exchange_rates.get(item_currency)
                rate_to = exchange_rates.get(merchant_currency)
                if rate_from and rate_to:
                    price_val = price_val * (rate_to / rate_from)
                else:
                    continue

            conf_label = (item.get("scrape_confidence") or "low").lower()
            conf_val = CONFIDENCE_MAP.get(conf_label, 0.3)
            groups.setdefault(pid, []).append((price_val, conf_val))

        stats_map: Dict[str, CompetitorStats] = {}
        for pid, tuples in groups.items():
            prices = sorted([p for p, _ in tuples])
            confs = [c for _, c in tuples]
            count = len(prices)
            min_price = prices[0]
            median_price = median(prices)
            mean_price = mean(prices) if count > 0 else 0.0
            stddev_price = stdev(prices) if count > 1 else 0.0
            p10 = percentile(prices, 0.10) or min_price
            p90 = percentile(prices, 0.90) or prices[-1]
            avg_conf = sum(confs) / len(confs) if confs else 0.0

            stats_map[pid] = CompetitorStats(
                product_id=pid,
                prices=prices,
                count=count,
                min_price=min_price,
                median_price=median_price,
                mean_price=mean_price,
                stddev_price=stddev_price,
                p10=p10,
                p90=p90,
                avg_confidence=avg_conf,
            )
        return stats_map

    def recommend_for(
        self,
        product_id: str,
        my_price: float,
        competitors_products: List[dict],
        merchant_currency: Optional[str] = None,
    ) -> Recommendation:
        try:
            my_price_val = float(my_price)
        except (ValueError, TypeError):
            return Recommendation(product_id, my_price, None, "manual_review", "invalid_my_price", 0.0, None)

        stats_map = self.aggregate_competitors(competitors_products, merchant_currency=merchant_currency)
        stats = stats_map.get(product_id)

        if not stats:
            return Recommendation(product_id, my_price_val, None, "manual_review", "no_competitor_data", 0.0, None)

        if stats.count < self.min_sample_size:
            return Recommendation(product_id, my_price_val, None, "manual_review", "insufficient_samples", stats.avg_confidence, stats)

        if stats.avg_confidence < self.min_avg_confidence:
            return Recommendation(product_id, my_price_val, None, "manual_review", "low_average_confidence", stats.avg_confidence, stats)

        median_price = stats.median_price
        if median_price <= 0:
            return Recommendation(product_id, my_price_val, None, "manual_review", "invalid_median", stats.avg_confidence, stats)

        volatility_ratio = stats.stddev_price / median_price if median_price > 0 else 0
        if stats.count >= 3 and volatility_ratio > self.volatility_threshold:
            return Recommendation(product_id, my_price_val, None, "manual_review", "high_volatility", stats.avg_confidence, stats)

        min_is_suspicious = stats.p10 and stats.p90 > 0 and stats.min_price < (stats.p10 * 0.7)

        gap = (my_price_val - median_price) / median_price if median_price != 0 else 0.0

        rec_conf = self._compute_recommendation_confidence(stats, volatility_ratio)

        REDUCE_THRESHOLD = 0.10
        INCREASE_THRESHOLD = -0.10  # merchant is > 10% below median

        if gap > REDUCE_THRESHOLD:
            # Merchant is too expensive — recommend reducing
            suggested = median_price * 0.98 if min_is_suspicious else max(stats.min_price, median_price * 0.98)
            reason = "median_above_by_{:.2f}%".format(gap * 100.0)
            return Recommendation(
                product_id=product_id,
                my_price=my_price_val,
                suggested_price=round(float(suggested), 2),
                action="reduce",
                reason=reason,
                rec_confidence=rec_conf,
                stats=stats,
            )

        if gap < INCREASE_THRESHOLD:
            # Merchant is significantly cheaper than market — opportunity to increase
            suggested = round(median_price * 0.95, 2)  # 5% below median to stay competitive
            reason = "median_below_by_{:.2f}%".format(abs(gap) * 100.0)
            return Recommendation(
                product_id=product_id,
                my_price=my_price_val,
                suggested_price=suggested,
                action="increase",
                reason=reason,
                rec_confidence=rec_conf,
                stats=stats,
            )

        return Recommendation(
            product_id=product_id,
            my_price=my_price_val,
            suggested_price=None,
            action="no_change",
            reason="competitive",
            rec_confidence=rec_conf,
            stats=stats,
        )