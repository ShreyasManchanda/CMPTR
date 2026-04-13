import requests
import logging
from functools import lru_cache
from typing import List, Optional, Dict
from statistics import mean, median, stdev
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def fetch_live_exchange_rates() -> dict:
    fallback = {
        "USD": 1.0,
        "EUR": 0.90,
        "GBP": 0.75,
        "INR": 83.00,
        "CAD": 1.35,
        "AUD": 1.50,
        "JPY": 150.00,
        "CNY": 7.20
    }
    try:
        response = requests.get("https://api.frankfurter.app/latest?from=USD", timeout=5)
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            rates["USD"] = 1.0
            logger.info("Successfully fetched live exchange rates from frankfurter.")
            return rates
    except Exception as e:
        logger.error(f"Failed to fetch exchange rates, using fallback: {e}")
    return fallback


CONFIDENCE_MAP = {'high' : 0.9, 'medium' : 0.6, 'low' : 0.3}


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def percentile(sorted_list: List[float], p:float) -> Optional[float]:
    if not sorted_list:
        return None
    n = len(sorted_list)
    idx = int(round(p * (n - 1)))
    idx = max(0, min(idx, n - 1))
    return sorted_list[idx]


@dataclass(frozen= True)
class CompetitorStats:
    product_id: str
    prices : List[float]
    count : int
    min_price : float
    median_price : float
    mean_price: float
    stddev_price : float
    p10: float
    p90: float
    avg_confidence : float

@dataclass(frozen=True)
class Recommendation:
    product_id : str
    my_price : float
    suggested_price : Optional[float]
    action : str
    reason : str
    rec_confidence : float
    stats : Optional[CompetitorStats]


class PricingEngine:
    def __init__(self,
    min_sample_size: int = 1,
    min_avg_confidence: float = 0.6,
    volatiity_threshold: float = 0.80 # Tripled to allow varied clearance pricing
    ):
        self.min_sample_size = min_sample_size
        self.min_avg_confidence = min_avg_confidence
        self.volatility_threshold = volatiity_threshold

    def aggregate_competitors(self, normalized_products: List[dict],
    merchant_currency: Optional[str] = None) -> Dict[str, CompetitorStats]:
        
        exchange_rates = fetch_live_exchange_rates()

        groups: Dict[str, List[tuple]] = {}
        for item in normalized_products:
            pid = item.get("product_id")
            price = item.get("current_price")
            if price is None:
                continue
            try:
                price_val = float(price)
            except Exception:
                continue
            if math.isnan(price_val) or price_val <= 0:
                continue
            
            item_currency = item.get("currency")
            if merchant_currency and item_currency and item_currency != merchant_currency:
                rate_from = exchange_rates.get(item_currency)
                rate_to = exchange_rates.get(merchant_currency)
                if rate_from and rate_to:
                    # Item price gives USD when divided by its rate, then multiplied by target rate
                    price_val = price_val * (rate_to / rate_from)
                elif item_currency != merchant_currency:
                    # Ignore if conversion rates are missing
                    continue

            conf_label = (item.get("scrape_confidence") or "low").lower()
            conf_val = CONFIDENCE_MAP.get(conf_label, 0.3)
            groups.setdefault(pid, []).append((price_val,conf_val))
        
        stats_map: Dict[str, CompetitorStats] = {}
        for pid, tuples in groups.items():
            prices = sorted([p for p,_ in tuples])
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
                avg_confidence=avg_conf
            )
        return stats_map
    
    def recommend_for(self, product_id: str, my_price: float, competitors_products: List[dict], merchant_currency: Optional[str] = None) -> Recommendation:
        try:
            my_price_val = float(my_price)
        except Exception:
            return Recommendation(product_id, my_price, None, "manual_review", "invalid_my_price", 0.0, None)
        
        stats_map = self.aggregate_competitors(competitors_products, merchant_currency=merchant_currency)
        stats= stats_map.get(product_id)

        if not stats:
            return Recommendation(product_id, my_price_val, None, "manual_review",
                                  "no_competitor_data", 0.0, None)
        
        if stats.count < self.min_sample_size:
            return Recommendation(product_id, my_price_val, None, "manual_review",
                                  "insufficient_samples", stats.avg_confidence, stats)

        if stats.avg_confidence < self.min_avg_confidence:
            return Recommendation(product_id, my_price_val, None, "manual_review",
                                  "low_average_confidence", stats.avg_confidence, stats)

        median_price = stats.median_price
        if median_price <= 0:
            return Recommendation(product_id, my_price_val, None, "manual_review",
                                  "invalid_median", stats.avg_confidence, stats)

        volatility_ratio = stats.stddev_price / median_price if median_price > 0 else 0
        # Only enforce volatility gate when we have enough data points for stddev to be meaningful
        if stats.count >= 3 and volatility_ratio > self.volatility_threshold:
            return Recommendation(product_id, my_price_val, None, "manual_review",
                                  "high_volatility", stats.avg_confidence, stats)
        
        min_is_suspicious = False
        if stats.p10 and stats.p90 > 0:
            if stats.min_price < (stats.p10 * 0.7):
                min_is_suspicious = True

        try:
            gap = (my_price_val - median_price) / median_price  # fractional gap
        except Exception:
            gap = 0.0

        # case: i'm cheapest
        if my_price_val < (stats.min_price * (1 - 0.05)):  # if I'm >5% below competitor min
            return Recommendation(product_id, my_price_val, None, "no_change",
                                  "already_cheapest", stats.avg_confidence, stats)

        REDUCE_THRESHOLD = 0.10

        if gap > REDUCE_THRESHOLD:
            if min_is_suspicious:
                suggested = median_price * 0.98
            else:
                suggested = max(stats.min_price, median_price*0.98)

            # Softer volatility penalty for apparel/clearance pricing:
            vol_penalty = clamp(1.0 - (volatility_ratio * 0.4), 0.7, 1.0)
            # Gentler curve: 1 sample=0.7, 2=0.85, 3+=1.0
            sample_boost = clamp(0.55 + (stats.count * 0.15), 0.7, 1.0)
            rec_conf = stats.avg_confidence * vol_penalty * sample_boost
            rec_conf = clamp(rec_conf, 0.0, 1.0)

            reason = "median_above_by_{:.2f}%".format((gap) * 100.0)
            return Recommendation(
                product_id=product_id,
                my_price=my_price_val,
                suggested_price=round(float(suggested), 2),
                action="reduce",
                reason=reason,
                rec_confidence=rec_conf,
                stats=stats
            )

        # Softer volatility penalty for apparel/clearance pricing:
        vol_penalty = clamp(1.0 - (volatility_ratio * 0.4), 0.7, 1.0)
        # Gentler curve: 1 sample=0.7, 2=0.85, 3+=1.0
        sample_boost = clamp(0.55 + (stats.count * 0.15), 0.7, 1.0)
        rec_conf = stats.avg_confidence * vol_penalty * sample_boost
        rec_conf = clamp(rec_conf, 0.0, 1.0)

        return Recommendation(
            product_id=product_id,
            my_price=my_price_val,
            suggested_price=None,
            action="no_change",
            reason="competitive",
            rec_confidence=rec_conf,
            stats=stats
        )



    