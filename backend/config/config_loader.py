import yaml
from pathlib import Path


def load_agents_config(config_path: str | None = None) -> dict:
    """Load agents.yaml relative to this package unless an absolute path is given."""
    if config_path is None:
        path = Path(__file__).resolve().parent / "agents.yaml"
    else:
        path = Path(config_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path.name
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
