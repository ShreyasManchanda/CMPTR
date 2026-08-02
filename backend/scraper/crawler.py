import os
import re
import json
import logging
import time
from urllib.parse import urlparse, urlunparse
from firecrawl import FirecrawlApp
from crewai import LLM

from utils.domain import (
    brand_from_domain,
    brand_label_matches_domain,
    clean_product_name,
    is_blocked_discovery_domain,
    is_department_store_domain,
    is_tier_mismatch,
    normalize_domain,
    domains_match,
)
from utils.match import CATEGORY_KEYWORDS, COLOR_SIZE_WORDS, tokenize

logger = logging.getLogger(__name__)


class Crawler():
    """
    scrapes from the shopify stores
    """
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL API KEY not set")

        self.firecrawl = FirecrawlApp(api_key=api_key)
        
        os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', '')
        self.llm = LLM(
            model="gemini-2.5-flash",
            temperature=0.2,
            timeout=60,
        )

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

    @staticmethod
    def _normalize_search_items(response) -> list[dict]:
        """Normalize Firecrawl v1/v2 search payloads into a list of {url, ...} dicts."""
        items = None

        if response is None:
            return []

        if hasattr(response, "web") and response.web is not None:
            items = response.web
        elif hasattr(response, "data") and response.data is not None:
            items = response.data
        elif isinstance(response, dict):
            items = response.get("web") or response.get("data") or []
        elif isinstance(response, list):
            items = response

        if not items:
            return []

        normalized: list[dict] = []
        for item in items:
            if hasattr(item, "model_dump"):
                item = item.model_dump()
            elif hasattr(item, "dict"):
                item = item.dict()
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append({"url": item})
        return normalized

    def _firecrawl_search(self, search_query: str, *, max_retries: int = 4):
        """Run Firecrawl search with rate-limit / transient retries."""
        retry_delay = 3.0
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.firecrawl.search(search_query)
            except Exception as e:
                last_error = e
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
                        f"Firecrawl search retry for {search_query!r} "
                        f"(attempt {attempt + 1}/{max_retries}): {e}. Waiting {wait:.0f}s..."
                    )
                    time.sleep(wait)
                    retry_delay = min(retry_delay * 2, 60)
                    continue
                raise
        if last_error:
            raise last_error
        return None

    def _parse_llm_json(self, raw: str) -> dict | list | None:
        text = (raw or "").strip()
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return None

    def _get_peer_brand_context(
        self,
        merchant_brand: str,
        product_name: str,
        *,
        merchant_price: float | None = None,
        currency: str | None = None,
        merchant_domain: str | None = None,
    ) -> dict:
        """
        One structured Gemini call: peer brands + avoid list + store search queries.
        """
        price_line = (
            f"Merchant price: {merchant_price} {currency or 'USD'}"
            if merchant_price and merchant_price > 0
            else "Merchant price: unknown"
        )
        prompt = f"""You help e-commerce merchants find true peer-brand competitors.

A competitor is the same product category AND similar price tier AND similar brand positioning/audience — direct-to-consumer retail, NOT resale marketplaces, NOT editorial sites.

Merchant brand: {merchant_brand}
Product: {product_name}
{price_line}
Merchant domain: {merchant_domain or "unknown"}

Return ONLY valid JSON:
{{
  "positioning": "short label e.g. streetwear mid-premium",
  "peer_brands": ["Brand A", "Brand B"],
  "avoid_brands": ["Hollister", "Shein"],
  "search_queries": ["Brand A official store buy", "brands like Brand B apparel"]
}}

Rules:
- peer_brands: 6-10 DTC retail brands shoppers cross-shop with {merchant_brand} for this product type.
- avoid_brands: mall/fast-fashion/discount brands that sell similar keywords but are NOT peers.
- search_queries: exactly 3 Firecrawl queries using PEER brand names and "official store", NOT the merchant SKU.
"""
        empty = {
            "positioning": "",
            "peer_brands": [],
            "avoid_brands": [],
            "search_queries": [],
        }
        try:
            res = self.llm.call(messages=[{"role": "user", "content": prompt}])
            parsed = self._parse_llm_json(res)
            if not isinstance(parsed, dict):
                return empty

            peer_brands = [
                str(b).strip()
                for b in (parsed.get("peer_brands") or [])
                if b and str(b).strip()
            ]
            avoid_brands = [
                str(b).strip()
                for b in (parsed.get("avoid_brands") or [])
                if b and str(b).strip()
            ]
            search_queries = [
                clean_product_name(str(q))
                for q in (parsed.get("search_queries") or [])
                if q and str(q).strip()
            ]
            positioning = str(parsed.get("positioning") or "").strip()

            ctx = {
                "positioning": positioning,
                "peer_brands": peer_brands[:10],
                "avoid_brands": avoid_brands[:15],
                "search_queries": search_queries[:3],
            }
            logger.info(
                "Peer brand context for %s: positioning=%r peers=%s avoid=%s",
                merchant_brand,
                positioning,
                peer_brands[:6],
                avoid_brands[:6],
            )
            return ctx
        except Exception as e:
            logger.error(f"Failed to generate peer brand context: {e}")
            return empty

    def _is_avoided_brand(self, domain: str, avoid_brands: list[str]) -> bool:
        for label in avoid_brands:
            if brand_label_matches_domain(label, domain):
                return True
        return False

    def _should_skip_discovery_candidate(
        self,
        domain: str,
        *,
        exclude: set[str],
        avoid_brands: list[str],
        merchant_domain: str | None,
    ) -> bool:
        if not domain or is_blocked_discovery_domain(domain):
            return True
        if is_department_store_domain(domain):
            return True
        if any(domains_match(domain, ex) for ex in exclude):
            return True
        if merchant_domain and is_tier_mismatch(merchant_domain, domain):
            return True
        if self._is_avoided_brand(domain, avoid_brands):
            return True
        return False

    def _retail_score(self, source_url: str, domain: str) -> int:
        """Higher = more likely a direct retail storefront."""
        score = 0
        path = (urlparse(source_url).path or "").lower()
        # Heuristics for "scrape-unfriendly" pages that often show up in search results.
        if any(x in path for x in ("/stores", "/locations", "/store-locator", "/dealers", "/dealer-locator")):
            score -= 5
        if any(x in path for x in ("/password", "/login", "/sign-in", "/account")):
            score -= 7
        if "/products/" in path or "/product/" in path:
            score += 3
        if "/collections/" in path and "/products/" in path:
            score += 2
        elif "/collections/" in path:
            score -= 1
        if any(x in path for x in ("/listing/", "/used/", "/resale/", "/marketplace/")):
            score -= 4
        if any(x in path for x in ("/article/", "/blog/", "/news/", "/guide")):
            score -= 5
        # Prefer shorter, brand-like domains over long SEO blogs
        if len(domain.split(".")) <= 2:
            score += 1
        return score

    @staticmethod
    def score_product_url(url: str, product_name: str = "") -> int:
        """Rank competitor product URLs; higher is better. <=0 means reject."""
        parsed = urlparse(url)
        path = (parsed.path or "").lower()
        if not path or path == "/":
            return -5

        score = 0
        if "/products/" in path or "/product/" in path:
            score += 6
        if "/shop/" in path and ("/p/" in path or path.rstrip("/").split("/")[-1].isdigit()):
            score += 5
        if re.search(r"/p/\w+", path):
            score += 4

        # Category / listing pages
        if "/collections/" in path and "/products/" not in path:
            score -= 12
        if any(
            frag in path
            for frag in (
                "/category/",
                "/categories/",
                "/guide",
                "/lookbook",
                "sold-out",
                "notification",
                "/search",
                "/cart",
                "/checkout",
                "/account",
                "/blog/",
                "/article/",
            )
        ):
            score -= 10

        # Prefer slug overlap with the merchant product name
        slug = path.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ")
        slug_tokens = tokenize(slug)
        name_tokens = tokenize(product_name) - COLOR_SIZE_WORDS
        if slug_tokens and name_tokens:
            shared = slug_tokens & name_tokens
            score += min(4, len(shared) * 2)
            cats = name_tokens & CATEGORY_KEYWORDS
            if cats and (slug_tokens & cats):
                score += 3

        return score

    def _collect_from_search(
        self,
        search_query: str,
        unique_domains: dict,
        exclude: set[str],
        max_results: int,
        matched_query: str,
        *,
        avoid_brands: list[str] | None = None,
        merchant_domain: str | None = None,
    ) -> None:
        logger.info(f"Discovering competitor stores with search: {search_query}")
        avoid = avoid_brands or []
        try:
            response = self._firecrawl_search(search_query)
            data = self._normalize_search_items(response)

            candidates: list[tuple[int, str, dict]] = []

            for item in data:
                url = item.get("url")
                if not url:
                    continue

                parsed = urlparse(url)
                if not parsed.netloc:
                    continue

                domain = normalize_domain(parsed.netloc)
                if self._should_skip_discovery_candidate(
                    domain,
                    exclude=exclude,
                    avoid_brands=avoid,
                    merchant_domain=merchant_domain,
                ):
                    continue

                root_url = urlunparse((parsed.scheme or "https", parsed.netloc, "", "", "", ""))
                if root_url in unique_domains:
                    continue

                entry = {
                    "store": parsed.netloc,
                    "url": root_url,
                    "matched_query": matched_query,
                    "source_url": url,
                }
                score = self._retail_score(url, domain)
                if score < 1:
                    continue
                candidates.append((score, root_url, entry))

            candidates.sort(key=lambda row: row[0], reverse=True)
            for _, root_url, entry in candidates:
                # Avoid overwriting a higher-scored candidate with a later lower-scored duplicate.
                if root_url in unique_domains:
                    continue
                unique_domains[root_url] = entry
                if len(unique_domains) >= max_results:
                    return
        except Exception as e:
            logger.error(f"Firecrawl discovery search error for {search_query}: {e}")

    def _fixed_search_queries(self, product_name: str) -> list[str]:
        """Deterministic search ladder — no LLM latency on the analyze path."""
        cleaned = clean_product_name(product_name)
        if not cleaned:
            return []

        tokens = cleaned.split()
        shortened = " ".join(t for t in tokens if t.lower() not in COLOR_SIZE_WORDS)
        if not shortened.strip():
            shortened = cleaned

        found = [t for t in tokens if t.lower() in CATEGORY_KEYWORDS]
        category = " ".join(dict.fromkeys(found)) if found else (tokens[-1] if tokens else cleaned)

        queries = [cleaned]
        if shortened.lower() != cleaned.lower():
            queries.append(shortened)
        if category.lower() not in {q.lower() for q in queries}:
            queries.append(category)
        return queries

    def find_competitor_product(self, store_domain: str, product_name: str, max_results: int = 3) -> list[str]:
        queries = self._fixed_search_queries(product_name)
        ranked: dict[str, int] = {}
        pool_limit = max(8, max_results * 3)

        for q in queries:
            if len([s for s in ranked.values() if s >= 3]) >= pool_limit:
                break

            search_query = f"{q} site:{store_domain}"
            logger.info(f"Trying search: {search_query}")
            try:
                response = self._firecrawl_search(search_query)
                data = self._normalize_search_items(response)

                for item in data or []:
                    url = item.get("url")
                    if not url:
                        continue
                    score = self.score_product_url(url, product_name)
                    prev = ranked.get(url, -999)
                    if score > prev:
                        ranked[url] = score
            except Exception as e:
                logger.error(f"Firecrawl search error for {search_query}: {e}")

        # Prefer real product URLs; fall back to best available if none score well.
        strong = [(u, s) for u, s in ranked.items() if s >= 3]
        pool = strong if strong else list(ranked.items())
        pool.sort(key=lambda row: row[1], reverse=True)
        limited = [u for u, _ in pool[:max_results]]

        if limited:
            logger.info(
                f"Returning {len(limited)} ranked links for {product_name} on {store_domain}: "
                f"{[(u, ranked[u]) for u in limited]}"
            )
            return limited

        logger.warning(f"Could not find any products for {product_name} on {store_domain}")
        return []

    def discover_competitor_stores(
        self,
        product_name: str,
        max_results: int = 5,
        *,
        exclude_domains: list[str] | None = None,
        merchant_brand: str | None = None,
        merchant_domain: str | None = None,
        merchant_price: float | None = None,
        currency: str | None = None,
        fast: bool = True,
    ) -> list[dict]:
        """
        Find competitor storefront URLs via peer-brand Firecrawl search.

        One Gemini call (when merchant brand is known) returns peer brands + avoid list.
        """
        cleaned = clean_product_name(product_name)
        brand = (merchant_brand or "").strip()
        merchant_dom = normalize_domain(merchant_domain or "")
        exclude = {normalize_domain(d) for d in (exclude_domains or []) if d}
        unique_domains: dict[str, dict] = {}
        peer_ctx: dict = {}

        if brand:
            peer_ctx = self._get_peer_brand_context(
                brand,
                cleaned,
                merchant_price=merchant_price,
                currency=currency,
                merchant_domain=merchant_dom,
            )
        avoid_brands = peer_ctx.get("avoid_brands") or []
        collect_kw = {
            "avoid_brands": avoid_brands,
            "merchant_domain": merchant_dom or None,
        }

        # 1) Peer-brand official store searches (best signal)
        peer_queries: list[str] = []
        peer_limit = 3 if fast else 8
        for peer in (peer_ctx.get("peer_brands") or [])[:peer_limit]:
            peer_queries.append(f"{peer} official store buy -stockx -grailed")
        for q in (peer_ctx.get("search_queries") or [])[: 2 if fast else 5]:
            if q not in peer_queries:
                peer_queries.append(f"{q} -stockx -grailed")

        for q in peer_queries:
            if len(unique_domains) >= max_results:
                break
            self._collect_from_search(
                q, unique_domains, exclude, max_results, q, **collect_kw
            )
            # Pace searches to stay under Firecrawl free-tier req/min limits.
            if fast:
                time.sleep(2.5)

        # 2) Lightweight deterministic fallback if peers didn't fill quota
        if fast and len(unique_domains) < max_results:
            if brand:
                quick_queries = [
                    f"brands like {brand} official store apparel -stockx -grailed",
                    f"{brand} competitors similar brand shop online",
                ]
            else:
                quick_queries = [
                    f"{cleaned} official store buy",
                    f"{cleaned} apparel brand shop",
                ]
            for q in quick_queries:
                if len(unique_domains) >= max_results:
                    break
                self._collect_from_search(
                    q, unique_domains, exclude, max_results, q, **collect_kw
                )

        results = list(unique_domains.values())
        if peer_ctx.get("positioning"):
            for row in results:
                row["positioning"] = peer_ctx["positioning"]

        if results:
            logger.info(
                "Discovered %s competitor stores for %s: %s",
                len(results),
                cleaned,
                [r.get("store") for r in results],
            )
            return results

        logger.warning(f"No competitor stores discovered for {cleaned}")
        return []
