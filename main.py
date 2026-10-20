import argparse
import sys
from pathlib import Path

from gpu_validator.collector import (
    ConfigLoadError,
    TelemetryLoadError,
    load_config,
    load_node,
)
from gpu_validator.reporter import (
    ReportWriteError,
    print_report,
    write_json_report,
)
from gpu_validator.validator import validate_node


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the validator."""
    parser = argparse.ArgumentParser(
        description="Validate simulated GPU node telemetry."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a GPU node telemetry JSON file.",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to a validation configuration JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the structured JSON report.",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    """Run the validation workflow and return a process exit code."""
    args = parse_args(arguments)

    try:
        node = load_node(args.input)
        config = load_config(args.config)
    except (TelemetryLoadError, ConfigLoadError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    result = validate_node(node, config)

    if args.output is not None:
        try:
            write_json_report(result, args.output)
        except ReportWriteError as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2

    print_report(result)

    if result["status"] == "PASS":
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
