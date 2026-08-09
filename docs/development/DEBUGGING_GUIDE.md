# Debugging Guide

Common failure modes in the `sim-retire` development workflow and how to
diagnose them, focused on SQLite persistence and dataset loading.

## 1. Exit codes

Every CLI command returns a documented `ExitCode` (`src/cli/error_handling.py`):

| Code | Constant | Meaning |
|------|----------|---------|
| `0` | `SUCCESS` | Command succeeded |
| `1` | `ERROR` | Execution error (study failed, I/O error) |
| `2` | `VALIDATION_ERROR` | Bad arguments, missing files, invalid study |
| `3` | `CONFIGURATION_ERROR` | Malformed configuration |
| `4` | `DATABASE_ERROR` | Database access failed |
| `130` | `INTERRUPTED` | Interrupted (Ctrl+C) |

If a command returns an unexpected code, start with the code to isolate the
layer: `2` → student/study parsing, `3` → config, `4` → persistence.

## 2. Dataset loading

Dataset files are JSON documents matching `data/<identifier>.json` under the
active data directory. Failures surface as `VALIDATION_ERROR` (`2`).

Common causes:

- **Wrong `--data-dir`** — when `--data-dir` is not supplied, the dataset
  resolver is empty and resolution fails. Point it at the actual location:
  `sim-retire --data-dir examples/data ...`.
- **Identifier mismatch** — the study's `dataset.identifier` is matched to the
  file stem. `identifier: "market_monthly"` requires `market_monthly.json`.
- **Corrupt JSON** — malformed files raise `StudyNotFoundError` during load
  (`src/infrastructure/persistence/context.py`). Validate with
  `python -m json.tool data/<name>.json`.

## 3. SQLite persistence issues

The library database is at `~/.sim-retire/studies.db` by default (see
`database.path` in the configuration, `docs/development/CONFIG_REFERENCE.md`).

| Symptom | Cause | Resolution |
|---------|-------|------------|
| `DATABASE_ERROR` (4) | Database file missing or unwritable | Confirm the `database.path` directory exists and is writable |
| Schema errors on save | Database created by an older schema | Schema version is tracked in `schema_version`; the DDL in `src/infrastructure/persistence/schema.py` is applied idempotently at open |
| `CorruptedDatabaseError` | File-level corruption (e.g. interrupted write) | Verify the file with the `sqlite3` CLI: `sqlite3 ~/.sim-retire/studies.db "PRAGMA integrity_check;"` |
| Missing primary key objects (experiment, plan, result) | The object was never saved, or `STUDY_ID` is wrong | Query via `sim-retire list`; persistence is keyed by `experiment_id` → `plan_id` → `result_id` |

The repository uses WAL mode and `synchronous=NORMAL`; those pragmas are set
on connection open.

## 4. CLI and study definition debugging

- **`sim-retire run --dry-run`** prints the plan summary (cohorts, parameter
  sweep, policies, total units, estimated time) and exits — the fastest
  sanity check before a full run.
- **`sim-retire validate <study>`** checks dataset, cohorts, parameter sweep,
  policies, and the resulting plan without executing.
- If `run` fails with a validation error, fix the study YAML, not the engine —
  the layered architecture surfaces the failure at the earliest boundary.

## 5. Common "silent failure" spots

- **Persistence warnings after a successful run** — `run` completes the
  simulation and only then attempts to persist; if persistence fails you see
  `WARNING: Persistence failed (execution completed)`. The simulation output
  of the CLI makes the run appear successful even though nothing was saved.
- **Dry-run vs real behaviour** — `--dry-run` validates the plan but does not
  execute or persist; a green dry-run does not guarantee a clean full run.
- **Determinism regressions** — if parallel results differ from sequential,
  focus on the executor (`src/infrastructure/execution/parallel_executor.py`);
  see [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md).

## 6. Environment and tooling

- **`sim-retire: command not found`** — activate the venv or install with
  `pip install -e ".[dev]"`.
- **`No module named pytest`** — the dev extras are not installed.
- **The full suite** is expected at **808 tests** (see
  [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) for the per-area split).

## See also

- [CLI_USAGE.md](CLI_USAGE.md) — commands and options.
- [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) — configuration keys.
- [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md) — benchmark-based checks.
- [EXTENSION_PATTERNS.md](EXTENSION_PATTERNS.md) — supported extension points.