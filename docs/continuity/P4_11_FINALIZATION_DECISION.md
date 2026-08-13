# P4.11 Finalization Decision Record

Status: Approved and implemented
Date: 2026-08-13
Scope: Phase 4, workstream P4.11 (Reference horizon chaining + grid CLI output)

This record finalizes the five open decisions from the P4.11 architectural review.
Each decision records the context, the options considered, the decision, and its
rationale. It is the authoritative reference for what was decided and why.

---

## Decision 1 — F5 (fast-path float execution) is NOT implemented

Context
- F5 proposed a fast-path executor computing a single float-precision trajectory
  as a cheaper approximation for grid sweeps.

Decision
- **DON'T DO** F5. It is rejected and will not be implemented in P4.11.

Rationale
- The reference chaining workstream already delivers the exact same results as
  the independent Reference engine at a fraction of the month-work (see
  Decision 2), which supersedes the need for an approximation path.
- A float fast path introduces a second, different answer set that must be
  reconciled with the Decimal-precision Reference engine, creating an
  unbounded accuracy-conformance surface. The cost is not justified by any
  remaining gap.
- No engine or default execution mode is changed.

---

## Decision 2 — Float default is retained; exactness is opt-in via `--reference-chained`

Context
- `config.execution.default_workers` is 1 and the default execution mode is the
  independent Reference engine. A float fast path exists as an opt-in flag.

Decision
- Keep the default execution mode unchanged: the independent Reference engine,
  run sequentially. Do not change `src/engine/**`.
- `--fast-path` (float) and `--reference-chained` (exact) remain explicit,
  opt-in flags; at most one may be set.
- The exact Reference path is `--reference-chained`.

Rationale
- No behavioral regression for existing users: default runs are byte-identical
  to before.
- Users who need exact grid results can opt into the chained Reference path,
  which reproduces the Reference engine exactly (it is the same engine, with
  shorter horizons derived from the longest-path evaluation of each horizon
  family instead of being recomputed).
- Approximate fast-path behaviour remains available for those who explicitly
  request it.

---

## Decision 3 — Slice-based chaining is the supported architecture; whole-plan materialization is prohibited

Context
- Chained materialization of the entire ERN grid holds ~0.37 MiB of timeline
  payload per unit, ~110 GiB in aggregate. Dispatching the whole plan to a
  single executor call (whole-definition batch dispatch) is the root cause of
  the potential out-of-memory failure.

Decision
- The CLI must never hand the whole plan to a single chained executor call.
- `execute_reference_chained` splits the plan into cohort-aligned slices (a
  cohort is never split, so horizon families stay grouped and the exact
  month-work reduction is preserved), dispatches each slice through
  `parallel_execute` with a shared `ChainedReferenceSimulationExecutor`, and
  merges the per-slice results back in original plan order.
- Slices are bounded by cohort count (`_DEFAULT_CHAINED_SLICE_COHORTS = 100`),
  keeping peak per-worker timeline residency bounded.

Rationale
- Bounded memory: the largest slice carries only the cohorts in one slice, so
  peak residency is a fixed multiple of a slice, never the whole grid.
- Exactness is preserved: slicing is cohort-aligned and result merging is order
  preserving, so the merged result equals a whole-plan execution of the same
  engine.
- Regression tests assert that no slice equals the full plan for a multi-cohort
  grid, and that sliced execution is equivalent to whole-plan execution of the
  chained engine.

---

## Decision 4 — Full-grid chained E2E stays opt-in / release-gated until CI exists

Context
- The full-grid reference-chained E2E (313,020 units) reproduces the
  independent Reference full-grid run cell-for-cell. There is no CI
  infrastructure in the repository yet.

Decision
- The full-grid reference-chained E2E remains opt-in and release-gated: it runs
  only when the explicit E2E opt-in flags are set, and is not part of any CI
  job (none exists).
- The E2E harness exercises the memory-safe CLI path
  (`--reference-chained` through `sim-retire run`), not a whole-plan API call.
- The runner must set `ERN_E2E_REFERENCE_CHAINED=1` and supply `ERN_E2E_WORKERS`
  explicitly to run it.

Rationale
- 313k units is heavy; it must never run by default in a test sweep.
- Running it through the CLI keeps the E2E aligned with the real supported
  memory-safe path.
- Once CI exists, this E2E can be wired in behind the same explicit opt-in flag
  or a release marker.

---

## Decision 5 — Generic grid per-cell output is implemented; a 4th axis is a real correctness bug fixed by the generic form

Context
- The ERN grid output previously hardcoded the three ERN axes
  (`equity_allocation`, `withdrawal_rate`, `horizon_years`). A grid study with a
  fourth axis (e.g. `n_duration`) would silently aggregate units that differ
  only on that axis into one cell.

Decision
- Implement the generic per-cell output: cell keys are derived from *all*
  parameter names in the unit's configuration, keeping the three ERN axes first
  in their original relative order (`_GRID_CELL_PARAMETER_ORDER`) for stable
  output, with any additional axis names appended in canonical order.
- The ERN E2E parser and expected cell layout are unchanged; for pure 3-axis
  ERN grids the printed lines are byte-identical to before.
- A regression test covers a 4-axis grid and asserts the extra axis appears in
  every cell key, that no two configurations collapse into one cell, and that
  units_run counts are per full configuration.

Rationale
- Cell identity is per full parameter configuration, not per the ERN triple.
- Keeping the ERN axes first preserves existing machine-parseable output for
  the supported ERN studies.
- The generic form removes the silent-aggregation bug for all future grids.