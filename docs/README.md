# FIRE Backtesting Framework — Documentation Index

**Current Version:** v0.2.3 (Research Infrastructure Complete)  
**Status:** Active Development → v0.3 Ready to Start  
**Last Updated:** 2026-07-23

---

## Quick Start for New Contributors

### Start Here (in order):

1. **[continuity/AI_ONBOARDING.md](continuity/AI_ONBOARDING.md)** — Orientation & reading guide (5 min)
2. **[continuity/PROJECT_CONTEXT.md](continuity/PROJECT_CONTEXT.md)** — Mission, vision, philosophy (10 min)
3. **[continuity/CURRENT_STATE.md](continuity/CURRENT_STATE.md)** — Operational status & next task (10 min)
4. **[continuity/NEXT_SESSION.md](continuity/NEXT_SESSION.md)** — Session initialization (5 min)
5. **[development/ARCHITECTURE_OVERVIEW.md](development/ARCHITECTURE_OVERVIEW.md)** — System design walkthrough

Then pick a task from **[continuity/CURRENT_STATE.md](continuity/CURRENT_STATE.md)** and consult the relevant specification.

---

## Documentation Organization

### 📋 Continuity Documents (Start Here)

**For AI developers transitioning into this project:**

| Document | Purpose | Read When |
|----------|---------|-----------|
| [AI_ONBOARDING.md](continuity/AI_ONBOARDING.md) | Orientation guide for future AI | Entering project |
| [PROJECT_CONTEXT.md](continuity/PROJECT_CONTEXT.md) | Mission, vision, philosophy | Want to understand "why" |
| [CURRENT_STATE.md](continuity/CURRENT_STATE.md) | Operational status & next task | Ready to start work |
| [NEXT_SESSION.md](continuity/NEXT_SESSION.md) | Session initialization checklist | Every new session |

---

### 🏗️ Architecture Documentation

**Design decisions and API contracts (frozen):**

#### Reviews (Architectural Decisions)

- [SIMULATION_RUNNER_ARCHITECTURAL_REVIEW.md](architecture/reviews/SIMULATION_RUNNER_ARCHITECTURAL_REVIEW.md)
- [SIMULATION_EXECUTOR_ARCHITECTURAL_REVIEW.md](architecture/reviews/SIMULATION_EXECUTOR_ARCHITECTURAL_REVIEW.md)
- [COHORT_GENERATOR_ARCHITECTURE_REVIEW.md](architecture/reviews/COHORT_GENERATOR_ARCHITECTURE_REVIEW.md)
- [PARAMETER_SWEEP_ENGINE_ARCHITECTURE_REVIEW.md](architecture/reviews/PARAMETER_SWEEP_ENGINE_ARCHITECTURE_REVIEW.md)
- [EXPERIMENT_DEFINITION_ARCHITECTURE_REVIEW.md](architecture/reviews/EXPERIMENT_DEFINITION_ARCHITECTURE_REVIEW.md)
- [RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md](architecture/reviews/RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md)
- [RESEARCH_SWROPTIMIZER_ARCHITECTURE_REVIEW.md](architecture/reviews/RESEARCH_SWROPTIMIZER_ARCHITECTURE_REVIEW.md)
- [SIMULATION_EXECUTOR_CODE_REVIEW.md](architecture/reviews/SIMULATION_EXECUTOR_CODE_REVIEW.md)
- [SIMULATION_EXECUTOR_REVIEW.md](architecture/reviews/SIMULATION_EXECUTOR_REVIEW.md)
- [SIMULATION_RUNNER_REVIEW.md](architecture/reviews/SIMULATION_RUNNER_REVIEW.md)

#### Public API Contracts (Frozen Interfaces)

- [COHORT_GENERATOR_PUBLIC_API.md](architecture/api/COHORT_GENERATOR_PUBLIC_API.md)
- [EXPERIMENT_DEFINITION_PUBLIC_API.md](architecture/api/EXPERIMENT_DEFINITION_PUBLIC_API.md)
- [PARAMETER_SWEEP_ENGINE_PUBLIC_API.md](architecture/api/PARAMETER_SWEEP_ENGINE_PUBLIC_API.md)
- [RESEARCH_EXECUTOR_PUBLIC_API.md](architecture/api/RESEARCH_EXECUTOR_PUBLIC_API.md)
- [SIMULATION_EXECUTOR_PUBLIC_API.md](architecture/api/SIMULATION_EXECUTOR_PUBLIC_API.md)
- [SIMULATION_EXECUTOR_PUBLIC_API_REVIEW.md](architecture/api/SIMULATION_EXECUTOR_PUBLIC_API_REVIEW.md)
- [RESEARCH_SWROPTIMIZER_PUBLIC_API_REVIEW.md](architecture/api/RESEARCH_SWROPTIMIZER_PUBLIC_API_REVIEW.md)

---

### 📖 Specifications (Implementation Contracts)

**Frozen specifications that implementations must match exactly:**

#### Engine Specifications (v0.1 — Frozen)

- [SIMULATION_RUNNER_SPECIFICATION.md](specifications/engine/SIMULATION_RUNNER_SPECIFICATION.md)
- [SIMULATION_EXECUTOR_SPECIFICATION.md](specifications/engine/SIMULATION_EXECUTOR_SPECIFICATION.md)
- [MARKET_EVOLUTION_SPECIFICATION.md](specifications/engine/MARKET_EVOLUTION_STEP_SPECIFICATION.md)
- [MONTHLY_RESULT_BUILDER_STEP_SPECIFICATION.md](specifications/engine/MONTHLY_RESULT_BUILDER_STEP_SPECIFICATION.md)
- [PORTFOLIO_REBALANCE_STEP_SPECIFICATION.md](specifications/engine/PORTFOLIO_REBALANCE_STEP_SPECIFICATION.md)
- [SIMULATION_STATE_UPDATE_STEP_SPECIFICATION.md](specifications/engine/SIMULATION_STATE_UPDATE_STEP_SPECIFICATION.md)
- [SIMULATION_STATISTICS_BUILDER_SPECIFICATION.md](specifications/engine/SIMULATION_STATISTICS_BUILDER_SPECIFICATION.md)
- [MARKET_EVOLUTION_SPECIFICATION_FINAL_APPROVAL.md](specifications/engine/MARKET_EVOLUTION_SPECIFICATION_FINAL_APPROVAL.md)

#### Research Specifications (v0.2.3 — Frozen)

- [COHORT_GENERATOR_SPECIFICATION.md](specifications/research/COHORT_GENERATOR_SPECIFICATION.md)
- [EXPERIMENT_DEFINITION_SPECIFICATION.md](specifications/research/EXPERIMENT_DEFINITION_SPECIFICATION.md)
- [PARAMETER_SWEEP_ENGINE_SPECIFICATION.md](specifications/research/PARAMETER_SWEEP_ENGINE_SPECIFICATION.md)
- [RESEARCH_EXECUTOR_SPECIFICATION.md](specifications/research/RESEARCH_EXECUTOR_SPECIFICATION.md)

#### Optimization Specifications (v0.3 — Ready to Implement)

- [RESEARCH_SWROPTIMIZER_SPECIFICATION.md](specifications/optimization/RESEARCH_SWROPTIMIZER_SPECIFICATION.md)
- [RESEARCH_STRATEGYCOMPARATOR_SPECIFICATION.md](specifications/optimization/RESEARCH_STRATEGYCOMPARATOR_SPECIFICATION.md)
- [RESEARCH_V0.3_SPECIFICATION.md](specifications/optimization/RESEARCH_V0.3_SPECIFICATION.md)

---

### 🗺️ Roadmaps & Planning

**Milestones and long-term planning:**

- [RESEARCH_LAYER_FINAL_ROADMAP.md](roadmaps/milestones/RESEARCH_LAYER_FINAL_ROADMAP.md) — **AUTHORITATIVE** milestone blueprint
- [RESEARCH_LAYER_ROADMAP.md](roadmaps/milestones/RESEARCH_LAYER_ROADMAP.md) — Earlier roadmap version
- [EXECUTION_ENGINE_COMPLETION.md](roadmaps/milestones/EXECUTION_ENGINE_COMPLETION.md) — v0.1 completion summary

---

### 📊 Reports & Analysis

**Implementation summaries and technical analysis:**

- [CLEANUP_SUMMARY.md](reports/CLEANUP_SUMMARY.md)
- [SIMULATION_RUNNER_IMPLEMENTATION_REPORT.md](reports/SIMULATION_RUNNER_IMPLEMENTATION_REPORT.md)
- [COHORT_GENERATOR_IMPLEMENTATION_SUMMARY.md](reports/COHORT_GENERATOR_IMPLEMENTATION_SUMMARY.md)
- [PARAMETER_SWEEP_ENGINE_IMPLEMENTATION_SUMMARY.md](reports/PARAMETER_SWEEP_ENGINE_IMPLEMENTATION_SUMMARY.md)
- [SIMULATION_STATISTICS_BUILDER_IMPLEMENTATION.md](reports/SIMULATION_STATISTICS_BUILDER_IMPLEMENTATION.md)
- [STATISTICS_BUILDER_INPUT_ANALYSIS.md](reports/STATISTICS_BUILDER_INPUT_ANALYSIS.md)
- [MARKET_EVOLUTION_IMPLEMENTATION_GUIDANCE.md](reports/MARKET_EVOLUTION_IMPLEMENTATION_GUIDANCE.md)
- [IMPLEMENTATION_PHASE_GUIDANCE.md](reports/IMPLEMENTATION_PHASE_GUIDANCE.md)
- [RESEARCH_SWROPTIMIZER_IMPLEMENTATION_DESIGN_REVIEW.md](reports/RESEARCH_SWROPTIMIZER_IMPLEMENTATION_DESIGN_REVIEW.md)

---

### 👨‍💻 Development Guidance

**How to work on this project:**

- [CONTRIBUTION.md](development/CONTRIBUTION.md) — Contribution guidelines
- [IMPLEMENTATION_PROMPT.md](development/IMPLEMENTATION_PROMPT.md) — How implementations are guided
- [ARCHITECTURE_OVERVIEW.md](development/ARCHITECTURE_OVERVIEW.md) — System architecture walkthrough

---

## Key Concepts

### Clean Architecture

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

### Frozen vs. Active

- **Frozen** — Immutable contracts that cannot change without architect approval
  - All specifications (`docs/specifications/`)
  - All architecture reviews (`docs/architecture/reviews/`)
  - All public API contracts (`docs/architecture/api/`)
  
- **Active** — Updated as work progresses
  - [CURRENT_STATE.md](continuity/CURRENT_STATE.md)
  - [NEXT_SESSION.md](continuity/NEXT_SESSION.md)
  - Implementation reports

### Version Status

| Version | Status | Frozen? | When |
|---------|--------|---------|------|
| v0.1 Execution Engine | ✅ Complete | Yes | 2024-Q1 |
| v0.2.3 Research Infrastructure | ✅ Complete | Yes | 2024-Q2 |
| v0.3 Optimization & Analytics | 📋 Ready | No | Ready now |
| v0.4 Infrastructure & Deployment | 📅 Planned | No | Q3–Q4 2024 |
| v0.5+ Extensions | 🎯 Future | No | 2025+ |

---

## Finding What You Need

### "I want to implement a component"

1. Go to [CURRENT_STATE.md](continuity/CURRENT_STATE.md) → Section 2 (Current Implementation Task)
2. Find the specification in `docs/specifications/`
3. Read the architecture review in `docs/architecture/reviews/`
4. Review the public API in `docs/architecture/api/`
5. Start coding against the specification

### "I want to understand how X works"

1. Find the component in `docs/architecture/reviews/`
2. Read its specification in `docs/specifications/`
3. Check the public API contract in `docs/architecture/api/`
4. Review code in `src/`

### "I want to know if I'm done"

1. Check the specification's "Acceptance Criteria" section
2. Run the test suite: `pytest tests/ -v`
3. Check mypy: `mypy src/`
4. Verify 0 errors in both

### "I'm stuck on ambiguity"

1. Check the specification's "Design Rationale" section
2. Read the architecture review
3. Look at existing tests for examples
4. If still stuck: Document the ambiguity, don't guess

---

## Document Status Summary

```
✅ FROZEN (Immutable Records)
├─ All specifications (docs/specifications/)
├─ All architecture reviews (docs/architecture/reviews/)
├─ All public APIs (docs/architecture/api/)
└─ All roadmaps (docs/roadmaps/)

📝 ACTIVE (Updated as Work Progresses)
├─ CURRENT_STATE.md
├─ NEXT_SESSION.md
└─ Implementation reports (docs/reports/)

📚 REFERENCE (Static Information)
├─ CONTRIBUTION.md
├─ IMPLEMENTATION_PROMPT.md
└─ ARCHITECTURE_OVERVIEW.md
```

---

## Getting Started Checklist

- [ ] Read [continuity/AI_ONBOARDING.md](continuity/AI_ONBOARDING.md)
- [ ] Read [continuity/PROJECT_CONTEXT.md](continuity/PROJECT_CONTEXT.md)
- [ ] Read [continuity/CURRENT_STATE.md](continuity/CURRENT_STATE.md)
- [ ] Read [continuity/NEXT_SESSION.md](continuity/NEXT_SESSION.md)
- [ ] Run tests: `pytest tests/ -v`
- [ ] Find your task in [continuity/CURRENT_STATE.md](continuity/CURRENT_STATE.md)
- [ ] Read corresponding specification
- [ ] Start implementation

---

## Questions?

See [continuity/AI_HANDOVER.md#section-11-getting-unblocked](continuity/AI_HANDOVER.md#11-getting-unblocked) for troubleshooting.

---

**Version:** 1.0  
**Last Updated:** 2026-07-23  
**Maintainer:** Chief Architect
