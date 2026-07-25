# NEXT_SESSION.md - Session Initialization Guide

**Previous Session:** 2026-07-23 (v0.3 StrategyComparator Implementation Complete)
**Current Status:** `v0.3` milestone complete, all specifications frozen, implementation accepted
**Milestone Status:** Milestone `v0.3` is complete, committed and tagged (`v0.3-optimization-analytics`).
**Next Phase (authoritative):** Per `INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md`, the next workstream is the Infrastructure & Deployment milestone (`v0.4`), which includes SQLite persistence, CLI interface, and parallel execution capabilities.

---

## Current Architecture Status

### Frozen (v0.1 Execution Engine — permanently frozen)

- Domain model, services, and policies required by the monthly execution flow.
- `SimulationRunner`, `SimulationStatisticsBuilder`, eight-step monthly pipeline.
- `SimulationExecutor`: multi-simulation experiment lifecycle management.
- Full test suite: 276+ tests across all three frozen layers.

### Complete (v0.2 Research Infrastructure Layer — frozen)

**Sub-Milestone v0.2.1** (committed, tag: `v0.2.1-cohort-schema`):
- `CohortSpecification`: immutable frozen dataclass value object.
- `ExperimentDefinition`: immutable declarative research study blueprint.
- `CohortGenerator`: stateless temporal windowing utility.

**Sub-Milestone v0.2.2** (frozen, tag: `v0.2.2-parameter-sweep`):
- `ParameterConfiguration`: immutable, hashable parameter assignments.
- `ParameterAxis`: immutable validated parameter dimensions.
- `ParameterSweepEngine`: stateless deterministic grid generation.

**Sub-Milestone v0.2.3** (frozen, tag: `v0.2.3-research-executor`):
- `ResearchPlan`: immutable materialized study plan.
- `ResearchExecutor`: stateless execution orchestrator.
- `ResultAggregator`: statistical result synthesis.
- `ResearchReproducibilityManager`: provenance tracking.

### Complete (v0.3 Optimization & Analytics Layer — frozen)

- `SWROptimizer`: Binary search for safe withdrawal rates (implementation complete)
- `StrategyComparator`: Comparative strategy analysis (implementation complete)
- All acceptance tests passing
- All public APIs frozen

### Ready for Implementation (v0.4 Infrastructure & Deployment)

**Architectural Specification (FROZEN):**
- [INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md](./milestones/INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md)

**Behavioral Specifications (FROZEN):**
- [INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md](../specifications/infrastructure/INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md)
- [CLI_INTERFACE_SPECIFICATION.md](../specifications/infrastructure/CLI_INTERFACE_SPECIFICATION.md)
- [PARALLEL_EXECUTION_SPECIFICATION.md](../specifications/infrastructure/PARALLEL_EXECUTION_SPECIFICATION.md)

**Next Implementation Task (IMMEDIATE):**

→ **Implement v0.4 Infrastructure & Deployment**

Three frozen specifications define complete implementation contracts. Follow architectural document for phase sequence:

1. **Phase 1:** Parallel execution engine (`PARALLEL_EXECUTION_SPECIFICATION.md`, `ProcessPoolExecutor`, determinism verification)
2. **Phase 2:** SQLite persistence layer (`INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md`, repository pattern, schema informed by Phase 1 output models)
3. **Phase 3:** CLI interface (`CLI_INTERFACE_SPECIFICATION.md`, commands, argument parsing, output formatting)
4. **Phase 4:** Integration and acceptance testing

**Why v0.4 Now?**
- All domain logic (v0.1, v0.2.3, v0.3) frozen and production-ready
- Research infrastructure proven with successful ERN study reproduction
- Next phase transforms library into production application
- Parallel execution necessary for large-scale sweeps (implemented first as pure algorithmic component)
- Persistence enables long-term study storage and reproducibility
- CLI enables non-programmer researchers to run studies

---

## Mandatory Architectural Invariants

1. **v0.1 Engine Frozen:** No modifications to execution engine code permitted.
2. **v0.2 Research Frozen:** No modifications to research infrastructure code permitted.
3. **v0.3 Optimization Frozen:** No modifications to optimization algorithms permitted.
4. **Domain-Infrastructure Boundary:** All external dependencies (SQLite, CLI, I/O) reside in v0.4 infrastructure layer. Domain layer depends on zero external libraries.
5. **Clean Architecture:** Dependencies flow unidirectionally: CLI → Research → Domain → Infrastructure (external). Never inward.
6. **Determinism Preserved:** Parallel execution must produce identical results to sequential (within numerical precision).
7. **Immutability Preserved:** All domain objects remain frozen dataclasses; no mutable wrappers.
8. **Atomic Commit Policy:** Create atomic commits ONLY after an implementation phase has successfully completed all validation gates (tests, type checks, traceability review, self-audit, and acceptance criteria).

---

## Validation Status

Full test suite: **276 / 276 tests passing**.
mypy: **0 errors**.

---

## Exact Next Task

Per `V0.4_IMPLEMENTATION_HANDOFF.md` (authoritative), begin **Phase 1: Parallel Execution Engine** of the v0.4 Infrastructure & Deployment milestone. Follow `PARALLEL_EXECUTION_SPECIFICATION.md` to implement `ParallelExecutor`, deterministic work batching, ordered result collection, and error isolation. Adhere strictly to the atomic commit policy upon passing all Phase 1 exit gate validation criteria.

