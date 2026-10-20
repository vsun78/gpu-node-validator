import json
from pathlib import Path


class ReportWriteError(Exception):
    """Raised when a JSON validation report cannot be written."""


def print_report(result: dict) -> None:
    """Print a human-readable validation report."""
    print(f"Node: {result['node_id']}")
    print(f"Status: {result['status']}")

    failures = result["failures"]

    if failures:
        print("Failures:")
        for failure in failures:
            print(f"{failure}")
    else:
        print("No validation failures.")


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
