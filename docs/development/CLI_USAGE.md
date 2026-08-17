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
| `--workers N` | Parallel workers (default from config: 1; `max` = every logical CPU) |
| `--format {csv,json,sqlite,all}` | Output format (default: `csv`) |
| `--dry-run` | Print the plan summary without executing |
| `--resume ID` | Resume an interrupted study |
| `--no-persist` | Execute without persisting study, plan or result data |
| `--summary-only` | Keep only aggregate statistics in memory (strips per-month timelines) |
| `--fast-path` | Use the closed-form fast path for constant-allocation + fixed-real-withdrawal studies |
| `--reference-chained` | Explicitly use the chained Reference executor (bit-exact horizon chaining); this is the default exact mode for plans that benefit from it |
| `--reference-independent` | Use the independent Reference executor (canonical Decimal engine, no chaining) — the oracle against which optimized execution is verified |
| `--validate` | Pre-flight: run a deterministic sample through both the fast path and the canonical Decimal reference engine, failing loudly on any divergence; requires `--fast-path` |

The execution-mode flags (`--fast-path`, `--reference-chained`,
`--reference-independent`) are mutually exclusive; requesting more than one is
rejected at pre-flight rather than silently merged.

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

### Execution modes

`sim-retire run` supports three mutually exclusive execution modes.

**Default — Reference Chained (exact).** With no execution-mode flag, the CLI
routes the plan through the chained Reference executor whenever the plan
actually benefits from horizon chaining (`derived_results > 0`, i.e.
multi-horizon, prefix-consistent grid families). The longest horizon of each
family is evaluated once through the canonical Decimal engine and every
shorter, prefix-consistent horizon is derived from it bit-exactly; any
non-eligible unit or family falls back to the independent Reference inside the
executor. The completion summary reports `Reference Chained:`, `Chained
Groups:`, and `Month-Work:` coverage.

Single-horizon and other non-chainable plans run without any flag through the
independent Reference dispatch exactly as before — no chaining overhead is paid
when nothing would be derived. The chained and independent paths are
bit-exact, so switching a plan between them never changes results, only
execution cost.

```bash
sim-retire --data-dir data run --summary-only <study.yaml>
```

**`--reference-independent` (canonical oracle).** Forces the independent
Reference executor: every unit is evaluated through the full 9-step Decimal
pipeline with no chaining. This is the development/verification oracle against
which optimized execution is tested and is not the normal production path.

```bash
sim-retire --data-dir data run --reference-independent --summary-only <study.yaml>
```

**`--reference-chained` (explicit force).** Explicitly requests the chained
Reference executor. This is the default exact mode for eligible plans; the flag
documents intent and is preserved for backward compatibility with existing
scripts. It is accepted for all plans, even when chaining derives nothing.

**`--fast-path` (approximate, opt-in).** See below. Mutually exclusive with
both Reference modes.

### Fast path and pre-flight validation

For studies using a `ConstantAllocationPolicy` + `FixedRealWithdrawalPolicy`
pair, `--fast-path` replaces the exact Reference execution (default: Reference
Chained) with an equivalent closed-form recurrence (`--no-persist` or
`--summary-only` is required, since
the fast path produces summary-grade results without per-month timelines).
Add `--validate` to compare a small deterministic sample of units through both
the fast path and the Decimal reference engine before executing:

```bash
sim-retire --data-dir data run \
  --fast-path --validate --summary-only <study.yaml>
```

The completion summary reports fast-path vs reference coverage
(`Fast Path:` / `Reference Path:`) and the pre-flight result
(`Validation: OK (N fast-path unit(s) vs Decimal reference)`).  Studies whose
policies fall outside the fast-path family are reported as 0 fast-path units
and `--validate` reports the sample as skipped.

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