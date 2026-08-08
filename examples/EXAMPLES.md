# Examples

This directory contains ready-to-run examples for the `sim-retire` CLI.

```
examples/
├── configs/
│   └── config.yaml            # Example configuration file
├── data/
│   └── market_monthly.json    # Synthetic monthly market dataset (1990-2024)
├── studies/
│   ├── basic_minimal.yaml      # Example 1: minimal single-strategy study
│   ├── sweep_equity_allocation.yaml  # Example 2: parameter sweep
│   └── multi_policy.yaml       # Example 3: multi-policy comparison
└── scripts/
    └── generate_dataset.py     # Regenerates the synthetic dataset
```

## Running the examples

From the repository root, pass `--data-dir examples/data` so the CLI can
resolve the `market_monthly` dataset referenced by each study.

### Example 1 — minimal study

A single fixed allocation and withdrawal rate.

```bash
# Validate the definition
sim-retire --data-dir examples/data validate examples/studies/basic_minimal.yaml

# Preview the plan without executing
sim-retire --data-dir examples/data run --dry-run examples/studies/basic_minimal.yaml

# Execute the study
sim-retire --data-dir examples/data run examples/studies/basic_minimal.yaml
```

### Example 2 — parameter sweep

Sweeps the equity allocation across `[0.50, 0.75, 0.90]`, generating a
`3 × <cohorts>` combination of simulation units.

```bash
sim-retire --data-dir examples/data run --dry-run examples/studies/sweep_equity_allocation.yaml

sim-retire --data-dir examples/data run examples/studies/sweep_equity_allocation.yaml \
  --workers 4
```

### Example 3 — multi-policy comparison

Defines three allocation policies (60/40, 75/25, 90/10) in a single study.

```bash
sim-retire --data-dir examples/data validate examples/studies/multi_policy.yaml

sim-retire --data-dir examples/data run --dry-run examples/studies/multi_policy.yaml \
  --workers 2
```

### Using the example configuration

The example config sets `default_workers: 4` and selects CSV output:

```bash
sim-retire --config examples/configs/config.yaml --data-dir examples/data run \
  examples/studies/basic_minimal.yaml
```

## Regenerating the dataset

The dataset is synthetic, generated deterministically. To regenerate it:

```bash
python examples/scripts/generate_dataset.py
```

## Notes

- The dataset is a toy market series used for demonstration; it does not
  represent real market data.
- Results are persisted to the SQLite database configured under `database.path`
  (default `~/.sim-retire/studies.db`). Use `sim-retire list` to see stored
  studies.

## More documentation

- [INSTALLATION_AND_QUICKSTART.md](../docs/development/INSTALLATION_AND_QUICKSTART.md)
- [CLI_USAGE.md](../docs/development/CLI_USAGE.md)
- [CONFIG_REFERENCE.md](../docs/development/CONFIG_REFERENCE.md)
- [CONFIG_PRECEDENCE.md](../docs/development/CONFIG_PRECEDENCE.md)