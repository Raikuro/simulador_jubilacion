# CLI Usage Guide

The `sim-retire` CLI exposes seven commands for defining, executing,
persisting, exporting, and comparing retirement-simulation studies.

## Global options

These come before the command name:

```bash
sim-retire [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | flag | — | Print version and exit |
| `--verbose` | flag | off | Enable verbose output |
| `--debug` | flag | off | Enable debug logging |
| `--data-dir DIR` | path | — | Directory containing dataset JSON files |
| `--config FILE` | path | `~/.sim-retire/config.yaml` | Configuration file |

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Execution error (study failed, I/O error) |
| `2` | Validation error (bad arguments, missing files) |
| `3` | Configuration error |
| `4` | Database error |
| `130` | Interrupted (Ctrl+C) |

---

## validate

Validate a YAML experiment definition without executing it.

```bash
sim-retire validate STUDY_FILE
```

Checks the dataset, cohorts, parameter sweep, policies, and resulting plan.
Exits `0` on success, `2` on any validation failure.

```bash
sim-retire --data-dir examples/data validate examples/studies/basic_minimal.yaml
```

---

## run

Execute a research study end-to-end and persist results.

```bash
sim-retire run [OPTIONS] STUDY_FILE
```

| Option | Description |
|--------|-------------|
| `--output-dir DIR` | Output directory (default from config: `./results/`) |
| `--workers N` | Parallel workers (default from config: 1) |
| `--format {csv,json,sqlite,all}` | Output format (default: `csv`) |
| `--dry-run` | Print the plan summary without executing |
| `--resume ID` | Resume an interrupted study |

Dry-run is the fastest way to sanity-check a study before a full run:

```bash
sim-retire --data-dir examples/data run --dry-run \
  examples/studies/basic_minimal.yaml
```

Full run:

```bash
sim-retire --data-dir examples/data run \
  examples/studies/basic_minimal.yaml --workers 4 --format csv
```

---

## list

Lists studies stored in the SQLite database.

```bash
sim-retire list [--format table|json|csv] \
  [--status all|completed|failed|pending] \
  [--sort date|name|status]
```

```bash
sim-retire list --format table --status completed
```

---

## export

Exports a stored study from the database to CSV or JSON.

```bash
sim-retire export [--format csv|json] [--output PATH] \
  [--metrics full|summary|aggregated] STUDY_ID
```

```bash
sim-retire export --format csv --metrics summary <STUDY_ID>
```

Get the `STUDY_ID` from `sim-retire list`.

---

## optimize

Finds the maximum sustainable withdrawal rate for a given allocation policy.

```bash
sim-retire optimize [--target-success-rate RATE] \
  [--initial-capital CAPITAL] --allocation-policy NAME \
  [--workers N] [--tolerance TOL] [--output-dir DIR] STUDY_FILE
```

| Option | Default | Description |
|--------|---------|-------------|
| `--target-success-rate` | — | Target success rate (0.0–1.0) |
| `--initial-capital` | — | Starting portfolio value in EUR |
| `--allocation-policy` | (required) | Policy name from the YAML |
| `--workers` | 1 | Parallel workers |
| `--tolerance` | — | Precision of the binary search over withdrawal rate |
| `--output-dir` | — | Output directory |

---

## compare

Compares two or more allocation policies on a single study.

```bash
sim-retire compare --strategy NAME [--strategy NAME2 ...] \
  [--withdrawal-policy NAME] [--group-by global|cohort|parameter_config] \
  [--workers N] [--initial-capital EUR] STUDY_FILE
```

`--strategy` selects allocation policies from the YAML and must be supplied
at least twice.

---

## config

Manages the configuration file.

```bash
sim-retire config set KEY VALUE      # e.g. output.default_directory ./results
sim-retire config get KEY            # e.g. output.default_directory
sim-retire config validate [--file FILE]
sim-retire config list
```

```bash
sim-retire config list
sim-retire config set execution.default_workers 8
sim-retire config validate
```

---

## Study file format

A study is a YAML document with six top-level sections:

```yaml
metadata:            # Optional descriptive fields (name, version, description)
dataset:
  identifier: "market_monthly"   # Matches the stem of a data/<name>.json
  start_year: 1990
  end_year: 2024
cohorts:
  type: "monthly_rolling"
  window_years: 30
allocation_policies:
  - name: "Static 75/25"
    type: "ConstantAllocationPolicy"
    equity_ratio: 0.75
withdrawal_policy:
  type: "ConstantInflationAdjustedWithdrawalPolicy"
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.50, 0.75, 0.90]
```

- `dataset.identifier` selects the dataset file; the loader matches the
  identifier to `data/<identifier>.json` under the active data directory.
- `cohorts.window_years` defines the length of each rolling window. The
  horizon in months is `window_years * 12`.
- `parameters` defines each sweep axis; all combinations are executed.

See [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) for the configuration file and
[EXAMPLES.md](../../examples/EXAMPLES.md) for ready-to-run studies.