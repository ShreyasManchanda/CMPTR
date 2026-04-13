from crewai import Agent, Crew, Process, Task, LLM
import json
from typing import Dict, Any, Optional, List
from utils.agent_setup import setup_agent_logging, setup_agent_environment, get_agent_config

logger = setup_agent_logging("explanation_agent")
setup_agent_environment()
agents_config = get_agent_config('explanation-agent')




class ExplanationAgent:

    def __init__(self):
        self.agents_config = agents_config

        self.llm = LLM(
            model="gemini-2.5-flash", 
            temperature=0.2, 
            timeout=120,           
            max_tokens=400,        
        )

        self.agent = Agent(
            role=self.agents_config['role'],
            goal=self.agents_config['goal'],
            backstory=self.agents_config['backstory'],
            llm= self.llm
        )

    def get_explanation(self, final_action, ambiguity_advice, metrics):
        task=Task(
            description=f"""
                You are given the final pricing decision and the supporting context.
                
                Final Action:
                {final_action}
                
                Ambiguity Advice:
                {ambiguity_advice}
                
                Metrics:
                {metrics}
                
                Write a clear Markdown explanation for a store owner in 3 t0 6 sentences.
                Explain what the system decided, why it decided that way, and what the merchant should do next.
                
                Rules:
                - Do not suggest prices.
                - Do not change the decision.
                - Do not mention raw URLs, HTML, or internal implementation details.
                """,
            expected_output="""
                A short Markdown explanation in 3 to 6 sentences that clearly explains the final pricing action, the reason behind it, any ambiguity advice if relevant, and the next step for the merchant.
                """,
            agent=self.agent
        )
        crew = Crew(
                agents=[self.agent],
                tasks = [task],
                process = Process.sequential
            )
        return crew.kickoff()







