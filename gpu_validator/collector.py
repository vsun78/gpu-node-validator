import json
from pathlib import Path

class TelemetryLoadError(Exception):
    """Raised when telemetry cannot be loaded or has an invalid structure."""

def load_node(path: str | Path) -> dict:
    """Load and perform basic structural checks on GPU node telemetry."""
    
    try:
        with open(path, encoding="utf-8") as file:
            node_data = json.load(file)

    except OSError as error:
        raise TelemetryLoadError(
            f"Could not read telemetry file: {path}"
        ) from error

    except json.JSONDecodeError as error:
        raise TelemetryLoadError(
            f"Telemetry file contains invalid JSON: {path}"
        )from error

    if not isinstance(node_data, dict):
        raise TelemetryLoadError(
            "Telemetry root must be a JSON object."
        )

    if "node_id" not in node_data:
        raise TelemetryLoadError(
            "Telemetry is missing required key: node_id"
        )

    if not isinstance(node_data["node_id"], str):
        raise TelemetryLoadError(
            "Telemetry node_id must be a string."
        )

    if not node_data["node_id"].strip():
        raise TelemetryLoadError(
            "Telemetry node_id cannot be empty."
        )

    if "gpus" not in node_data:
        raise TelemetryLoadError(
            "Telemetry is missing required key: gpus"
        )

    if not isinstance(node_data["gpus"], list):
        raise TelemetryLoadError(
            "Telemetry gpus must be a JSON array."
        )

    return node_data