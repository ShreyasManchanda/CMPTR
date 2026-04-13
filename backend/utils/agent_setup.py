import os
import logging
from dotenv import load_dotenv
from config import load_agents_config

def setup_agent_logging(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)
    return logger

def setup_agent_environment():
    load_dotenv()
    os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')

def get_agent_config(agent_name: str):
    llm_config = load_agents_config()
    return llm_config.get(agent_name)
