import csv
import socket
import subprocess
from datetime import datetime, timezone
from io import StringIO


NVIDIA_QUERY_FIELDS = (
    "index",
    "name",
    "temperature.gpu",
    "utilization.gpu",
    "memory.used",
    "memory.total",
    "driver_version",
)

NVIDIA_SMI_COMMAND = (
    "nvidia-smi",
    f"--query-gpu={','.join(NVIDIA_QUERY_FIELDS)}",
    "--format=csv,noheader,nounits",
)

UNAVAILABLE_VALUES = {
    "",
    "n/a",
    "[n/a]",
    "not supported",
    "[not supported]",
}


class NvidiaSmiError(Exception):
    """Raised when live NVIDIA telemetry cannot be collected or parsed."""


def _parse_number(value: str, field_name: str) -> int | float:
    """Parse a required numeric NVIDIA SMI value."""
    normalized = value.strip()

    if normalized.lower() in UNAVAILABLE_VALUES:
        raise NvidiaSmiError(
            f"NVIDIA SMI did not provide required field: {field_name}"
        )

    try:
        number = float(normalized)
    except ValueError as error:
        raise NvidiaSmiError(
            f"NVIDIA SMI returned invalid {field_name}: {normalized!r}"
        ) from error

    if number.is_integer():
        return int(number)

    return number


def _parse_optional_number(
    value: str,
    field_name: str,
) -> int | float | None:
    """Parse a numeric metric, returning None when the GPU does not support it."""
    if value.strip().lower() in UNAVAILABLE_VALUES:
        return None

    return _parse_number(value, field_name)


def parse_nvidia_smi_output(
    output: str,
    node_id: str | None = None,
) -> dict:
    """Convert NVIDIA SMI CSV output into the validator's node format."""
    rows = [
        row
        for row in csv.reader(StringIO(output), skipinitialspace=True)
        if any(cell.strip() for cell in row)
    ]

    if not rows:
        raise NvidiaSmiError("NVIDIA SMI returned no GPU telemetry.")

    gpus = []

    for position, row in enumerate(rows):
        if len(row) != len(NVIDIA_QUERY_FIELDS):
            raise NvidiaSmiError(
                f"NVIDIA SMI row {position} contained {len(row)} fields; "
                f"expected {len(NVIDIA_QUERY_FIELDS)}."
            )

        (
            index_text,
            name,
            temperature_text,
            utilization_text,
            memory_used_text,
            memory_total_text,
            driver_version,
        ) = (value.strip() for value in row)

        gpu_id = _parse_number(index_text, "GPU index")
        if not isinstance(gpu_id, int) or gpu_id < 0:
            raise NvidiaSmiError(
                f"NVIDIA SMI returned invalid GPU index: {index_text!r}"
            )

        if not name:
            raise NvidiaSmiError("NVIDIA SMI returned an empty GPU name.")

        if not driver_version:
            raise NvidiaSmiError(
                "NVIDIA SMI returned an empty driver version."
            )

        gpus.append(
            {
                "gpu_id": gpu_id,
                "name": name,
                "detected": True,
                "temperature_c": _parse_number(
                    temperature_text,
                    "temperature.gpu",
                ),
                "error_count": None,
                "utilization_percent": _parse_optional_number(
                    utilization_text,
                    "utilization.gpu",
                ),
                "memory_used_mb": _parse_optional_number(
                    memory_used_text,
                    "memory.used",
                ),
                "memory_total_mb": _parse_optional_number(
                    memory_total_text,
                    "memory.total",
                ),
                "driver_version": driver_version,
            }
        )

    resolved_node_id = (node_id or socket.gethostname()).strip()
    if not resolved_node_id:
        resolved_node_id = "local-node"

    return {
        "node_id": resolved_node_id,
        "telemetry_source": "nvidia-smi",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "gpus": gpus,
    }


def collect_nvidia_telemetry() -> dict:
    """Run NVIDIA SMI and return normalized live GPU telemetry."""
    try:
        completed_process = subprocess.run(
            NVIDIA_SMI_COMMAND,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except FileNotFoundError as error:
        raise NvidiaSmiError(
            "nvidia-smi was not found. Install an NVIDIA driver or add "
            "nvidia-smi to PATH."
        ) from error
    except subprocess.TimeoutExpired as error:
        raise NvidiaSmiError(
            "nvidia-smi timed out while collecting telemetry."
        ) from error
    except subprocess.CalledProcessError as error:
        details = (error.stderr or error.stdout or "").strip()
        message = "nvidia-smi failed while collecting telemetry"
        if details:
            message = f"{message}: {details}"
        raise NvidiaSmiError(message) from error
    except OSError as error:
        raise NvidiaSmiError(
            f"Could not execute nvidia-smi: {error}"
        ) from error

    return parse_nvidia_smi_output(completed_process.stdout)
