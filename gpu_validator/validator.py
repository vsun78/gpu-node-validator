REQUIRED_GPU_FIELDS = (
    "gpu_id",
    "detected",
    "temperature_c",
    "error_count",
)


def _is_number(value: object) -> bool:
    """return T for integers and floats, but not booleans."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def validate_node(node: dict, config: dict) -> dict:
    """validate GPU telemetry against the configured health rules."""
    failures = []
    warnings = []
    gpus = node["gpus"]

    expected_count = config["expected_gpu_count"]
    actual_count = len(gpus)

    if actual_count != expected_count:
        failures.append(
            f"Expected {expected_count} GPUs but found {actual_count}."
        )

    for position, gpu in enumerate(gpus):
        if not isinstance(gpu, dict):
            failures.append(
                f"GPU record {position} must be a JSON object."
            )
            continue

        missing_fields = [
            field
            for field in REQUIRED_GPU_FIELDS
            if field not in gpu
        ]

        if missing_fields:
            for field in missing_fields:
                failures.append(
                    f"GPU record {position} is missing "
                    f"required metric: {field}."
                )

            continue

        gpu_id = gpu["gpu_id"]

        if isinstance(gpu_id, bool) or not isinstance(gpu_id, int):
            failures.append(
                f"GPU record {position} gpu_id must be an integer."
            )
            gpu_label = f"GPU record {position}"
        else:
            gpu_label = f"GPU {gpu_id}"

        detected = gpu["detected"]

        if not isinstance(detected, bool):
            failures.append(
                f"{gpu_label} detected must be true or false."
            )
        elif not detected:
            failures.append(
                f"{gpu_label} is not detected."
            )

        temperature = gpu["temperature_c"]

        if not _is_number(temperature):
            failures.append(
                f"{gpu_label} temperature_c must be a number."
            )
        elif temperature > config["max_temperature_c"]:
            failures.append(
                f"{gpu_label} temperature {temperature} C exceeds "
                f"limit {config['max_temperature_c']} C."
            )

        error_count = gpu["error_count"]

        if error_count is None:
            warnings.append(
                f"{gpu_label} error_count is unavailable; "
                "error-count rule skipped."
            )
        elif (
            isinstance(error_count, bool)
            or not isinstance(error_count, int)
        ):
            failures.append(
                f"{gpu_label} error_count must be an integer."
            )
        elif error_count < 0:
            failures.append(
                f"{gpu_label} error_count cannot be negative."
            )
        elif error_count > config["max_error_count"]:
            failures.append(
                f"{gpu_label} error count {error_count} exceeds "
                f"limit {config['max_error_count']}."
            )

    status = "FAIL" if failures else "PASS"

    return {
        "node_id": node["node_id"],
        "telemetry_source": node.get("telemetry_source", "unknown"),
        "collected_at_utc": node.get("collected_at_utc"),
        "simulation_seed": node.get("simulation_seed"),
        "status": status,
        "failures": failures,
        "warnings": warnings,
        "gpus": gpus,
    }
