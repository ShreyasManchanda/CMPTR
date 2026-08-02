import logging
import os
from typing import Optional

from crewai import LLM

from pricing.rules_agent import FinalAction

logger = logging.getLogger(__name__)


class ExplanationAgent:
    """Direct Gemini call — avoids CrewAI kickoff overhead for a single text task."""

    def __init__(self):
        os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
        self.llm = LLM(
            model="gemini-2.5-flash",
            temperature=0.2,
            timeout=60,
        )

    def get_explanation(
        self,
        final_action: FinalAction,
        ambiguity_advice: Optional[dict],
        metrics: dict,
    ) -> str:
        prompt = f"""
You are given the final pricing decision and the supporting context.

Final Action:
{final_action}

Ambiguity Advice:
{ambiguity_advice}

Metrics:
{metrics}

Write a clear Markdown explanation for a store owner in 3 to 6 sentences.
Explain what the system decided, why it decided that way, and what the merchant should do next.

Rules:
- You MAY state the engine's suggested_price and current confidence exactly as given.
- Do NOT invent a different price or change the decision.
- Do not mention raw URLs, HTML, or internal implementation details.
""".strip()

        try:
            result = self.llm.call(messages=[{"role": "user", "content": prompt}])
            text = str(result).strip()
            return text or "Pricing recommendation is ready. Review the suggested price against your margins before applying it."
        except Exception as e:
            logger.error(f"Explanation agent failed: {e}")
            action = getattr(final_action, "final_action", "review")
            price = getattr(final_action, "suggested_price", None)
            if price is not None:
                return (
                    f"The system recommends **{action}** with a suggested price of **{price}**. "
                    "Review competitor positioning and margin impact before changing your live price."
                )
            return (
                f"The system recommends **{action}**. "
                "Review the competitor sample and confidence before making a pricing change."
            )
