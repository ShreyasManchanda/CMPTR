"""
AI Agent tests (requires GEMINI_API_KEY).

Run from backend/:
    python tests/test_agents.py
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(dotenv_path="../../.env")

from tests.helpers import header, passed, RED, RESET


def test_agents():
    if not os.getenv("GEMINI_API_KEY"):
        print(f"{RED}ERROR: GEMINI_API_KEY not found. Skipping AI tests.{RESET}")
        return

    from agent.ambiguity_agent import AmbiguityAgent
    from agent.explanation_agent import ExplanationAgent

    header("Ambiguity Agent Reasoning")
    ambig = AmbiguityAgent()
    result = ambig.resolve_ambiguity(
        final_action="insufficient_samples",
        stats_map={"product_id": "test-shirt", "count": 1, "median_price": 50.0},
        metrics={"raw_count": 5, "normalized_count": 1},
    )
    passed(f"Ambiguity advice: {str(result)[:200]}...")

    header("Explanation Agent Output")
    explainer = ExplanationAgent()
    explanation = explainer.get_explanation(
        final_action={"final_action": "reduce", "suggested_price": 45.0, "confidence": 0.8},
        ambiguity_advice=None,
        metrics={"normalized_count": 5},
    )
    passed(f"Explanation: {str(explanation)[:200]}...")


if __name__ == "__main__":
    test_agents()
