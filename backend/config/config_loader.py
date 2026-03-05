import yaml
from pathlib import Path

def load_agents_config(config_path: str='config/agents.yaml') -> dict:
    with open(Path(config_path),'r') as f:
        return yaml.safe_load(f)