# Installing the FIRE Backtesting Framework (retirement-simulator)

This guide covers installing and getting your first study running with
`sim-retire`, the FIRE Backtesting Framework CLI.

## Requirements

- Python 3.13 or later
- `pip`

## Installation

Create and activate a virtual environment, then install the package with its
development extras:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs the `sim-retire` console script plus the test, lint, and type
checking tooling used across the project.

## Sanity check

Confirm the CLI is on your PATH and reports a version:

```bash
sim-retire --version
# 0.1.0
```

## Next steps

- Read [CLI_USAGE.md](CLI_USAGE.md) for every command and its options.
- Read [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) for the configuration file.
- Read [CONFIG_PRECEDENCE.md](CONFIG_PRECEDENCE.md) for how CLI flags, the
  configuration file, and built-in defaults interact.
- Browse the runnable examples under [`examples/`](../../examples/) with their
  walkthrough in [EXAMPLES.md](../../examples/EXAMPLES.md).

## Verifying the installation

Run the full test suite to confirm the installation is healthy:

```bash
pytest -q
```

The suite expects 808 tests covering the engine, research, infrastructure,
CLI, integration tests, and performance benchmarks.

## Troubleshooting

- **`sim-retire: command not found`** — the virtual environment is not active,
  or the package was not installed with `-e`.
- **`No module named pytest`** — install the dev extras:
  `pip install -e ".[dev]"`.
- **Dataset not found** — pass `--data-dir` pointing to a directory of dataset
  JSON files, e.g. `sim-retire --data-dir examples/data ...`.