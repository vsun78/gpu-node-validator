import pytest

from gpu_validator.simulator import (
    MAX_SIMULATED_GPUS,
    SimulationError,
    generate_simulated_telemetry,
)


def test_simulator_generates_requested_gpu_count() -> None:
    node = generate_simulated_telemetry(gpu_count=25, seed=12345)

    assert node["node_id"] == "simulated-node"
    assert node["telemetry_source"] == "generated-simulation"
    assert node["simulation_seed"] == 12345
    assert node["collected_at_utc"]
    assert len(node["gpus"]) == 25


def test_simulator_generates_valid_metric_ranges() -> None:
    node = generate_simulated_telemetry(gpu_count=50, seed=9876)

    for expected_id, gpu in enumerate(node["gpus"]):
        assert gpu["gpu_id"] == expected_id
        assert isinstance(gpu["detected"], bool)
        assert 30 <= gpu["temperature_c"] <= 110
        assert 0 <= gpu["error_count"] <= 5
        assert 0 <= gpu["utilization_percent"] <= 100
        assert 0 <= gpu["memory_used_mb"] <= gpu["memory_total_mb"]
        assert gpu["driver_version"] == "simulated-1.0"


def test_same_seed_reproduces_identical_gpu_data() -> None:
    first_node = generate_simulated_telemetry(gpu_count=10, seed=42)
    second_node = generate_simulated_telemetry(gpu_count=10, seed=42)

    assert first_node["simulation_seed"] == second_node["simulation_seed"]
    assert first_node["gpus"] == second_node["gpus"]


def test_different_seeds_generate_different_gpu_data() -> None:
    first_node = generate_simulated_telemetry(gpu_count=10, seed=1)
    second_node = generate_simulated_telemetry(gpu_count=10, seed=2)

    assert first_node["gpus"] != second_node["gpus"]


@pytest.mark.parametrize(
    "gpu_count",
    [-1, MAX_SIMULATED_GPUS + 1, 1.5, True],
)
def test_simulator_rejects_invalid_gpu_count(gpu_count) -> None:
    with pytest.raises(SimulationError, match="GPU count"):
        generate_simulated_telemetry(gpu_count=gpu_count, seed=1)


def test_simulator_creates_and_records_random_seed() -> None:
    node = generate_simulated_telemetry(gpu_count=1)

    assert isinstance(node["simulation_seed"], int)
