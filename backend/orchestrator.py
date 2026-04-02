import logging
from typing import List, Dict, Any
from dataclasses import asdict

from scraper.crawler import Crawler
from scraper.scraper import Scraper
from normalizer.normalize_product import ProductNormalizer, NormalizedProduct
from pricing.pricing_engine import PricingEngine, Recommendation
from pricing.rules_agent import RulesAgent, FinalAction
from agent.ambiguity_agent import AmbiguityAgent
from agent.explanation_agent import ExplanationAgent

logger = logging.getLogger(__name__)

class PricingOrchestrator:
    def __init__(self):
        # 1. Initialize all specialized tools and agents
        self.crawler = Crawler()
        self.scraper = Scraper()
        self.normalizer = ProductNormalizer()
        self.engine = PricingEngine()
        self.rules = RulesAgent()
        
        self.ambiguity_ai = AmbiguityAgent()
        self.explainer_ai = ExplanationAgent()

    def run_pipeline(self, my_product_url: str, competitor_store_urls: List[str]) -> Dict[str, Any]:
        """
        Runs the end-to-end pricing pipeline.
        """
        logger.info(f"Starting pipeline for product: {my_product_url}")
        
        # --- PHASE 1: Scrape YOUR Product ---
        raw_my_product = self.scraper.scrape_product(my_product_url)
        norm_my_product, diag = self.normalizer.normalize_product(raw_my_product)

        # If we can't figure out the price of your own product, stop the pipeline.
        if not norm_my_product or not norm_my_product.current_price:
            logger.error("Could not parse your product URL or find its current price.")
            return {
                "status": "error", 
                "message": "Could not parse your product URL or find its current price."
            }

        my_price = norm_my_product.current_price
        product_id = norm_my_product.product_id
        merchant_currency = norm_my_product.currency

        logger.info(f"Target product identified: ID={product_id}, Price={my_price} {merchant_currency}")

        # --- PHASE 2: Collect Market Data (The Loop) ---
        all_competitor_raw_data = []
        overall_scrape_stats = []

        for store_url in competitor_store_urls:
            logger.info(f"Crawling competitor store: {store_url}")
            links = self.crawler.crawl_website(store_url)
            
            if not links:
                logger.warning(f"No product links found on {store_url}")
                continue
                
            logger.info(f"Batch scraping {len(links)} products from {store_url}")
            raw_products, stats = self.scraper.batch_scrape_products(links)
            
            all_competitor_raw_data.extend(raw_products)
            overall_scrape_stats.append({
                "store": store_url,
                "stats": stats
            })

        if not all_competitor_raw_data:
            return {
                 "status": "error",
                 "message": "No competitor data found across provided stores.",
                 "product_id": product_id,
                 "my_price": my_price
            }

        # --- PHASE 3: Normalize Everything ---
        logger.info(f"Normalizing {len(all_competitor_raw_data)} competitor products.")
        normalized_competitors, norm_metrics = self.normalizer.normalize_batch(all_competitor_raw_data)

        # --- PHASE 4: Deterministic Pricing Math ---
        # The engine expects a list of dicts. We convert Pydantic objects using .model_dump() / .dict()
        competitor_dicts = [p.dict() for p in normalized_competitors]
        
        recommendation: Recommendation = self.engine.recommend_for(
            product_id=product_id,
            my_price=my_price,
            competitors_products=competitor_dicts,
            merchant_currency=merchant_currency
        )

        # --- PHASE 5: Apply Policy Rules ---
        final_decision: FinalAction = self.rules.decide(recommendation)
        logger.info(f"Rule Agent decision: {final_decision.final_action}")

        # --- PHASE 6: AI Ambiguity Resolution (Branching) ---
        ambiguity_advice = None
        if final_decision.final_action == "manual_review":
            logger.info("Decision is manual_review, invoking Ambiguity Agent.")
            ambiguity_advice = str(self.ambiguity_ai.resolve_ambiguity(
                final_action=final_decision.policy_reason,
                stats_map=recommendation.stats,
                metrics=norm_metrics
            ))

        # --- PHASE 7: AI Explanation (The Final Output) ---
        logger.info("Invoking Explanation Agent.")
        human_explanation = str(self.explainer_ai.get_explanation(
            final_action=final_decision,
            ambiguity_advice=ambiguity_advice,
            metrics=norm_metrics
        ))

        # --- Return Final Payload ---
        return {
            "status": "success",
            "product_id": product_id,
            "my_price": my_price,
            "currency": merchant_currency,
            "decision": {
                "action": final_decision.final_action,
                "suggested_price": final_decision.suggested_price,
                "policy_reason": final_decision.policy_reason,
                "confidence": final_decision.confidence
            },
            "ai_advice": ambiguity_advice,
            "explanation": human_explanation,
            "metrics": {
                "scrape_stats": overall_scrape_stats,
                "normalization": norm_metrics,
                "competitor_stats": asdict(recommendation.stats) if recommendation.stats else None
            }
        }
