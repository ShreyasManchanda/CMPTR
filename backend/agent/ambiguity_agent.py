from crewai import Agent, Crew, Process, Task, LLM
import json
from typing import Dict, Any, Optional, List
from utils.agent_setup import setup_agent_logging, setup_agent_environment, get_agent_config

logger = setup_agent_logging("ambiguity_agent")
setup_agent_environment()
agents_config = get_agent_config('ambiguity-agent')



class AmbiguityAgent:

    def __init__(self):
        self.agents_config = agents_config

        self.llm = LLM(
            model="gemini-2.5-flash",
            temperature=0.2,
            timeout=120,
            max_tokens=300,
        )

        self.agent = Agent(
            role=self.agents_config['role'],
            goal=self.agents_config['goal'],
            backstory=self.agents_config['backstory'],
            llm=self.llm
        )

    def resolve_ambiguity(self, final_action, stats_map, metrics):
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
            agent=self.agent
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential
        )

        return crew.kickoff()






