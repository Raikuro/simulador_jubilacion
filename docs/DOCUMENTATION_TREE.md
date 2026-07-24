# Documentation Tree

**Document Type:** Reference Guide  
**Status:** Active  
**Last Updated:** 2026-07-23

---

## 1. Continuity Documents (Entry Point)

### docs/continuity/

| Document | Purpose | Reading Order |
|----------|---------|---------------|
| **AI_ONBOARDING.md** | AI handover & continuity guide | 1 |
| **PROJECT_CONTEXT.md** | Project mission, vision, philosophy | 2 |
| **OPERATIONAL_DASHBOARD.md** | Current status & next tasks | 3 |
| **NEXT_SESSION.md** | Session initialization checklist | 4 |
| **SESSION_COMPLETION_REPORT.md** | Session completion reports | 5 |
| **GOVERNANCE.md** | Documentation governance rules | Reference |
| **SOURCE_OF_TRUTH.md** | Canonical source references | Reference |

---

## 2. Architecture Documentation

### docs/architecture/

#### Reviews (Design Decisions)

| Document | Purpose | Status |
|----------|---------|--------|
| **COHORT_GENERATOR_ARCHITECTURE_REVIEW.md** | Cohort generation design | Frozen |
| **EXPERIMENT_DEFINITION_ARCHITECTURE_REVIEW.md** | Experiment definition design | Frozen |
| **PARAMETER_SWEEP_ENGINE_ARCHITECTURE_REVIEW.md** | Parameter sweep design | Frozen |
| **RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md** | Research orchestration design | Frozen |
| **RESEARCH_SWROPTIMIZER_ARCHITECTURE_REVIEW.md** | Optimization design | Frozen |
| **SIMULATION_EXECUTOR_ARCHITECTURAL_REVIEW.md** | Simulation execution design | Frozen |
| **SIMULATION_EXECUTOR_CODE_REVIEW.md** | Code review documentation | Frozen |
| **SIMULATION_EXECUTOR_REVIEW.md** | Implementation review | Frozen |
| **SIMULATION_RUNNER_ARCHITECTURAL_REVIEW.md** | Runner design | Frozen |
| **SIMULATION_RUNNER_REVIEW.md** | Runner implementation review | Frozen |

#### Public APIs (Interface Contracts)

| Document | Purpose | Status |
|----------|---------|--------|
| **COHORT_GENERATOR_PUBLIC_API.md** | Cohort generator interface | Frozen |
| **EXPERIMENT_DEFINITION_PUBLIC_API.md** | Experiment definition interface | Frozen |
| **PARAMETER_SWEEP_ENGINE_PUBLIC_API.md** | Parameter sweep interface | Frozen |
| **RESEARCH_EXECUTOR_PUBLIC_API.md** | Research executor interface | Frozen |
| **SIMULATION_EXECUTOR_PUBLIC_API.md** | Simulation executor interface | Frozen |
| **SIMULATION_EXECUTOR_PUBLIC_API_REVIEW.md** | Simulation executor API review | Frozen |
| **RESEARCH_SWROPTIMIZER_PUBLIC_API_REVIEW.md** | Optimization API review | Frozen |

---

## 3. Specifications (Implementation Contracts)

### docs/specifications/

#### Engine Specifications (v0.1 — Frozen)

| Document | Purpose | Status |
|----------|---------|--------|
| **MARKET_EVOLUTION_STEP_SPECIFICATION.md** | Market evolution pipeline | Frozen |
| **MONTHLY_RESULT_BUILDER_STEP_SPECIFICATION.md** | Monthly result builder | Frozen |
| **PORTFOLIO_REBALANCE_STEP_SPECIFICATION.md** | Portfolio rebalancing | Frozen |
| **SIMULATION_EXECUTOR_SPECIFICATION.md** | Simulation executor | Frozen |
| **SIMULATION_RUNNER_SPECIFICATION.md** | Simulation runner | Frozen |
| **SIMULATION_STATE_UPDATE_STEP_SPECIFICATION.md** | State update pipeline | Frozen |
| **SIMULATION_STATISTICS_BUILDER_SPECIFICATION.md** | Statistics builder | Frozen |
| **MARKET_EVOLUTION_SPECIFICATION_FINAL_APPROVAL.md** | Final approval | Frozen |

#### Research Specifications (v0.2.3 — Frozen)

| Document | Purpose | Status |
|----------|---------|--------|
| **COHORT_GENERATOR_SPECIFICATION.md** | Cohort generator contract | Frozen |
| **EXPERIMENT_DEFINITION_SPECIFICATION.md** | Experiment definition contract | Frozen |
| **PARAMETER_SWEEP_ENGINE_SPECIFICATION.md** | Parameter sweep contract | Frozen |
| **RESEARCH_EXECUTOR_SPECIFICATION.md** | Research executor contract | Frozen |

#### Optimization Specifications (v0.3 — Ready)

| Document | Purpose | Status |
|----------|---------|--------|
| **RESEARCH_SWROPTIMIZER_SPECIFICATION.md** | SWROptimizer contract | Ready |
| **RESEARCH_STRATEGYCOMPARATOR_SPECIFICATION.md** | Strategy comparator contract | Ready |
| **RESEARCH_V0.3_SPECIFICATION.md** | v0.3 overview | Ready |

---

## 4. Roadmaps & Planning

### docs/roadmaps/milestones/

| Document | Purpose | Status |
|----------|---------|--------|
| **RESEARCH_LAYER_FINAL_ROADMAP.md** | Authoritative milestone blueprint | Frozen |
| **RESEARCH_LAYER_ROADMAP.md** | Earlier roadmap version | Frozen |
| **EXECUTION_ENGINE_COMPLETION.md** | v0.1 completion summary | Frozen |

---

## 5. Reports & Analysis

### docs/reports/

| Document | Purpose | Status |
|----------|---------|--------|
| **CLEANUP_SUMMARY.md** | Cleanup summary | Active |
| **SIMULATION_RUNNER_IMPLEMENTATION_REPORT.md** | Runner implementation | Active |
| **COHORT_GENERATOR_IMPLEMENTATION_SUMMARY.md** | Cohort generator summary | Active |
| **PARAMETER_SWEEP_ENGINE_IMPLEMENTATION_SUMMARY.md** | Parameter sweep summary | Active |
| **SIMULATION_STATISTICS_BUILDER_IMPLEMENTATION.md** | Statistics builder implementation | Active |
| **STATISTICS_BUILDER_INPUT_ANALYSIS.md** | Input analysis | Active |
| **MARKET_EVOLUTION_IMPLEMENTATION_GUIDANCE.md** | Implementation guidance | Active |
| **IMPLEMENTATION_PHASE_GUIDANCE.md** | Phase guidance | Active |
| **RESEARCH_SWROPTIMIZER_IMPLEMENTATION_DESIGN_REVIEW.md** | Optimization design review | Active |

---

## 6. Development Guidelines

### docs/development/

| Document | Purpose | Status |
|----------|---------|--------|
| **ARCHITECTURE_OVERVIEW.md** | High-level system overview | Active |
| **CONTRIBUTION.md** | Contribution guidelines | Active |
| **IMPLEMENTATION_PROMPT.md** | Implementation guidance | Active |

---

## 7. Main Index

### docs/README.md

**Purpose:** Main documentation index and navigation hub

**Content:**
- Quick start for new contributors
- Documentation organization with links
- Key concepts (Clean Architecture, frozen vs. active)
- Version status matrix
- How to find specific information
- Document status summary
- Getting started checklist

---

## 8. Historical Documents

### docs/history/

**Purpose:** Historical migration records and documentation evolution

**Note:** Currently empty - ready for future historical documents

---

## 9. Project Root

### MIGRATION_REPORT.md

**Purpose:** Documentation migration report

**Content:**
- List of all files moved
- Files renamed
- Broken links fixed
- Documents requiring stakeholder review
- Assumptions made during migration

---

## 10. Directory Structure Summary

```
docs/
├── README.md                          [NEW - Documentation index]
├── continuity/                        [6 files - AI handover & governance]
│   ├── AI_ONBOARDING.md                [Orientation guide]
│   ├── PROJECT_CONTEXT.md             [Mission, vision, philosophy]
│   ├── OPERATIONAL_DASHBOARD.md       [Current status & next tasks]
│   ├── NEXT_SESSION.md                [Session initialization]
│   ├── SESSION_COMPLETION_REPORT.md   [Session completion]
│   ├── GOVERNANCE.md                  [Documentation governance]
│   └── SOURCE_OF_TRUTH.md             [Canonical sources]
│
├── architecture/                      [17 files - Design decisions & APIs]
│   ├── reviews/                       [10 files - Design decisions]
│   │   ├── COHORT_GENERATOR_ARCHITECTURE_REVIEW.md
│   │   ├── EXPERIMENT_DEFINITION_ARCHITECTURE_REVIEW.md
│   │   ├── PARAMETER_SWEEP_ENGINE_ARCHITECTURE_REVIEW.md
│   │   ├── RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md
│   │   ├── RESEARCH_SWROPTIMIZER_ARCHITECTURE_REVIEW.md
│   │   ├── SIMULATION_EXECUTOR_ARCHITECTURAL_REVIEW.md
│   │   ├── SIMULATION_EXECUTOR_CODE_REVIEW.md
│   │   ├── SIMULATION_EXECUTOR_REVIEW.md
│   │   ├── SIMULATION_RUNNER_ARCHITECTURAL_REVIEW.md
│   │   └── SIMULATION_RUNNER_REVIEW.md
│   │
│   └── api/                           [7 files - Public APIs]
│       ├── COHORT_GENERATOR_PUBLIC_API.md
│       ├── EXPERIMENT_DEFINITION_PUBLIC_API.md
│       ├── PARAMETER_SWEEP_ENGINE_PUBLIC_API.md
│       ├── RESEARCH_EXECUTOR_PUBLIC_API.md
│       ├── SIMULATION_EXECUTOR_PUBLIC_API.md
│       ├── SIMULATION_EXECUTOR_PUBLIC_API_REVIEW.md
│       └── RESEARCH_SWROPTIMIZER_PUBLIC_API_REVIEW.md
│
├── specifications/                    [13 files - Implementation contracts]
│   ├── engine/                        [8 files - v0.1 specs]
│   │   ├── MARKET_EVOLUTION_STEP_SPECIFICATION.md
│   │   ├── MONTHLY_RESULT_BUILDER_STEP_SPECIFICATION.md
│   │   ├── PORTFOLIO_REBALANCE_STEP_SPECIFICATION.md
│   │   ├── SIMULATION_EXECUTOR_SPECIFICATION.md
│   │   ├── SIMULATION_RUNNER_SPECIFICATION.md
│   │   ├── SIMULATION_STATE_UPDATE_STEP_SPECIFICATION.md
│   │   ├── SIMULATION_STATISTICS_BUILDER_SPECIFICATION.md
│   │   └── MARKET_EVOLUTION_SPECIFICATION_FINAL_APPROVAL.md
│   │
│   ├── research/                      [4 files - v0.2.3 specs]
│   │   ├── COHORT_GENERATOR_SPECIFICATION.md
│   │   ├── EXPERIMENT_DEFINITION_SPECIFICATION.md
│   │   ├── PARAMETER_SWEEP_ENGINE_SPECIFICATION.md
│   │   └── RESEARCH_EXECUTOR_SPECIFICATION.md
│   │
│   └── optimization/                  [3 files - v0.3 specs]
│       ├── RESEARCH_SWROPTIMIZER_SPECIFICATION.md
│       ├── RESEARCH_STRATEGYCOMPARATOR_SPECIFICATION.md
│       └── RESEARCH_V0.3_SPECIFICATION.md
│
├── roadmaps/                           [1 file - Planning docs]
│   └── milestones/                    [3 files - Milestone planning]
│       ├── RESEARCH_LAYER_FINAL_ROADMAP.md
│       ├── RESEARCH_LAYER_ROADMAP.md
│       └── EXECUTION_ENGINE_COMPLETION.md
│
├── reports/                           [9 files - Implementation summaries]
│   ├── CLEANUP_SUMMARY.md
│   ├── SIMULATION_RUNNER_IMPLEMENTATION_REPORT.md
│   ├── COHORT_GENERATOR_IMPLEMENTATION_SUMMARY.md
│   ├── PARAMETER_SWEEP_ENGINE_IMPLEMENTATION_SUMMARY.md
│   ├── SIMULATION_STATISTICS_BUILDER_IMPLEMENTATION.md
│   ├── STATISTICS_BUILDER_INPUT_ANALYSIS.md
│   ├── MARKET_EVOLUTION_IMPLEMENTATION_GUIDANCE.md
│   ├── IMPLEMENTATION_PHASE_GUIDANCE.md
│   └── RESEARCH_SWROPTIMIZER_IMPLEMENTATION_DESIGN_REVIEW.md
│
├── development/                       [3 files - Dev guidelines]
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── CONTRIBUTION.md
│   └── IMPLEMENTATION_PROMPT.md
│
└── history/                           [empty - Ready for historical docs]
```

---

## 11. Key Principles

### Frozen vs. Active Documentation

**Frozen (Immutable Records):**
- All specifications (`docs/specifications/`)
- All architecture reviews (`docs/architecture/reviews/`)
- All public APIs (`docs/architecture/api/`)
- All roadmaps (`docs/roadmaps/milestones/`)

**Active (Updated as Work Progresses):**
- Continuity documents (`docs/continuity/`)
- Implementation reports (`docs/reports/`)
- Development guidelines (`docs/development/`)

### Reading Order for New Contributors

1. **docs/continuity/AI_ONBOARDING.md** — Orientation & reading guide (5 min)
2. **docs/continuity/PROJECT_CONTEXT.md** — Mission, vision, philosophy (10 min)
3. **docs/continuity/OPERATIONAL_DASHBOARD.md** — Operational status & next task (10 min)
4. **docs/continuity/NEXT_SESSION.md** — Session initialization (5 min)
5. **docs/README.md** — Development setup (10 min)
6. **docs/development/ARCHITECTURE_OVERVIEW.md** — System design walkthrough

### Quality Gates

**Before starting work:**

- [ ] Read `docs/continuity/AI_ONBOARDING.md`
- [ ] Read `docs/continuity/PROJECT_CONTEXT.md`
- [ ] Read `docs/continuity/OPERATIONAL_DASHBOARD.md`
- [ ] Read `docs/continuity/NEXT_SESSION.md`
- [ ] Run tests: `pytest tests/ -v`
- [ ] Find your task in `docs/continuity/OPERATIONAL_DASHBOARD.md`
- [ ] Read corresponding specification
- [ ] Start implementation

---

## 12. Success Metrics

**Documentation is successful when:**

- ✅ Every important project question has exactly one canonical source
- ✅ No document duplicates canonical content
- ✅ Each document has a single, clear responsibility
- ✅ The governance rule is understood and followed
- ✅ New documentation follows the established patterns
- ✅ All 276 tests still passing
- ✅ 0 mypy errors
- ✅ All specifications frozen and approved
- ✅ Clear separation of frozen vs. active documentation
- ✅ Excellent onboarding capability for new AI developers

---

## 13. Contact

For questions about documentation governance, consult the Chief Architect.

---

**Document Status:** Complete & Accurate  
**Last Updated:** 2026-07-23  
**Maintainer:** Chief Architect