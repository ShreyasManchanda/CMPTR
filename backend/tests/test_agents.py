"""
Unified AI Agent Tests (Requires GEMINI_API_KEY).
Tests AmbiguityAgent and ExplanationAgent reasoning.

Run from backend/:
    python tests/test_agents.py
"""

import os
import sys
import json
from dotenv import load_dotenv

# Ensure the backend/ directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure we have our env setup utility
from utils.agent_setup import setup_agent_logging, setup_agent_environment

load_dotenv(dotenv_path="../../.env")
setup_agent_environment()

# COLOR HELPERS
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def header(title):
    print(f"\n{'='*60}")
    print(f"{CYAN}  TESTING: {title}{RESET}")
    print(f"{'='*60}")

def test_agents():
    if not os.getenv("GEMINI_API_KEY"):
        print(f"{RED}ERROR: GEMINI_API_KEY not found. Skipping AI tests.{RESET}")
        return

    from agent.ambiguity_agent import AmbiguityAgent
    from agent.explanation_agent import ExplanationAgent

    # 1. Ambiguity Agent
    header("Ambiguity Agent Reasoning")
    ambig = AmbiguityAgent()
    result = ambig.resolve_ambiguity(
        final_action="insufficient_samples",
        stats_map={"product_id": "test-shirt", "count": 1, "median_price": 50.0},
        metrics={"raw_count": 5, "normalized_count": 1}
    )
    print(f"{GREEN}[PASS]{RESET} Ambiguity advice: {str(result)[:200]}...")

    # 2. Explanation Agent
    header("Explanation Agent Output")
    explainer = ExplanationAgent()
    explanation = explainer.get_explanation(
        final_action={"final_action": "reduce", "suggested_price": 45.0, "confidence": 0.8},
        ambiguity_advice="None",
        metrics={"normalized_count": 5}
    )
    print(f"{GREEN}[PASS]{RESET} Explanation: {str(explanation)[:200]}...")

if __name__ == "__main__":
    test_agents()
