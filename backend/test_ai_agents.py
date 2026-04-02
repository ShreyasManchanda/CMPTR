"""
Test script for AI Agents (requires valid GEMINI_API_KEY in .env).

Run from inside the backend/ directory:
    python test_ai_agents.py
"""

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def header(title):
    print(f"\n{'='*60}")
    print(f"{CYAN}  TESTING: {title}{RESET}")
    print(f"{'='*60}")

def passed(msg):
    print(f"  {GREEN}[PASS]{RESET} — {msg}")

def failed(msg):
    print(f"  {RED}[FAIL]{RESET} — {msg}")


# Check API key first
if not os.getenv("GEMINI_API_KEY"):
    print(f"\n{RED}ERROR: GEMINI_API_KEY not found in environment.{RESET}")
    print(f"Set it in your .env file or export it before running this script.")
    exit(1)


# Fake context to pass to the agents
FAKE_FINAL_ACTION_REASON = "low_average_confidence"

FAKE_STATS = {
    "product_id": "cool-widget",
    "count": 3,
    "median_price": 45.0,
    "mean_price": 44.5,
    "stddev_price": 2.1,
    "avg_confidence": 0.45
}

FAKE_METRICS = {
    "raw_count": 8,
    "normalized_count": 5,
    "dropped_count": 3,
    "avg_confidence": 0.55,
    "low_confidence_pct": 0.4
}

FAKE_FINAL_DECISION = {
    "final_action": "manual_review",
    "suggested_price": None,
    "confidence": 0.45,
    "policy_reason": "low_average_confidence"
}


# ============================================================
# TEST: Ambiguity Agent
# ============================================================
header("Ambiguity Agent (LIVE AI CALL)")
try:
    from agent.ambiguity_agent import AmbiguityAgent

    agent = AmbiguityAgent()
    result = agent.resolve_ambiguity(
        final_action=FAKE_FINAL_ACTION_REASON,
        stats_map=FAKE_STATS,
        metrics=FAKE_METRICS
    )

    output = str(result)
    passed(f"Ambiguity Agent returned response ({len(output)} chars)")
    print(f"\n  {YELLOW}Response:{RESET}")
    print(f"  {output[:500]}")

except Exception as e:
    failed(f"Ambiguity Agent crashed: {e}")
    import traceback; traceback.print_exc()


# ============================================================
# TEST: Explanation Agent
# ============================================================
header("Explanation Agent (LIVE AI CALL)")
try:
    from agent.explanation_agent import ExplanationAgent

    agent = ExplanationAgent()
    result = agent.get_explanation(
        final_action=FAKE_FINAL_DECISION,
        ambiguity_advice="Recommended action: rescrape. Reasoning: Data quality is poor with high drop rate.",
        metrics=FAKE_METRICS
    )

    output = str(result)
    passed(f"Explanation Agent returned response ({len(output)} chars)")
    print(f"\n  {YELLOW}Response:{RESET}")
    print(f"  {output[:500]}")

except Exception as e:
    failed(f"Explanation Agent crashed: {e}")
    import traceback; traceback.print_exc()


print(f"\n{CYAN}{'='*60}")
print(f"  AI AGENT TESTS COMPLETE")
print(f"{'='*60}{RESET}\n")
