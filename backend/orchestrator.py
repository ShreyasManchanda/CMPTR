import logging
from typing import List, Dict, Any
from dataclasses import asdict
from urllib.parse import urlparse
from datetime import datetime

from scraper.crawler import Crawler
from scraper.scraper import Scraper
from normalizer.normalize_product import ProductNormalizer, NormalizedProduct
from pricing.pricing_engine import PricingEngine, Recommendation, fetch_live_exchange_rates
from pricing.rules_agent import RulesAgent, FinalAction
from agent.ambiguity_agent import AmbiguityAgent
from agent.explanation_agent import ExplanationAgent
from constants import CONFIDENCE_MAP

logger = logging.getLogger(__name__)


class PricingOrchestrator:
    def __init__(self):
        self.crawler = Crawler()
        self.scraper = Scraper()
        self.normalizer = ProductNormalizer()
        self.engine = PricingEngine()
        self.rules = RulesAgent()
        self.ambiguity_ai = AmbiguityAgent()
        self.explainer_ai = ExplanationAgent()

    def run_pipeline(self, my_product_url: str, competitor_store_urls: List[str]) -> Dict[str, Any]:
        """Run the end-to-end pricing pipeline."""
        logger.info(f"Starting pipeline for product: {my_product_url}")

        # Scrape the merchant's own product
        raw_my_product = self.scraper.scrape_product(my_product_url)
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

        # Collect competitor market data
        all_competitor_raw_data = []
        overall_scrape_stats = []

        MAX_TOTAL_SCRAPES = 15
        max_per_domain = min(max(1, MAX_TOTAL_SCRAPES // len(competitor_store_urls)), 5)

        for store_url in competitor_store_urls:
            domain = urlparse(store_url).netloc or store_url
            domain = domain.split('/')[0]

            logger.info(f"Searching '{domain}' for '{product_name}' (cap: {max_per_domain})")
            links = self.crawler.find_competitor_product(domain, product_name, max_results=max_per_domain)

            if not links:
                logger.warning(f"No product links found on {domain}")
                continue

            logger.info(f"Batch scraping {len(links)} products from {store_url}")
            raw_products, stats = self.scraper.batch_scrape_products(links)

            all_competitor_raw_data.extend(raw_products)
            overall_scrape_stats.append({"store": store_url, "stats": stats})

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
        for comp in normalized_competitors:
            logger.info(f"  Competitor: {comp.product_name} | {comp.current_price} {comp.currency} | confidence={comp.scrape_confidence}")

        # Deterministic pricing math
        competitor_dicts = [p.model_dump() for p in normalized_competitors]

        # Align all competitor data points to the target product_id for aggregation
        for comp in competitor_dicts:
            comp["product_id"] = product_id

        recommendation: Recommendation = self.engine.recommend_for(
            product_id=product_id,
            my_price=my_price,
            competitors_products=competitor_dicts,
            merchant_currency=merchant_currency,
        )

        # Apply policy rules
        final_decision: FinalAction = self.rules.decide(recommendation)
        logger.info(f"Rule Agent decision: {final_decision.final_action}")

        # AI ambiguity resolution (only for manual_review outcomes)
        ambiguity_advice = None
        if final_decision.final_action == "manual_review":
            logger.info("Decision is manual_review, invoking Ambiguity Agent.")
            ambiguity_advice = str(self.ambiguity_ai.resolve_ambiguity(
                final_action=final_decision.policy_reason,
                stats_map=recommendation.stats,
                metrics=norm_metrics,
            ))

        # AI explanation generation
        logger.info("Invoking Explanation Agent.")
        human_explanation = str(self.explainer_ai.get_explanation(
            final_action=final_decision,
            ambiguity_advice=ambiguity_advice,
            metrics=norm_metrics,
        ))

        # Build per-competitor detail array with currency conversion
        exchange_rates = fetch_live_exchange_rates()

        competitor_details = []
        for comp in normalized_competitors:
            display_price = comp.current_price
            if comp.currency and merchant_currency and comp.currency != merchant_currency:
                rate_from = exchange_rates.get(comp.currency)
                rate_to = exchange_rates.get(merchant_currency)
                if rate_from and rate_to and display_price:
                    display_price = round(display_price * (rate_to / rate_from), 2)

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

        return {
            "status": "success",
            "product_id": product_id,
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
