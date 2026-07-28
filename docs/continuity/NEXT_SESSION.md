# NEXT_SESSION.md - Session Initialization Guide

**Previous Session:** 2026-07-28 (P3.9 Compare Command Frozen — 8866ada)
**Current Status:** `v0.4` Phase 1 (Parallel Execution) and Phase 2 (SQLite Persistence) complete. Packages P3.1 through P3.9 all complete and frozen. Package P3.10 (Configuration, Documentation & Handoff) is next.
**Milestone Status:** Phase 1: dda449a. Phase 2: 128bb54. P3.1: efbeb61. P3.2: 39977c6. P3.3: 90eafbb. P3.4: eb0518f. P3.5: 6a7c5b6. P3.6: 492299f. P3.7: b9705d8. P3.8: 8bbd7f6. P3.9: 8866ada.

---

## Current Architecture Status

### Frozen (v0.1 Execution Engine permanently frozen)

- Domain model, services, policies for monthly execution flow.
- SimulationRunner, SimulationStatisticsBuilder, eight-step monthly pipeline.
- SimulationExecutor: multi-simulation experiment lifecycle management.
- Full test suite: 360+ tests across all three frozen layers.

### Complete (v0.2 Research Infrastructure Layer frozen)

**Sub-Milestone v0.2.1** (v0.2.1-cohort-schema):
- CohortSpecification, ExperimentDefinition, CohortGenerator.

**Sub-Milestone v0.2.2** (v0.2.2-parameter-sweep):
- ParameterConfiguration, ParameterAxis, ParameterSweepEngine.

**Sub-Milestone v0.2.3** (v0.2.3-research-executor):
- ResearchPlan, ResearchExecutor, ResultAggregator, ResearchReproducibilityManager.

### Complete (v0.3 Optimization & Analytics Layer frozen)

- SWROptimizer, StrategyComparator. All acceptance tests passing. All public APIs frozen.

### In Progress (v0.4 Infrastructure & Deployment Phase 3 — P3.9 Frozen, P3.10 Next)

**Architectural Specification (FROZEN):**
- INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md

**Phase 1 (COMPLETE) Parallel Execution:**
- Commit: dda449a. 8 tests passing. Determinism verified, error isolation working.

**Phase 2 (COMPLETE) SQLite Persistence:**
- Commit: 128bb54. 10 tables, lossless round-trip, reconstruction context. 39 tests.

**Phase 3 (ACTIVE) CLI Interface:**

| Package | Objective | Status |
|---------|-----------|--------|
| P3.1 | Concrete Persistence Codecs | ✅ Done (efbeb61) |
| P3.2 | Persistence Context Factory & Dataset Loading | ✅ Done (39977c6) |
| P3.3 | CLI Entry Point & Framework | ✅ Done (90eafbb) — FROZEN |
| P3.4 | `validate` command | ✅ Done (eb0518f) — FROZEN |
| P3.5 | `run` command | ✅ Done (6a7c5b6) — FROZEN |
| P3.6 | `list` command | ✅ Done (492299f) — FROZEN |
| P3.7 | `export` command | ✅ Done (b9705d8) — FROZEN |
| P3.8 | `optimize` command | ✅ Done (8bbd7f6) — FROZEN |
| P3.9 | `compare` command | ✅ Done (8866ada) — FROZEN |
| P3.10 | Configuration, Documentation & Handoff | ⬜ NEXT |

**Phase 4 (FUTURE) Integration & Acceptance:**
- End-to-end workflow tests, performance validation, documentation completion.

---

## Mandatory Architectural Invariants

1. v0.1 Engine Frozen: No modifications to execution engine code permitted.
2. v0.2 Research Frozen: No modifications to research infrastructure code permitted.
3. v0.3 Optimization Frozen: No modifications to optimization algorithms permitted.
4. Domain-Infrastructure Boundary: All external dependencies (SQLite, CLI, I/O) reside in v0.4 infrastructure layer. Domain depends on zero external libraries.
5. Clean Architecture: Dependencies flow unidirectionally: CLI → Research → Domain → Infrastructure (external). Never inward.
6. Determinism Preserved: Parallel execution must produce identical results to sequential.
7. Immutability Preserved: All domain objects remain frozen dataclasses; no mutable wrappers.
8. Atomic Commit Policy: Create atomic commits ONLY after all validation gates pass.
9. P3.4 Frozen: Do not modify `src/cli/commands/validate_command.py` or related test files without architect approval.
10. P3.5 Frozen: Do not modify `src/cli/commands/run_command.py` or related test files without architect approval.
11. P3.6 Frozen: Do not modify `src/cli/commands/list_command.py` or related test files without architect approval.
12. P3.7 Frozen (b9705d8): Do not modify `src/cli/commands/export_command.py` or related test files without architect approval.
13. P3.8 Frozen (8bbd7f6): Do not modify `src/cli/commands/optimize_command.py`, `src/cli/policies.py`, or related test files without architect approval.
14. P3.9 Frozen (8866ada): Do not modify `src/cli/commands/compare_command.py` or related test files without architect approval.
15. `src/cli/builders.py` is shared and evolvable: new commands add builder functions, but do not modify existing function signatures.
16. Handoff Consistency: Every implementation handoff must pass an internal consistency review before approval. Package scope, architectural constraints, acceptance criteria, quality gates, and stopping point must not contradict each other. (Added 2026-07-28 per P3.5 architectural review governance improvement.)

---

## Validation Status

Committed test suite: **605 / 605 tests passing** (360 domain/research/optimization + 96 infrastructure + 149 CLI).
Infrastructure mypy (src/infrastructure/persistence/ --strict): 0 errors (previous session)
CLI mypy (src/cli/ --strict): 0 errors
Full codebase mypy (src/ --strict): 21 pre-existing errors in engine/research domain (not v0.4).
P3.9 freeze commit: 8866ada.

---

## Exact Next Task

Implement **Package P3.10: Configuration, Documentation & Handoff**.

**Scope (informative — see handoff for canonical specification):**
1. Configuration file loading integration
2. `sim-retire config` command
3. Documentation completion
4. Final v0.4 Phase 3 integration testing
5. Phase 4 readiness review

**Dependencies:**
- `cli.commands.base.BaseCommand` — P3.3 framework
- `cli.error_handling.ExitCode` — P3.3 framework
- Complete Phase 3 CLI command set (P3.3–P3.9)

---

## Stopping Point

Package P3.9 is complete and frozen (8866ada).

Package P3.10 is the final Phase 3 package. It covers configuration, documentation, and the final handoff to Phase 4.

**Do not proceed beyond P3.10 without explicit architect approval.**
