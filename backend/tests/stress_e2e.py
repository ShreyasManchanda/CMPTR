"""
Full system E2E test: discover → analyze/jobs → decisions.
Run from backend/:
    python tests/stress_e2e.py
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
        "name": "Stussy hoodie",
        "product_url": "https://www.stussy.com/collections/sweats/products/1924740faded-graphic-zip-hoodie-washed-olive",
        "min_comps": 2,
    },
    {
        "name": "Tentree hoodie",
        "product_url": "https://www.tentree.com/products/getaway-relaxed-hoodie-meteorite-black-light-moss",
        "min_comps": 2,
    },
]

MALL = ("hollister", "shein", "boohoo", "forever21", "abercrombie")


def headers():
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def discover(product_url: str) -> dict:
    t0 = time.time()
    r = requests.post(
        f"{BASE}/discover-competitors",
        json={"product_url": product_url},
        headers=headers(),
        timeout=180,
    )
    r.raise_for_status()
    data = r.json()
    data["_elapsed"] = round(time.time() - t0, 1)
    return data


def analyze_job(product_url: str, competitor_urls: list[str]) -> dict:
    t0 = time.time()
    r = requests.post(
        f"{BASE}/analyze/jobs",
        json={"product_url": product_url, "competitor_urls": competitor_urls},
        headers=headers(),
        timeout=30,
    )
    r.raise_for_status()
    job = r.json()
    job_id = job["job_id"]

    for _ in range(90):
        time.sleep(3)
        poll = requests.get(f"{BASE}/analyze/jobs/{job_id}", headers=headers(), timeout=30)
        poll.raise_for_status()
        status = poll.json()
        if status["status"] in ("completed", "failed", "error"):
            status["_elapsed"] = round(time.time() - t0, 1)
            return status
    raise TimeoutError(f"Job {job_id} did not finish in 270s")


def run_case(case: dict) -> tuple[bool, list[str]]:
    notes: list[str] = []
    ok = True

    print(f"\n{'='*60}\n{case['name']}\n{'='*60}")

    # 1. Discover
    try:
        disc = discover(case["product_url"])
        stores = disc.get("suggestions", [])
        notes.append(f"Discover: {len(stores)} stores in {disc['_elapsed']}s, price={disc.get('merchant_price')}")
        if not stores:
            notes.append("FAIL: discover returned no stores")
            return False, notes
        mall = [s["store"] for s in stores if any(m in s["store"].lower() for m in MALL)]
        if mall:
            notes.append(f"WARN: mall brands in discover: {mall}")
        else:
            notes.append("OK: discover peers look reasonable")
        print(json.dumps({k: v for k, v in disc.items() if k != "suggestions"}, indent=2))
        print("Stores:", [s["store"] for s in stores])
    except Exception as e:
        notes.append(f"FAIL discover: {e}")
        return False, notes

    # 2. Analyze with top 4 discovered stores
    comp_urls = [s["url"] for s in stores[:4]]
    try:
        job = analyze_job(case["product_url"], comp_urls)
        notes.append(f"Analyze job: status={job['status']} in {job.get('_elapsed')}s")
        if job["status"] != "completed":
            notes.append(f"FAIL analyze: {job.get('error', job)}")
            return False, notes

        result = job.get("result") or {}
        comps = result.get("competitors") or result.get("competitor_details") or []
        decision = result.get("decision") or {}
        action = decision.get("final_action") or decision.get("action") or result.get("action")
        my_price = result.get("my_price")
        decision_id = result.get("decision_id")

        notes.append(f"OK: action={action}, my_price={my_price}, comps={len(comps)}, decision_id={decision_id}")

        if len(comps) < case["min_comps"]:
            notes.append(f"FAIL: only {len(comps)} matched comps (need {case['min_comps']})")
            ok = False
        else:
            notes.append(f"OK: {len(comps)} matched competitors")
            for c in comps[:5]:
                name = c.get("product_name", "?")
                price = c.get("price", c.get("current_price", "?"))
                store = c.get("store", "?")
                notes.append(f"  - {store}: {name} @ {price}")

        if not action:
            notes.append("WARN: no pricing action returned")
        if not decision_id:
            notes.append("WARN: no decision_id (persistence may have failed)")

        print(json.dumps({
            "action": action,
            "my_price": my_price,
            "comp_count": len(comps),
            "decision_id": decision_id,
            "suggested_price": decision.get("suggested_price") or result.get("suggested_price"),
        }, indent=2))

        # 3. Fetch decision from DB
        if decision_id:
            dec = requests.get(f"{BASE}/decisions/{decision_id}", headers=headers(), timeout=15)
            if dec.status_code == 200:
                notes.append(f"OK: decision/{decision_id} persisted")
            else:
                notes.append(f"WARN: decision fetch returned {dec.status_code}")

    except Exception as e:
        notes.append(f"FAIL analyze: {e}")
        ok = False

    return ok, notes


def main():
    print(f"E2E system test @ {BASE}\n")

    # Health
    h = requests.get(f"{BASE}/health", timeout=10).json()
    print(f"Health: {h}")
    if h.get("status") != "ok":
        print("FAIL: backend unhealthy")
        sys.exit(1)

    passed = 0
    for case in CASES:
        ok, notes = run_case(case)
        for n in notes:
            print(f"  {n}")
        if ok:
            passed += 1

    print(f"\n{'='*60}")
    print(f"E2E: {passed}/{len(CASES)} cases passed")
    sys.exit(0 if passed == len(CASES) else 1)


if __name__ == "__main__":
    main()
