# FIRE Backtesting Framework — P4.10 F7 Follow-up: `--fast-path --validate` Implementation Report

**Deliverable:** F7 (`--fast-path --validate`) runtime cross-validation, as deferred in `docs/continuity/P4_10_ARCHITECTURAL_REVIEW.md` and `docs/continuity/P4_10_CONDITIONAL_APPROVAL_FIXES_REPORT.md`
**Date:** 2026-08-11
**Status:** IMPLEMENTED + VERIFIED. Reference Decimal engine untouched; `--fast-path` remains opt-in. Committed as part of the P4.11 pre-work baseline cleanup.

---

## 1. Scope

This is a follow-up to `docs/continuity/P4_10_ARCHITECTURAL_REVIEW.md`, where finding **F7** ("Continuous validation") was recorded as a recommendation and explicitly **deferred** ("⏸ Not implemented") in `P4_10_CONDITIONAL_APPROVAL_FIXES_REPORT.md`. This work implements F7 so the "reference-as-oracle" property is continuously enforced at runtime rather than only by the fixed test grids.

The change is **purely additive**: it ships an opt-in `--fast-path --validate` flag, new pure validation helpers in `src/cli/fast_path.py`, and their tests. No existing execution path is altered, and the reference Decimal engine is byte-for-byte untouched.

---

## 2. Implementation

### 2.1 Deterministic eligible-unit sampling (`src/cli/fast_path.py`)

`select_validation_units(plan, max_units=8)` returns a small, deterministic sample of a plan's fast-path-eligible units:

- Only fast-path-eligible units are sampled. Comparing a unit that falls back to the reference would validate the reference against itself, so ineligible units are excluded.
- Sampling is deterministic: eligible units are ordered by plan index and a fixed-seed RNG (`FAST_PATH_VALIDATION_SEED`) selects the sample indices. The same plan always yields the same units across calls, processes and hosts.
- Sample size is capped at `FAST_PATH_VALIDATION_MAX_UNITS = 8`.
- Eligibility uses `_unit_simulation_context`, which translates a `PlannedSimulationUnit` into the engine `SimulationContext` exactly as `ResearchExecutor._create_context_for_unit` does, so validation operates on the very contexts the executor would build.

### 2.2 Comparison against the Decimal reference engine

`run_fast_path_validation(plan, max_units=8, tolerance=Decimal("0.05"))`:

1. Samples eligible units via `select_validation_units`.
2. Executes the sample through **both** paths using `sequential_execute`:
   - the canonical Decimal reference engine (default executor), and
   - `FastPathSimulationExecutor(precision="float")` — the exact path `--fast-path` requests.
3. Compares each pair with `_compare_fast_path_result`.

`_compare_fast_path_result` validates three things per unit:

| Check | Semantics |
|---|---|
| **outcome** | success/failure must match |
| **failure month** | on failure, the depletion month must match |
| **final wealth** | on success, `|reference − fast| <= 0.05 EUR` tolerance |

Any divergence raises `FastPathValidationError` naming the diverging unit (cohort start date and parameter configuration) with the observed vs expected statistics. On success it returns `(sampled_units, eligible_units)`.

### 2.3 CLI `--fast-path --validate` (`src/cli/commands/run_command.py`)

- New `--validate` flag on `sim-retire run`.
- **Guard:** `--validate` without `--fast-path` is rejected pre-flight with `ExitCode.VALIDATION_ERROR` and an explanatory message (`--validate` compares the fast path against the Decimal reference, so it is meaningless without it).
- **Pre-flight:** when both flags are set, `run_fast_path_validation(plan)` runs **before** the requested execution. A `FastPathValidationError` fails the run loudly; otherwise the CLI reports the outcome:

```
Validation:     OK (8 fast-path unit(s) vs Decimal reference)
Validation:     skipped (no fast-path-eligible units)
```

- The validation is purely additive: it never mutates or replaces the results of the requested execution path, and only ever runs the two engines on the small (≤ 8 unit) sample.

---

## 3. Regression Tests Added

`tests/cli/test_fast_path.py` (`TestFastPathValidation`):
- `test_validation_success` — an eligible plan validates cleanly; sample equals the cap.
- `test_validation_returns_zero_when_nothing_eligible` — no eligible units → `(0, 0)`.
- `test_validation_detects_divergence` — a perturbed fast path raises `FastPathValidationError` naming the first sampled cohort and the `final_wealth` divergence.
- `test_validation_sampling_is_deterministic` — the sample is stable and bounded.
- `test_validation_sample_skips_ineligible_units` — the sample never includes reference-fallback units.

`tests/cli/test_run_command.py`:
- `test_validate_requires_fast_path` — `--validate` alone → `VALIDATION_ERROR` with a `--fast-path` hint.
- `test_fast_path_validate_runs_and_reports` — `--fast-path --validate --no-persist` runs the pre-flight, prints `Validation: OK (N fast-path unit(s) vs Decimal reference)`, and skips the repository.

New tests: **+7** (867 → 874 in the full suite).

---

## 4. Validation Gates

| Gate | Command | Result |
|---|---|---|
| Full test suite | `pytest tests -q` | **874 passed, 4 skipped** (E2E ERN gated off) |
| F7 unit tests | `pytest tests/cli/test_fast_path.py` | **29 passed** |
| CLI tests | `pytest tests/cli/test_run_command.py` | **22 passed** |
| Lint | `ruff check src/ tests/` | Clean |
| Typing | `mypy --strict src/ tests/` | **0 errors** (188 files) |

The 180-cell ERN grid was **not** re-run for this change: the reference engine is untouched, the F7 changes are additive, and the grid had already passed under the previous baseline.

---

## 5. Diff Hygiene

Only the intended files are committed: the F7 edits (`run_command.py`, `fast_path.py`), the F7 tests, the ERN E2E worker-selection change and its tests, and the two documentation updates (`CLI_USAGE.md`, `DEVELOPMENT_WORKFLOW.md`). No changes under `src/engine/**`. The reference Decimal engine is byte-for-byte untouched.

---

## 6. Notes / Follow-ups

- The ERN E2E worker-selection change (`ERN_E2E_WORKERS` default / `N` / `max`, `tests/e2e/ern/constants.py::resolve_e2e_workers`) is intentionally an E2E/test-harness feature committed in the same baseline. A generic CLI `--workers max` remains a separate architectural item (P4.11 scope), not part of this change.
- **P4.11 (not started):** representing the complete ERN 180-cell grid as one generic `ResearchPlan`, wiring parameter sweeps to policy construction, multi-horizon support with horizon chaining, and the generic CLI `--workers max`.
