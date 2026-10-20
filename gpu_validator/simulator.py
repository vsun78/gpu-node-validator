import random
from datetime import datetime, timezone


MAX_SIMULATED_GPUS = 1000
SIMULATED_MEMORY_TOTALS_MB = (4096, 8192, 12288, 16384, 24576)
SIMULATED_GPU_MODELS = (
    "Simulated Compute GPU",
    "Simulated Graphics GPU",
    "Simulated Data Center GPU",
)


class SimulationError(Exception):
    """Raised when simulated telemetry cannot be generated."""


def generate_simulated_telemetry(
    gpu_count: int,
    seed: int | None = None,
) -> dict:
    """Generate randomized, reproducible telemetry in the common node format."""
    if (
        isinstance(gpu_count, bool)
        or not isinstance(gpu_count, int)
        or not 0 <= gpu_count <= MAX_SIMULATED_GPUS
    ):
        raise SimulationError(
            "Simulated GPU count must be an integer between "
            f"0 and {MAX_SIMULATED_GPUS}."
        )

    if isinstance(seed, bool) or (
        seed is not None and not isinstance(seed, int)
    ):
        raise SimulationError("Simulation seed must be an integer.")

    resolved_seed = (
        seed
        if seed is not None
        else random.SystemRandom().randrange(2**63)
    )
    generator = random.Random(resolved_seed)
    gpus = []

    for gpu_id in range(gpu_count):
        memory_total_mb = generator.choice(
            SIMULATED_MEMORY_TOTALS_MB
        )
        error_count = (
            0
            if generator.random() < 0.85
            else generator.randint(1, 5)
        )

        gpus.append(
            {
                "gpu_id": gpu_id,
                "name": generator.choice(SIMULATED_GPU_MODELS),
                "detected": generator.random() >= 0.05,
                "temperature_c": generator.randint(30, 110),
                "error_count": error_count,
                "utilization_percent": generator.randint(0, 100),
                "memory_used_mb": generator.randint(
                    0,
                    memory_total_mb,
                ),
                "memory_total_mb": memory_total_mb,
                "driver_version": "simulated-1.0",
            }
        )

    return {
        "node_id": "simulated-node",
        "telemetry_source": "generated-simulation",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "simulation_seed": resolved_seed,
        "gpus": gpus,
    }
