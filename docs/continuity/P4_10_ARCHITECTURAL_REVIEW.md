# FIRE Backtesting Framework — P4.10: Performance Optimizations — Architectural Review

**Review scope:** P4.10 (IPC fix, float fast path, horizon chaining, `--fast-path` CLI wiring)
**Date:** 2026-08-10
**Reviewer:** Chief Architect (AI), per architect stop-order before further optimization work
**Verdict:** **CONDITIONAL APPROVAL** — retain all three optimizations; the reference Decimal engine stays untouched (both paths retained). **One high-severity guard required before `--fast-path` ships to general users** (Finding 1). Several lower-severity findings to address in the same review cycle.

---

## 1. Review Criteria

The architect's stated acceptance criteria for P4.10:

1. **IPC fix** — low risk, clear gain → retain. **Verified.**
2. **Float fast path** — a second execution path; must preserve equivalence with the reference Decimal engine; opt-in is correct. **Verified equivalent; opt-in confirmed.**
3. **Horizon chaining** — largest code/test surface; prefix-closed for ERN's 30/40/50/60y cohorts; most scrutiny. **Verified sound within plan-built definitions; one latent hazard found (F2).**
4. **`--fast-path`** — must be *completely clear* when it applies, when it falls back, and correctness must not be assumed merely because it matches current ERN test cases. **Partly addressed; gaps found (F1, F6, F7).**
5. **Do not replace or weaken the reference Decimal engine** — keep both paths as an internal numerical-regression reference. **Confirmed: reference untouched.**

---

## 2. Findings

| # | Severity | Area | Finding |
|---|---|---|---|
| F1 | **HIGH** | `--fast-path` + persistence | Fast path returns `SimulationTimeline(monthly_results=())` — empty timelines. Persistence is the CLI **default**. `fire run <study> --fast-path` therefore persists empty per-month timelines silently. The reference persists full timelines. Any timeline consumer (export, plot, reconstruction) gets empty data with no error. The ERN E2E masks this because it always runs `--summary-only --no-persist`. **Guard required** (see §3). |
| F2 | MEDIUM | Chained executor grouping | `ChainedFastPathSimulationExecutor` groups contexts by `(start_date, equity_allocation, withdrawal_rate)` **only** (fast_path.py:343-347). Dataset identity, `initial_wealth`, and `initial_portfolio` are not in the key. Two contexts with equal keys but different datasets/wealth would be merged and derived from the longest context's path — silently wrong results. Plan-built definitions are safe (cohort/wealth are constant within a cohort), but the executor's public contract accepts any `ExperimentDefinition`. **Guard required** (see §3). |
| F3 | LOW | Eligibility guard | `is_fast_path_eligible` checks `len(dataset.snapshots) >= 1` but the recurrence requires `len >= horizon_months` (accesses index `horizon-1`). A short dataset + long horizon → `IndexError` inside `evaluate_path`, surfacing as a failed run in the parallel path. Add the length check to eligibility. |
| F4 | LOW | Failure final_wealth | On depletion the fast path reports `final_wealth = 0.00`; the reference reports a sub-1e-22 EUR Decimal rounding residual (`(units·price)/price` at 28-digit context). Outcome and failure month match exactly; both values are "zero" to any monetary precision. Fast-path semantics are actually *cleaner*; the difference is benign. **Document it** and keep the success-only final-wealth assertion in the equivalence tests (it is currently already success-only). |
| F5 | LOW | Documentation | `fast_path.py` module docstring claims "~2-3 orders of magnitude speedup on the ERN grid". Measured end-to-end combined speedup is **~4.2×**. Correct the docstring to avoid misleading claims. |
| F6 | MEDIUM | `--fast-path` transparency | The CLI gives the user **no feedback** on how many units took the fast path vs fell back to the reference. Since eligibility is silent, a user running `--fast-path` on a plan whose policies are not `ConstantAllocationPolicy` + `FixedRealWithdrawalPolicy` (e.g. the common `ConstantWithdrawalPolicy`) gets **zero speedup with no warning**. Add a fallback-count line to the completion summary ("N units fast path, M units reference"). |
| F7 | RECOMMENDATION | Continuous validation | Float equivalence is currently proven only by the fixed test grids (synthetic + ERN smoke). To keep the "reference vs optimized" property alive, add an opt-in runtime cross-check (e.g. `--fast-path --validate`), which evaluates a small deterministic sample of contexts through **both** paths and asserts equivalence. This directly answers the architect's requirement that correctness not be assumed merely from the current ERN test cases. |
| F8 | INFO (verified) | max_drawdown / execution_time | Both the reference builder (`statistics_builder.py:64,68`) and the fast path report `0.0`. Not a discrepancy — but note `max_drawdown` is a placeholder in **both** paths; neither produces a real drawdown today. |
| F9 | INFO (verified) | Batch ordering / IPC | `create_work_batches` slices `plan.units[i:i+batch_size]` contiguously, so the index-based reconstruction in the IPC fix maps results correctly. Determinism tests green. |

---

## 3. Required Guard for F1 (before general release of `--fast-path`)

`--fast-path` must either:

- **(a)** reject the combination `--fast-path` + persisted timelines (mirror the existing `--summary-only` guard at `run_command.py:316`), **or**
- **(b)** generate real per-month timelines in the fast path (materialize each `monthly_values` entry into a `MonthlySimulationResult`).

Recommendation: **(a)** for P4.10 scope (2 lines, no new code); revisit (b) as a separate feature if fast-path timeline persistence becomes a requirement. This keeps the fast path honest: it is a summary-grade path by design until timelines are implemented.

For **F2**, the guard is: include dataset identity, `initial_wealth`, and `initial_portfolio` in the chaining group key (or verify equality across grouped contexts and refuse grouping otherwise). Both guards are small, contained changes to fast-path code only.

---

## 4. Equivalence Evidence (beyond the existing tests)

Because the architect explicitly disallows trusting the current ERN test cells alone, an independent stress run was executed (throwaway script, `/tmp`, not committed) comparing the float fast path against the reference Decimal executor over a random-walk grid not present in the test suite:

- **1,008 cases**: 6 datasets × {120,240,360,480} months × 6 weights × 7 withdrawal rates (0.02–0.12, including early-depletion regimes).
- **Outcome (success + failure_month): 0 mismatches** across all 1,008 cases, including 336 depletion cases.
- **Worst success final_wealth deviation: 0.005 EUR** over 480 simulated months (tolerance 0.05 EUR).
- Failure final_wealth: see F4 (reference reports a 1e-23 EUR rounding residual; fast path reports 0.00).

This independently confirms equivalence for the float path across a materially wider grid than the committed tests.

**Benchmarks (committed suite, `tests/benchmarks/test_fast_path_performance.py`):**

| Scenario | Speedup |
|---|---|
| ERN 180-cell grid, end-to-end (`--fast-path`) | ~4.2× |
| Single path, float closed form vs reference recursion | ~2.3× |
| 4 horizons × same cohort (chaining) | ~1.4× |
| Transfer-bound parallel sweep (IPC fix) | ~1.3× |

**Quality gates:** full suite 849 passed / 4 skipped; `ruff check` clean; `mypy --strict` 0 errors on `src/` (107 files) and `tests/` (80 files); ERN fast-path acceptance cells pass vs the reference under `RUN_ERN_E2E=1 ERN_E2E_FAST_PATH=1`.

---

## 5. Confirmed Invariants

- **Reference Decimal engine untouched.** No file under `src/engine/**` was modified. Both paths coexist; the fast path is a wrapper that delegates every non-eligible context to the reference.
- **Opt-in enforced.** `--fast-path` must be passed explicitly; the default execution path is byte-for-byte unchanged (verified by the 849-test suite).
- **Determinism preserved.** Parallel results identical to sequential (existing determinism tests green; IPC index mapping verified order-preserving, §F9).
- **Governance note.** `run_command.py` is frozen per invariant #10; the change there is additive and default-preserving (one `--fast-path` flag). The architect's stop-order for this review implicitly covers this file; approval of the finding guards (§3) should explicitly ratify it.

---

## 6. Decision

**CONDITIONAL APPROVAL.** All three optimizations are architecturally sound and their performance claims are verified. Before `--fast-path` is exposed to general users:

1. **Implement F1 guard** (required).
2. **Implement F2 guard** (required for the chained executor's public contract).
3. Apply the small F3/F5 fixes and F6 transparency line (recommended, same cycle).
4. Decide on F7 (continuous validation hook) as an explicit follow-up work item — recommended, not blocking.

No further optimization work is proposed. The reference Decimal engine remains the canonical output and the internal numerical-regression oracle.

---

## 7. Next Steps (proposed, not started)

- [ ] Implement F1 guard in `run_command.py` (+ test).
- [ ] Implement F2 group-key guard in `fast_path.py` (+ test with two contexts differing only in dataset/wealth).
- [ ] F3 eligibility length check, F5 docstring correction, F6 fallback-count summary (+ tests).
- [ ] F7: opt-in `--fast-path --validate` cross-check (separate work item).
- [ ] Re-run full gates and ERN acceptance after changes.
