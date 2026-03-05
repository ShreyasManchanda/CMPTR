import os
from crewai import Agent, Crew, Process, Task, LLM
from config import load_agents_config
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import logging


logger = logging.getLogger("ambiguity_agent_direct")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)



load_dotenv()
os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')

llm_config = load_agents_config()
agents_config = llm_config['explanation-agent']




class ExplanationAgent:
    llm = LLM(
    model="gemini-2.5-flash", 
    temperature=0.2, 
    timeout=120,           
    max_tokens=400,        
)

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

    def get_explanation(self, )
    







