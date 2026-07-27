# NEXT_SESSION.md - Session Initialization Guide

**Previous Session:** 2026-07-27 (v0.4 Phase 2 SQLite Persistence Complete)
**Current Status:** `v0.4` Infrastructure & Deployment — Phase 1 (Parallel Execution) and Phase 2 (SQLite Persistence) complete. Phase 3 (CLI Interface) is next.
**Milestone Status:** v0.4 Phase 1 committed as `dda449a`. Phase 2 committed as `128bb54`. Phase 2 architecturally accepted.
**Next Phase (authoritative):** Per `V0.4_IMPLEMENTATION_HANDOFF.md`, Phase 3 is the CLI Interface implementation.

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

### In Progress (v0.4 Infrastructure & Deployment — Phase 3 Next)

**Architectural Specification (FROZEN):**
- [INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md](./milestones/INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md)

**Phase 1 (COMPLETE) — Parallel Execution:**
- Specification: [PARALLEL_EXECUTION_SPECIFICATION.md](../specifications/infrastructure/PARALLEL_EXECUTION_SPECIFICATION.md)
- Commit: `dda449a`
- Status: ✅ Determinism verified, error isolation working, 8 tests passing

**Phase 2 (COMPLETE) — SQLite Persistence:**
- Specification: [INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md](../specifications/infrastructure/INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md)
- Commit: `128bb54`
- Status: ✅ 10 tables, lossless round-trip, reconstruction context pattern, 39 tests passing

**Phase 3 (NEXT) — CLI Interface:**

→ **Implement CLI Interface per `CLI_INTERFACE_SPECIFICATION.md`**

Specification: [CLI_INTERFACE_SPECIFICATION.md](../specifications/infrastructure/CLI_INTERFACE_SPECIFICATION.md)

**Scope:**
- `sim-retire` entry point with 6 subcommands (run, list, validate, export, optimize, compare)
- Argument parsing and validation
- Output formatters (CSV, JSON, table)
- Exit codes consistent
- Help text discoverable


**Phase 4 (FUTURE) — Integration & Acceptance:**
- End-to-end workflow tests
- Performance validation
- Documentation completion

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

Full test suite: **407 / 407 tests passing** (276 domain/research + 84 optimization + 47 infrastructure).
Infrastructure layer mypy (`src/infrastructure/persistence/ --strict`): **0 errors** ✅
Full codebase mypy (`src/ --strict`): 21 pre-existing errors in engine/research domain (not introduced by v0.4).

---

## Exact Next Task

Per `V0.4_IMPLEMENTATION_HANDOFF.md` (authoritative), begin **Phase 3: CLI Interface** of the v0.4 Infrastructure & Deployment milestone. Follow `CLI_INTERFACE_SPECIFICATION.md` to implement the `sim-retire` entry point, all 6 subcommands (run, list, validate, export, optimize, compare), argument parsing and validation, output formatters (CSV, JSON), exit codes, and help text. Adhere strictly to the atomic commit policy upon passing all Phase 3 exit gate validation criteria.

**Integration points to use:**
- `SQLiteRepository` (Phase 2) for persistence operations
- `ParallelExecutor` (Phase 1) for parallel study execution
- Frozen public APIs from v0.1, v0.2.3, v0.3 for domain operations

**Quality gates (Phase 3 exit):**
```bash
pytest tests/cli/ -v            # Expected: 100% passing
sim-retire --help               # Expected: Help text displayed
mypy src/cli/ --strict          # Expected: 0 errors
```

