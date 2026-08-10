# ADR-003: Soft Deletion Is Reversible Only by Semantic Equivalence

**Status:** Accepted
**Date:** 2026-08-10
**Milestone:** v0.4 Infrastructure & Deployment — SQLite persistence / P4.9

---

## Context

The persistence layer implements soft deletion: `experiments` and
`research_plans` carry a `deleted_at` column, and logically deleted rows are
hidden from every query API. Soft deletion is intended to be reversible so an
interrupted/re-executed study can reclaim its original identity.

The naive reversal — *"a save whose ID collides with a soft-deleted row clears
`deleted_at` and reuses that ID"* — is unsafe: an ID alone is not evidence of
identity. Two executions of the same study get distinct storage-generated UUIDs,
so the persisted ID is incidental. Reusing a deleted row on the basis of a
matching ID could resurrect a row whose *content* is unrelated to what is now
being saved.

## Decision

**A logically deleted entity may be restored if and only if the entity that
would otherwise be saved is semantically equivalent to the stored deleted
entity. Matching a persistence ID alone is never sufficient.**

Concretely, in `SQLiteRepository.save_experiment`:

1. Look up the natural identity `(name, revision)`.
2. **No row** → create normally.
3. **Active row** → the existing duplicate/idempotency semantics apply
   (an active duplicate raises `DuplicateStudyError`).
4. **Soft-deleted row** → build a deterministic canonical snapshot of both the
   incoming experiment and the stored experiment:
   - if they are **equivalent**, clear `deleted_at` on the stored row and reuse
     its `experiment_id` (restore);
   - if they are **not equivalent**, treat it as a genuine collision: raise
     `DuplicateStudyError` ("Refusing to restore"), leaving the deleted row
     untouched.

Enforcement lives in `_restore_if_semantically_equivalent`, and the comparison
is implemented by `experiments_semantically_equivalent`
(`src/infrastructure/persistence/sqlite_repository.py`).

## What "equivalent" means

The comparison uses **semantic content fields** only, serialized to a
deterministic canonical snapshot. For an experiment these are:

| Field | Role |
|---|---|
| `name`, `revision` | Natural identity (already equal by the lookup key) |
| `description` | User-defined content |
| `dataset_identifier` | Which dataset the simulation consumed |
| `horizon_months` | Simulation horizon |
| `initial_wealth`, `initial_wealth_currency` | Starting capital |
| `allocation_policies` | Serialized policies in index order |
| `withdrawal_policies` | Serialized policies in index order |
| `cohort_start_dates` | Cohort set (sorted) |

Explicitly **excluded** as non-deterministic / incidental:

- `created_at`, `updated_at`, `deleted_at` — wall-clock provenance;
- `experiment_id`, `plan_id`, `result_id` — storage-generated UUIDs;
- `duration_seconds`, `execution_time_seconds` — measurement noise;
- simulation results and per-month timelines — outputs, not configuration.

These rules are encoded in the snapshot builders
(`_experiment_snapshot_from_object`, `_experiment_snapshot_from_rows`) and
documented by `_DETERMINISTIC_EXPERIMENT_FIELDS` /
`_NON_DETERMINISTIC_FIELDS_DOC` in `sqlite_repository.py`. Any future persisted
entity (plans, results) must define its own explicit equivalent-field set rather
than comparing raw rows.

## Consequences

- Restoring an equivalent study reuses its original `experiment_id`, keeping
  export/query links stable across re-runs.
- Saving a materially different study under a soft-deleted natural identity
  fails loudly instead of silently resurrecting stale rows.
- Timestamps and provenance never influence the equivalence result.
- Covered by tests in `tests/infrastructure/test_sqlite_persistence.py` for all
  four cases:
  - no existing entity → create;
  - active equivalent entity → existing duplicate semantics;
  - soft-deleted equivalent entity → restore and reuse;
  - soft-deleted non-equivalent entity → refused, row stays deleted, no
    duplicate row created.
- Timestamp-difference restore is explicitly tested
  (`test_restore_allowed_timestamp_differences_do_not_block`), and the
  non-equivalence case verifies the old row remains deleted
  (`test_non_equivalent_save_leaves_deleted_row_deleted`).

## Affected Documents

| Document | Nature of Impact |
|---|---|
| [INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md](../../specifications/infrastructure/INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md) | Frozen v0.4 persistence spec; this ADR documents the soft-delete reversibility rule layered on it |
