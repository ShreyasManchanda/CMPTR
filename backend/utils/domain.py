"""Domain helpers for competitor discovery filtering."""

from __future__ import annotations

from urllib.parse import urlparse

# Domains that are never valid competitor storefronts.
DISCOVERY_BLACKLIST = {
    "amazon.com",
    "ebay.com",
    "walmart.com",
    "etsy.com",
    "target.com",
    "aliexpress.com",
    "bestbuy.com",
    "shopify.com",
    "google.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "redd.it",
    "old.reddit.com",
    "youtube.com",
    "youtu.be",
    "pinterest.com",
    "quora.com",
    "tiktok.com",
    "linkedin.com",
    "wikipedia.org",
    "medium.com",
    "blogspot.com",
    "wordpress.com",
    "tumblr.com",
    "yelp.com",
    "trustpilot.com",
    "glassdoor.com",
    "indeed.com",
    "news.google.com",
    "bbc.com",
    "cnn.com",
    "nytimes.com",
    # Resale / marketplace / aggregator — not direct retail competitors
    "stockx.com",
    "grailed.com",
    "goat.com",
    "depop.com",
    "poshmark.com",
    "mercari.com",
    "vinted.com",
    "tradesy.com",
    "buyma.com",
    "kickscrew.com",
    "reversible.com",
    "editorialist.com",
    "stylight.com",
    "lyst.com",
    "therealreal.com",
    "vestiairecollective.com",
    "flightclub.com",
    "stadiumgoods.com",
    "klekt.com",
    "novelship.com",
    # Editorial / media / aggregators — not retail competitors
    "gq.com",
    "vogue.com",
    "menshealth.com",
    "womenshealthmag.com",
    "lemon8-app.com",
    "thegoodtrade.com",
    "eco-stylist.com",
    "modesens.com",
    "shopstyle.com",
    "wirecutter.com",
    "nytimes.com",
    "forbes.com",
    "businessinsider.com",
    "hypebeast.com",
    "highsnobiety.com",
    "complex.com",
    "ssense.com",  # luxury multi-brand marketplace-ish
    "anyasreviews.com",
    "coca-colastore.com",
}

# Substrings that usually indicate resale, not a brand storefront.
MARKETPLACE_DOMAIN_FRAGMENTS = (
    "stockx",
    "grailed",
    "goat",
    "depop",
    "poshmark",
    "mercari",
    "vinted",
    "buyma",
    "kickscrew",
    "reversible",
    "editorialist",
    "therealreal",
    "vestiaire",
    "flightclub",
    "stadiumgoods",
    "klekt",
    "novelship",
    "farfetch",
    "modesens",
    "shopstyle",
    "hypebeast",
    "highsnobiety",
    "lemon8",
)

STORE_PREFIXES = {"www", "shop", "store", "us", "uk", "ca", "eu", "m"}

# Mall / fast-fashion — valid peers only when the merchant is in the same tier.
MALL_FAST_FASHION_DOMAINS = {
    "hollisterco.com",
    "hollister.com",
    "abercrombie.com",
    "abercrombiekids.com",
    "forever21.com",
    "boohoo.com",
    "boohooman.com",
    "shein.com",
    "shein.co.uk",
    "fashionnova.com",
    "primark.com",
    "hm.com",
    "h&m.com",
    "aeropostale.com",
    "ae.com",
    "americaneagle.com",
    "pacsun.com",
    "romwe.com",
    "prettylittlething.com",
    "missguided.com",
    "asos.com",
    "oldnavy.com",
    "gap.com",
    "bananarepublic.com",
    "express.com",
    "forever21.com",
    "cottonon.com",
    "uniqlo.com",
    "zara.com",
    "pullandbear.com",
    "bershka.com",
    "stradivarius.com",
    "topshop.com",
    "riverisland.com",
    "newlook.com",
    "nastygal.com",
    "wish.com",
    "temu.com",
}

MALL_FAST_FASHION_FRAGMENTS = (
    "hollister",
    "abercrombie",
    "forever21",
    "boohoo",
    "shein",
    "fashionnova",
    "aeropostale",
    "americaneagle",
    "pacsun",
    "prettylittlething",
    "missguided",
    "oldnavy",
    "romwe",
    "nastygal",
)

# Multi-brand department / aggregator retail — not DTC peer brands.
DEPARTMENT_STORE_DOMAINS = {
    "nordstrom.com",
    "macys.com",
    "bloomingdales.com",
    "saks.com",
    "saksfifthavenue.com",
    "neimanmarcus.com",
    "barneys.com",
    "selfridges.com",
    "harrods.com",
    "johnlewis.com",
    "rei.com",
    "backcountry.com",
    "dickssportinggoods.com",
    "footlocker.com",
    "finishline.com",
    "jd.com",
    "zappos.com",
}


def normalize_domain(netloc: str | None) -> str:
    if not netloc:
        return ""
    domain = netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def domain_from_url(url: str | None) -> str:
    if not url:
        return ""
    return normalize_domain(urlparse(url).netloc)


def domains_match(a: str | None, b: str | None) -> bool:
    da, db = normalize_domain(a), normalize_domain(b)
    if not da or not db:
        return False
    return da == db or da.endswith(f".{db}") or db.endswith(f".{da}")


def is_blocked_discovery_domain(domain: str, extra: set[str] | None = None) -> bool:
    domain = normalize_domain(domain)
    if not domain:
        return True

    blocked = DISCOVERY_BLACKLIST | (extra or set())
    for needle in blocked:
        if domain == needle or domain.endswith(f".{needle}"):
            return True

    # Forums / social path patterns on otherwise unknown hosts
    junk_fragments = ("reddit", "facebook", "instagram", "twitter", "youtube", "pinterest")
    if any(fragment in domain for fragment in junk_fragments):
        return True

    return any(fragment in domain for fragment in MARKETPLACE_DOMAIN_FRAGMENTS)


def brand_from_domain(domain: str | None) -> str:
    """Best-effort merchant brand label from a store domain (e.g. stussy.com → Stussy)."""
    domain = normalize_domain(domain)
    if not domain:
        return ""
    parts = [p for p in domain.split(".") if p and p not in STORE_PREFIXES]
    if not parts:
        return ""
    # Prefer registrable label before TLD (stussy from stussy.com or shop.stussy.com)
    brand_token = parts[-2] if len(parts) >= 2 and parts[-1] in {"com", "co", "net", "io", "org", "shop"} else parts[0]
    if brand_token in STORE_PREFIXES and len(parts) > 1:
        brand_token = parts[0]
    return brand_token.replace("-", " ").title()


def product_name_from_url(url: str) -> str:
    """Fast product name guess from URL slug — no network call."""
    path = (urlparse(url).path or "").strip("/")
    if not path:
        return ""
    slug = path.split("/")[-1]
    slug = slug.replace("-", " ").replace("_", " ")
    parts = slug.split()
    return " ".join(parts).title() if parts else ""


def clean_product_name(name: str) -> str:
    """Strip leading SKU codes and extra whitespace from product titles."""
    if not name:
        return ""
    parts = name.strip().split()
    # Drop leading numeric SKU tokens (e.g. "118553 Faded Graphic Hoodie")
    while parts and (parts[0].isdigit() or (len(parts[0]) >= 5 and parts[0][:5].isdigit())):
        parts.pop(0)
    cleaned = " ".join(parts).strip()
    return cleaned or name.strip()


def is_mall_fast_fashion_domain(domain: str) -> bool:
    domain = normalize_domain(domain)
    if not domain:
        return False
    for needle in MALL_FAST_FASHION_DOMAINS:
        if domain == needle or domain.endswith(f".{needle}"):
            return True
    return any(fragment in domain for fragment in MALL_FAST_FASHION_FRAGMENTS)


def is_department_store_domain(domain: str) -> bool:
    domain = normalize_domain(domain)
    if not domain:
        return False
    for needle in DEPARTMENT_STORE_DOMAINS:
        if domain == needle or domain.endswith(f".{needle}"):
            return True
    return False


def is_tier_mismatch(merchant_domain: str, competitor_domain: str) -> bool:
    """Reject mall/fast-fashion comps when the merchant is not in that tier."""
    merchant = normalize_domain(merchant_domain)
    competitor = normalize_domain(competitor_domain)
    if not merchant or not competitor:
        return False
    if is_mall_fast_fashion_domain(competitor) and not is_mall_fast_fashion_domain(merchant):
        return True
    return False


def brand_label_matches_domain(brand_label: str, domain: str) -> bool:
    """True if a brand name token appears in the domain (e.g. Hollister → hollisterco.com)."""
    label = (brand_label or "").lower().strip()
    domain = normalize_domain(domain)
    if not label or not domain:
        return False
    token = label.replace(" ", "").replace("-", "")
    domain_flat = domain.replace("-", "").replace(".", "")
    if len(token) < 3:
        return False
    return token in domain_flat or token in domain
