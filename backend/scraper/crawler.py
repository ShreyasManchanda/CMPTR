import os
import json
import re
import unicodedata
import logging
import time
from urllib.parse import urlparse, urlunparse
from firecrawl import FirecrawlApp
from crewai import LLM

logger = logging.getLogger(__name__)


class Crawler:
    """Searches competitor product pages and discovers likely competitor stores."""

    BANNED_DOMAINS = {
        'amazon.com',
        'ebay.com',
        'walmart.com',
        'etsy.com',
        'target.com',
        'aliexpress.com',
        'bestbuy.com',
        'shopify.com',
        'google.com',
        'facebook.com',
        'instagram.com',
        'twitter.com',
        'reddit.com',
        'youtube.com',
        'linkedin.com',
        'pinterest.com',
        'namecheap.com',
        'ionos.com',
        'godaddy.com',
        'wix.com',
        'squarespace.com',
        'wordpress.com',
        'medium.com',
        'wikipedia.org',
    }

    PRODUCT_PATH_HINTS = (
        '/product',
        '/products',
        '/shop',
        '/store',
        '/item',
        '/p/',
        '/buy',
    )

    NON_PRODUCT_PATH_HINTS = (
        '/blog',
        '/news',
        '/article',
        '/help',
        '/support',
        '/forum',
        '/community',
        '/docs',
        '/careers',
        '/about',
        '/contact',
        '/terms',
        '/privacy',
    )

    ECOMMERCE_HINTS = (
        'buy',
        'shop',
        'store',
        'product',
        'add to cart',
        'price',
        'sale',
        'collection',
        'in stock',
    )

    DISCOVERY_QUERY_HINTS = (
        'buy online',
        'product page',
        'shop',
        'store',
        'official',
        'sale',
    )

    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL_API_KEY not set")

        self.firecrawl = FirecrawlApp(api_key=api_key)

        os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', '')
        self.llm = LLM(
            model="gemini/gemini-2.5-flash",
            temperature=0.2,
            timeout=60,
        )

    def _extract_search_results(self, response) -> list[dict]:
        if isinstance(response, dict):
            return response.get("data", [])
        return getattr(response, "data", [])

    def _base_domain(self, netloc: str) -> str:
        domain = netloc.lower().replace('www.', '')
        return domain

    def _is_banned_domain(self, netloc: str) -> bool:
        domain = self._base_domain(netloc)
        return any(domain == banned or domain.endswith(f'.{banned}') for banned in self.BANNED_DOMAINS)

    def _is_likely_product_url(self, url: str, title: str = '', description: str = '') -> bool:
        parsed = urlparse(url)
        path = (parsed.path or '').lower()

        if any(hint in path for hint in self.NON_PRODUCT_PATH_HINTS):
            return False

        if any(hint in path for hint in self.PRODUCT_PATH_HINTS):
            return True

        context = f"{title} {description}".lower()
        return any(hint in context for hint in self.ECOMMERCE_HINTS)

    def _is_explicitly_non_product_url(self, url: str) -> bool:
        parsed = urlparse(url)
        path = (parsed.path or '').lower()
        return any(hint in path for hint in self.NON_PRODUCT_PATH_HINTS)

    def _score_discovery_candidate(
        self,
        url: str,
        title: str,
        description: str,
        search_query: str,
        domain_seen_count: int,
    ) -> int:
        score = 0

        parsed = urlparse(url)
        path = (parsed.path or '').lower()
        context = f"{title} {description}".lower()
        query_l = search_query.lower()

        if any(h in path for h in self.PRODUCT_PATH_HINTS):
            score += 4
        if any(h in context for h in self.ECOMMERCE_HINTS):
            score += 3
        if any(h in query_l for h in self.DISCOVERY_QUERY_HINTS):
            score += 1
        if path in ('', '/'):
            score += 1
        if domain_seen_count > 0:
            score += min(domain_seen_count, 3)

        return score

    def _get_search_queries(self, product_name: str) -> list[str]:
        prompt = f"""
        Given the specific e-commerce product name: "{product_name}"

        Your task: Generate 3 search query strings that would help find this product on competitor websites.

        CRITICAL RULES:
        - Return ONLY search queries (keywords/phrases people type into search engines)
        - DO NOT include store names, domains, or URLs (e.g., NO "mohawkgeneralstore.com", NO "amazon.com")
        - DO NOT hallucinate specific retailers
        - Focus on: brand name, product type, key attributes, category
        - Keep queries concise (2-5 words each)
        - Remove special characters, hyphens, and extra words

        Output format: JSON array of 3 strings
        Example for "Nike Air Max 90 Running Shoes": ["Nike Air Max 90", "Nike running shoes", "athletic sneakers"]
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
        except Exception as e:
            logger.error(f"Failed to generate search queries: {e}")

        return [self._clean_product_name(product_name), "shirt", "clothing"]

    def _clean_product_name(self, product_name: str) -> str:
        cleaned = product_name or ""
        cleaned = cleaned.replace("â€”", " ").replace("â€“", " ").replace("â€˜", "'").replace("â€™", "'")
        cleaned = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode("ascii")
        cleaned = re.sub(r"[|/]+", " ", cleaned)
        cleaned = cleaned.replace("—", " ").replace("–", " ").replace("-", " ")
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        parts = cleaned.split()
        return " ".join(parts[:8]) if parts else product_name

    def find_competitor_product(self, store_domain: str, product_name: str, max_results: int = 3) -> list[str]:
        queries = self._get_search_queries(product_name)
        all_links: list[str] = []
        seen = set()

        for q in queries:
            if len(all_links) >= max_results:
                break

            search_query = f"{q} site:{store_domain}"
            logger.info(f"Trying search: {search_query}")

            max_retries = 3
            retry_delay = 2
            data = None

            for attempt in range(max_retries):
                try:
                    response = self.firecrawl.search(search_query)
                    data = self._extract_search_results(response)
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    is_transient = "502" in error_str or "503" in error_str or "504" in error_str or "timeout" in error_str or "gateway" in error_str
                    
                    if is_transient and attempt < max_retries - 1:
                        logger.warning(f"Firecrawl search transient error for {search_query} (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(f"Firecrawl search error for {search_query} after {attempt + 1} attempts: {e}")
                        continue

            if not data:
                continue

            strict_hits = []
            fallback_hits = []

            for item in data:
                url = item.get("url")
                if not url or url in seen:
                    continue

                title = item.get("title", "")
                desc = item.get("description", "")
                if self._is_likely_product_url(url, title, desc):
                    strict_hits.append(url)
                else:
                    fallback_hits.append(url)

            ordered_hits = strict_hits + fallback_hits
            for url in ordered_hits:
                if len(all_links) >= max_results:
                    break
                if url in seen:
                    continue
                seen.add(url)
                all_links.append(url)

            logger.info(f"Found {len(ordered_hits)} links for query '{q}' (total kept: {len(all_links)})")

        if all_links:
            logger.info(f"Returning {len(all_links)} total links for {product_name} on {store_domain}")
            return all_links[:max_results]

        logger.warning(f"Could not find any products for {product_name} on {store_domain}")
        return []

    def discover_competitor_stores(self, product_name: str, max_results: int = 5) -> list[dict]:
        cleaned_product = self._clean_product_name(product_name)
        llm_queries = self._get_search_queries(cleaned_product)
        queries = []
        queries.extend(q for q in llm_queries if q)
        if cleaned_product:
            queries.extend(
                [
                    cleaned_product,
                    f"\"{cleaned_product}\"",
                    f"{cleaned_product} buy online",
                    f"{cleaned_product} price",
                    f"{cleaned_product} sale",
                ]
            )
            cleaned_tokens = cleaned_product.split()
            if cleaned_tokens:
                queries.append(" ".join(cleaned_tokens[:3]))
                queries.append(" ".join(cleaned_tokens[:2]))
        queries = list(dict.fromkeys(queries))
        unique_domains: dict[str, dict] = {}
        domain_seen_count: dict[str, int] = {}
        loose_fallback_domains: dict[str, dict] = {}
        stop_terms = {
            "the", "and", "for", "with", "from", "tops", "shirts", "shirt", "brown", "black",
            "white", "men", "women", "kids", "sale", "new"
        }
        term_tokens = [t for t in cleaned_product.lower().split() if len(t) > 2 and t not in stop_terms]
        if not term_tokens and cleaned_product:
            term_tokens = [t for t in cleaned_product.lower().split() if len(t) > 1][:3]

        discovery_queries = []
        for q in queries:
            discovery_queries.extend(
                [
                    q,
                    f'"{q}" buy online',
                    f'"{q}" product page',
                    f'{q} shop',
                    f'{q} online store',
                ]
            )
        if term_tokens:
            short_query = " ".join(term_tokens[:3])
            discovery_queries.extend(
                [
                    short_query,
                    f"{short_query} buy",
                    f"{short_query} official store",
                ]
            )
        discovery_queries = list(dict.fromkeys(discovery_queries))

        for search_query in discovery_queries:
            if len(unique_domains) >= max_results:
                break

            logger.info(f"Discovering competitor stores with search: {search_query}")
            
            max_retries = 3
            retry_delay = 2
            data = None

            for attempt in range(max_retries):
                try:
                    response = self.firecrawl.search(search_query)
                    data = self._extract_search_results(response)
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    is_transient = "502" in error_str or "503" in error_str or "504" in error_str or "timeout" in error_str or "gateway" in error_str
                    
                    if is_transient and attempt < max_retries - 1:
                        logger.warning(f"Firecrawl discovery search transient error for {search_query} (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(f"Firecrawl discovery search error for {search_query} after {attempt + 1} attempts: {e}")
                        continue

            if not data:
                logger.info(f"No search results for '{search_query}'")
                continue

            logger.info(f"Discovery search results for '{search_query}': {len(data)}")

            for item in data:
                url = item.get("url")
                if not url:
                    continue

                parsed = urlparse(url)
                if not parsed.netloc:
                    continue

                if self._is_banned_domain(parsed.netloc):
                    continue

                root_url = urlunparse((parsed.scheme or "https", parsed.netloc, "", "", "", ""))
                if root_url not in loose_fallback_domains:
                    loose_fallback_domains[root_url] = {
                        "store": parsed.netloc,
                        "url": root_url,
                        "matched_query": search_query,
                        "source_url": url,
                    }

                title = item.get("title", "")
                desc = item.get("description", "")
                domain_seen_count[root_url] = domain_seen_count.get(root_url, 0) + 1

                likely_product = self._is_likely_product_url(url, title, desc)
                score = self._score_discovery_candidate(
                    url=url,
                    title=title,
                    description=desc,
                    search_query=search_query,
                    domain_seen_count=domain_seen_count[root_url],
                )
                if likely_product:
                    score += 5
                else:
                    score += 1

                context = f"{title} {desc}".lower()
                if any(tok in context for tok in term_tokens):
                    score += 2
                if any(h in context for h in self.ECOMMERCE_HINTS):
                    score += 2

                if root_url in unique_domains:
                    if score > unique_domains[root_url]["score"]:
                        unique_domains[root_url].update(
                            {
                                "matched_query": search_query,
                                "source_url": url,
                                "score": score,
                                "likely_product": likely_product,
                            }
                        )
                    continue

                unique_domains[root_url] = {
                    "store": parsed.netloc,
                    "url": root_url,
                    "matched_query": search_query,
                    "source_url": url,
                    "score": score,
                    "likely_product": likely_product,
                }

        ranked = sorted(
            unique_domains.values(),
            key=lambda x: (x["likely_product"], x["score"]),
            reverse=True,
        )
        results = [
            {
                "store": item["store"],
                "url": item["url"],
                "matched_query": item["matched_query"],
                "source_url": item["source_url"],
            }
            for item in ranked[:max_results]
        ]
        if results:
            logger.info(f"Discovered {len(results)} competitor stores for {product_name}")
            return results

        if loose_fallback_domains:
            fallback_results = list(loose_fallback_domains.values())[:max_results]
            logger.warning(
                f"No strong product-page matches for {product_name}; returning {len(fallback_results)} loose domain matches."
            )
            return fallback_results

        logger.warning(f"No competitor stores discovered for {product_name}")
        return []
