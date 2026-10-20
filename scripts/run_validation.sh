#!/usr/bin/env bash

set -uo pipefail

script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "$script_directory/.." && pwd)"

cd "$project_root"

input_path="${1:-samples/healthy_node.json}"
config_path="${2:-config.json}"
output_path="${3:-reports/result.json}"
python_command="${PYTHON_BIN:-python3}"

"$python_command" main.py \
    --input "$input_path" \
    --config "$config_path" \
    --output "$output_path"

exit_code=$?
echo "Validator exit code: $exit_code"
exit "$exit_code"
