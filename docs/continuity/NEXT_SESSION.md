# NEXT_SESSION.md - Session Initialization Guide

**Previous Session:** 2026-07-22 (ResearchExecutor Design Phase — Public API Review Approved)
**Current Status:** `RESEARCH_EXECUTOR_SPECIFICATION.md`, `RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md`, and `RESEARCH_EXECUTOR_PUBLIC_API.md` are all approved and frozen.
**Milestone Status:** Sub-Milestone `v0.2.3` is complete, committed and tagged (`v0.2.3`).
**Next Phase (authoritative):** Per `RESEARCH_LAYER_FINAL_ROADMAP.md`, the next workstream is the Optimization & Strategy Analysis milestone (`v0.3`), which contains consumer/optimization components such as `SWROptimizer` and `StrategyComparator`.

---

## Current Architecture Status

### Frozen (v0.1 Execution Engine — permanently frozen)

- Domain model, services, and policies required by the monthly execution flow.
- `SimulationRunner`, `SimulationStatisticsBuilder`, eight-step monthly pipeline.
- `SimulationExecutor`: multi-simulation experiment lifecycle management.
- Full test suite: 183 tests as of v0.1 baseline (now 276 with Research Layer tests).

### Complete (v0.2.1 — committed, tag: v0.2.1-cohort-schema)

- `CohortSpecification`: immutable frozen dataclass value object. Canonical identity is `start_date`. External `id` defaults to `start_date.isoformat()`.
- `ExperimentDefinition`: immutable declarative research study blueprint. Public Research Domain Contract. Validates only intrinsic local invariants.
- `CohortGenerator`: stateless temporal windowing utility.

### Complete (v0.2.2 — frozen, tag: `v0.2.2-parameter-sweep`)

- `ParameterConfiguration`: immutable, hashable, domain-agnostic named scalar assignment.
- `ParameterAxis`: immutable, validated construction-time parameter dimension.
- `ParameterSweepEngine`: stateless deterministic range/axis and Cartesian-product generator.

### Complete (v0.2.3 — committed and tagged)

- `RESEARCH_EXECUTOR_SPECIFICATION.md`: Behavioural contract **Approved and frozen**.
- `RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md`: Architectural review **Approved and frozen**.
- `RESEARCH_EXECUTOR_PUBLIC_API.md`: Public API contracts **Approved and frozen**.

The `v0.2` Research Infrastructure milestone is now considered frozen. Future consumer/optimization components are scheduled under `v0.3` per the authoritative final roadmap.

---

## Mandatory Architectural Invariants

1. The v0.1 Execution Engine is permanently frozen. No changes permitted.
2. `ResearchPlan` is an immutable domain value object representing a fully materialised study.
3. Construction of `ResearchPlan` belongs exclusively to a dedicated planning component introduced in a future specification. `ResearchExecutor` accepts only an already validated `ResearchPlan` and never constructs, builds, modifies, adds, removes, reorders, or materialises plan contents.
4. `ResearchExecutor` is a stateless execution orchestrator that delegates execution exactly once to `SimulationExecutor`.
5. All outputs preserve lossless 1-to-1 ordered association between `PlannedSimulationUnit` and engine `SimulationResult`.

---

## Validation Status

Full test suite: **276 / 276 tests passing**.
mypy: **0 errors**.

---

## Exact Next Task

Per `RESEARCH_LAYER_FINAL_ROADMAP.md` (authoritative), continue the mandatory workflow for Sub-Milestone `v0.3` (Optimization & Strategy Analysis). The next required activity is:

1. Produce the Behavioural Specification for `v0.3` covering `StrategyComparator`.
2. Begin implementation of `StrategyComparator`.

Do not begin architecture, API, or implementation work for `StrategyComparator` until the Behavioural Specification is reviewed and approved.

