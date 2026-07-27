# NEXT_SESSION.md - Session Initialization Guide

**Previous Session:** 2026-07-27 (P3.2 Persistence Context Factory & Dataset Loading Complete)
**Current Status:** `v0.4` Phase 1 (Parallel Execution) and Phase 2 (SQLite Persistence) complete. Packages P3.1 (Concrete Persistence Codecs) and P3.2 (Persistence Context Factory & Dataset Loading) complete. Package P3.3 (CLI Entry Point & Framework) is next.
**Milestone Status:** v0.4 Phase 1 committed as `dda449a`. Phase 2 committed as `128bb54`. P3.1 committed as `efbeb61`. P3.2 committed as `39977c6`.
**Next Phase (authoritative):** Per `V0.4_IMPLEMENTATION_HANDOFF.md`, Phase 3 is the CLI Interface implementation. Phase 3 is subdivided into sequential packages. The next package is defined in a P3.3 handoff document (to be created).

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

**Phase 3 (ACTIVE) — CLI Interface (Package P3.3 next):**

Phase 3 is implemented as a sequence of small, independently reviewable packages. See individual package handoff documents for each step.

| Package | Objective | Status |
|---------|-----------|--------|
| **P3.1** | Concrete Persistence Codecs | ✅ Done |
| **P3.2** | Persistence Context Factory & Dataset Loading | ✅ Done |
| P3.3 | CLI Entry Point & Framework | ⬜ Next |
| P3.4 | `validate` command | ⬜ |
| P3.5 | `run` command | ⬜ |
| P3.6 | `list` command | ⬜ |
| P3.7 | `export` command | ⬜ |
| P3.8 | `optimize` command | ⬜ |
| P3.9 | `compare` command | ⬜ |
| P3.10 | Configuration, Documentation & Handoff | ⬜ |

**Current Package Handoff:** [V0.4_P3.2_CONTEXT_FACTORY_HANDOFF.md](./milestones/V0.4_P3.2_CONTEXT_FACTORY_HANDOFF.md) (completed, architectural review approved)

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

## P3.2 Technical Debt

The following items were identified during the P3.2 architectural review. They are documented here for scheduling in appropriate future packages.

| # | Item | Severity | Planned Package | Description |
|---|------|----------|----------------|-------------|
| TD-1 | Dummy-marker coupling | Low | P3.x cleanup | `SQLiteRepository._save_simulation_result` inserts `{"dummy": True}` markers for empty timelines. `SimulationResultCodec.load()` skips payloads lacking a `"date"` key, coupling the codec to this internal convention. A dedicated marker field (e.g., `"__marker__"`) would decouple them. |
| ~~TD-2~~ | ~~Registry-only dataset loading~~ | ~~Medium~~ | ~~P3.2~~ | ~~`DefaultDatasetResolver` currently only supports an in-memory registry. No file-based data loading exists. Must be addressed before production.~~ ✅ **Resolved in P3.2** |
| TD-3 | Privacy boundary: `from_data_dir` imports private `_load_datasets_from_dir` | Low | P3.x cleanup | `codecs.py` (`DefaultDatasetResolver.from_data_dir`) imports `_load_datasets_from_dir` (a `_`-prefixed function) from `context.py`. Either make it public or relocate the classmethod. |
| TD-4 | AssetClass round-trip metadata loss | Low | P3.x cleanup | `_snapshot_from_dict` creates `AssetClass(id=k, name="", description="")`; `name` and `description` are lost on round-trip. By design per handoff, but worth noting. |

---

## Validation Status

Full test suite: **436 / 436 tests passing** (276 domain/research + 84 optimization + 76 infrastructure).
Infrastructure layer mypy (`src/infrastructure/persistence/ --strict`): **0 errors** ✅
Full codebase mypy (`src/ --strict`): 21 pre-existing errors in engine/research domain (not introduced by v0.4).

---

## Exact Next Task

Plan **Package P3.3: CLI Entry Point & Framework**.

P3.3 begins the CLI layer by providing:
1. **CLI entry point** — `sim-retire` console script, argument parser, subcommand discovery.
2. **CLI framework** — base command class, shared options, exit code conventions, help formatting.

The persistence infrastructure is complete (`create_persistence_context()` available). P3.3 does not implement any specific CLI commands — those are P3.4 through P3.9. It provides the framework that those commands will use.

**Expected scope (to be confirmed during planning):**
1. `pyproject.toml` console script entry point
2. `src/cli/` package structure
3. Root CLI parser with `argparse`
4. Base command class or protocol
5. Subcommand registration mechanism (lazy-loaded)
6. Shared options (data directory, verbose mode)
7. `--help` output formatting
8. Error handling and exit codes
9. Tests for CLI framework behaviour

**P3.3 is an infrastructure layer package** — it provides the CLI framework, not application orchestration.

**Project-level quality gates (Phase 3 exit — not applicable until P3.10):**
```bash
pytest tests/cli/ -v            # Expected: 100% passing
sim-retire --help               # Expected: Help text displayed
mypy src/cli/ --strict          # Expected: 0 errors
```

