"""Product-name similarity helpers used to filter false competitor matches."""

from __future__ import annotations

import re
from typing import Iterable, Set


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "for",
    "with",
    "of",
    "in",
    "on",
    "to",
    "by",
    "from",
    "mens",
    "men",
    "womens",
    "women",
    "unisex",
    "new",
    "sale",
    "official",
    "online",
    "store",
    "shop",
}

CATEGORY_KEYWORDS = {
    "hoodie",
    "hoodies",
    "sweatshirt",
    "sweatshirts",
    "crewneck",
    "crew",
    "zip",
    "jacket",
    "jackets",
    "pants",
    "jeans",
    "shorts",
    "tee",
    "tees",
    "tshirt",
    "shirt",
    "shirts",
    "sneaker",
    "sneakers",
    "runner",
    "runners",
    "shoe",
    "shoes",
    "boot",
    "boots",
    "hat",
    "cap",
    "beanie",
    "bag",
    "bags",
    "dress",
    "skirt",
    "coat",
    "pullover",
    "sweater",
    "sweaters",
    "sock",
    "socks",
}

COLOR_SIZE_WORDS = {
    "black",
    "white",
    "washed",
    "olive",
    "green",
    "blue",
    "red",
    "grey",
    "gray",
    "navy",
    "brown",
    "beige",
    "cream",
    "pink",
    "purple",
    "yellow",
    "orange",
    "meteorite",
    "moss",
    "light",
    "dark",
    "xs",
    "s",
    "m",
    "l",
    "xl",
    "xxl",
    "small",
    "medium",
    "large",
}


def tokenize(name: str | None) -> Set[str]:
    if not name:
        return set()
    tokens = set(_TOKEN_RE.findall(name.lower()))
    return {t for t in tokens if len(t) > 1 and t not in _STOPWORDS}


def category_tokens(name: str | None) -> Set[str]:
    return tokenize(name) & CATEGORY_KEYWORDS


def name_similarity(a: str | None, b: str | None) -> float:
    """Jaccard similarity over normalized name tokens in [0, 1]."""
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def content_overlap(a: str | None, b: str | None) -> int:
    ta = tokenize(a) - COLOR_SIZE_WORDS
    tb = tokenize(b) - COLOR_SIZE_WORDS
    return len(ta & tb)


def is_likely_match(
    merchant_name: str | None,
    competitor_name: str | None,
    *,
    threshold: float = 0.15,
) -> bool:
    """
    Category-aware gate for retail comps.

    When the merchant name has a category (hoodie/tee/…), require a shared
    category token. Otherwise fall back to Jaccard similarity.
    """
    tm, tc = tokenize(merchant_name), tokenize(competitor_name)
    if not tm or not tc:
        return False

    cat_m = tm & CATEGORY_KEYWORDS
    cat_c = tc & CATEGORY_KEYWORDS

    if cat_m:
        shared_cat = cat_m & cat_c
        if not shared_cat:
            return False
        # Same category: accept if there is real overlap (category counts)
        # or soft Jaccard for near-titles.
        overlap = content_overlap(merchant_name, competitor_name)
        if overlap >= 1:
            return True
        return name_similarity(merchant_name, competitor_name) >= threshold

    return name_similarity(merchant_name, competitor_name) >= threshold


def filter_matching_products(
    merchant_name: str | None,
    products: Iterable,
    *,
    threshold: float = 0.15,
    name_attr: str = "product_name",
) -> tuple[list, list]:
    """Split products into (matched, rejected) by category-aware similarity."""
    matched, rejected = [], []
    for product in products:
        if hasattr(product, name_attr):
            name = getattr(product, name_attr)
        elif isinstance(product, dict):
            name = product.get(name_attr)
        else:
            name = None
        score = name_similarity(merchant_name, name)
        if is_likely_match(merchant_name, name, threshold=threshold):
            matched.append(product)
        else:
            rejected.append({
                "name": name,
                "score": round(score, 3),
                "categories": sorted(category_tokens(name)),
            })
    return matched, rejected
