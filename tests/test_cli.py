from pathlib import Path

from main import main


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
