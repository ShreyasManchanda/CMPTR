"""
Live stress test for /discover-competitors.
Run from backend/:
    python tests/stress_discover.py
"""
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

BASE = os.getenv("CMPT_API_BASE", "http://127.0.0.1:8000")
API_KEY = os.getenv("CMPT_API_KEY", "")

CASES = [
    {
        "name": "Stussy hoodie (streetwear)",
        "url": "https://www.stussy.com/collections/sweats/products/1924740faded-graphic-zip-hoodie-washed-olive",
        "bad_fragments": ("hollister", "shein", "boohoo", "forever21", "abercrombie", "stockx", "grailed", "nordstrom", "rei.com"),
        "good_fragments": ("represent", "carhartt", "obey", "champion", "kith", "palace", "noah", "stussy"),
    },
    {
        "name": "Tentree hoodie (sustainable outdoor)",
        "url": "https://www.tentree.com/products/getaway-relaxed-hoodie-meteorite-black-light-moss",
        "bad_fragments": ("hollister", "shein", "boohoo", "stockx", "grailed", "fast fashion", "nordstrom", "rei.com"),
        "good_fragments": ("patagonia", "prana", "columbia", "reformation", "everlane", "allbirds", "tentree"),
    },
]

MALL_FRAGMENTS = (
    "hollister", "abercrombie", "forever21", "boohoo", "shein",
    "fashionnova", "aeropostale", "pacsun", "oldnavy",
)


def discover(product_url: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    t0 = time.time()
    r = requests.post(
        f"{BASE}/discover-competitors",
        json={"product_url": product_url},
        headers=headers,
        timeout=120,
    )
    elapsed = time.time() - t0
    r.raise_for_status()
    data = r.json()
    data["_elapsed_sec"] = round(elapsed, 1)
    return data


def score_case(case: dict, result: dict) -> tuple[int, list[str]]:
    notes: list[str] = []
    score = 0
    stores = [s.get("store", "").lower() for s in result.get("suggestions", [])]
    urls = [s.get("url", "").lower() for s in result.get("suggestions", [])]

    if not stores:
        notes.append("FAIL: no suggestions returned")
        return 0, notes

    score += 2
    notes.append(f"OK: {len(stores)} stores in {result.get('_elapsed_sec')}s")

    mall_hits = [s for s in stores if any(m in s for m in MALL_FRAGMENTS)]
    if mall_hits:
        notes.append(f"FAIL: mall/fast-fashion leaked: {mall_hits}")
    else:
        score += 3
        notes.append("OK: no mall/fast-fashion domains")

    bad = [s for s in stores if any(b in s for b in case["bad_fragments"])]
    if bad:
        notes.append(f"WARN: bad fragments in stores: {bad}")
    else:
        score += 2
        notes.append("OK: no explicitly bad fragments")

    good = [s for s in stores if any(g in s for g in case["good_fragments"])]
    if good:
        score += 2
        notes.append(f"OK: plausible peers found: {good[:4]}")
    else:
        notes.append(f"WARN: no expected peer fragments in {stores}")

    positioning = next(
        (s.get("positioning") for s in result.get("suggestions", []) if s.get("positioning")),
        None,
    )
    if positioning:
        score += 1
        notes.append(f"OK: positioning={positioning!r}")

    if result.get("merchant_price"):
        notes.append(f"OK: merchant_price={result['merchant_price']} {result.get('currency', '')}")

    return score, notes


def main():
    print(f"Stress testing discover at {BASE}\n")
    total = 0
    max_score = 0
    for case in CASES:
        print("=" * 60)
        print(case["name"])
        print(case["url"])
        try:
            result = discover(case["url"])
            print(json.dumps(result, indent=2))
            case_score, notes = score_case(case, result)
            total += case_score
            max_score += 10
            for n in notes:
                print(f"  {n}")
        except Exception as e:
            print(f"  ERROR: {e}")
            max_score += 10
        print()

    print("=" * 60)
    print(f"Total score: {total}/{max_score}")
    if total >= max_score * 0.7:
        print("PASS: discover quality acceptable")
        sys.exit(0)
    print("FAIL: discover needs more tuning")
    sys.exit(1)


if __name__ == "__main__":
    main()
