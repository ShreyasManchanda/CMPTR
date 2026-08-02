"""
Stress test the full pipeline (discover -> analyze/jobs -> decision fetch)
for a single product URL.

Run from backend/:
    python tests/stress_single_product.py
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

PRODUCT_URL = "https://www.stussy.com/collections/sweats/products/1924740faded-graphic-zip-hoodie-washed-olive"

HEADERS = {"Content-Type": "application/json"}
if API_KEY:
    HEADERS["X-API-Key"] = API_KEY


def discover(product_url: str) -> dict:
    t0 = time.time()
    r = requests.post(
        f"{BASE}/discover-competitors",
        json={"product_url": product_url},
        headers=HEADERS,
        timeout=180,
    )
    r.raise_for_status()
    data = r.json()
    data["_elapsed_sec"] = round(time.time() - t0, 1)
    return data


def analyze_job(product_url: str, competitor_store_urls: list[str]) -> dict:
    r = requests.post(
        f"{BASE}/analyze/jobs",
        json={"product_url": product_url, "competitor_urls": competitor_store_urls},
        headers=HEADERS,
        timeout=60,
    )
    r.raise_for_status()
    job_id = r.json()["job_id"]

    t0 = time.time()
    for _ in range(120):  # 120 * 3s = 6 min
        time.sleep(3)
        poll = requests.get(f"{BASE}/analyze/jobs/{job_id}", headers=HEADERS, timeout=30)
        poll.raise_for_status()
        status = poll.json()
        if status["status"] in ("completed", "failed"):
            status["_elapsed_sec"] = round(time.time() - t0, 1)
            return status

    raise TimeoutError(f"Job {job_id} did not finish in time")


def main():
    runs = int(os.getenv("STRESS_SINGLE_RUNS", "3"))
    print(f"Stress test single product: {PRODUCT_URL}")
    print(f"Runs: {runs} | Base: {BASE}\n")

    passed = 0

    for i in range(runs):
        print("=" * 60)
        print(f"Run {i + 1}/{runs}")
        disc = discover(PRODUCT_URL)
        suggestions = disc.get("suggestions", [])
        stores = [s["url"] for s in suggestions[:4] if s.get("url")]

        print(f"Discover: {len(suggestions)} suggestions in {disc.get('_elapsed_sec')}s")
        print("Top stores:", stores)

        if not stores:
            print("FAIL: no stores discovered")
            continue

        job = analyze_job(PRODUCT_URL, stores)
        if job["status"] != "completed":
            print(f"FAIL: job failed: {job.get('error')}")
            continue

        res = job.get("result") or {}
        comps = res.get("metrics", {}).get("competitor_stats", [])
        decision = res.get("decision") or {}

        print(
            json.dumps(
                {
                    "action": decision.get("action"),
                    "my_price": res.get("my_price"),
                    "comps": len(comps),
                    "from_history": res.get("from_history"),
                    "fallback": res.get("fallback"),
                    "fallback_reason": res.get("fallback_reason"),
                    "decision_id": res.get("decision_id"),
                },
                indent=2,
            )
        )

        # "Pass" means we returned a usable completion (either fresh or cached).
        if res.get("from_history") and comps:
            passed += 1
        elif comps:
            passed += 1

    print("\n" + "=" * 60)
    print(f"Result: {passed}/{runs} runs produced competitor data")
    sys.exit(0 if passed >= max(1, runs - 1) else 1)


if __name__ == "__main__":
    main()

