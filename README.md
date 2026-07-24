# FIRE Backtesting Framework

**Version:** v0.2.3 (Research Infrastructure Complete)  
**Status:** Active Development → v0.3 Ready to Start  
**Last Updated:** 2026-07-23

---

## What is FIRE Backtesting Framework?

FIRE Backtesting Framework (FBF) is a deterministic financial simulation engine designed to reproduce and extend the Safe Withdrawal Rate (SWR) studies published by EarlyRetirementNow. The project is built on a rigorously defined Clean Architecture with a frozen v0.1 execution engine layer and an evolving research infrastructure layer (v0.2). The codebase prioritizes correctness, reproducibility, and maintainability in that order, never sacrificing accuracy for performance.

## Project Goals

The project aims to:

1. **Reproduce** the Safe Withdrawal Rate calculations published in the EarlyRetirementNow Part 19 study ("Equity Glidepaths") with exact numerical accuracy
2. **Extend** the simulation engine to support new research questions and strategies
3. **Automate** large-scale backtesting studies across thousands of historical cohorts
4. **Enable** parameter optimization and strategy comparison through systematic research execution
5. **Provide** a reusable, deterministic financial simulation platform for retirement studies

## Key Features

- ✅ **Deterministic execution engine** (v0.1) — 8-step monthly pipeline, fully tested, production-ready
- ✅ **Research infrastructure** (v0.2.3) — Experiment definitions, cohort generation, parameter sweeps, execution orchestration
- 📋 **Optimization layer** (v0.3) — SWROptimizer, StrategyComparator (specifications approved, implementation pending)
- ✅ **Clean Architecture** — Four distinct layers with unidirectional dependencies
- ✅ **Specification-driven development** — All architectural decisions documented in frozen design documents
- ✅ **Comprehensive testing** — 276+ passing tests, 0 mypy errors
- ✅ **Documentation system** — Scalable, well-organized documentation with clear governance

## Quick Start

### For New Contributors

1. **Read documentation:** Start with `docs/continuity/AI_ARCHITECT_GUIDE.md` for AI onboarding
2. **Run tests:** `pytest tests/ -v` to verify baseline
3. **Find your task:** Read `docs/continuity/OPERATIONAL_DASHBOARD.md` for current milestone and next task
4. **Implement:** Follow the specification in `docs/specifications/`
5. **Test:** Ensure all tests pass and mypy errors are zero

### For AI Developers

1. **Read AI_SESSION_BOOTSTRAP.md** — Understanding how to work in this project
2. **Read PROJECT_CONTEXT.md** — Project mission, vision, philosophy
3. **Read OPERATIONAL_DASHBOARD.md** — Current status and next task
4. **Read NEXT_SESSION.md** — Session initialization
5. **Read docs/README.md** — Documentation navigation

## Documentation

The project has a comprehensive documentation system organized into categories:

- **Continuity documents** (`docs/continuity/`) — AI handover, project context, operational status
- **Architecture documentation** (`docs/architecture/`) — Design decisions and API contracts
- **Specifications** (`docs/specifications/`) — Implementation contracts (frozen)
- **Roadmaps** (`docs/roadmaps/milestones/`) — Project planning
- **Reports** (`docs/reports/`) — Implementation summaries
- **Development guidelines** (`docs/development/`) — Contribution procedures

**Start here:** `docs/continuity/AI_SESSION_BOOTSTRAP.md`

## Technical Details

### Architecture

The project follows Clean Architecture principles with four distinct layers:

1. **Domain Layer** — Pure business logic (no external dependencies)
   - Engine (v0.1) ✅ Frozen
   - Research (v0.2.3) ✅ Frozen
   - Optimization (v0.3) 📋 Ready

2. **Application Layer** — Orchestration and coordination
   - ResearchExecutor, SimulationExecutor

3. **Infrastructure Layer** — External dependencies
   - SQLite (planned v0.4)
   - CSV I/O (planned v0.4)

4. **Presentation Layer** — CLI and user interfaces
   - CLI (planned v0.4)

### Dependencies

**Dependency Flow:**
```
CLI → Research → Engine → Infrastructure
```

**Technology Stack:**
- Python 3.13+
- Zero external dependencies (domain layer)
- Decimal arithmetic for financial values
- Type hints throughout
- Comprehensive test coverage

### Quality Standards

- **Correctness First** — Mathematical precision > convenience
- **Reproducibility** — Identical inputs → identical outputs (always)
- **Immutability** — Domain objects don't mutate; state transitions are explicit
- **Separation of Concerns** — Engine ≠ Research ≠ Infrastructure
- **Specification-Driven** — Code implements specs; specs don't describe code

## Quality Metrics

```
Total Passing Tests:  276
├─ Engine Tests:       200+
├─ Research Tests:      76+
└─ Infrastructure Tests: 0 (pending v0.4)

Type Checking:   0 mypy errors ✅
Specification Compliance: 100% ✅
Determinism: 100% ✅
```

## Current Status

**Milestone Transition Point:**

- ✅ **v0.1 (Execution Engine)** — Complete, frozen, 200+ tests passing
- ✅ **v0.2.3 (Research Infrastructure)** — Complete, frozen, 76+ tests passing
- 📋 **v0.3 (Optimization Layer)** — Specifications approved, ready for implementation
- 📅 **v0.4+ (Infrastructure & Deployment)** — Planned (SQLite, CLI, parallelization)

**Immediate Next Task:** Implement SWROptimizer component using binary search algorithm.

## Getting Help

### For Questions About:

| Question | Resource |
|----------|----------|
| "What should I implement?" | Read `docs/continuity/OPERATIONAL_DASHBOARD.md` |
| "How should it work?" | Read specification in `docs/specifications/` |
| "Why was it designed this way?" | Read architecture review in `docs/architecture/reviews/` |
| "What's the public API?" | Read `docs/architecture/api/` |
| "Is this in scope?" | Check specification scope section |
| "Am I done?" | Check specification's "Acceptance Criteria" section |

### Documentation Navigation

See `docs/README.md` for complete documentation navigation and category overview.

## License

This project is part of the FIRE Backtesting Framework initiative. See individual component licenses for specific terms.

---

**Version:** 1.0  
**Last Updated:** 2026-07-23  
**Maintainer:** Chief Architect