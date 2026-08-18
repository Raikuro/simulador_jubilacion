# Extension Patterns

This guide shows the supported extension points in `sim-retire`. It covers
dataset format, policies, CLI commands, and the frozen layers you must not
modify.

## 1. Frozen layers (do not modify)

The engine (v0.1), research (v0.2), and optimization (v0.3) layers are
frozen. Add behaviour through the infrastructure layer (`src/infrastructure`,
`src/cli`) and the supported seams listed below. See
`docs/continuity/NEXT_SESSION.md` — "Mandatory Architectural Invariants".

## 2. Add a dataset

A dataset is a single JSON file matching the identifier used by the study.
The stem of the filename is the identifier.

Given `examples/data/market_monthly.json`, the format is:

```json
{
  "version": "1.0",
  "frequency": "monthly",
  "snapshots": [
    {
      "date": "1990-01-01",
      "inflation": "0.002466269772303599979971653",
      "inflation_cumulative": "1.002466269772303599979971653",
      "is_ath": true,
      "is_underwater": false,
      "running_ath": "100.6434030110003454833917179",
      "index_levels": {
        "equity": "100.6434030110003454833917179",
        "bond": "100.2870898719076627617009256"
      }
    }
  ]
}
```

- Every decimal is stored as a string to preserve exact `Decimal` values.
- `index_levels` maps an asset-class identifier to its level.
- The loader matches a study's `dataset.identifier` to `data/<identifier>.json`
  under the active data directory (the `--data-dir` argument; without it the
  resolver registry is empty).

To add a dataset, drop the JSON file into the active data directory. Existing
datasets are discovered automatically by
`src/infrastructure/persistence/context.py`
(`_load_datasets_from_dir` → `DefaultDatasetResolver.from_data_dir`).

## 2. Add or extend a policy

The concrete policy types live in `src/cli/policies.py`
(`ConstantAllocationPolicy`, `ConstantWithdrawalPolicy`,
`FixedRealWithdrawalPolicy`). The normalized study configuration
(`StudyConfiguration`) interprets the singular YAML base policies
(`allocation_policy:` / `withdrawal_policy:`) and `build_study_plan` threads
them into the research plan; all commands consume this single interpretation
layer via `src/cli/builders.py`:

| Policy | YAML key | Builder option(s) | Implementation |
|--------|----------|-------------------|----------------|
| Constant allocation | `allocation_policy` | `equity_allocation` | `ConstantAllocationPolicy` |
| Constant withdrawal | `withdrawal_policy` | `withdrawal_rate` | `ConstantWithdrawalPolicy` |
| Fixed real withdrawal | `withdrawal_policy` | `withdrawal_rate` | `FixedRealWithdrawalPolicy` |

To add a new policy type, keep the `src/cli/builders.py` convention: add a
builder function without changing existing signatures, and pair the new type
with a codec so it round-trips through SQLite persistence
(`src/infrastructure/persistence/codecs.py`, registered in
`create_persistence_context`).

## 3. Add a CLI command

Each command lives in `src/cli/commands/<name>_command.py` and subclasses
`BaseCommand`:

```python
class RunCommand(BaseCommand):
    name = "run"
    help_text = "Execute a research study"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("study_file", type=str, help="Path to YAML experiment definition")
        ...

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        ...
        return ExitCode.SUCCESS
```

- `name` is the CLI verb; `help_text` is shown in `--help`.
- `execute` returns an `ExitCode` (`SUCCESS`, `VALIDATION_ERROR`,
  `CONFIGURATION_ERROR`, etc.).
- Register the command in `src/cli/main.py` when adding it to the dispatch
  table.
- Command modules must not write to `src/engine/`, `src/research/`, or
  `src/optimization/` layers (frozen). They consume them through the public
  APIs.

## 4. Persistence / repository extensions

`SQLiteRepository` (`src/infrastructure/persistence/sqlite_repository.py`) is
the persistence seam. It is constructed with a database path:

```python
from infrastructure.persistence import SQLiteRepository, create_persistence_context
repo = SQLiteRepository("~/.sim-retire/studies.db")
context = create_persistence_context(data_dir)
repo.save_experiment(identity, experiment_def, context)
```

Schema DDL lives in `src/infrastructure/persistence/schema.py` (v0.4). See
the SQLite persistence specification:
`docs/specifications/infrastructure/INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md`.

## 5. Performance seams (measure where specified)

Instrumented surfaces are defined in [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md):
CLI startup, plan translation, parallel dispatch, and persistence writes.

## Summary checklist

When extending the framework:

1. Respect frozen layers (engine, research, optimization, CLI commands).
2. Add builder/helper functions in the command modules without changing
   existing signatures (`src/cli/builders.py` and the command helpers).
3. Add decoders/encoders in `src/infrastructure/persistence/` for new
   persisted objects.
4. Add tests (unit → integration → regression), then run the full suite.
5. Update the docs that describe the changed behaviour (see
   [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) — "Documentation
   responsibilities").

## See also

- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) — system overview.
- [CLI_USAGE.md](CLI_USAGE.md) — command interface details.
- [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) — configuration keys.
- [CONTRIBUTION.md](CONTRIBUTION.md) — contributing rules.