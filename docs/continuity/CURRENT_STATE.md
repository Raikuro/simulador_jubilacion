# Current State & Next Tasks

**Document Type:** Operational Status  
**Status:** Active (Updated at milestone boundaries)  
**Last Updated:** 2026-07-28  
**Milestone:** v0.3 Complete | v0.4 Phase 3 P3.6 Complete → P3.7 Next

---

## Executive Summary

**FIRE Backtesting Framework** is at a milestone transition point:

- ✅ **v0.1 (Execution Engine)** — Complete, frozen, 200+ tests passing
- ✅ **v0.2.3 (Research Infrastructure)** — Complete, frozen, 76+ tests passing
- ✅ **v0.3 (Optimization Layer)** — Complete, frozen, all implementations delivered
- ✅ **v0.4 (Infrastructure & Deployment) — Phase 1 (Parallel Execution) Complete** — ProcessPoolExecutor, deterministic batching, error isolation
- ✅ **v0.4 (Infrastructure & Deployment) — Phase 2 (SQLite Persistence) Complete** — 10 tables, reconstruction context pattern, lossless round-trip, lock retry
- ✅ **v0.4 (Infrastructure & Deployment) — Phase 3 (CLI Interface) P3.3 (CLI Framework) Complete** — argparse entry point, BaseCommand framework, command registry, exit code conventions, 26 tests passing
- ✅ **v0.4 (Infrastructure & Deployment) — Phase 3 (CLI Interface) P3.4 (Validate Command) Complete** — YAML parsing, ExperimentDefinition construction, ResearchPlan validation, structured output, 16 new tests
- ✅ **v0.4 (Infrastructure & Deployment) — Phase 3 (CLI Interface) P3.5 (Run Command) Complete** — YAML experiment execution, dry-run orchestration, execution pipeline wired up, result persistence, 14 new tests, 56 total CLI tests
- ✅ **v0.4 (Infrastructure & Deployment) — Phase 3 (CLI Interface) P3.6 (List Command) Complete** — SQLite study listing, table/JSON/CSV output, status filtering, sort ordering, 15 new tests, 71 total CLI tests

**Immediate Next Task:** Package P3.7 — Export Command. Please refer to `NEXT_SESSION.md` for the current canonical task assignment.

---

## 1. Completed Milestones (Frozen)

### v0.1 Execution Engine ✅ FROZEN

**Status:** Complete, production-ready, no further development planned

**What it does:**
- Deterministic monthly simulation pipeline (8-step)
- Portfolio state management
- Market return application
- Rebalancing & withdrawal execution
- Monthly result aggregation

**Quality Metrics:**
- 200+ passing tests
- 0 mypy errors
- 100% specification compliance
- Deterministic (identical inputs → identical outputs)

**Key Components:**
- `SimulationRunner` — Orchestrates month-by-month execution
- `SimulationExecutor` — Executes individual simulation run
- 8 pipeline steps (evolution, allocation, rebalancing, withdrawal, metrics, capture)

**Architectural Decisions (Frozen):**
- Monthly deterministic pipeline
- Immutable monthly results (MonthlyResult snapshots)
- Policy-based decision abstraction
- Decimal money arithmetic

**Important:** DO NOT modify v0.1 without explicit architect approval.

---

### v0.2.3 Research Infrastructure ✅ FROZEN

**Status:** Complete, frozen APIs, no further development planned

**What it does:**
- Study composition (ExperimentDefinition)
- Cohort generation (temporal windows over market history)
- Parameter sweeping (grid-based parameter variation)
- Study orchestration (ResearchExecutor)
- Multi-simulation batch execution (SimulationExecutor)
- Result aggregation

**Quality Metrics:**
- 76+ passing tests
- Full research API documented
- All public interfaces published
- Deterministic execution

**Key Components:**
- `ExperimentDefinition` — Declarative study specification
- `CohortGenerator` — Time-window based cohort creation
- `ParameterSweepEngine` — Parameter grid materialization
- `ResearchPlan` — Fully materialized execution plan
- `ResearchExecutor` — Study orchestration
- `SimulationExecutor` — Batch simulation coordinator

**Frozen Public APIs:**
- `CohortGenerator` — [docs/architecture/api/COHORT_GENERATOR_PUBLIC_API.md](../architecture/api/COHORT_GENERATOR_PUBLIC_API.md)
- `ExperimentDefinition` — [docs/architecture/api/EXPERIMENT_DEFINITION_PUBLIC_API.md](../architecture/api/EXPERIMENT_DEFINITION_PUBLIC_API.md)
- `ParameterSweepEngine` — [docs/architecture/api/PARAMETER_SWEEP_ENGINE_PUBLIC_API.md](../architecture/api/PARAMETER_SWEEP_ENGINE_PUBLIC_API.md)
- `ResearchExecutor` — [docs/architecture/api/RESEARCH_EXECUTOR_PUBLIC_API.md](../architecture/api/RESEARCH_EXECUTOR_PUBLIC_API.md)
- `SimulationExecutor` — [docs/architecture/api/SIMULATION_EXECUTOR_PUBLIC_API.md](../architecture/api/SIMULATION_EXECUTOR_PUBLIC_API.md)

**Important:** DO NOT modify v0.2.3 without explicit architect approval.

---

## 2. Completed Milestone (v0.3 — Frozen)

### v0.3 Optimization & Analytics Layer ✅ FROZEN

**Status:** Complete, frozen APIs, production-ready

**What it does:**
- SWROptimizer — Binary search algorithm for safe withdrawal rates
- StrategyComparator — Comparative strategy analysis and metrics
- ResultAggregator — Statistical result synthesis (quantiles, success rates)
- ResearchReproducibilityManager — Audit trails & verification

**Quality Metrics:**
- 100% specification compliance
- All acceptance tests passing
- Implementation review approved
- All public APIs frozen
- 0 mypy errors

**Key Components:**
- `SWROptimizer` — Iterative numerical solver
- `StrategyComparator` — Multi-strategy comparative analysis
- `ResultAggregator` — Statistical aggregation
- `ResearchReproducibilityManager` — Provenance tracking

**Frozen Public APIs:**
- `SWROptimizer` — [docs/architecture/api/RESEARCH_SWROPTIMIZER_PUBLIC_API_REVIEW.md](../architecture/api/RESEARCH_SWROPTIMIZER_PUBLIC_API_REVIEW.md)
- `StrategyComparator` — [docs/specifications/optimization/RESEARCH_STRATEGYCOMPARATOR_API_CONTRACT.md](../specifications/optimization/RESEARCH_STRATEGYCOMPARATOR_API_CONTRACT.md)

**Architectural Reviews:**
- [RESEARCH_SWROPTIMIZER_ARCHITECTURE_REVIEW.md](../architecture/reviews/RESEARCH_SWROPTIMIZER_ARCHITECTURE_REVIEW.md)
- [RESEARCH_STRATEGYCOMPARATOR_ARCHITECTURE_REVIEW.md](../architecture/reviews/RESEARCH_STRATEGYCOMPARATOR_ARCHITECTURE_REVIEW.md)

**Important:** DO NOT modify v0.3 without explicit architect approval.

---

## 3. Active Milestone (Ready to Start)

### v0.4 Infrastructure & Deployment ✅ ACTIVE — Phase 3 P3.6 Complete

**Status:** Architecture approved and frozen. Phase 1 (Parallel Execution) and Phase 2 (SQLite Persistence) complete. Phase 3 (CLI Interface) active — P3.1 through P3.6 complete, P3.7 next.

**What it will do:**
- **SQLite Persistence** — Store experiment definitions, research plans, and results
- **CSV/JSON Export** — Export results for downstream analysis
- **CLI Interface** — Command-line tool for study execution
- **Parallel Execution** — Multi-core support via ProcessPoolExecutor

**Key Specifications (Approved & Frozen):**
- [INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md](../specifications/infrastructure/INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md)
- [CLI_INTERFACE_SPECIFICATION.md](../specifications/infrastructure/CLI_INTERFACE_SPECIFICATION.md)
- [PARALLEL_EXECUTION_SPECIFICATION.md](../specifications/infrastructure/PARALLEL_EXECUTION_SPECIFICATION.md)

**Architectural Document:**
- [INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md](./milestones/INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md)

**Current Status (Ready for Implementation):**

All architectural decisions frozen. Three behavioral specifications provide complete implementation contracts:

1. **Parallel Execution**: Work distribution, determinism guarantees, error handling
2. **Persistence**: SQLite schema, serialization contracts, transaction semantics
3. **CLI**: Command syntax, argument contracts, error codes, help text

**Implementation Phases (Completed → Next):**

✅ **Phase 1 (Parallel Execution)** — Complete (commit `dda449a`):
- ProcessPoolExecutor integration
- Determinism verification tests
- Error isolation and progress tracking implementation

✅ **Phase 2 (Persistence)** — Complete (commit `128bb54`):
- SQLite adapter with 10 tables
- Reconstruction context pattern (DatasetResolver, PolicyCodec, SimulationResultCodec)
- Lossless round-trip serialization for all domain objects
- Lock-contention retry and WAL journal mode

✅ **Phase 3 (CLI) — P3.1–P3.6 Complete, P3.7 Next**:

**P3.1 (Concrete Persistence Codecs)** — Complete (commit `efbeb61`):
- AllocationPolicyCodec, WithdrawalPolicyCodec, SimulationResultCodec
- DefaultDatasetResolver (in-memory registry)
- 30 tests

**P3.2 (Persistence Context Factory & Dataset Loading)** — Complete (commit `39977c6`):
- JSON dataset file format & loader
- `DefaultDatasetResolver.from_data_dir()` classmethod
- `create_persistence_context()` factory function
- 19 tests

**P3.3 (CLI Entry Point & Framework)** — Complete:
- `sim-retire` console script in pyproject.toml
- argparse root parser with global options
- BaseCommand abstract class, COMMANDS registry, ExecutionContext
- ExitCode enum (0, 1, 2, 130), format_error, handle_exception
- 26 tests, 0 mypy errors

**P3.4 (Validate Command)** — Complete (commit `eb0518f`):
- ValidateCommand class (BaseCommand subclass)
- YAML parsing with pyyaml, error handling with line numbers
- ExperimentDefinition construction and validation
- ResearchPlan creation with cohort/parameter/policy validation
- Structured validation output (sections, emoji indicators, verdict)
- Exit codes: 0 success, 2 validation failure
- `cli.builders` module extracted: `load_yaml`, `resolve_dataset`, `build_cohort_specs`, `build_parameter_configs`, `build_initial_portfolio`, `build_research_plan`
- 16 new tests, 0 mypy errors
- **FROZEN** — Architectural review approved

**P3.5 (Run Command)** — Complete:
- RunCommand class (BaseCommand subclass)
- YAML loading via `cli.builders` (shared module)
- ResearchPlan construction with command-specific policy subclasses
- Dry-run orchestration (prints plan summary, exits 0)
- Execution pipeline wired up (`sequential_execute`/`parallel_execute`, persistence context)
- Completion summary output (status, units, execution time)
- `--workers N` for parallel execution
- Error handling (file, YAML, definition, execution, interrupt)
- 14 new tests, 56 total CLI tests, 0 mypy errors
- **FROZEN** — Architectural review approved

**P3.6 (List Command)** — Complete (commit `492299f`):
- ListCommand class (BaseCommand subclass)
- SQLite database query for stored studies with LEFT JOIN on research_plans
- Output formats: table, JSON, CSV
- Status filtering: `--status all|completed|failed|pending`
- Sort ordering: `--sort date|name|status`
- Database error handling with exit code 1
- 15 new tests, 71 total CLI tests, 0 mypy errors
- **FROZEN** — Architectural review approved

📋 **Phase 4 (Integration)**:
- End-to-end workflow tests
- Performance validation
- Documentation completion

---

## 4. Planned Milestones (Future)
**Likely Timeline:** TBD

### v0.5+ Community & Extension

**Possible extensions** (pending stakeholder approval):
- Tax modeling
- Behavioral adaptation
- Multi-currency support
- Open-source release

---

## 5. Quality Checkpoints

### Before Starting v0.3 Implementation

✅ **Pre-implementation checklist:**

- [x] All v0.3 specifications approved & marked "Approved & Frozen"
- [x] Architecture review completed (see reviews section)
- [x] Public API contracts defined
- [x] Dependencies verified (all depend on frozen v0.1 & v0.2.3)
- [x] Test infrastructure ready
- [x] Integration points identified

### Code Quality Standards (No Exceptions)

Every implementation must:

- ✅ Pass 100% of tests
- ✅ Achieve 0 mypy errors
- ✅ Match specification exactly
- ✅ Use Decimal (never float) for financial values
- ✅ Maintain immutability for domain objects
- ✅ Have comprehensive docstrings
- ✅ Follow Clean Architecture layer boundaries
- ✅ Include architecture review comment linking to spec

### Handoff Consistency Standard (Added 2026-07-28)

Every implementation handoff must pass an **internal consistency review** before approval:

- ✅ Package scope and architectural constraints agree
- ✅ Acceptance criteria can be traced to requirements
- ✅ Quality gates are achievable given the scope
- ✅ Stopping point matches acceptance criteria
- ✅ No contradictory requirements exist between sections

This standard applies to all future package handoffs (P3.6–P3.10) and is enforced during the pre-implementation architectural review.

---

## 6. Test Suite Status

### Current Test Coverage

```
Total Passing Tests:  527
├─ Engine/Research/Optimization:  360
├─ CLI Tests:                     71
│  ├─ Framework (P3.3):           26
│  ├─ Validate Command (P3.4):    16
│  ├─ Run Command (P3.5):         14
│  └─ List Command (P3.6):        15
└─ Infrastructure Tests:          96
    ├─ Parallel Execution:          8
    ├─ SQLite Persistence:         39
    ├─ Concrete Codecs:            30
    └─ Context Factory:            19

Type Checking:
  src/cli/ --strict:                         0 errors ✅
  src/infrastructure/persistence/ --strict:  0 errors ✅
  src/ --strict:                             21 pre-existing errors in engine/research domain (not v0.4)

### Test Locations

- Engine/Research/Optimization tests: `tests/test_*.py` (core domain)
- Infrastructure tests: `tests/infrastructure/` (parallel execution: 8, persistence: 39, codecs: 30, context: 19)
- CLI tests: `tests/cli/` (framework: 26, validate: 16, run: 14)
- Integration tests: `tests/test_integration_*.py` (cross-layer)

### Adding New Tests (v0.4 Requirements)

Every new v0.4 component must have:
- Unit tests (algorithm correctness)
- Round-trip tests (serialization/deserialization)
- Error handling tests (edge cases, failure modes)
- Integration tests (with frozen layers)

---

## 7. Known Blockers

### Current Blockers

**NONE** — v0.4 Phase 3 P3.5 (CLI run command) implementation is ready to start.

All dependencies are in place:
- v0.1 Execution Engine ✅ Available
- v0.2.3 Research Infrastructure ✅ Available
- v0.3 Optimization Layer ✅ Available
- v0.4 Phase 1 (Parallel Execution) ✅ Complete
- v0.4 Phase 2 (SQLite Persistence) ✅ Complete
- v0.4 Phase 3 P3.1 (Persistence Codecs) ✅ Complete
- v0.4 Phase 3 P3.2 (Context Factory) ✅ Complete
- v0.4 Phase 3 P3.3 (CLI Framework) ✅ Complete
- v0.4 Phase 3 P3.4 (validate command) ✅ Complete
- CLI Interface Spec ✅ Approved & Frozen

### Potential Risks

| Risk | Mitigation |
|------|-----------|
| CLI-Application boundary coupling | Use clean separation: CLI only parses/renders; app layer orchestrates |
| Output format validation | Comprehensive CSV/JSON schema tests |
| Integration with phase 1 & 2 APIs | Use frozen public API contracts |
| Large result sets (memory) | Streaming output formatters |

---

## 8. Architecture at a Glance

### Clean Architecture Layers

```
┌─────────────────────────────────────┐
│ CLI / Presentation Layer (v0.4)     │
│ (input parsing, output formatting)  │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Application Layer (v0.2.3)          │
│ (ResearchExecutor, orchestration)   │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Domain Layer (v0.1 + v0.3 + ...)    │
│ ├─ Engine (v0.1)     ✅ Frozen      │
│ ├─ Research (v0.2.3) ✅ Frozen      │
│ └─ Optimization (v0.3) 📋 Ready     │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Infrastructure Layer (v0.4+)        │
│ (SQLite, CSV, I/O)                  │
└─────────────────────────────────────┘
```

**Dependency Flow:**
- CLI depends on Application
- Application depends on Domain
- Domain depends ONLY on Python stdlib
- Infrastructure isolated; not used by domain

---

## 9. Key Files & Locations

| Path | Purpose | Status |
|------|---------|--------|
| `src/engine/` | Execution engine | ✅ Frozen v0.1 |
| `src/research/` | Research layer | ✅ Frozen v0.2.3 |
| `src/research/optimization/` | Optimization (v0.3) | ✅ Frozen, implemented |
| `src/infrastructure/persistence/` | SQLite persistence (v0.4 Phase 2) | ✅ Complete |
| `src/infrastructure/execution/` | Parallel execution (v0.4 Phase 1) | ✅ Complete |
| `src/cli/` | CLI framework, builders, validate + run + list commands (v0.4 Phase 3 P3.3–P3.6) | ✅ Complete |
| `src/cli/builders.py` | Shared CLI builder functions (YAML→domain) | ✅ Complete |
| `tests/` | Test suite | ✅ 527 passing |
| `tests/infrastructure/` | Infrastructure tests | ✅ 96 passing |
| `tests/cli/` | CLI tests (framework: 26, validate: 16, run: 14, list: 15) | ✅ 71 passing |
| `docs/continuity/` | Handover documents | 📝 This folder |
| `docs/specifications/` | Implementation contracts | ✅ Frozen |
| `docs/specifications/infrastructure/` | v0.4 infrastructure specs | ✅ Frozen |
| `docs/architecture/reviews/` | Design decisions | ✅ Frozen |

---

## 10. Session Initialization

### Starting a New Session

1. ✅ Read [AI_ARCHITECT_GUIDE.md](AI_ARCHITECT_GUIDE.md) (5 min)
2. ✅ Read [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) (10 min)
3. ✅ Read this document (10 min)
4. ✅ Read [NEXT_SESSION.md](NEXT_SESSION.md) (5 min)
5. ⬜ Run tests to verify baseline: `pytest tests/ -v` (expect 512 passing)
6. ⬜ Review CLI specification: `docs/specifications/infrastructure/CLI_INTERFACE_SPECIFICATION.md`
7. ⬜ Read P3.7 handoff: `docs/roadmaps/milestones/V0.4_P3.7_EXPORT_HANDOFF.md`
8. ⬜ Begin P3.7: export command implementation

### Validation Checklist

Before starting work each session:

- [ ] All 527 tests still passing
- [ ] 0 mypy errors in all v0.4 modules (infrastructure + cli)
- [ ] I've read the relevant frozen specification
- [ ] I understand the exact scope from the spec
- [ ] I've identified the test file for my component

---

## 11. Quick Reference: What's Frozen vs. What's Active

### FROZEN (Do Not Change Without Approval)

✅ v0.1 Execution Engine
✅ v0.2.3 Research Infrastructure
✅ All specifications in `docs/specifications/`
✅ All architecture reviews in `docs/architecture/reviews/`
✅ All public API contracts in `docs/architecture/api/`
✅ P3.4 Validate Command (`src/cli/commands/validate_command.py`, `tests/cli/test_validate_command.py`)
✅ P3.5 Run Command (`src/cli/commands/run_command.py`, `tests/cli/test_run_command.py`)
✅ P3.6 List Command (`src/cli/commands/list_command.py`, `tests/cli/test_list_command.py`)
✅ `src/cli/commands/__init__.py` (command registry — extends only via registration)
✅ `src/cli/builders.py` (shared builder module — add only, do not modify existing signatures)

### EVOLVABLE (Shared, Not Frozen to Any Package)

📝 `src/cli/builders.py` — Shared CLI builder functions. New commands add, not modify.
📝 `src/cli/main.py` — Dispatch framework. Expands automatically via COMMANDS registry.

### ACTIVE (Update as Work Progresses)

📝 This document (CURRENT_STATE.md)
📝 [NEXT_SESSION.md](NEXT_SESSION.md)
📝 Implementation reports in `docs/reports/`
📝 P3.7 Export Command — Next implementation package

---

## 12. Communication Channels

### For Questions About:

| Question | Resource |
|----------|----------|
| "What should I implement?" | Read [NEXT_SESSION.md](NEXT_SESSION.md) |
| "How should it work?" | Read specification in `docs/specifications/` |
| "Why was it designed this way?" | Read architecture review in `docs/architecture/reviews/` |
| "What's the public API?" | Read `docs/architecture/api/` |
| "Is this in scope?" | Check specification scope section |
| "Am I done?" | Check specification acceptance criteria |

---

## 13. Updates to This Document

**When to update CURRENT_STATE.md:**

- After each milestone completion
- When blockers are identified/resolved
- When priorities shift
- At session boundaries (major state changes)

**What NOT to change:**
- Frozen milestone descriptions (v0.1, v0.2.3)
- Specification locations
- Architecture decisions

---

## Next Steps (In Order)

1. ✅ You've read this (CURRENT_STATE.md)
2. ✅ Read [NEXT_SESSION.md](NEXT_SESSION.md)
3. ⬜ Run full test suite: `pytest tests/ -v` (expect 527)
4. ⬜ Read P3.7 handoff: `docs/roadmaps/milestones/V0.4_P3.7_EXPORT_HANDOFF.md`
5. ⬜ Start P3.7: export command implementation

---

**Document Status:** Complete & Accurate  
**Test Status:** All 527 tests passing ✅  
**Blockers:** None  
**Next Action:** Read P3.7 handoff → Begin P3.7 export command implementation
