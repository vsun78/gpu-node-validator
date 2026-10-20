from gpu_validator.validator import validate_node


CONFIG = {
    "expected_gpu_count": 2,
    "max_temperature_c": 85,
    "max_error_count": 0,
}


def make_healthy_node() -> dict:
    return {
        "node_id": "node-01",
        "gpus": [
            {
                "gpu_id": 0,
                "detected": True,
                "temperature_c": 60,
                "error_count": 0,
            },
            {
                "gpu_id": 1,
                "detected": True,
                "temperature_c": 68,
                "error_count": 0,
            },
        ],
    }


def test_healthy_node_passes() -> None:
    node = make_healthy_node()

    result = validate_node(node, CONFIG)

    assert result["status"] == "PASS"
    assert result["failures"] == []


def test_unexpected_gpu_count_fails() -> None:
    node = make_healthy_node()
    node["gpus"].pop()

    result = validate_node(node, CONFIG)

    assert result["status"] == "FAIL"
    assert "Expected 2 GPUs but found 1." in result["failures"]


def test_undetected_gpu_fails() -> None:
    node = make_healthy_node()
    node["gpus"][0]["detected"] = False

    result = validate_node(node, CONFIG)

    assert result["status"] == "FAIL"
    assert "GPU 0 is not detected." in result["failures"]


def test_overheated_gpu_fails() -> None:
    node = make_healthy_node()
    node["gpus"][0]["temperature_c"] = 95

    result = validate_node(node, CONFIG)

    assert result["status"] == "FAIL"
    assert (
        "GPU 0 temperature 95 C exceeds limit 85 C."
        in result["failures"]
    )


def test_gpu_errors_fail() -> None:
    node = make_healthy_node()
    node["gpus"][0]["error_count"] = 2

    result = validate_node(node, CONFIG)

    assert result["status"] == "FAIL"
    assert (
        "GPU 0 error count 2 exceeds limit 0."
        in result["failures"]
    )


def test_missing_metric_fails() -> None:
    node = make_healthy_node()
    del node["gpus"][0]["temperature_c"]

    result = validate_node(node, CONFIG)

    assert result["status"] == "FAIL"
    assert (
        "GPU record 0 is missing required metric: temperature_c."
        in result["failures"]
    )


def test_invalid_temperature_type_fails() -> None:
    node = make_healthy_node()
    node["gpus"][0]["temperature_c"] = "hot"

    result = validate_node(node, CONFIG)

    assert result["status"] == "FAIL"
    assert (
        "GPU 0 temperature_c must be a number."
        in result["failures"]
    )


def test_unavailable_error_count_adds_warning_without_failing() -> None:
    node = make_healthy_node()
    node["gpus"][0]["error_count"] = None

    result = validate_node(node, CONFIG)

    assert result["status"] == "PASS"
    assert result["failures"] == []
    assert (
        "GPU 0 error_count is unavailable; error-count rule skipped."
        in result["warnings"]
    )
