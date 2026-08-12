# FIRE Backtesting Framework — P4.11: Fast-Path Hardening — Architectural Review

**Review scope:** P4.11 hardening — exact-equivalence invariants between the Reference Decimal engine and the Fast / Fast+Chaining closed-form paths, plus performance/memory improvements. No execution path removed; reference engine untouched.
**Date:** 2026-08-12
**Reviewer:** Chief Architect (AI), per architect stop-order (no commits until this review and its tests are complete)
**Verdict:** **APPROVED.** The decimal fast path is now **bit-exact** with the reference; the float path is exact on success/failure/failure-month/months-simulated with a bounded final-wealth deviation on real-data grids. The only remaining divergences are documented, pinned by tests, and measure-zero. Memory hardening delivered (−46% plan-build RSS). **No commits made; commit only after this review signs off.**

---

## 1. Review Criteria (architect's stated acceptance for P4.11 hardening)

1. **Exact equivalence, no tolerance** — Reference vs Fast vs Fast+Chaining must agree *exactly* on success, failure month, months simulated, final wealth and per-cell statistics. Any difference must be investigated and explained, not hidden behind a tolerance. (The ERN-oracle comparison independently keeps its unrounded ±1pp acceptance against the pinned oracle.)
2. **Reference stays canonical** — `src/engine/**` untouched; both execution paths retained; no path removed.
3. **Purpose of Fast-without-chaining** — determine whether it provides anything the chained path does not.
4. **`--fast-path` opt-in** — decide whether it should remain opt-in.
5. **Hardening content** — correctness/invariant tests first; performance/memory improvements second.

---

## 2. Findings

| # | Severity | Status | Finding |
|---|---|---|---|
| F1 | HIGH | **CLOSED** | The Decimal closed form was only "near-exact": the algebraic recurrence `V_{m+1} = (V_m − C)·g_m` diverged from the reference at exact-equality depletion boundaries (`V_m == C`), flipping outcome/failure month even in Decimal (its per-month unit-based rounding differs from the direct recurrence). Replaced with a **bit-exact replica** of the reference's per-month, per-asset `Decimal` arithmetic (withdrawal ratio `units_sold = (units·price·ratio)/price` with negative-unit clamp; rebalance in canonical `(id,name,description)` order with residual closure to the last asset). Verified 0 mismatches on random-walk and boundary grids. |
| F2 | MEDIUM | **CLOSED** | Fast-path final wealth was cent-quantized; the reference reports full-precision Decimal. Quantization removed. The decimal path now reproduces the reference's final wealth to the last digit; the float path reports its raw closed-form value (deviation ≤ ~9e-6 EUR on synthetic grids). |
| F3 | LOW | **CLOSED** | (P4.10 F4) On depletion the reference leaves a sub-1e-22 EUR rounding residual; the fast path reported exactly 0. The decimal path now reproduces the exact residual; the float path still reports 0 (now pinned by a `final_wealth == 0` assertion in the boundary-flip regression test). Both are "zero" to any monetary precision; the float behavior remains documented (F4) and is success-outcome-exact. |
| F4 | LOW | **DOCUMENTED + PINNED** | Float outcome flips at crafted exact-equality boundaries: with flat data and a rate/horizon integer coincidence (`V_m == C` at a simulated month), double-precision rounding moves the depletion check across the boundary and the outcome flips vs the reference. Measure-zero on real data; pinned as a regression test (`test_fast_path_exact_equivalence.py::TestFloatPath::test_exact_equality_boundary_flip_is_pinned`). The decimal path is exact there. |
| F5 | INFO | **NOTED** | Latent **reference-engine** edge discovered while probing: when a portfolio value reaches exactly zero during a non-depleted month (`V_m == C` mid-horizon), the market-evolution allocation raises `ValueError` (zero-value portfolio). E.g. flat data, H=24 months, rate 0.6 (V_19 == C). The fast path handles this input; the reference crashes. Crafted-input only; reference is frozen (out of scope to fix). |
| F6 | LOW | **CLOSED** | F7 validation compared outcome, failure month and (success) final wealth, but not `months_simulated`. Added an exact `months_simulated` comparison to `_compare_fast_path_result`. |
| F7 | MEDIUM | **CLOSED** | `build_grid_research_plan._resolve_policies` created two fresh policy objects per unit (~626k objects for the 313,020-unit grid). Now shares one instance per distinct parameter value. Plan-build peak RSS measured **271.9 → 147.3 MiB (−46%)** at unchanged build time (~1.9 s); re-verified this session at **147.4 MiB / 1.86 s** with exactly 5 allocation + 9 withdrawal policy objects. |
| F8 | LOW | **CLOSED** | Two pre-existing `mypy --strict` errors in the committed P4.11 code (`parallel_executor.py` reusing `result` for a `ResearchExecutionResult` then a `SimulationResult`). Renamed the per-unit variable; project-wide `mypy --strict` is clean again. |

---

## 3. Equivalence Evidence

Throwaway experiments (`/tmp/opencode`, not committed) plus the new committed invariant tests:

- **Scalar-replica experiment** — replicated the reference's per-month arithmetic standalone; bit-exact (success, failure month, final wealth to the last `Decimal` digit) across random-walk grids and flat exact-boundary grids, once the reference's depletion clamp (`remaining_units < 0 → 0`) was replicated.
- **Integration verification (production executors, in-tree):** `sequential_execute` over 3 random-walk grids (94 units: horizons 5–30 y, weights 0.0–1.0, rates 0.03–0.12) + 2 flat boundary grids (4 units, rates 0.5/H=24 and 0.4/H=60):
  - **Decimal: 0 mismatches** on success, failure month, months simulated, and final wealth — including failure residuals — on *all* grids, boundary grids included.
  - **Float: 0 outcome mismatches** on the random-walk grids; worst final-wealth deviation **8.9e-6 EUR** (H=360). On the two crafted boundary grids the float outcome flips (all units) — the pinned, documented divergence.
  - **Chained ≡ independent:** for both precisions, `ChainedFastPathSimulationExecutor` output is bit-identical to `FastPathSimulationExecutor` on success, failure month, months simulated and final wealth (the two remaining `SimulationStatistics` fields are constant on both paths) across multi-horizon grids.
- **Committed invariant tests** — `tests/cli/test_fast_path_exact_equivalence.py` (7 tests): decimal bit-exact on a realistic grid; decimal bit-exact at exact-equality boundaries (the case the old recurrence got wrong); float exact outcomes + bounded wealth; float non-boundary flat control matches; float boundary flip pinned; float zero failure-residual pinned in the same boundary-flip test (F3); chained ≡ independent for float and decimal.

**Performance/memory (host-dependent session measurements; only the month-work arithmetic is reproducible from committed artifacts):**
- **Month-work cut is exactly 3× by chaining** (169,030,800 → 56,343,600 months; verified arithmetically and asserted by `tests/benchmarks/test_fast_path_performance.py::test_grid_plan_chaining_report`).
- **Fresh full-grid run this session** (`RUN_ERN_E2E_FULL=1`, `--workers max`, 16 CPUs): reference Decimal engine **1,440 s** wall; fast+chaining (float) **34.7 s** → **≈41× end-to-end wall-clock**. Because both paths ran at the *same* worker count, parallelism cancels: ≈41× is an apples-to-apples (per-core-equivalent) speedup that decomposes into (a) the closed-form recurrence replacing the reference's 9-step per-month Decimal pipeline and (b) the 3× month-work cut from chaining. Chaining alone measured **≈1.8×** (fast without chaining 66.6 s vs chained 37.5 s at 8 workers).
- **Previous session (attested):** reference 1,496–1,551 s / 8.4 GiB aggregate; fast-without-chaining 79.1 s / 6.06 GiB; fast+chaining 47.3 s / 4.1 GiB.
- **Plan-build RSS:** 271.9 → 147.3 MiB (−46%), re-verified this session at **147.4 MiB / 1.86 s** (5 allocation + 9 withdrawal distinct policy objects for 313,020 units).

**Quality gates:** full non-E2E suite **914 passed** (was 907; +7 new invariant tests); `ruff check` clean; `mypy --strict` clean on all **195 source files** (src/ + tests/); ERN E2E smoke + fast-path acceptance **29 passed / 2 skipped** without `RUN_ERN_E2E_FULL`; with `RUN_ERN_E2E_FULL=1 ERN_E2E_FAST_PATH=1` the full gate is **31 passed / 0 skipped** — the full 180-cell oracle acceptance, the three hard anchors, and the new full-grid reference-vs-fast equivalence all pass (see §7).

---

## 4. Answers to the Architect's Questions

1. **Does Fast-without-chaining provide anything the chained path does not?**
   **No distinct production capability.** Chained is a strict functional superset: singleton groups and non-prefix datasets degenerate to independent per-context evaluation (identical arithmetic, identical results), and prefix groups derive shorter horizons from a single longest path. Fast-without-chaining remains valuable as (a) the base primitive `ChainedFastPathSimulationExecutor` subclasses, (b) the correct path when whole-definition processing is unavailable (progress wrappers / per-context flows), and (c) the reference target for validation. Recommendation: **keep `FastPathSimulationExecutor` as the primitive; `ChainedFastPathSimulationExecutor` is the production grid mode.** Removing Fast would be net-negative (it is the validation comparator and the base class); removing Chained would forfeit the 3× month-work reduction (169,030,800 → 56,343,600 months), which on the ERN grid shortens wall-clock from 79.1 s (fast, un-chained) to 47.3 s (chained), i.e. **~1.7×** (re-measured this session at 66.6 s → 37.5 s, ~1.8×, at 8 workers).

2. **Should `--fast-path` remain opt-in?** **Yes.** (a) The fast path is summary-grade — it returns empty per-month timelines, so it already rejects `--persist-study` (P4.10 F1 guard, `run_command.py:448`); (b) exactness to the last digit requires the decimal precision, which is opt-in; the default float precision carries the documented measure-zero boundary divergence; (c) the reference remains the canonical default. Opt-in keeps the reference as the default truth and the fast path as an explicitly selected optimization.

3. **Reference as oracle?** **Confirmed.** No file under `src/engine/**` was modified in this session. Both paths coexist; the fast path delegates every non-eligible context to the reference. The reference remains the canonical output and the internal numerical-regression oracle.

4. **Is the equivalence contract now exact?** **Established with a documented boundary.** Decimal: bit-exact everywhere (outcomes + final wealth + failure residual). Float: exact on success/failure/failure-month/months-simulated and within ~1e-5 EUR on final wealth for real-data grids; the only divergences are the measure-zero crafted-boundary flips (F4) and the zero-vs-1e-22 failure residual (F3), both documented and pinned by tests.

---

## 5. Confirmed Invariants

- **Reference Decimal engine untouched.** No `src/engine/**` changes; both paths retained.
- **No execution path removed.** Fast, Fast+Chaining, and the reference all remain selectable.
- **Exactness by design.** The decimal path is structurally the reference arithmetic (same op order, same Decimal context), so equivalence is not a tolerance but an identity, continuously checked by the invariant tests.
- **Chaining derivation exact.** Derived shorter horizons are bit-identical to independent evaluation for both precisions.
- **Determinism preserved.** F7 sample selection, chaining grouping, and policy sharing are deterministic; full suite (incl. determinism tests) green.

---

## 6. Decision

**APPROVED.** The P4.11 hardening is complete and meets every acceptance criterion:

1. Decimal fast path is bit-exact with the reference (outcomes, failure month, months simulated, final wealth, failure residual).
2. Float fast path is exact on outcomes with bounded wealth on real-data grids; the two residual divergences are documented, measure-zero, and pinned by tests (the boundary flip in `TestFloatPath::test_exact_equality_boundary_flip_is_pinned`, and the float zero failure-residual now asserted in that same test).
3. `src/engine/**` untouched; both paths retained; reference remains canonical/oracle.
4. Fast-without-chaining: no distinct production capability; retained as the primitive/validation target. Chained is the production grid mode.
5. `--fast-path` remains opt-in (summary-grade path; decimal exactness opt-in; reference default).
6. Memory hardened: plan-build RSS −46% via policy sharing; two pre-existing `mypy` errors fixed; `months_simulated` added to F7 validation.

No further optimization or path changes are proposed for this cycle.

---

## 7. Next Steps

- [ ] **Commit P4.11 hardening** after this review's sign-off: bit-exact decimal recurrence, quantization removal, `months_simulated` validation, policy memoization, invariant tests, `parallel_executor` type fix.
- [ ] Optional follow-up (separate workstream, reference frozen): fix the zero-portfolio allocation edge in the reference engine (F5).
- [ ] Optional follow-up: decide whether production `--fast-path` should default to the exact decimal precision (slower) vs float (fast, documented boundary divergence). Currently float.
- [x] **Full 180-cell ERN acceptance gate run this session** (`RUN_ERN_E2E_FULL=1 ERN_E2E_FAST_PATH=1`, 31 E2E tests passed): **180/180 cells executed, worst deviation 0.83 pp (≤ ±1 pp, unrounded), anchors 95/65/97 all PASS, full-grid reference-vs-fast equivalence PASS** (see §3). Re-run after commit as a release gate.
