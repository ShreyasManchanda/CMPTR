import os
import logging
from typing import Optional

from dotenv import load_dotenv
from crewai import Agent, LLM

from config import load_agents_config


def setup_agent_logging(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)
    return logger


def setup_agent_environment():
    load_dotenv()
    os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', '')


def get_agent_config(agent_name: str) -> dict:
    return load_agents_config().get(agent_name)


def create_crewai_agent(
    config_name: str,
    max_tokens: int = 300,
    temperature: float = 0.2,
    timeout: int = 120,
) -> Agent:
    """Factory: builds a CrewAI Agent from the agents.yaml config."""
    setup_agent_environment()
    cfg = get_agent_config(config_name)

    llm = LLM(
        model="gemini-2.5-flash",
        temperature=temperature,
        timeout=timeout,
        max_tokens=max_tokens,
    )

    return Agent(
        role=cfg['role'],
        goal=cfg['goal'],
        backstory=cfg['backstory'],
        llm=llm,
    )
