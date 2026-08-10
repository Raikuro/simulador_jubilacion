# FIRE Backtesting Framework — P4.10: Conditional-Approval Fixes (F1–F6) — Implementation Report

**Deliverable:** Implementation + verification of the P4.10 architectural-review findings F1–F6
**Date:** 2026-08-10
**Status:** IMPLEMENTED + FULLY VERIFIED. Reference Decimal engine untouched; `--fast-path` remains opt-in. No commit made (per instruction).

---

## 1. Scope

Per the architect's stop-order, this change implements the six actionable findings from `docs/continuity/P4_10_ARCHITECTURAL_REVIEW.md` and **no further optimization work**. F7 (`--fast-path --validate`) is explicitly deferred to a future work item.

| Finding | Severity | Status |
|---|---|---|
| F1 — reject `--fast-path` when timelines would be persisted | HIGH (blocking) | ✅ Done |
| F2 — chaining must refuse contexts that differ (data/wealth/portfolio) | HIGH (blocking) | ✅ Done |
| F3 — eligibility requires `dataset length >= horizon_months` | LOW | ✅ Done |
| F5 — correct the misleading 2–3 orders-of-magnitude docstring | LOW | ✅ Done |
| F6 — CLI transparency: fast-path vs reference unit counts | MEDIUM | ✅ Done |
| F7 — opt-in runtime cross-validation | deferred | ⏸ Not implemented |

---

## 2. Implementation

### F1 — `--fast-path` + persistence guard (`src/cli/commands/run_command.py`)

The fast path returns `SimulationTimeline(monthly_results=())` (summary-grade by design). Since persistence is the CLI default, `fire run <study> --fast-path` previously persisted empty timelines silently. A guard now mirrors the existing `--summary-only` conflict check:

```
ERROR: --fast-path cannot be combined with --persist-study
       The fast path produces summary-grade results without
       per-month timelines, so persisted results would be
       silently empty. Re-run with --no-persist or --summary-only.
```

Returns `ExitCode.VALIDATION_ERROR`. Valid combinations `--fast-path --no-persist` and `--fast-path --summary-only` are unchanged.

### F2 — chaining safety (`src/cli/fast_path.py`)

Two hardening changes to `ChainedFastPathSimulationExecutor.execute`:

1. **Group key extended** from `(start_date, equity_allocation, withdrawal_rate)` to also include `context.initial_wealth` and `context.initial_portfolio`. Contexts differing in either now land in separate groups and are never cross-derived.
2. **Dataset prefix verification**: even within a group (same key), every non-longest context must satisfy `_dataset_is_identity_prefix(ctx, longest_ctx)` — its dataset's `MarketSnapshot` objects must be the very same objects held by the longest context's dataset (`Dataset.slice` shares the underlying snapshot objects). Contexts failing the check are evaluated individually via `evaluate_closed_form` instead of being derived from the longest path.

This preserves the optimization for the legitimate ERN pattern (30/40/50/60y horizons are prefixes of the same trajectory, same wealth/portfolio) while refusing to chain anything whose data differs.

> **Post-commit-benchmark refinement (F2):** the prefix check was initially implemented by rebuilding full Decimal index series per context, which the pre-commit benchmark showed added ~52% overhead to the chained path (halving the chaining benefit). It was replaced with the identity-based snapshot-prefix check above, which costs O(months) cheap `is` comparisons and no Decimal work. Refusing to chain is always safe (correct results, just no reuse), so the strict guarantee "results are never cross-derived from different data" is fully preserved.

### F3 — eligibility dataset-length check (`src/cli/fast_path.py`)

`is_fast_path_eligible` now returns `False` when `len(dataset.snapshots) < horizon_months`, since the recurrence reads index levels up to `horizon_months - 1`. Previously this could raise `IndexError` deep in `evaluate_path`.

### F5 — documentation (`src/cli/fast_path.py`)

The module docstring no longer claims "~2-3 orders of magnitude". It now states the measured figures: combined `--fast-path` ≈ **4.2× end-to-end** on the ERN 180-cell grid; single closed-form path ≈ **2.3×** vs the reference recursion (with a pointer to the benchmark suite).

### F6 — CLI transparency (`src/cli/fast_path.py` + `run_command.py`)

New pure helper `fast_path_unit_counts(plan) -> (fast_units, reference_units)` mirrors `ResearchExecutor`'s unit→context translation and applies the same `is_fast_path_eligible` predicate, so the count is exact and independent of the execution path (sequential/parallel). The `run` completion summary now prints, only when `--fast-path` is active:

```
Fast Path:      4,000 units (closed form)
Reference Path:   200 units (fallback)
```

This makes it visible when a plan's policies are outside the closed-form family (e.g. `ConstantWithdrawalPolicy`) and the user gets zero speedup.

---

## 3. Regression Tests Added

`tests/cli/test_fast_path.py`:
- `test_eligibility_requires_dataset_covering_horizon` — F3: 480-month horizon on a 120-month dataset → ineligible; 120-on-120 → eligible.
- `test_chained_executor_refuses_different_initial_wealth` — F2: same key, different wealth → chained results identical to per-context fast path (would fail on the old coarse key).
- `test_chained_executor_refuses_non_prefix_dataset` — F2: same key, divergent dataset trajectory → not chained; per-context equality holds.
- `test_fast_path_unit_counts_mixed` — F6: mixed eligible/non-eligible plan yields correct `(fast, reference)` split and the all-eligible baseline.

`tests/cli/test_run_command.py`:
- `test_fast_path_conflicts_with_persist` — F1: `--fast-path` with default persistence → `VALIDATION_ERROR` and clear message.
- `test_fast_path_with_no_persist_reports_coverage` — F1+F6: `--fast-path --no-persist` succeeds, prints `Fast Path:` / `Reference Path:`, and skips the repository.

New tests: **+6** (849 → 855 in the full suite).

---

## 4. Validation Gates

| Gate | Command | Result |
|---|---|---|
| Full test suite | `pytest tests -q` | **855 passed, 4 skipped** |
| E2E (incl. fast-path acceptance) | `RUN_ERN_E2E=1 ERN_E2E_FAST_PATH=1 pytest tests/e2e` | **12 passed, 1 skipped** |
| ERN full 180-cell acceptance | `RUN_ERN_E2E=1 RUN_ERN_E2E_FULL=1 pytest …::test_full_grid_matches_oracle` | **1 passed** (wall 26:22; all cells within ±1pp, anchors 95/65/97) |
| Lint | `ruff check src/ tests/` | Clean |
| Typing | `mypy --strict src/ tests/` | **0 errors** (107 + 80 files) |

The full 180-cell ERN acceptance was re-run to confirm the untouched reference engine still reproduces the published Table 1; the fast-path acceptance cells confirm `--fast-path` reproduces the reference success rates exactly on the smoke grid.

## 5. Chaining Benchmark After F2 (no-regression check)

ERN-style grid: synthetic 120-year dataset, 40 cohorts × {30, 40, 50, 60}y horizons (160 contexts), float precision, measured on the development host:

| Configuration | Wall time | Speedup vs per-context |
|---|---|---|
| Per-context (`FastPathSimulationExecutor`) | 179.3 ms (1.12 ms/ctx) | 1.00× |
| **Chained (F2 identity check active)** | **62.6 ms** (0.39 ms/ctx) | **2.87×** |
| Chained with prefix check bypassed | 60.8 ms | — |

**F2 validation overhead: 1.8 ms (2.9% of chained time)** — no meaningful regression. The original value-based series check measured 66.3 ms (52% overhead, cutting the benefit to ~1.44×), which is why the identity-based form was adopted. Note the committed benchmark suite (`test_chained_vs_non_chained`, 2 horizons) reports the more conservative 1.4× figure; the realistic 4-horizon grid above shows ~2.9×.

---

## 6. Diff Hygiene

`git status` shows only the intended files: the F1–F6 edits (`run_command.py`, `fast_path.py`), the prior P4.10 optimization work, new tests, and the two continuity docs. No debug artifacts, no stray files, no changes under `src/engine/**`. The reference Decimal engine is byte-for-byte untouched.

**Do not commit yet** — per instruction, the working tree is left uncommitted for architectural review.

---

## 7. Notes / Follow-ups

- **F7 deferred** (documented in the review). Recommended as the next P4.10 follow-up: an opt-in `--fast-path --validate` that evaluates a deterministic sample through both paths and asserts equivalence, keeping the reference-as-oracle property continuously enforced.
- **F4** (failure final_wealth: `0.00` vs a reference-side sub-1e-22 EUR rounding residual) was assessed as benign in the review and intentionally left as documented behavior; the equivalence tests assert final_wealth on success only.
