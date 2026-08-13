# P4.11 Finalization Implementation & Validation Report

**Deliverable:** P4.11 finalization — conservative worker-count default, memory-safe CLI chained Reference dispatch, generic grid per-cell output, and the five approved decisions from `docs/continuity/P4_11_FINALIZATION_DECISION.md`
**Date:** 2026-08-13
**Status:** IMPLEMENTED + VERIFIED. Reference Decimal engine untouched; default execution mode unchanged; all gates green. Awaiting review before commit.

---

## 1. Scope

This report covers the two workstreams closed out in this finalization:

1. **Conservative worker-count default** (approved change): the project no longer auto-uses every logical CPU; the implicit default is `min(8, os.cpu_count() or 1)`, CPU-agnostic, with explicit `--workers` / `ERN_E2E_WORKERS` overrides preserved exactly.
2. **P4.11 finalization plan** (approved items): memory-safe CLI dispatch for `--reference-chained` (no whole-plan materialization), generalized per-cell grid output (4th axis is a real correctness bug), regression coverage, full-grid reference-chained E2E on the memory-safe path, and the decision record.

Constraints honored throughout: `src/engine/**` untouched, default execution mode unchanged (independent Reference), no future-workstream items started, no commit made.

---

## 2. Decision 3 — Memory-safe slice dispatch (Item 3)

### 2.1 Problem

The chained Reference executor materializes ~0.37 MiB of timeline payload per unit (~110 GiB for the 313,020-unit ERN grid). The pre-finalization CLI handed the whole plan to a single executor call (whole-definition batch dispatch), the OOM root cause identified in the architectural review.

### 2.2 Fix (`src/infrastructure/execution/reference_chaining.py`)

`execute_reference_chained(plan, max_workers, progress_callback, summary_only, slice_cohorts=100)`:

- Splits the plan into cohort-aligned slices via `_slice_plan_units` (a cohort is never split, so every horizon family stays grouped and the exact month-work reduction is preserved; relies on the cohort-major ordering the plan materializers produce).
- Dispatches each slice through `parallel_execute` with a shared `ChainedReferenceSimulationExecutor`.
- Merges per-slice results back in original plan order with index provenance (`ResearchExecutionResult` requires `len(plan.units) == len(results)`, so the merge is structurally enforced).
- Progress is reported once per completed slice with global completed/total counts.

`run_command.py` now routes `--reference-chained` exclusively through `execute_reference_chained` (its own try/except → `ExitCode.ERROR`), never through a whole-plan executor call. This also fixed a latent control-flow bug: the previous reference-chained branch fell through into the generic `try:` block and re-executed via the independent `sequential_execute`, overwriting the result.

### 2.3 Regression coverage (`tests/infrastructure/test_reference_chaining.py`)

New `TestSliceDispatchMemorySafety`:

- `_slice_plan_units` is cohort-aligned and order-preserving (recombined slices == original plan order).
- No cohort is split across slices (within a slice, cohort start dates are monotonic).
- Every slice is strictly smaller than the whole plan.
- `execute_reference_chained` with a multi-cohort plan dispatches ≥3 sub-plans, each strictly smaller than the whole plan (patches the module-local `parallel_execute`).
- Slice equivalence: a 2-cohort-per-slice run reproduces the single-slice run result-for-result exactly.

### 2.4 Memory behaviour

Slice size is bounded by cohort count (default 100 cohorts/slice), keeping peak per-worker timeline residency a fixed multiple of a slice, never the whole grid. The regression tests pin the "never the whole plan in one call" invariant.

---

## 3. Decision 5 — Generic per-cell grid output (Item 5)

### 3.1 Problem

The grid output hardcoded the three ERN axes (`equity_allocation`, `withdrawal_rate`, `horizon_years`). A study with a fourth axis (e.g. `n_duration`) silently aggregated units that differ only on that axis into one cell — a real correctness bug, not a future concern.

### 3.2 Fix (`src/cli/commands/run_command.py`)

`_print_grid_per_cell_results` now derives cell keys/labels from **all** parameter axes of each unit's `ParameterConfiguration`, keeping the three ERN axes first in their historical relative order (`_GRID_CELL_PARAMETER_ORDER`) and appending any additional axes in canonical sorted order. For pure 3-axis ERN grids the printed lines are byte-identical (the E2E parser and `tests/cli/test_grid_chaining.py::TestGridPerCellByteLayout` pin the exact byte layout).

### 3.3 Regression coverage

- `tests/cli/test_grid_chaining.py::TestGridCliFourthAxis`: a `horizon_years × n_duration` grid emits one cell line per full configuration (4 lines, no collapse), every line carries the 4th axis, and `units_run` counts are per full configuration.
- `tests/cli/test_grid_chaining.py::TestGridPerCellByteLayout`: a 3-axis ERN grid keeps the historical `cell: equity_allocation=… withdrawal_rate=… horizon_years=…` field order and exact byte layout.

---

## 4. Conservative worker-count default

- `src/infrastructure/execution/parallel_executor.py`: `_DEFAULT_MAX_WORKERS = 8`; `default_max_workers()` = `min(8, os.cpu_count() or 1)`; the `parallel_execute` fallback (None/≤0 workers) now uses it. `ExecutionConfig.max_workers` docstring updated.
- `src/infrastructure/execution/reference_chaining.py`: `execute_reference_chained` resolves None/≤0 workers through `default_max_workers()`.
- Explicit overrides preserved exactly: `--workers N` → N, `--workers max` → `os.cpu_count() or 1` (all logical CPUs, unchanged), `ERN_E2E_WORKERS=N`/`=max` unchanged. CLI `run` default without `--workers` stays `config.execution.default_workers` (default 1).
- E2E: `_resolve_workers_arg()` unset now passes the conservative baseline (via `resolve_e2e_workers`) instead of literal `"max"`; docstrings/comment block updated in `tests/e2e/ern/constants.py`.
- Docs: `CLI_USAGE.md`, `CONFIG_REFERENCE.md`, `PARALLEL_EXECUTION_SPECIFICATION.md`.
- New tests in `tests/infrastructure/test_parallel_execution.py`: cap at 8 on large hosts, host count below cap, floor 1 when `cpu_count()` is None, explicit override bypasses the default.

---

## 5. Decision record

`docs/continuity/P4_11_FINALIZATION_DECISION.md` records the five decisions (F5 DON'T DO; float default retained with opt-in `--reference-chained`; slice-based chaining supported / whole-plan prohibited; full-grid chained E2E opt-in until CI; generic grid output implemented), each with context, options, decision, and rationale.

---

## 6. Validation

### 6.1 Static gates

| Gate | Result |
|---|---|
| `ruff check src/ tests/` | All checks passed |
| `mypy --strict src/` | Success, 109 source files |
| `mypy --strict tests/` | Success, 88 test files |

### 6.2 Unit / integration suite

`pytest tests/ -m "not ern_e2e"` → **975 passed, 6 deselected** (~92 s).

Focused: `test_reference_chaining.py` 15 passed; `test_grid_chaining.py` 11 passed; `test_run_command.py` (incl. `TestExecutionModeSelection` 6/6) + `test_parallel_execution.py` + E2E parser all pass.

### 6.3 Black-box E2E (public CLI subprocess)

| Test | Result |
|---|---|
| Smoke grid matches oracle (independent Reference) | PASS |
| Smoke reference-chained reproduces reference (CLI `--reference-chained`) | PASS (~112 s) |
| Smoke fast-path reproduces reference | PASS |
| Full-grid reference-chained reproduces reference (313,020 units, 180 cells, via `sim-retire run --reference-chained`) | **PASS** (~39 min wall) |

The full-grid chained run exercises the memory-safe CLI slice path end-to-end on the complete ERN grid and matches the independent Reference cell-for-cell exactly (bit-exact equality per the E2E's exact-equality assertion). The full-grid fast-path and full-grid reference-chained equivalence runs remain opt-in (`RUN_ERN_E2E_FULL` + the corresponding `ERN_E2E_*` flag), as decided.

---

## 7. Files changed

- `src/infrastructure/execution/parallel_executor.py` — conservative default worker resolution
- `src/infrastructure/execution/reference_chaining.py` — memory-safe slice dispatch + default workers
- `src/cli/commands/run_command.py` — exclusive `--reference-chained` route (fixed fall-through bug), generic per-cell output, `_GRID_CELL_PARAMETER_ORDER`
- `tests/infrastructure/test_reference_chaining.py` — slice memory-safety + equivalence tests
- `tests/infrastructure/test_parallel_execution.py` — default worker policy tests
- `tests/cli/test_grid_chaining.py` — 4th-axis + byte-layout regression tests
- `tests/cli/test_run_command.py` — chained routing tests updated to module-local patch
- `tests/e2e/ern/constants.py`, `tests/e2e/ern/test_ern_swr_replication.py` — conservative E2E worker default + docstrings
- `docs/development/CLI_USAGE.md`, `docs/development/CONFIG_REFERENCE.md`, `docs/specifications/infrastructure/PARALLEL_EXECUTION_SPECIFICATION.md`
- `docs/continuity/P4_11_FINALIZATION_DECISION.md` — decision record (new)

---

## 8. Awaiting review

Stopped before commit, per instruction. All five P4.11 decisions are implemented and verified; the reference Decimal engine and the default execution mode are unchanged.