import json
from pathlib import Path

def load_node(path: str | Path) -> dict:
    """Load simulated GPU node telemetry from  a JSON file."""
    with open(path, encoding="utf-8") as file:
        node_data = json.load(file)

    return node_data