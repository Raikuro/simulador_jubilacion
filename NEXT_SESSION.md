# NEXT_SESSION.md - Session Initialization Guide

**Previous Session:** 2026-07-22 (ParameterSweepEngine Implementation — Sub-Milestone v0.2.2)
**Current Status:** Sub-milestone v0.2.2 is complete and frozen (tag: `v0.2.2-parameter-sweep`).
**Next Phase:** ResearchExecutor (Behavioural Specification)

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

### Complete (v0.2.2 — frozen, tag: `v0.2.2-parameter-sweep`)

- `ParameterConfiguration`: immutable, hashable, domain-agnostic named scalar assignment.
- `ParameterAxis`: immutable, validated construction-time parameter dimension.
- `ParameterSweepEngine`: stateless deterministic range/axis and Cartesian-product generator.
- Public parameter types exported from `research`.
- 276 / 276 tests passing; 45 dedicated parameter-sweep tests passing.

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

Begin `ResearchExecutor` design work.

Mandatory workflow step 1: produce `RESEARCH_EXECUTOR_SPECIFICATION.md`.

Do not implement code until the specification is approved.

### ResearchExecutor Context (from roadmap)

- **Responsibility:** Coordinate cohort and parameter configurations into research simulation tasks.
- **Boundary:** Own policy materialisation and orchestration; do not alter the frozen v0.1 execution engine.
- **Inputs:** `ExperimentDefinition`, `CohortGenerator`, and `ParameterSweepEngine` outputs.
- **First action:** Define the frozen behavioural contract before architecture, API, or implementation work.
