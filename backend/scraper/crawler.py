import os
import json
import logging
from urllib.parse import urlparse, urlunparse

from firecrawl import FirecrawlApp
from crewai import LLM

logger = logging.getLogger(__name__)


class Crawler:
    """Discovers and searches competitor product pages via Firecrawl search."""

    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL_API_KEY not set")

        self.firecrawl = FirecrawlApp(api_key=api_key)

        os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', '')
        self.llm = LLM(
            model="gemini-2.5-flash",
            temperature=0.2,
            timeout=60,
        )

    def _get_search_queries(self, product_name: str) -> list[str]:
        prompt = f"""
        Given the specific e-commerce product name: "{product_name}"
        Return ONLY a JSON array of 3 strings mapping to search queries:
        1. A cleaned up exact product name.
        2. A broader category + key descriptor.
        3. The most generic category.
        Example: ["Exact Product Name", "Broad Descriptor Name", "Generic Category"]
        """
        try:
            res = self.llm.call(messages=[{"role": "user", "content": prompt}])
            text = res.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]

            queries = json.loads(text.strip())
            if isinstance(queries, list) and len(queries) > 0:
                logger.info(f"Generated search queries: {queries}")
                return queries
        except (json.JSONDecodeError, ValueError, RuntimeError) as e:
            logger.error(f"Failed to generate search queries: {e}")

        return [product_name, "shirt", "clothing"]

    def _extract_search_results(self, response) -> list[dict]:
        """Extract data list from Firecrawl search response."""
        if isinstance(response, dict):
            return response.get("data", [])
        return getattr(response, "data", [])

    def find_competitor_product(self, store_domain: str, product_name: str, max_results: int = 3) -> list[str]:
        queries = self._get_search_queries(product_name)
        all_links: set[str] = set()

        for q in queries:
            if len(all_links) >= max_results:
                break

            search_query = f"{q} site:{store_domain}"
            logger.info(f"Trying search: {search_query}")
            try:
                response = self.firecrawl.search(search_query)
                data = self._extract_search_results(response)

                if data:
                    links = [item.get("url") for item in data if item.get("url")]
                    all_links.update(links)
                    logger.info(f"Found {len(links)} links for query '{q}' (total: {len(all_links)})")
            except Exception as e:
                logger.error(f"Firecrawl search error for '{search_query}': {e}")

        if all_links:
            limited_links = list(all_links)[:max_results]
            logger.info(f"Returning {len(limited_links)} total links for {product_name} on {store_domain}")
            return limited_links

        logger.warning(f"Could not find any products for {product_name} on {store_domain}")
        return []

    def discover_competitor_stores(self, product_name: str, max_results: int = 5) -> list[dict]:
        queries = self._get_search_queries(product_name)
        unique_domains: dict[str, dict] = {}
        blacklist = {
            'amazon.com', 'ebay.com', 'walmart.com', 'etsy.com', 'target.com',
            'aliexpress.com', 'bestbuy.com', 'shopify.com', 'google.com',
            'facebook.com', 'instagram.com', 'twitter.com',
        }

        for q in queries:
            if len(unique_domains) >= max_results:
                break

            search_query = f"{q} direct competitor stores selling {product_name}"
            logger.info(f"Discovering competitor stores: {search_query}")
            try:
                response = self.firecrawl.search(search_query)
                data = self._extract_search_results(response)

                for item in data:
                    url = item.get("url")
                    if not url:
                        continue

                    parsed = urlparse(url)
                    if not parsed.netloc:
                        continue

                    domain = parsed.netloc.lower()
                    if any(b in domain for b in blacklist):
                        continue

                    root_url = urlunparse((parsed.scheme or "https", parsed.netloc, "", "", "", ""))
                    if root_url in unique_domains:
                        continue

                    unique_domains[root_url] = {
                        "store": parsed.netloc,
                        "url": root_url,
                        "matched_query": q,
                        "source_url": url,
                    }

                    if len(unique_domains) >= max_results:
                        break

            except Exception as e:
                logger.error(f"Firecrawl discovery search error for '{search_query}': {e}")

        results = list(unique_domains.values())
        if results:
            logger.info(f"Discovered {len(results)} competitor stores for {product_name}")
            return results

        logger.warning(f"No competitor stores discovered for {product_name}")
        return []
