"""Quick targeted analyze with scrape-friendly peer stores."""
import os, sys, time, json, requests
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
BASE = "http://127.0.0.1:8000"
h = {"Content-Type": "application/json", "X-API-Key": os.getenv("CMPT_API_KEY", "")}

CASES = [
    {
        "name": "Tentree (scrape-friendly peers)",
        "product_url": "https://www.tentree.com/products/getaway-relaxed-hoodie-meteorite-black-light-moss",
        "competitors": [
            "https://www.patagonia.com",
            "https://www.everlane.com",
            "https://vuoriclothing.com",
            "https://wearpact.com",
        ],
    },
    {
        "name": "Stussy (scrape-friendly peers)",
        "product_url": "https://www.stussy.com/collections/sweats/products/1924740faded-graphic-zip-hoodie-washed-olive",
        "competitors": [
            "https://www.carhartt-wip.com",
            "https://noahny.com",
            "https://representclo.com",
            "https://www.champion.com",
        ],
    },
]

def run(case):
    print(f"\n=== {case['name']} ===")
    r = requests.post(f"{BASE}/analyze/jobs", json={
        "product_url": case["product_url"],
        "competitor_urls": case["competitors"],
    }, headers=h, timeout=30)
    r.raise_for_status()
    job_id = r.json()["job_id"]
    t0 = time.time()
    for _ in range(90):
        time.sleep(3)
        s = requests.get(f"{BASE}/analyze/jobs/{job_id}", headers=h).json()
        if s["status"] in ("completed", "failed"):
            elapsed = round(time.time() - t0, 1)
            if s["status"] == "failed":
                print(f"FAILED in {elapsed}s:", s.get("error"))
                return False
            res = s["result"]
            stats = res.get("metrics", {}).get("competitor_stats", [])
            dec = res.get("decision", {})
            print(f"OK in {elapsed}s: action={dec.get('action')} price={res.get('my_price')} comps={len(stats)} id={res.get('decision_id')}")
            for c in stats[:6]:
                print(f"  {c.get('store')}: {c.get('product_name')} @ {c.get('price')} {c.get('original_currency')}")
            return len(stats) >= 2
    print("TIMEOUT")
    return False

ok = sum(run(c) for c in CASES)
print(f"\nTargeted analyze: {ok}/{len(CASES)} passed")
sys.exit(0 if ok == len(CASES) else 1)
