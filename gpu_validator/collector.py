import json
from pathlib import Path


class TelemetryLoadError(Exception):
    """Raised when telemetry cannot be loaded or has an invalid structure."""


class ConfigLoadError(Exception):
    """Raised when validation configuration cannot be loaded or is invalid."""


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
        ) from error

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

    node_data.setdefault("telemetry_source", "json-file")

    return node_data


def load_config(path: str | Path) -> dict:
    """Load and validate the health-rule configuration."""
    try:
        with open(path, encoding="utf-8") as file:
            config = json.load(file)
    except OSError as error:
        raise ConfigLoadError(
            f"Could not read configuration file: {path}"
        ) from error
    except json.JSONDecodeError as error:
        raise ConfigLoadError(
            f"Configuration file contains invalid JSON: {path}"
        ) from error

    if not isinstance(config, dict):
        raise ConfigLoadError(
            "Configuration root must be a JSON object."
        )

    required_keys = (
        "expected_gpu_count",
        "max_temperature_c",
        "max_error_count",
    )

    for key in required_keys:
        if key not in config:
            raise ConfigLoadError(
                f"Configuration is missing required key: {key}"
            )

    expected_count = config["expected_gpu_count"]
    if (
        isinstance(expected_count, bool)
        or not isinstance(expected_count, int)
        or expected_count < 0
    ):
        raise ConfigLoadError(
            "Configuration expected_gpu_count must be a nonnegative integer."
        )

    max_temperature = config["max_temperature_c"]
    if (
        isinstance(max_temperature, bool)
        or not isinstance(max_temperature, (int, float))
    ):
        raise ConfigLoadError(
            "Configuration max_temperature_c must be a number."
        )

    max_errors = config["max_error_count"]
    if (
        isinstance(max_errors, bool)
        or not isinstance(max_errors, int)
        or max_errors < 0
    ):
        raise ConfigLoadError(
            "Configuration max_error_count must be a nonnegative integer."
        )

    return config
