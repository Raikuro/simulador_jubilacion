# NEXT_SESSION.md - Session Initialization Guide

**Previous Session:** 2026-07-22 (CohortGenerator Implementation — Sub-Milestone v0.2.1)
**Current Status:** Sub-milestone v0.2.1 complete and committed. Beginning v0.2.2.
**Next Phase:** ParameterSweepEngine — Sub-Milestone v0.2.2 (Behavioural Specification)

---

## Current Architecture Status

### Frozen (v0.1 Execution Engine — permanently frozen)

- Domain model, services, and policies required by the monthly execution flow.
- `SimulationRunner`, `SimulationStatisticsBuilder`, eight-step monthly pipeline.
- `SimulationExecutor`: multi-simulation experiment lifecycle management.
- Full test suite: 183 tests as of v0.1 baseline (now 231 with Research Layer tests).

### Complete (v0.2.1 — committed, tag: v0.2.1-cohort-schema)

- `CohortSpecification`: immutable frozen dataclass value object. Canonical identity is `start_date`. External `id` defaults to `start_date.isoformat()`.
- `ExperimentDefinition`: immutable declarative research study blueprint. Public Research Domain Contract. Validates only intrinsic local invariants.
- `CohortGenerator`: stateless temporal windowing utility.
  - `generate_rolling_monthly`: full dataset scan, silent tail exclusion.
  - `generate_range`: era-bounded scan, silent tail exclusion, ValueError on empty result.
  - `from_start_dates`: strict fail-fast validation per explicitly requested date.
- All three components exported from `research` top-level package.
- 231 / 231 tests passing. mypy: 0 errors.

---

## Mandatory Architectural Invariants

1. The v0.1 Execution Engine is permanently frozen. No changes permitted.
2. `CohortGenerator` is completely decoupled from `ExperimentDefinition` at the implementation level. `ResearchExecutor` extracts primitive arguments before calling `CohortGenerator`.
3. Canonical identity of `CohortSpecification` is strictly `start_date`. `id` is a reporting/serialization field only.
4. `ExperimentDefinition` validates only intrinsic local invariants. Dataset snapshot completeness is a `CohortGenerator` / execution planning concern.
5. All output tuples from `CohortGenerator` are ordered by `start_date` ascending, unconditionally.

---

## Key API Design Decisions (Frozen)

- `generate_range` raises `ValueError` on empty feasible cohort set (misconfigured study era, not a natural boundary).
- `from_start_dates` deduplicates via `dict.fromkeys`; insertion order is discarded; chronological sort always takes precedence.
- `ExperimentDefinition` duplicate cohort check uses canonical `start_date`, not external `id`.

---

## Validation Status

Full test suite: **231 / 231 tests passing**.
mypy: **0 errors (12 research source files)**.

---

## Exact Next Task

Begin Sub-Milestone v0.2.2: `ParameterSweepEngine`.

Mandatory workflow step 1: produce `PARAMETER_SWEEP_ENGINE_SPECIFICATION.md`.

Do not implement code until the specification is approved.

### ParameterSweepEngine Context (from roadmap)

- **Responsibility:** Generates multi-dimensional parameter grids and search spaces for research studies.
- **Scope:** Emits Cartesian products of policy settings (e.g., equity allocation steps, glidepath start/end ratios and duration, withdrawal rates).
- **Invariant:** Emits structured collections of parameterised policy configurations without executing them.
- **Consumer:** `ResearchExecutor` (v0.2.2) — not `CohortGenerator`.
- **Target ERN studies:** SWR Part 19 (Equity Glidepaths), SWR Part 20/25 (Dynamic Withdrawals), SWR Part 28 (CAPE-based Allocation).
