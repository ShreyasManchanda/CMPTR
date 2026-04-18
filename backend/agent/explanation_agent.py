import logging
from typing import Optional

from crewai import Crew, Process, Task

from pricing.rules_agent import FinalAction
from utils.agent_setup import create_crewai_agent

logger = logging.getLogger(__name__)


class ExplanationAgent:

    def __init__(self):
        self.agent = create_crewai_agent("explanation-agent", max_tokens=400)

    def get_explanation(
        self,
        final_action: FinalAction,
        ambiguity_advice: Optional[str],
        metrics: dict,
    ):
        task = Task(
            description=f"""
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
                - Do not suggest prices.
                - Do not change the decision.
                - Do not mention raw URLs, HTML, or internal implementation details.
                """,
            expected_output="""
                A short Markdown explanation in 3 to 6 sentences that clearly explains the final pricing action, the reason behind it, any ambiguity advice if relevant, and the next step for the merchant.
                """,
            agent=self.agent,
        )
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
        )
        return crew.kickoff()
