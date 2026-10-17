# GPU Node Validator

A Python command-line tool that validates simulated GPU-node telemetry against configurable health rules.

## Current scope

The validator will read JSON telemetry, evaluate GPU health checks, display a human-readable result, produce a structured JSON report, and return a CI-friendly exit code.

This project uses simulated telemetry and does not query real GPU hardware or AMD internal tools.
