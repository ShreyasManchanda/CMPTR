import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from dataclasses import asdict
from urllib.parse import urlparse
from datetime import datetime

from scraper.crawler import Crawler
from scraper.scraper import Scraper
from normalizer.normalize_product import ProductNormalizer
from pricing.pricing_engine import PricingEngine, Recommendation, fetch_live_exchange_rates
from pricing.rules_agent import RulesAgent, FinalAction
from agent.ambiguity_agent import AmbiguityAgent
from agent.explanation_agent import ExplanationAgent
from constants import CONFIDENCE_MAP
from utils.match import filter_matching_products
from utils.domain import domain_from_url, is_tier_mismatch, normalize_domain

logger = logging.getLogger(__name__)

# Hard budget to protect Firecrawl / Gemini quota.
MAX_TOTAL_SCRAPES = 15
MAX_PER_DOMAIN = 2
STORE_WORKERS = 3
MATCH_THRESHOLD = 0.15
PRICE_BAND_LOW = 0.55
PRICE_BAND_HIGH = 1.75


class PricingOrchestrator:
    def __init__(self):
        self.crawler = Crawler()
        self.scraper = Scraper()
        self.normalizer = ProductNormalizer()
        self.engine = PricingEngine()
        self.rules = RulesAgent()
        self.ambiguity_ai = AmbiguityAgent()
        self.explainer_ai = ExplanationAgent()

    def _collect_store(self, store_url: str, product_name: str, max_per_domain: int) -> tuple[list, dict]:
        domain = urlparse(store_url).netloc or store_url
        domain = domain.split("/")[0]

        logger.info(f"Searching '{domain}' for '{product_name}' (cap: {max_per_domain})")
        links = self.crawler.find_competitor_product(domain, product_name, max_results=max_per_domain)

        if not links:
            logger.warning(f"No product links found on {domain}")
            return [], {"store": store_url, "stats": {"product_urls": 0, "valid_product_urls": 0, "scraped": 0, "low_confidence": 0, "failed": 0}}

        logger.info(f"Batch scraping {len(links)} products from {store_url}")
        raw_products, stats = self.scraper.batch_scrape_products(links, mode="competitor", max_workers=4)
        return raw_products, {"store": store_url, "stats": stats}

    def run_pipeline(self, my_product_url: str, competitor_store_urls: List[str]) -> Dict[str, Any]:
        """Run the end-to-end pricing pipeline."""
        logger.info(f"Starting pipeline for product: {my_product_url}")

        # Scrape the merchant's own product (rich extract path)
        raw_my_product = self.scraper.scrape_product(my_product_url, mode="merchant")
        norm_my_product, diag = self.normalizer.normalize_product(raw_my_product)

        if not norm_my_product or not norm_my_product.current_price:
            logger.error("Could not parse your product URL or find its current price.")
            return {
                "status": "error",
                "message": "Could not parse your product URL or find its current price.",
            }

        my_price = norm_my_product.current_price
        product_id = norm_my_product.product_id
        merchant_currency = norm_my_product.currency
        product_name = norm_my_product.product_name or product_id

        logger.info(f"Target product: Name='{product_name}', ID={product_id}, Price={my_price} {merchant_currency}")

        all_competitor_raw_data = []
        overall_scrape_stats = []

        if not competitor_store_urls:
            return {
                "status": "error",
                "message": "At least one competitor store URL is required.",
                "product_id": product_id,
                "my_price": my_price,
            }

        merchant_domain = normalize_domain(domain_from_url(my_product_url))
        filtered_stores: list[str] = []
        for store_url in competitor_store_urls:
            comp_domain = normalize_domain(urlparse(store_url).netloc)
            if merchant_domain and comp_domain and is_tier_mismatch(merchant_domain, comp_domain):
                logger.warning(
                    "Skipping tier-mismatched competitor store %s for merchant %s",
                    comp_domain,
                    merchant_domain,
                )
                continue
            filtered_stores.append(store_url)
        competitor_store_urls = filtered_stores

        if not competitor_store_urls:
            return {
                "status": "error",
                "message": "All competitor stores were filtered as wrong price tier/positioning for your brand.",
                "product_id": product_id,
                "my_price": my_price,
            }

        max_per_domain = min(MAX_PER_DOMAIN, max(1, MAX_TOTAL_SCRAPES // len(competitor_store_urls)))
        store_workers = min(STORE_WORKERS, len(competitor_store_urls))

        with ThreadPoolExecutor(max_workers=store_workers) as executor:
            futures = {
                executor.submit(self._collect_store, store_url, product_name, max_per_domain): store_url
                for store_url in competitor_store_urls
            }
            for future in as_completed(futures):
                raw_products, store_stats = future.result()
                all_competitor_raw_data.extend(raw_products)
                overall_scrape_stats.append(store_stats)

        # Soft enforce global scrape budget if parallel stores overshot.
        if len(all_competitor_raw_data) > MAX_TOTAL_SCRAPES:
            logger.warning(
                "Truncating competitor scrapes from %s to %s (budget)",
                len(all_competitor_raw_data),
                MAX_TOTAL_SCRAPES,
            )
            all_competitor_raw_data = all_competitor_raw_data[:MAX_TOTAL_SCRAPES]

        if not all_competitor_raw_data:
            return {
                "status": "error",
                "message": "No competitor data found across provided stores.",
                "product_id": product_id,
                "my_price": my_price,
            }

        # Normalize all competitor data
        logger.info(f"Normalizing {len(all_competitor_raw_data)} competitor products.")
        normalized_competitors, norm_metrics = self.normalizer.normalize_batch(all_competitor_raw_data)
        logger.info(
            f"Normalization: {norm_metrics['normalized_count']} kept, "
            f"{norm_metrics['dropped_count']} dropped. Reasons: {norm_metrics.get('drop_reasons', {})}"
        )

        # Drop weak name matches before aggregation
        matched_competitors, rejected_matches = filter_matching_products(
            product_name,
            normalized_competitors,
            threshold=MATCH_THRESHOLD,
        )
        norm_metrics["match_rejected_count"] = len(rejected_matches)
        norm_metrics["match_rejected"] = rejected_matches[:20]
        if rejected_matches:
            logger.info(
                "Name-match filter dropped %s competitors (threshold=%.2f)",
                len(rejected_matches),
                MATCH_THRESHOLD,
            )
        normalized_competitors = matched_competitors

        if not normalized_competitors:
            return {
                "status": "error",
                "message": "No competitor products matched your product name closely enough.",
                "product_id": product_id,
                "my_price": my_price,
                "metrics": {"normalization": norm_metrics, "scrape_stats": overall_scrape_stats},
            }

        for comp in normalized_competitors:
            logger.info(
                f"  Competitor: {comp.product_name} | {comp.current_price} {comp.currency} | "
                f"confidence={comp.scrape_confidence}"
            )

        # Build display rows + drop extreme FX outliers before pricing math.
        exchange_rates = fetch_live_exchange_rates()
        competitor_details = []
        competitor_dicts = []

        for comp in normalized_competitors:
            display_price = comp.current_price
            if comp.currency and merchant_currency and comp.currency != merchant_currency:
                rate_from = exchange_rates.get(comp.currency)
                rate_to = exchange_rates.get(merchant_currency)
                if rate_from and rate_to and display_price:
                    display_price = round(display_price * (rate_to / rate_from), 2)
                else:
                    logger.warning(
                        "Skipping competitor with unknown FX %s→%s",
                        comp.currency,
                        merchant_currency,
                    )
                    continue

            if not display_price or display_price <= 0:
                continue

            if my_price > 0:
                ratio = display_price / my_price
                if ratio > PRICE_BAND_HIGH or ratio < PRICE_BAND_LOW:
                    logger.warning(
                        "Skipping competitor outside price band (ratio %.2f, band %.2f–%.2f): %s",
                        ratio,
                        PRICE_BAND_LOW,
                        PRICE_BAND_HIGH,
                        display_price,
                    )
                    continue

            if not Scraper._is_plausible_retail_price(display_price):
                logger.warning("Skipping implausible display price %s", display_price)
                continue

            competitor_details.append({
                "store": urlparse(comp.product_url).netloc if comp.product_url else "unknown",
                "product_name": comp.product_name or "Unknown Product",
                "price": display_price,
                "original_price": comp.current_price,
                "original_currency": comp.currency,
                "stock_status": comp.stock_status,
                "confidence": CONFIDENCE_MAP.get((comp.scrape_confidence or "low").lower(), 0.3),
                "scraped_at": comp.scraped_at.isoformat() if comp.scraped_at else datetime.utcnow().isoformat(),
            })
            competitor_dicts.append({
                "product_id": product_id,
                "current_price": display_price,
                "currency": merchant_currency,
                "scrape_confidence": comp.scrape_confidence,
            })

        if not competitor_details:
            return {
                "status": "error",
                "message": "Competitor prices looked invalid after sanity checks. Try different store URLs.",
                "product_id": product_id,
                "my_price": my_price,
                "metrics": {"normalization": norm_metrics, "scrape_stats": overall_scrape_stats},
            }

        recommendation: Recommendation = self.engine.recommend_for(
            product_id=product_id,
            my_price=my_price,
            competitors_products=competitor_dicts,
            merchant_currency=merchant_currency,
        )

        final_decision: FinalAction = self.rules.decide(recommendation)
        logger.info(f"Rule Agent decision: {final_decision.final_action}")

        ambiguity_advice = None
        if final_decision.final_action == "manual_review":
            logger.info("Decision is manual_review, invoking Ambiguity Agent.")
            ambiguity_advice = self.ambiguity_ai.resolve_ambiguity(
                final_action=final_decision.policy_reason,
                stats_map=recommendation.stats,
                metrics=norm_metrics,
            )

        logger.info("Invoking Explanation Agent.")
        human_explanation = str(self.explainer_ai.get_explanation(
            final_action=final_decision,
            ambiguity_advice=ambiguity_advice,
            metrics=norm_metrics,
        ))

        return {
            "status": "success",
            "product_id": product_id,
            "product_name": product_name,
            "product_url": my_product_url,
            "my_price": my_price,
            "currency": merchant_currency,
            "decision": {
                "action": final_decision.final_action,
                "suggested_price": final_decision.suggested_price,
                "policy_reason": final_decision.policy_reason,
                "confidence": final_decision.confidence,
            },
            "ai_advice": ambiguity_advice,
            "explanation": human_explanation,
            "metrics": {
                "scrape_stats": overall_scrape_stats,
                "normalization": norm_metrics,
                "competitor_stats": competitor_details,
                "aggregated_stats": asdict(recommendation.stats) if recommendation.stats else None,
            },
        }
