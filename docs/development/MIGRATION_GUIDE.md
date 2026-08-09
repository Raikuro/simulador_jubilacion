# Migration Guide

How versioned artifacts in the repository evolve and how to migrate work
between them. This covers the SQLite schema, dataset files, and the
configuration file, plus the documentation history that led to today's layout.

## 1. SQLite library schema

The library (`~/.sim-retire/studies.db`) is versioned through the
`schema_version` table (`src/infrastructure/persistence/schema.py`):

```sql
CREATE TABLE schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
);
```

- `SCHEMA_VERSION = 1` (v0.4). The DDL statements are applied idempotently
  on every connection open (`_initialize_schema`), so opening an existing
  database never fails on re-run.
- Persisted records reference the previous version's tables through foreign
  keys (`experiments` → `cohorts` → `planned_units` → results). A clean new
  database is created automatically on first use; no user migration step is
  required.
- If a future schema change is needed, bump `SCHEMA_VERSION` and add the DDL
  to `ALL_DDL` rather than deleting old tables. Migration concerns are
  handled in the persistence layer, not the frozen engine/research layers.

## 2. Dataset JSON format

Datasets are self-describing JSON. Each file has an explicit `version` field,
so a dataset archive can be migrated independently of code:

```json
{
  "version": "1.0",
  "frequency": "monthly",
  "snapshots": [ ... ]
}
```

- The dataset `version` is preserved through persistence and round-trips,
  including dataset *resource identity* across reloads (fixed in
  `000323e`, "preserve dataset resource identity across reloads").
- All numeric values are stored as strings so `Decimal` precision is exact.
- Migration of a dataset is *adding a new version**; existing datasets keep
  their `version` value and are not rewritten.

## Configuration file

The user-facing configuration lives in `~/.sim-retire/config.yaml` (see
[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)) and has a fixed section
structure:

```yaml
database:
  path: ~/.sim-retire/studies.db
output:
  default_format: csv
  default_directory: ./results/
execution:
  default_workers: 4
logging:
  level: INFO
```

- Old config keys are removed in updates; use `config validate` to check a
  file against the current schema.
- New keys have built-in defaults; an existing config file remains valid until
  an intentional breaking change. When a user updates the config format, run
  `sim-retire config validate` after editing.

## Documentation history

Documentation was reorganized on **2026-07-24**; this history is recorded in
`docs/history/` (e.g. `CLEANUP_SUMMARY.md`) and the git rename history. The
`MIGRATION_REPORT.md` file referenced by older planning documents was never
created; its scope is covered by `docs/DOCUMENTATION_TREE.md` and the git
rename history.

The development guides have been split into user-facing
(`CLI_USAGE`, `CONFIG_*`) and developer-facing
(`DEVELOPMENT_WORKFLOW`, `EXTENSION_PATTERNS`, `PERFORMANCE_GUIDE`,
`DEBUGGING_GUIDE`) documents under `docs/development/`.

## Migration checklist

When upgrading a codebase or a persisted dataset:

1. Confirm the CLI contract: `sim-retire --version` (0.1.0).
2. Check `schema_version` on the target DB: `sim-retire list` should run with
   no `DATABASE_ERROR`.
3. If a dataset `version` changes, keep the historical version reachable or
   regenerate the dataset JSON, preserving the `Decimal` string format.
4. Re-run [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) steps 2 and 4
   (CLI docs vs behaviour, full test suite) after any code migration.
5. Run the full suite: `pytest -q` (808 tests).

## See also

- [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) — failure diagnostics.
- [EXTENSION_PATTERNS.md](EXTENSION_PATTERNS.md) — adding new artifacts.
- [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) — configuration file format.
- [DOCUMENTATION_TREE.md](../DOCUMENTATION_TREE.md) — repository-wide layout.