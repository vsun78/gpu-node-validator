import argparse
import sys
from pathlib import Path

from gpu_validator.collector import (
    ConfigLoadError,
    TelemetryLoadError,
    load_config,
    load_node,
)
from gpu_validator.nvidia_collector import (
    NvidiaSmiError,
    collect_nvidia_telemetry,
)
from gpu_validator.reporter import (
    ReportWriteError,
    print_report,
    write_json_report,
)
from gpu_validator.simulator import (
    MAX_SIMULATED_GPUS,
    SimulationError,
    generate_simulated_telemetry,
)
from gpu_validator.validator import validate_node


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the validator."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate JSON, generated, or live NVIDIA GPU node telemetry."
        )
    )
    telemetry_source = parser.add_mutually_exclusive_group(required=True)
    telemetry_source.add_argument(
        "--input",
        type=Path,
        help="Path to a GPU node telemetry JSON file.",
    )
    telemetry_source.add_argument(
        "--live-nvidia",
        action="store_true",
        help="Collect live GPU telemetry using nvidia-smi.",
    )
    telemetry_source.add_argument(
        "--simulate",
        action="store_true",
        help="Generate randomized GPU telemetry.",
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
    parser.add_argument(
        "--gpu-count",
        type=int,
        help=(
            "Number of GPUs to generate in simulation mode; defaults "
            "to expected_gpu_count from the configuration."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional simulation seed for reproducible random telemetry.",
    )

    args = parser.parse_args(arguments)

    if not args.simulate and (
        args.gpu_count is not None or args.seed is not None
    ):
        parser.error("--gpu-count and --seed require --simulate")

    if args.gpu_count is not None and not (
        0 <= args.gpu_count <= MAX_SIMULATED_GPUS
    ):
        parser.error(
            "--gpu-count must be between 0 and "
            f"{MAX_SIMULATED_GPUS}"
        )

    return args


def main(arguments: list[str] | None = None) -> int:
    """Run the validation workflow and return a process exit code."""
    args = parse_args(arguments)

    try:
        config = load_config(args.config)
        if args.live_nvidia:
            node = collect_nvidia_telemetry()
        elif args.simulate:
            gpu_count = (
                args.gpu_count
                if args.gpu_count is not None
                else config["expected_gpu_count"]
            )
            node = generate_simulated_telemetry(
                gpu_count=gpu_count,
                seed=args.seed,
            )
        else:
            node = load_node(args.input)
    except (
        TelemetryLoadError,
        ConfigLoadError,
        NvidiaSmiError,
        SimulationError,
    ) as error:
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
