# FIRE Backtesting Framework — P4.11 Deferred: Reference Horizon Chaining — Architectural Recommendation

**Scope:** Phase A of the P4.11 deferred workstream — prove that a Reference-engine executor extended with **horizon chaining** reproduces the canonical Reference Decimal execution **bit-exactly**, and decide whether to integrate it as the default Reference execution path.
**Date:** 2026-08-12
**Reviewer:** Chief Architect (AI). No commits made; recommendation only.
**Verdict:** **CONDITIONAL — APPROVE as the production Reference-grid execution path, do NOT change the public default.** See §6.

---

## 1. Recommendation (TL;DR)

| Question | Answer |
|---|---|
| Is `ChainedReferenceSimulationExecutor` bit-exact with the canonical Reference? | **Yes — proven over the entire 313,020-unit ERN grid: 0 mismatches.** |
| Does it speed up Reference execution? | **Yes — 2.60× end-to-end wall-clock at equal worker count** (Reference 1,558.1 s → chained 600.2 s, 18-slice full grid, 8 workers). Month-work cut is exactly 3.0× (169,030,800 → 56,343,600). |
| Is memory safe? | **In parallel, yes** (~0.37 MiB per materialized unit → per-slice worker residency ≈ 830 MiB per worker at 8 workers, peak aggregate ≈ 6.7 GiB). Whole-plan sequential chaining is infeasible: extrapolates to ~110 GiB. Use slice-based dispatch. |
| Does `src/engine/**` stay untouched? | **Yes.** The chained executor delegates every independent evaluation to the canonical reference executor (`_evaluate_reference`); only `infrastructure/` + tests + tool scripts are new. |
| What should the CLI default be? | **Unchanged: Reference independent.** Chained Reference becomes the *production grid* executor used by tooling when a grid plan is detected; the independent executor remains the validation oracle. Do not flip `fire run` default semantics without a separate CLI decision. |

---

## 2. What was built

`src/infrastructure/execution/reference_chaining.py` — a `SimulationExecutor` with `processes_whole_definition = True` that:

1. Groups an engine definition's simulation contexts by `(start_date, equity_allocation, withdrawal_rate, initial_wealth, initial_portfolio)` into **horizon families** (`_reference_chaining_group_key` — scalar policy values via `ConstantAllocationPolicy`/`FixedRealWithdrawalPolicy` casts, mirroring the fast path's `_chaining_group_key`).
2. Executes only the **longest-horizon** context of each family through the canonical reference (exactly one 720-month Decimal run per family).
3. Derives every shorter-horizon context from that run when its dataset is an **identity prefix** of the longest (`_dataset_is_identity_prefix`, memoized) — i.e. all snapshots are the *same object* instances.
4. Otherwise falls back to an independent reference evaluation (same arithmetic, same engine — correctness is structural, not coincidental).

The executor reports a `ReferenceChainingReport` (logical units, chained groups, longest-path evaluations, derived vs independent counts, month-work).

**Verified decomposition of the full grid:** 313,020 logical units → 78,255 chaining groups → 234,765 derived + 0 independent evaluations; month-work 169,030,800 → 56,343,600 (exactly 3.0×).

---

## 3. Equivalence Evidence (full grid)

Run with `tools/ern/reference_chaining_fullgrid.py --workers 8 --slice-cohorts 100` (18 slices × 18,000 units): **313,020 units, 0 mismatches** on success, failure month, months simulated, final wealth, and max drawdown between Reference independent and Reference chained.

- All 18 slices `exact=True` (each slice ≈ 18,000 units except the last, 7,020).
- `compare_results` also asserts exact agreement on every statistic field; equality uses `Decimal` value equality (no tolerance).
- Earlier support probes (this session): full-object equality incl. per-month timelines, 0 mismatches over 1,800 units; subset 10-cohort run, exact match over 1,800 units.

### Failure-semantics handling (the subtle part)

Reference failure semantics (verified against `src/engine/application/runner.py` and the step pipeline) are:

- When a portfolio fails at period N, `simulation.statistics.failure_month == N` **and** `months_simulated == N`. The runner breaks out of the pipeline **before** `MonthlyResultBuilderStep` for the failing month, so the timeline contains months `0..N-1` (N entries) and the failing month is **not** recorded.
- `_build_derived_result` mirrors this exactly:
  - derived horizon `H <= failure_month` → reuse the first `H` monthly results, success, `months_simulated = H`;
  - derived horizon `H > failure_month` → truncate at `failure_month`, `success=False`, `months_simulated = failure_month`, `final_wealth` and `max_drawdown` copied from the longest run, `execution_time_seconds = 0.0`.
- A **prior bug** derived the failure branch with `failure_month + 1`; fixed to `failure_month` and locked by focused unit tests (`tests/infrastructure/test_reference_chaining.py`).

---

## 4. Performance & Memory

Measured this session (host: 16 cores, 15 GiB RAM); marked as host-dependent, non-reproducible without the same machine:

### Wall clock (apples-to-apples: same worker count per comparison)

| Strategy | Full grid (313,020 units, 8 workers, sliced) | 10-cohort subset (1,800 units, 8 workers) |
|---|---|---|
| Reference independent | 1,558.1 s | 9.6 s |
| Reference chained | 600.2 s | 3.7 s |
| **Speedup** | **2.60×** | **2.60×** |
| Fast path (float, unchained) | — | 0.6 s |
| Fast path chained | — | 0.3 s |

(The 3.0× month-work reduction yields 2.60× wall-clock because chaining still serializes the longest-horizon runs within each group and trades month-work for derivation + prefix validation.)

### Memory

- Each materialized completed result holds ≈ **0.37 MiB** of per-month payload (measured: full 313,020-unit plan build = 149.9 MiB; +540 in-process chained results = +200 MiB).
- **Whole-plan sequential chained execution is infeasible**: 36,000 units → 12,700 MiB peak RSS (~110 GiB extrapolated for the full grid).
- **Parallel is bounded**: `parallel_execute` distributes cohorts across workers; per-slice worker residency ≈ `slice_units/workers × 0.37 MiB`. With the full grid sliced at 100 cohorts × 8 workers ≈ **830 MiB/worker** (peak aggregate ≈ 6.7 GiB) — safely within this host's 15 GiB.
- Consequence for tooling: default to **slice-based dispatch** (the `reference_chaining_fullgrid.py` approach) rather than whole-plan `parallel_execute` (which would reflect ~7 GiB/worker and OOM at 16 workers).

---

## 5. Confirmed Invariants

- **Reference engine untouched.** No file under `src/engine/**` changed; the chained executor delegates to the canonical reference for every independent evaluation.
- **Bit-exact, not tolerance-based.** Derived results reuse the *identical* `MonthlySimulationResult` objects and `Decimal` statistics from the canonical run; equality is identity/a-equivalence, verified over the whole grid.
- **Failure semantics preserved** exactly (failure month, months simulated, truncated timeline).
- **Grouping is sound.** Group key covers start date, allocation, withdrawal rate, initial wealth, initial portfolio; dataset-prefix eligibility requires object identity of snapshots (`a is b`), eliminating the silent-merge hazard noted for the fast path (P4.10 F2). Non-prefix families degrade to independent evaluation.
- **Determinism preserved.** Grouping is deterministic; `parallel_execute` guarantees bit-for-bit equivalence to sequential (existing invariant); full infrastructure + CLI suites green (141 + 17 tests).

---

## 6. Decision

**APPROVE as the production *grid* Reference execution path** (for tooling and benchmarks), with conditions:

1. **Do not change the public `fire run` default.** Reference independent remains the CLI default and the validation oracle (consistent with the reference-is-canonical invariant). The chained executor is selected explicitly (new executor class / tool flag).
2. **Do not ship whole-plan sequential chaining** given the ~110 GiB extrapolation. Integrate through slice-based dispatch with per-worker residency bounded below the host memory.
3. Keep `ChainedReferenceSimulationExecutor` as the **only** chained Reference executor (drop the independent `ReferenceChainingReport` redundancy? No — keep the report; it is the month-work/intent auditing surface). No new paths.
4. The fast path (P4.11, float) remains the *fastest* grid option (≈41× vs Reference; ≈1.8–1.95× chained sub-gain), but carries its documented measure-zero float divergences and empty timelines. Reference chaining is the **exact** middle option: Reference-canonical values, full timelines, 2.60×. Both remain opt-in; neither replaces the independent Reference oracle.

**Net:** Reference chaining is bit-exact, architecturally clean (infrastructure-layer only, engine untouched), materially faster (2.60×), and memory-safe when sliced. It is worth integrating for exactness-sensitive grid workloads that need Reference fidelity with a 2.6× speed and full timelines — the exact case the float path cannot serve.

---

## 7. Next Steps

- [x] **Phase B (integration) — DONE.** `--reference-chained` CLI flag wired to `ChainedReferenceSimulationExecutor` (`sim-retire run --reference-chained`); the default stays the independent Reference; `--fast-path` remains a separate opt-in; incompatible combinations (`--reference-chained` + `--fast-path`) are rejected explicitly at pre-flight. Plan-level `expected_reference_chaining_report` drives the CLI summary (families, derived vs independent counts, month-work). Regression coverage: CLI executor selection + rejection, default-independent unchanged, bit-exact equivalence on representative multi-horizon grids (incl. a 3-horizon × 5-weight × 3-rate grid), non-prefix fallback to independent Reference, parallel/worker handling, plan-level oracle == live executor report, and opt-in ERN E2E cells (`ERN_E2E_REFERENCE_CHAINED=1`: smoke grid identical; full grid identical when `RUN_ERN_E2E_FULL=1`).
- [x] **Commit Phase A + Phase B** as a single "Reference Chaining" change (working tree: `reference_chaining.py`, `__init__.py` export, `test_reference_chaining.py`, `TestReferenceChainingBitExact` additions, CLI wiring + tests, `tools/ern/` scripts, this document).
- [x] Post-commit full-grid release gate re-run: 313,020-unit chained-vs-independent check (0 mismatches) re-executed after integration.
- [ ] Phase C deferred items remain: F5 reference zero-portfolio edge (`ValueError: Cannot derive allocation for zero-value portfolio`), Decimal-vs-float production precision decision, memory architecture for whole-grid in-memory runs, E2E gating policy, generic grid output.