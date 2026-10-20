import subprocess

import pytest

from gpu_validator.nvidia_collector import (
    NVIDIA_SMI_COMMAND,
    NvidiaSmiError,
    collect_nvidia_telemetry,
    parse_nvidia_smi_output,
)


SAMPLE_OUTPUT = (
    "0, NVIDIA GeForce RTX 3050 Ti Laptop GPU, "
    "51, 0, 0, 4096, 591.55\n"
)


def test_parse_nvidia_smi_output_normalizes_metrics() -> None:
    node = parse_nvidia_smi_output(
        SAMPLE_OUTPUT,
        node_id="surface-laptop",
    )

    assert node["node_id"] == "surface-laptop"
    assert node["telemetry_source"] == "nvidia-smi"
    assert node["collected_at_utc"]
    assert node["gpus"] == [
        {
            "gpu_id": 0,
            "name": "NVIDIA GeForce RTX 3050 Ti Laptop GPU",
            "detected": True,
            "temperature_c": 51,
            "error_count": None,
            "utilization_percent": 0,
            "memory_used_mb": 0,
            "memory_total_mb": 4096,
            "driver_version": "591.55",
        }
    ]


def test_parse_nvidia_smi_output_supports_multiple_gpus() -> None:
    output = SAMPLE_OUTPUT + (
        "1, NVIDIA RTX A4000, 63, 75, 2048, 16384, 591.55\n"
    )

    node = parse_nvidia_smi_output(output, node_id="gpu-node")

    assert len(node["gpus"]) == 2
    assert node["gpus"][1]["gpu_id"] == 1
    assert node["gpus"][1]["utilization_percent"] == 75


def test_parse_nvidia_smi_output_allows_optional_unavailable_metrics() -> None:
    output = (
        "0, NVIDIA GPU, 50, N/A, [N/A], Not Supported, 591.55\n"
    )

    node = parse_nvidia_smi_output(output, node_id="gpu-node")
    gpu = node["gpus"][0]

    assert gpu["temperature_c"] == 50
    assert gpu["utilization_percent"] is None
    assert gpu["memory_used_mb"] is None
    assert gpu["memory_total_mb"] is None


def test_parse_nvidia_smi_output_rejects_missing_fields() -> None:
    output = "0, NVIDIA GPU, 50\n"

    with pytest.raises(NvidiaSmiError, match="contained 3 fields"):
        parse_nvidia_smi_output(output)


def test_parse_nvidia_smi_output_requires_temperature() -> None:
    output = "0, NVIDIA GPU, N/A, 0, 0, 4096, 591.55\n"

    with pytest.raises(NvidiaSmiError, match="temperature.gpu"):
        parse_nvidia_smi_output(output)


def test_collect_nvidia_telemetry_runs_expected_command(
    monkeypatch,
) -> None:
    def fake_run(command, **options):
        assert command == NVIDIA_SMI_COMMAND
        assert options == {
            "capture_output": True,
            "text": True,
            "check": True,
            "timeout": 10,
        }
        return subprocess.CompletedProcess(
            command,
            returncode=0,
            stdout=SAMPLE_OUTPUT,
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    node = collect_nvidia_telemetry()

    assert node["telemetry_source"] == "nvidia-smi"
    assert node["gpus"][0]["temperature_c"] == 51


def test_collect_nvidia_telemetry_handles_missing_executable(
    monkeypatch,
) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(NvidiaSmiError, match="was not found"):
        collect_nvidia_telemetry()


def test_collect_nvidia_telemetry_handles_command_failure(
    monkeypatch,
) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=NVIDIA_SMI_COMMAND,
            stderr="driver unavailable",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(NvidiaSmiError, match="driver unavailable"):
        collect_nvidia_telemetry()
