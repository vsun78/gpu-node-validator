from pathlib import Path
from gpu_validator.collector import load_node

SAMPLE_PATH = Path("samples/healthy_node.json")

def main() -> None:
    node = load_node(SAMPLE_PATH)
    gpus = node["gpus"]

    print(f"Node ID: {node['node_id']}")
    print(f"GPU count: {len(gpus)}")

    for gpu in gpus:
        print(
            f"GPU {gpu['gpu_id']}: "
            f"temperature={gpu['temperature_c']} C, "
            f"detected={gpu['detected']}, "
            f"errors={gpu['error_count']}"
        )

if __name__ == "__main__":
    main()