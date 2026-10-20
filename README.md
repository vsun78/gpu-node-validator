# GPU Node Validator

A Python command-line tool that validates fixture-based JSON, randomly generated, or live NVIDIA GPU telemetry against configurable health rules. It produces human-readable output, optionally writes a structured JSON report, and returns an exit code suitable for automation and CI.

Live collection uses the public `nvidia-smi` utility. The collector is separated from validation so another hardware source, such as AMD SMI on compatible hardware, can be added without replacing the validation engine. This project does not reproduce AMD internal tools.

## Architecture

```mermaid
flowchart LR
    CLI[CLI main.py] --> JSON[JSON collector]
    CLI --> Simulation[Random telemetry simulator]
    CLI --> NVIDIA[NVIDIA SMI collector]
    JSON --> Node[Normalized node telemetry]
    Simulation --> Node
    NVIDIA --> Node
    CLI --> Config[Rule configuration]
    Node --> Validator[Validator]
    Config --> Validator
    Validator --> Result[Structured result]
    Result --> Reporter[Terminal and JSON reporting]
    Reporter --> Exit[Exit code]
```

- `main.py` parses arguments and coordinates the workflow.
- `collector.py` loads and performs basic structural checks on JSON inputs.
- `simulator.py` generates random, reproducible GPU telemetry at scale.
- `nvidia_collector.py` queries `nvidia-smi` and normalizes live metrics.
- `validator.py` applies configurable GPU health rules.
- `reporter.py` prints results and writes JSON reports.

## Setup

Create and activate a virtual environment, then install the test dependency:

```powershell
py -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
python -m pip install -r requirements.txt
```

## Usage

Run a healthy example:

```powershell
python main.py --input samples/healthy_node.json --config config.json
```

Run an unhealthy example:

```powershell
python main.py --input samples/unhealthy_node.json --config config.json
```

Collect and validate live NVIDIA telemetry:

```powershell
python main.py --live-nvidia --config config.nvidia.json
```

Save a live report:

```powershell
python main.py `
    --live-nvidia `
    --config config.nvidia.json `
    --output reports/live-nvidia.json
```

The live configuration expects one NVIDIA GPU because `nvidia-smi` does not enumerate an Intel integrated GPU.

Generate eight random GPUs using the simulation configuration:

```powershell
python main.py --simulate --config config.simulation.json
```

Every unseeded run creates different telemetry. The terminal and JSON report show the generated seed. Reuse it to reproduce the same GPU data:

```powershell
python main.py `
    --simulate `
    --config config.simulation.json `
    --seed 2026 `
    --output reports/simulation-2026.json
```

Override the number of generated GPUs:

```powershell
python main.py `
    --simulate `
    --config config.simulation.json `
    --gpu-count 100 `
    --output reports/simulation-100-gpus.json
```

If `--gpu-count` differs from `expected_gpu_count`, the validator intentionally reports a GPU-count failure. The simulator permits up to 1,000 GPUs per run.

Write a structured JSON report:

```powershell
python main.py `
    --input samples/healthy_node.json `
    --config config.json `
    --output reports/healthy.json
```

Show all CLI options:

```powershell
python main.py --help
```

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Validation completed and the node passed |
| `1` | Validation completed and the node failed |
| `2` | The tool could not load/collect inputs or write the requested report |

## Tests

Run the complete test suite:

```powershell
python -m pytest -v
```

Tests cover JSON loading, reproducible random simulation, mocked NVIDIA SMI collection, configuration validation, GPU health rules, CLI integration, report output, and exit codes. CI uses mocked NVIDIA output because a standard GitHub-hosted runner does not provide this laptop's GPU.

## Bash wrapper

From Linux or WSL, run the defaults:

```bash
bash scripts/run_validation.sh
```

Or provide input, configuration, and output paths:

```bash
bash scripts/run_validation.sh \
    samples/unhealthy_node.json \
    config.json \
    reports/unhealthy.json
```

The wrapper uses `python3` by default. Set `PYTHON_BIN` to choose a different interpreter.

## Continuous integration

GitHub Actions runs the full pytest suite and smoke-tests both the CLI and Bash wrapper on every push and pull request.

## Current validation rules

- GPU count must match `expected_gpu_count`.
- Every GPU must contain `gpu_id`, `detected`, `temperature_c`, and `error_count`.
- Every GPU must be detected.
- Temperature must not exceed `max_temperature_c`.
- Error count must not exceed `max_error_count`.
- Missing or invalid metrics fail validation.
- When a hardware source cannot provide an error counter, the report warns that the rule was skipped instead of treating the unknown value as zero.

## Limitations

- Live hardware collection currently supports NVIDIA GPUs exposed by `nvidia-smi`; the Intel integrated GPU is not included.
- NVIDIA consumer GPUs do not expose the same diagnostic counters as data-center GPUs, so unavailable error counts are reported as warnings.
- GitHub Actions validates parsing with mocked output rather than accessing physical GPU hardware.
- Generated telemetry models test scenarios; it does not represent measurements from physical hardware.
- Thresholds are demonstration rules, not AMD hardware specifications.
- AMD SMI, XML input, distributed polling, dashboards, and anomaly detection are outside the current scope.
