# NEXT_SESSION.md - Session Initialization Guide

**Previous Session:** 2026-07-27 (P3.1 Concrete Persistence Codecs Complete)
**Current Status:** `v0.4` Phase 1 (Parallel Execution) and Phase 2 (SQLite Persistence) complete. Package P3.1 (Concrete Persistence Codecs) complete. Package P3.2 (Minimal Application Layer) is next.
**Milestone Status:** v0.4 Phase 1 committed as `dda449a`. Phase 2 committed as `128bb54`. P3.1 committed as `<P3.1_COMMIT_HASH>`.
**Next Phase (authoritative):** Per `V0.4_IMPLEMENTATION_HANDOFF.md`, Phase 3 is the CLI Interface implementation. Phase 3 is subdivided into sequential packages; the next package is defined in `V0.4_P3.2_APPLICATION_HANDOFF.md` (to be created).

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

**Phase 3 (ACTIVE) — CLI Interface (Package P3.2 next):**

Phase 3 is implemented as a sequence of small, independently reviewable packages. See individual package handoff documents for each step.

| Package | Objective | Status |
|---------|-----------|--------|
| **P3.1** | Concrete Persistence Codecs | ✅ Done |
| P3.2 | Minimal Application Layer | ⬜ Next |
| P3.3 | CLI Entry Point & Framework | ⬜ |
| P3.4 | `validate` command | ⬜ |
| P3.5 | `run` command | ⬜ |
| P3.6 | `list` command | ⬜ |
| P3.7 | `export` command | ⬜ |
| P3.8 | `optimize` command | ⬜ |
| P3.9 | `compare` command | ⬜ |
| P3.10 | Configuration, Documentation & Handoff | ⬜ |

**Current Package Handoff:** [V0.4_P3.1_CODECS_HANDOFF.md](./milestones/V0.4_P3.1_CODECS_HANDOFF.md) (completed, see architectural review for P3.2 scope)

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

## P3.1 Technical Debt

The following items were identified during the P3.1 architectural review. They are documented here for scheduling in appropriate future packages.

| # | Item | Severity | Planned Package | Description |
|---|------|----------|----------------|-------------|
| TD-1 | Dummy-marker coupling | Low | P3.x cleanup | `SQLiteRepository._save_simulation_result` inserts `{"dummy": True}` markers for empty timelines. `SimulationResultCodec.load()` skips payloads lacking a `"date"` key, coupling the codec to this internal convention. A dedicated marker field (e.g., `"__marker__"`) would decouple them. |
| TD-2 | Registry-only dataset loading | Medium | P3.2 | `DefaultDatasetResolver` currently only supports an in-memory registry. No file-based data loading exists. Must be addressed before production. |

---

## Validation Status

Full test suite: **417 / 417 tests passing** (276 domain/research + 84 optimization + 57 infrastructure).
Infrastructure layer mypy (`src/infrastructure/persistence/ --strict`): **0 errors** ✅
Full codebase mypy (`src/ --strict`): 21 pre-existing errors in engine/research domain (not introduced by v0.4).

---

## Exact Next Task

Implement **Package P3.2: Minimal Application Layer**.

P3.2 provides a minimal application-layer factory that constructs a fully-wired `PersistenceReconstructionContext` with concrete codecs, including file-based dataset loading for `DefaultDatasetResolver`. It also addresses TD-2 from the P3.1 technical debt list.

**Scope (from P3.1 architectural review):**
1. Application-layer factory — function or class that creates a wired `PersistenceReconstructionContext`
2. Data-file loading for `DefaultDatasetResolver` (JSON-based dataset loader)
3. No CLI code, no configuration, no P3.1 codec changes
4. Keep the package small and independently reviewable; split into sub-packages if it grows beyond comfort

**P3.2 handoff document:** To be created as `docs/roadmaps/milestones/V0.4_P3.2_APPLICATION_HANDOFF.md`.

**Project-level quality gates (Phase 3 exit — not applicable until P3.10):**
```bash
pytest tests/cli/ -v            # Expected: 100% passing
sim-retire --help               # Expected: Help text displayed
mypy src/cli/ --strict          # Expected: 0 errors
```

