from pathlib import Path

import pytest

from gpu_validator.collector import (
    ConfigLoadError,
    TelemetryLoadError,
    load_config,
    load_node,
)


def test_load_node_reads_valid_json(tmp_path: Path) -> None:
    telemetry_file = tmp_path / "healthy.json"
    telemetry_file.write_text(
        '{"node_id": "node-01", "gpus": []}',
        encoding="utf-8",
    )

    result = load_node(telemetry_file)

    assert result["node_id"] == "node-01"
    assert result["gpus"] == []


def test_load_node_rejects_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.json"

    with pytest.raises(TelemetryLoadError, match="Could not read"):
        load_node(missing_file)


def test_load_node_rejects_malformed_json(tmp_path: Path) -> None:
    telemetry_file = tmp_path / "malformed.json"
    telemetry_file.write_text(
        '{"node_id": "node-01",',
        encoding="utf-8",
    )

    with pytest.raises(TelemetryLoadError, match="invalid JSON"):
        load_node(telemetry_file)


def test_load_node_requires_json_object(tmp_path: Path) -> None:
    telemetry_file = tmp_path / "list.json"
    telemetry_file.write_text(
        '["this", "is", "a", "list"]',
        encoding="utf-8",
    )

    with pytest.raises(TelemetryLoadError, match="JSON object"):
        load_node(telemetry_file)


def test_load_node_requires_node_id(tmp_path: Path) -> None:
    telemetry_file = tmp_path / "missing_node_id.json"
    telemetry_file.write_text(
        '{"gpus": []}',
        encoding="utf-8",
    )

    with pytest.raises(TelemetryLoadError, match="node_id"):
        load_node(telemetry_file)


def test_load_node_rejects_empty_node_id(tmp_path: Path) -> None:
    telemetry_file = tmp_path / "empty_node_id.json"
    telemetry_file.write_text(
        '{"node_id": "   ", "gpus": []}',
        encoding="utf-8",
    )

    with pytest.raises(TelemetryLoadError, match="cannot be empty"):
        load_node(telemetry_file)


def test_load_node_requires_gpus(tmp_path: Path) -> None:
    telemetry_file = tmp_path / "missing_gpus.json"
    telemetry_file.write_text(
        '{"node_id": "node-01"}',
        encoding="utf-8",
    )

    with pytest.raises(TelemetryLoadError, match="gpus"):
        load_node(telemetry_file)


def test_load_node_requires_gpu_list(tmp_path: Path) -> None:
    telemetry_file = tmp_path / "invalid_gpus.json"
    telemetry_file.write_text(
        '{"node_id": "node-01", "gpus": {}}',
        encoding="utf-8",
    )

    with pytest.raises(TelemetryLoadError, match="JSON array"):
        load_node(telemetry_file)


def test_load_config_reads_valid_config(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        (
            '{"expected_gpu_count": 2, '
            '"max_temperature_c": 85, '
            '"max_error_count": 0}'
        ),
        encoding="utf-8",
    )

    result = load_config(config_file)

    assert result["expected_gpu_count"] == 2
    assert result["max_temperature_c"] == 85
    assert result["max_error_count"] == 0


def test_load_config_rejects_malformed_json(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"expected_gpu_count": 2,',
        encoding="utf-8",
    )

    with pytest.raises(ConfigLoadError, match="invalid JSON"):
        load_config(config_file)


def test_load_config_requires_all_keys(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"expected_gpu_count": 2, "max_temperature_c": 85}',
        encoding="utf-8",
    )

    with pytest.raises(ConfigLoadError, match="max_error_count"):
        load_config(config_file)


def test_load_config_rejects_invalid_gpu_count(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        (
            '{"expected_gpu_count": "two", '
            '"max_temperature_c": 85, '
            '"max_error_count": 0}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigLoadError, match="nonnegative integer"):
        load_config(config_file)


def test_load_config_rejects_negative_error_limit(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        (
            '{"expected_gpu_count": 2, '
            '"max_temperature_c": 85, '
            '"max_error_count": -1}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigLoadError, match="nonnegative integer"):
        load_config(config_file)
