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

Checks the dataset, cohorts, parameter configurations, policies, and resulting plan.
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
| `--validate` | Pre-flight: run a deterministic sample through both the fast path and the canonical Decimal reference engine, failing loudly on any divergence; requires `--fast-path` |

The execution-mode flags (`--fast-path`, `--reference-chained`) are mutually
exclusive; requesting more than one is rejected at pre-flight rather than
silently merged.

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

`sim-retire run` supports two mutually exclusive execution modes.

**Default — Reference Chained (exact).** With no execution-mode flag, the CLI
routes the plan through the chained Reference executor. The longest horizon of
each family is evaluated once through the canonical Decimal engine and every
shorter, prefix-consistent horizon is derived from it bit-exactly; any
non-eligible unit or family is evaluated through the canonical engine inside
the executor. The completion summary reports `Reference Chained:`, `Chained
Groups:`, and `Month-Work:` coverage.

Single-horizon and other non-chainable plans also route through Reference
Chained; each unit is evaluated directly through the canonical engine, so no
chaining overhead is paid when nothing would be derived. Reference Chained is
the sole reference execution strategy — there is no separate independent
dispatch.

```bash
sim-retire --data-dir data run --summary-only <study.yaml>
```

**`--reference-chained` (explicit force).** Explicitly requests the chained
Reference executor. This is the default exact mode for all plans; the flag
documents intent and is preserved for backward compatibility with existing
scripts. It is accepted for all plans, even when chaining derives nothing.

**`--fast-path` (approximate, opt-in).** See below. Mutually exclusive with
`--reference-chained`.

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

Finds the maximum sustainable withdrawal rate for a study's allocation policy.

The study must declare a **single configuration**: `withdrawal_policy.withdrawal_rate`
must have exactly one value (the optimizer owns the candidate withdrawal rates),
and `allocation_policy.equity_allocation` and `cohorts.horizon_years` must each
have exactly one value. `withdrawal_policy.type` supplies the policy mechanism;
each candidate is substituted for the declared single withdrawal rate.

```bash
sim-retire optimize [--target-success-rate RATE] \
  [--initial-capital CAPITAL] \
  [--workers N] [--tolerance TOL] [--output-dir DIR] STUDY_FILE
```

| Option | Default | Description |
|--------|---------|-------------|
| `--target-success-rate` | 0.95 | Target success rate (0.0–1.0) |
| `--initial-capital` | 1000000 | Starting portfolio value in EUR |
| `--workers` | 1 | Parallel workers |
| `--tolerance` | 0.001 | Precision of the binary search over withdrawal rate |
| `--output-dir` | ./results/ | Output directory |

---

## compare

Compares two or more generated parameter configurations side-by-side.

The study's parameter configurations are the comparison strategies: the single
plan is executed once and the results are partitioned by configuration.

```bash
sim-retire compare [--strategy name=value ...] \
  [--group-by global|cohort|parameter_config] \
  [--workers N] [--initial-capital EUR] STUDY_FILE
```

- `--strategy name=value` is optional and repeatable; each one is a filter
  (AND-ed) that selects a subset of configurations already declared in the YAML.
  Without it every generated configuration is compared.
- A study whose value arrays declare multiple values yields multiple strategies
  (the Cartesian product of `allocation_policy.equity_allocation`,
  `withdrawal_policy.withdrawal_rate`, and `cohorts.horizon_years`). Fewer than
  two selected configurations is a validation error.
- The withdrawal policy comes from the normalized study configuration; there is
  no policy-name selection.

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

A study is a YAML document with five top-level sections. The study YAML is the
sole source of study-definition parameters: there are no CLI options that set,
override, or filter-in equity allocation, withdrawal rate, or horizon values.

```yaml
metadata:            # Optional descriptive fields (name, version, description)
dataset:
  identifier: "market_monthly"   # Matches the stem of a data/<name>.json
cohorts:
  horizon_years: [30]
allocation_policy:
  type: "ConstantAllocationPolicy"
  equity_allocation: [0.75]
withdrawal_policy:
  type: "ConstantWithdrawalPolicy"
  withdrawal_rate: [0.04]
```

- `dataset.identifier` selects the dataset file; the loader matches the
  identifier to `data/<identifier>.json` under the active data directory.
- `allocation_policy` / `withdrawal_policy` declare the policy `type` and its
  value array. Supported withdrawal types are `FixedRealWithdrawalPolicy` and
  `ConstantWithdrawalPolicy`.
- Every value-bearing field is an array — even a single value is written as
  `[0.75]`. The study configuration space is the Cartesian product of
  `allocation_policy.equity_allocation`, `withdrawal_policy.withdrawal_rate`,
  and `cohorts.horizon_years`; every generated configuration carries all three
  values.
- `cohorts.horizon_years` defines the per-configuration horizons in years (each
  is a prefix slice of the canonical dataset). Cohorts are generated as rolling
  monthly windows against the longest declared horizon.
- Value arrays must be non-empty; there are no implicit defaults, and the
  legacy `parameters` section, `cohorts.window_years`, and `cohorts.type` are
  rejected.

See [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) for the configuration file and
[EXAMPLES.md](../../examples/EXAMPLES.md) for ready-to-run studies.