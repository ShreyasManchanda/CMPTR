import logging
from typing import Optional

from crewai import Crew, Process, Task

from pricing.pricing_engine import CompetitorStats
from utils.agent_setup import create_crewai_agent

logger = logging.getLogger(__name__)


class AmbiguityAgent:

    def __init__(self):
        self.agent = create_crewai_agent("ambiguity-agent", max_tokens=300)

    def resolve_ambiguity(
        self,
        final_action: str,
        stats_map: Optional[CompetitorStats],
        metrics: dict,
    ):
        task = Task(
            description=f"""
                You are given a pricing decision that resulted in "manual_review" due to uncertainty.

                Your job is to determine the safest next action for a human based on data quality and market signals.

                Final Action:
                {final_action}

                Competitor Stats:
                {stats_map}

                Data Quality Metrics:
                {metrics}

                Choose exactly ONE of the following actions:
                - rescrape → if data quality is poor or insufficient
                - ignore_outliers → if extreme values are distorting the dataset
                - manual_review → if the situation is still too uncertain

                Rules:
                - You must NOT suggest prices.
                - You must NOT override system policy.
                - You must return only ONE action.
                - Be conservative in your decision.

                Output must be JSON only with:
                - recommended_action
                - reasoning (under 40 words)
                - confidence_in_advice (0.0 to 1.0)
                """,
            expected_output="""
                A JSON object with:
                {
                "recommended_action": "rescrape | ignore_outliers | manual_review",
                "reasoning": "short explanation under 40 words",
                "confidence_in_advice": float between 0.0 and 1.0
                }
                """,
            agent=self.agent,
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
        )

        return crew.kickoff()
