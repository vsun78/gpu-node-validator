import json
from pathlib import Path

import pytest

from main import main
from gpu_validator.nvidia_collector import NvidiaSmiError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config.json"
HEALTHY_PATH = PROJECT_ROOT / "samples" / "healthy_node.json"
UNHEALTHY_PATH = PROJECT_ROOT / "samples" / "unhealthy_node.json"


def test_healthy_node_prints_pass_and_returns_zero(capsys) -> None:
    exit_code = main(
        [
            "--input",
            str(HEALTHY_PATH),
            "--config",
            str(CONFIG_PATH),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Status: PASS" in captured.out
    assert "No validation failures." in captured.out
    assert captured.err == ""


def test_unhealthy_node_prints_fail_and_returns_one(capsys) -> None:
    exit_code = main(
        [
            "--input",
            str(UNHEALTHY_PATH),
            "--config",
            str(CONFIG_PATH),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Status: FAIL" in captured.out
    assert "GPU 0 is not detected." in captured.out
    assert "temperature 95 C exceeds limit 85 C" in captured.out
    assert "error count 2 exceeds limit 0" in captured.out
    assert captured.err == ""


def test_missing_input_prints_error_and_returns_two(
    tmp_path: Path,
    capsys,
) -> None:
    missing_path = tmp_path / "missing.json"

    exit_code = main(
        [
            "--input",
            str(missing_path),
            "--config",
            str(CONFIG_PATH),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "ERROR: Could not read telemetry file" in captured.err


def test_output_option_writes_json_report(
    tmp_path: Path,
    capsys,
) -> None:
    report_path = tmp_path / "reports" / "healthy.json"

    exit_code = main(
        [
            "--input",
            str(HEALTHY_PATH),
            "--config",
            str(CONFIG_PATH),
            "--output",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["node_id"] == "node-01"
    assert report["status"] == "PASS"
    assert report["failures"] == []
    assert "Status: PASS" in captured.out
    assert captured.err == ""


def test_unwritable_output_returns_two(
    tmp_path: Path,
    capsys,
) -> None:
    directory_instead_of_file = tmp_path / "report.json"
    directory_instead_of_file.mkdir()

    exit_code = main(
        [
            "--input",
            str(HEALTHY_PATH),
            "--config",
            str(CONFIG_PATH),
            "--output",
            str(directory_instead_of_file),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "ERROR: Could not write JSON report" in captured.err


def test_live_nvidia_collects_validates_and_reports(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    live_config = tmp_path / "config.nvidia.json"
    live_config.write_text(
        (
            '{"expected_gpu_count": 1, '
            '"max_temperature_c": 85, '
            '"max_error_count": 0}'
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "live-report.json"

    monkeypatch.setattr(
        "main.collect_nvidia_telemetry",
        lambda: {
            "node_id": "surface-laptop",
            "telemetry_source": "nvidia-smi",
            "collected_at_utc": "2026-10-20T05:21:42+00:00",
            "gpus": [
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
            ],
        },
    )

    exit_code = main(
        [
            "--live-nvidia",
            "--config",
            str(live_config),
            "--output",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "Telemetry source: nvidia-smi" in captured.out
    assert "temperature=51 C" in captured.out
    assert "Status: PASS" in captured.out
    assert "error-count rule skipped" in captured.out
    assert captured.err == ""
    assert report["gpus"][0]["memory_total_mb"] == 4096
    assert report["warnings"]


def test_live_nvidia_collection_error_returns_two(
    capsys,
    monkeypatch,
) -> None:
    def fail_collection() -> dict:
        raise NvidiaSmiError("nvidia-smi was not found")

    monkeypatch.setattr(
        "main.collect_nvidia_telemetry",
        fail_collection,
    )

    exit_code = main(
        [
            "--live-nvidia",
            "--config",
            str(CONFIG_PATH),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "ERROR: nvidia-smi was not found" in captured.err


def test_cli_requires_exactly_one_telemetry_source() -> None:
    with pytest.raises(SystemExit) as missing_source:
        main(["--config", str(CONFIG_PATH)])

    with pytest.raises(SystemExit) as multiple_sources:
        main(
            [
                "--input",
                str(HEALTHY_PATH),
                "--live-nvidia",
                "--config",
                str(CONFIG_PATH),
            ]
        )

    assert missing_source.value.code == 2
    assert multiple_sources.value.code == 2


def test_simulation_generates_validates_and_writes_report(
    tmp_path: Path,
    capsys,
) -> None:
    simulation_config = tmp_path / "config.simulation.json"
    simulation_config.write_text(
        (
            '{"expected_gpu_count": 12, '
            '"max_temperature_c": 85, '
            '"max_error_count": 0}'
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "simulation.json"

    exit_code = main(
        [
            "--simulate",
            "--config",
            str(simulation_config),
            "--seed",
            "2026",
            "--output",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["telemetry_source"] == "generated-simulation"
    assert report["simulation_seed"] == 2026
    assert len(report["gpus"]) == 12
    assert exit_code == (0 if report["status"] == "PASS" else 1)
    assert "Telemetry source: generated-simulation" in captured.out
    assert "Simulation seed: 2026" in captured.out
    assert captured.err == ""


def test_simulation_gpu_count_can_override_configured_count(
    tmp_path: Path,
    capsys,
) -> None:
    report_path = tmp_path / "simulation.json"

    exit_code = main(
        [
            "--simulate",
            "--config",
            str(CONFIG_PATH),
            "--gpu-count",
            "5",
            "--seed",
            "10",
            "--output",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert len(report["gpus"]) == 5
    assert "Expected 2 GPUs but found 5." in report["failures"]
    assert "Status: FAIL" in captured.out


def test_simulation_options_require_simulation_mode() -> None:
    with pytest.raises(SystemExit) as error:
        main(
            [
                "--input",
                str(HEALTHY_PATH),
                "--config",
                str(CONFIG_PATH),
                "--seed",
                "42",
            ]
        )

    assert error.value.code == 2
