import json
from pathlib import Path


class ReportWriteError(Exception):
    """Raised when a JSON validation report cannot be written."""


def print_report(result: dict) -> None:
    """Print a human-readable validation report."""
    print(f"Node: {result['node_id']}")
    print(f"Telemetry source: {result['telemetry_source']}")

    if result["collected_at_utc"] is not None:
        print(f"Collected at: {result['collected_at_utc']}")

    if result["simulation_seed"] is not None:
        print(f"Simulation seed: {result['simulation_seed']}")

    print(f"Status: {result['status']}")

    for gpu in result["gpus"]:
        gpu_label = f"GPU {gpu.get('gpu_id', '?')}"
        if gpu.get("name"):
            gpu_label = f"{gpu_label} ({gpu['name']})"

        metrics = []
        if gpu.get("temperature_c") is not None:
            metrics.append(f"temperature={gpu['temperature_c']} C")
        if gpu.get("utilization_percent") is not None:
            metrics.append(
                f"utilization={gpu['utilization_percent']}%"
            )
        if (
            gpu.get("memory_used_mb") is not None
            and gpu.get("memory_total_mb") is not None
        ):
            metrics.append(
                f"memory={gpu['memory_used_mb']}/"
                f"{gpu['memory_total_mb']} MiB"
            )
        if gpu.get("driver_version"):
            metrics.append(f"driver={gpu['driver_version']}")

        if metrics:
            print(f"{gpu_label}: {', '.join(metrics)}")

    failures = result["failures"]

    if failures:
        print("Failures:")
        for failure in failures:
            print(f"{failure}")
    else:
        print("No validation failures.")

    warnings = result["warnings"]
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(warning)


def write_json_report(result: dict, output_path: str | Path) -> None:
    """Write a structured validation report as formatted JSON."""
    path = Path(output_path)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=2)
            file.write("\n")
    except OSError as error:
        raise ReportWriteError(
            f"Could not write JSON report: {path}"
        ) from error
