# Documentation Tree

**Document Type:** Reference Guide  
**Status:** Active  
**Last Updated:** 2026-08-08

---

## 1. Continuity Documents (Entry Point)

### docs/continuity/

| Document | Purpose | Reading Order |
|----------|---------|---------------|
| **AI_ARCHITECT_GUIDE.md** | AI handover & continuity guide | 1 |
| **PROJECT_CONTEXT.md** | Project mission, vision, philosophy | 2 |
| **OPERATIONAL_DASHBOARD.md** | Operational health & metrics | 3 |
| **CURRENT_STATE.md** | Detailed technical state & next tasks | 4 |
| **NEXT_SESSION.md** | Session initialization checklist | 5 |
| **IMPLEMENTATION_PROGRESS.md** | Active phase completion tracking | 6 |
| **HUMAN_CONTRIBUTOR_GUIDE.md** | Human-AI collaboration workflow | Reference |
| **GOVERNANCE.md** | Documentation governance rules | Reference |
| **SOURCE_OF_TRUTH.md** | Canonical source references | Reference |
| **IMPLEMENTATION_PROGRESS_TEMPLATE.md** | Template for phase progress tracking | Reference |
| **P4_INTEGRATION_HANDOFF.md** | Final P4 integration handoff | 7 |
| **PHASE3_CLOSURE_REPORT.md** | Phase 3 closure report | Historical |
| **P4_11_REFERENCE_CHAINED_DEFAULT_DECISION.md** | Reference Chained promoted to default exact execution mode | Decision |
| **V0_5_STUDY_CONFIG_MODEL_DECISION.md** | v0.5 study-configuration model workstream (COMPLETE / CLOSED) | Decision |

---

## 2. Architecture Documentation

### docs/architecture/

#### Architecture Decision Records

| Document | Purpose | Status |
|----------|---------|--------|
| **ADR-001-cli-framework-selection.md** | CLI framework: argparse vs click | Accepted |
| **ADR-002-retroactive-real-engine-approval.md** | Retroactive approval of real-engine corrections | Approved |

#### Reviews (Design Decisions)

| Document | Purpose | Status |
|----------|---------|--------|
| **COHORT_GENERATOR_ARCHITECTURE_REVIEW.md** | Cohort generation design | Frozen |
| **EXPERIMENT_DEFINITION_ARCHITECTURE_REVIEW.md** | Experiment definition design | Frozen |
| **PARAMETER_SWEEP_ENGINE_ARCHITECTURE_REVIEW.md** | Parameter sweep design | Frozen |
| **RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md** | Research orchestration design | Frozen |
| **RESEARCH_STRATEGYCOMPARATOR_ARCHITECTURE_REVIEW.md** | Strategy comparator architecture | Frozen |
| **RESEARCH_SWROPTIMIZER_ARCHITECTURE_REVIEW.md** | Optimization design | Frozen |
| **SIMULATION_EXECUTOR_ARCHITECTURAL_REVIEW.md** | Simulation execution design | Frozen |
| **SIMULATION_EXECUTOR_CODE_REVIEW.md** | Code review documentation | Frozen |
| **SIMULATION_EXECUTOR_REVIEW.md** | Implementation review | Frozen |
| **SIMULATION_RUNNER_ARCHITECTURAL_REVIEW.md** | Runner design | Frozen |
| **SIMULATION_RUNNER_REVIEW.md** | Runner implementation review | Frozen |
| **LIST_COMMAND_ARCHITECTURE_REVIEW.md** | List command design review | Frozen |

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
| **DATASET_MODEL_SPECIFICATION.md** | Dataset domain model (identifier, slice) | Frozen |

#### Research Specifications (v0.2.3 — Frozen)

| Document | Purpose | Status |
|----------|---------|--------|
| **COHORT_GENERATOR_SPECIFICATION.md** | Cohort generator contract | Frozen |
| **EXPERIMENT_DEFINITION_SPECIFICATION.md** | Experiment definition contract | Frozen |
| **PARAMETER_SWEEP_ENGINE_SPECIFICATION.md** | Parameter sweep contract | Frozen |
| **RESEARCH_EXECUTOR_SPECIFICATION.md** | Research executor contract | Frozen |
| **RESEARCH_PLAN_MATERIALIZATION_SPECIFICATION.md** | Research plan materialization contract | Frozen |

#### Optimization Specifications (v0.3 — Frozen)

| Document | Purpose | Status |
|----------|---------|--------|
| **RESEARCH_SWROPTIMIZER_SPECIFICATION.md** | SWROptimizer contract | Frozen |
| **RESEARCH_STRATEGYCOMPARATOR_API_CONTRACT.md** | Strategy comparator API contract | Frozen |
| **RESEARCH_STRATEGYCOMPARATOR_SPECIFICATION.md** | Strategy comparator contract | Frozen |
| **RESEARCH_V0.3_SPECIFICATION.md** | v0.3 overview | Frozen |

#### Infrastructure Specifications (v0.4 — Frozen)

| Document | Purpose | Status |
|----------|---------|--------|
| **PARALLEL_EXECUTION_SPECIFICATION.md** | Parallel execution contract | Frozen ✅ Phase 1 done |
| **INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md** | SQLite persistence contract | Frozen ✅ Phase 2 done |
| **CLI_INTERFACE_SPECIFICATION.md** | CLI command specification | Frozen 📋 Phase 3 next |

---

## 4. Roadmaps & Planning

### docs/roadmaps/milestones/

| Document | Purpose | Status |
|----------|---------|--------|
| **EXECUTION_ENGINE_COMPLETION.md** | v0.1 completion summary | Frozen |
| **INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md** | v0.4 infrastructure milestone architecture | Frozen |
| **RESEARCH_LAYER_FINAL_ROADMAP.md** | Authoritative milestone blueprint | Frozen |
| **RESEARCH_LAYER_ROADMAP.md** | Earlier roadmap version (historical) | Frozen |
| **V0.4_IMPLEMENTATION_HANDOFF.md** | v0.4 implementation handoff package | Frozen |
| **V0.4_P3.1_CODECS_HANDOFF.md** | P3.1 concrete persistence codecs | Frozen |
| **V0.4_P3.2_CONTEXT_FACTORY_HANDOFF.md** | P3.2 context factory & dataset loading | Frozen |
| **V0.4_P3.3_CLI_FRAMEWORK_HANDOFF.md** | P3.3 CLI entry point & framework | Frozen |
| **V0.4_P3.4_VALIDATE_HANDOFF.md** | P3.4 validate command | Frozen |
| **V0.4_P3.5_RUN_HANDOFF.md** | P3.5 run command | Frozen |
| **V0.4_P3.6_LIST_HANDOFF.md** | P3.6 list command | Frozen |
| **V0.4_P3.7_EXPORT_HANDOFF.md** | P3.7 export command | Frozen |
| **V0.4_P3.8_OPTIMIZE_HANDOFF.md** | P3.8 optimize command | Frozen |
| **V0.4_P3.9_COMPARE_HANDOFF.md** | P3.9 compare command | Frozen |
| **V0.4_P3.10_CONFIG_HANDOFF.md** | P3.10 config command | Frozen |

---

## 5. Reports & Analysis

### docs/reports/

| Document | Purpose | Status |
|----------|---------|--------|
| **ARCHITECTURE_RESOLUTION_REPORT_V0.4.md** | v0.4 architecture resolution | Active |
| **RESEARCH_STRATEGYCOMPARATOR_IMPLEMENTATION_HANDOFF.md** | StrategyComparator implementation handoff | Active |
| **P4.5_DOCUMENTATION_SYNCHRONIZATION_AUDIT_REPORT.md** | P4.5 documentation sync audit | Historical |
| **P4.5_IMPLEMENTATION_REPORT.md** | P4.5 implementation report | Historical |
| **P4.8_CORRECTION_AND_RELEASE_READINESS_REPORT.md** | P4.8 final validation review | Active |

### docs/history/

*Historical implementation records migrated from root and reports directories during the 2026-07-24 documentation reorganization.*

| Document | Purpose | Status |
|----------|---------|--------|
| **CLEANUP_SUMMARY.md** | Cleanup summary | Historical |
| **SIMULATION_RUNNER_IMPLEMENTATION_REPORT.md** | Runner implementation | Historical |
| **COHORT_GENERATOR_IMPLEMENTATION_SUMMARY.md** | Cohort generator summary | Historical |
| **PARAMETER_SWEEP_ENGINE_IMPLEMENTATION_SUMMARY.md** | Parameter sweep summary | Historical |
| **SIMULATION_STATISTICS_BUILDER_IMPLEMENTATION.md** | Statistics builder implementation | Historical |
| **STATISTICS_BUILDER_INPUT_ANALYSIS.md** | Input analysis | Historical |
| **MARKET_EVOLUTION_IMPLEMENTATION_GUIDANCE.md** | Implementation guidance | Historical |
| **IMPLEMENTATION_PHASE_GUIDANCE.md** | Phase guidance | Historical |
| **RESEARCH_SWROPTIMIZER_IMPLEMENTATION_DESIGN_REVIEW.md** | Optimization design review | Historical |

---

## 6. Development Guidelines

### docs/development/

| Document | Purpose | Status |
|----------|---------|--------|
| **ARCHITECTURE_OVERVIEW.md** | High-level system overview | Active |
| **CONTRIBUTION.md** | Contribution guidelines | Active |
| **IMPLEMENTATION_PROMPT.md** | Implementation guidance | Active |
| **INSTALLATION_AND_QUICKSTART.md** | Installation and first steps | Active |
| **CLI_USAGE.md** | CLI command reference | Active |
| **CONFIG_REFERENCE.md** | Configuration file reference | Active |
| **CONFIG_PRECEDENCE.md** | CLI/config/default precedence | Active |
| **DEVELOPMENT_WORKFLOW.md** | Day-to-day development loop | Active |
| **EXTENSION_PATTERNS.md** | Supported extension points | Active |
| **PERFORMANCE_GUIDE.md** | Benchmark suite & performance rules | Active |
| **DEBUGGING_GUIDE.md** | SQLite & dataset troubleshooting | Active |
| **MIGRATION_GUIDE.md** | Migrating schema, datasets, config | Active |

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

**Note:** Historical implementation records from prior milestones are listed in **section 5** *(Reports & Analysis / docs/history/)*. This directory is reserved for new historical records created by future reorganizations.

---

## 9. Project Root

*No project-root documentation files exist outside `docs/`.*

| Document | Purpose | Status |
|----------|---------|--------|
| **RELEASE_CHECKLIST.md** | Release readiness checklist for v0.4 | Active |

*The previously referenced `MIGRATION_REPORT.md` was planned but never created in any commit; its scope is covered by this document and the git rename history.*

---

## 10. Directory Structure Summary

```
docs/
├── README.md                          [NEW - Documentation index]
├── RELEASE_CHECKLIST.md               [Release readiness checklist]
├── continuity/                        [22 files - AI handover & governance]
│   ├── AI_ARCHITECT_GUIDE.md          [Orientation guide]
│   ├── PROJECT_CONTEXT.md             [Mission, vision, philosophy]
│   ├── OPERATIONAL_DASHBOARD.md       [Operational health & metrics]
│   ├── CURRENT_STATE.md               [Detailed technical state]
│   ├── NEXT_SESSION.md                [Session initialization]
│   ├── IMPLEMENTATION_PROGRESS.md     [Phase completion tracking]
│   ├── IMPLEMENTATION_PROGRESS_TEMPLATE.md [Phase tracking template]
│   ├── HUMAN_CONTRIBUTOR_GUIDE.md     [Human-AI collaboration]
│   ├── GOVERNANCE.md                  [Documentation governance]
│   ├── SOURCE_OF_TRUTH.md             [Canonical sources]
│   ├── P4_INTEGRATION_HANDOFF.md      [Final P4 integration handoff]
│   ├── PHASE3_CLOSURE_REPORT.md       [Phase 3 closure report]
│   ├── P4_11_REFERENCE_CHAINED_DEFAULT_DECISION.md [P4.11 default-mode decision]
│   └── V0_5_STUDY_CONFIG_MODEL_DECISION.md [v0.5 study-config model — COMPLETE / CLOSED]
│
├── architecture/                      [21 files - Design decisions & APIs]
│   ├── decisions/                     [2 files - Architecture Decision Records]
│   │   ├── ADR-001-cli-framework-selection.md
│   │   └── ADR-002-retroactive-real-engine-approval.md
│   ├── reviews/                       [12 files - Design decisions]
│   │   ├── COHORT_GENERATOR_ARCHITECTURE_REVIEW.md
│   │   ├── EXPERIMENT_DEFINITION_ARCHITECTURE_REVIEW.md
│   │   ├── PARAMETER_SWEEP_ENGINE_ARCHITECTURE_REVIEW.md
│   │   ├── RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md
│   │   ├── RESEARCH_STRATEGYCOMPARATOR_ARCHITECTURE_REVIEW.md
│   │   ├── RESEARCH_SWROPTIMIZER_ARCHITECTURE_REVIEW.md
│   │   ├── SIMULATION_EXECUTOR_ARCHITECTURAL_REVIEW.md
│   │   ├── SIMULATION_EXECUTOR_CODE_REVIEW.md
│   │   ├── SIMULATION_EXECUTOR_REVIEW.md
│   │   ├── SIMULATION_RUNNER_ARCHITECTURAL_REVIEW.md
│   │   ├── SIMULATION_RUNNER_REVIEW.md
│   │   └── LIST_COMMAND_ARCHITECTURE_REVIEW.md
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
├── specifications/                    [21 files - Implementation contracts]
│   ├── engine/                        [9 files - v0.1 specs]
│   │   ├── MARKET_EVOLUTION_STEP_SPECIFICATION.md
│   │   ├── MONTHLY_RESULT_BUILDER_STEP_SPECIFICATION.md
│   │   ├── PORTFOLIO_REBALANCE_STEP_SPECIFICATION.md
│   │   ├── SIMULATION_EXECUTOR_SPECIFICATION.md
│   │   ├── SIMULATION_RUNNER_SPECIFICATION.md
│   │   ├── SIMULATION_STATE_UPDATE_STEP_SPECIFICATION.md
│   │   ├── SIMULATION_STATISTICS_BUILDER_SPECIFICATION.md
│   │   ├── MARKET_EVOLUTION_SPECIFICATION_FINAL_APPROVAL.md
│   │   └── DATASET_MODEL_SPECIFICATION.md
│   │
│   ├── research/                      [5 files - v0.2.3 specs]
│   │   ├── COHORT_GENERATOR_SPECIFICATION.md
│   │   ├── EXPERIMENT_DEFINITION_SPECIFICATION.md
│   │   ├── PARAMETER_SWEEP_ENGINE_SPECIFICATION.md
│   │   ├── RESEARCH_EXECUTOR_SPECIFICATION.md
│   │   └── RESEARCH_PLAN_MATERIALIZATION_SPECIFICATION.md
│   │
│   ├── optimization/                  [4 files - v0.3 specs]
│   │   ├── RESEARCH_SWROPTIMIZER_SPECIFICATION.md
│   │   ├── RESEARCH_STRATEGYCOMPARATOR_API_CONTRACT.md
│   │   ├── RESEARCH_STRATEGYCOMPARATOR_SPECIFICATION.md
│   │   └── RESEARCH_V0.3_SPECIFICATION.md
│   │
│   └── infrastructure/                [3 files - v0.4 specs]
│       ├── PARALLEL_EXECUTION_SPECIFICATION.md
│       ├── INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md
│       └── CLI_INTERFACE_SPECIFICATION.md
│
├── roadmaps/                           [1 file - Planning docs]
│   └── milestones/                    [15 files - Milestone planning + handoff]
│       ├── RESEARCH_LAYER_FINAL_ROADMAP.md
│       ├── RESEARCH_LAYER_ROADMAP.md
│       ├── EXECUTION_ENGINE_COMPLETION.md
│       ├── INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md
│       ├── V0.4_IMPLEMENTATION_HANDOFF.md
│       ├── V0.4_P3.1_CODECS_HANDOFF.md
│       ├── V0.4_P3.2_CONTEXT_FACTORY_HANDOFF.md
│       ├── V0.4_P3.3_CLI_FRAMEWORK_HANDOFF.md
│       ├── V0.4_P3.4_VALIDATE_HANDOFF.md
│       ├── V0.4_P3.5_RUN_HANDOFF.md
│       ├── V0.4_P3.6_LIST_HANDOFF.md
│       ├── V0.4_P3.7_EXPORT_HANDOFF.md
│       ├── V0.4_P3.8_OPTIMIZE_HANDOFF.md
│       ├── V0.4_P3.9_COMPARE_HANDOFF.md
│       └── V0.4_P3.10_CONFIG_HANDOFF.md
│
├── reports/                           [5 files - Implementation reports]
│   ├── ARCHITECTURE_RESOLUTION_REPORT_V0.4.md
│   ├── RESEARCH_STRATEGYCOMPARATOR_IMPLEMENTATION_HANDOFF.md
│   ├── P4.5_DOCUMENTATION_SYNCHRONIZATION_AUDIT_REPORT.md
│   ├── P4.5_IMPLEMENTATION_REPORT.md
│   └── P4.8_CORRECTION_AND_RELEASE_READINESS_REPORT.md
│
├── development/                       [12 files - Dev guidelines]
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── CONTRIBUTION.md
│   ├── IMPLEMENTATION_PROMPT.md
│   ├── INSTALLATION_AND_QUICKSTART.md
│   ├── CLI_USAGE.md
│   ├── CONFIG_REFERENCE.md
│   ├── CONFIG_PRECEDENCE.md
│   ├── DEVELOPMENT_WORKFLOW.md
│   ├── EXTENSION_PATTERNS.md
│   ├── PERFORMANCE_GUIDE.md
│   ├── DEBUGGING_GUIDE.md
│   └── MIGRATION_GUIDE.md
│
└── history/                           [9 files - Historical migration records]
    ├── CLEANUP_SUMMARY.md
    ├── COHORT_GENERATOR_IMPLEMENTATION_SUMMARY.md
    ├── IMPLEMENTATION_PHASE_GUIDANCE.md
    ├── MARKET_EVOLUTION_IMPLEMENTATION_GUIDANCE.md
    ├── PARAMETER_SWEEP_ENGINE_IMPLEMENTATION_SUMMARY.md
    ├── RESEARCH_SWROPTIMIZER_IMPLEMENTATION_DESIGN_REVIEW.md
    ├── SIMULATION_RUNNER_IMPLEMENTATION_REPORT.md
    ├── SIMULATION_STATISTICS_BUILDER_IMPLEMENTATION.md
    └── STATISTICS_BUILDER_INPUT_ANALYSIS.md
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

1. **docs/continuity/AI_ARCHITECT_GUIDE.md** — Orientation & reading guide (5 min)
2. **docs/continuity/PROJECT_CONTEXT.md** — Mission, vision, philosophy (10 min)
3. **docs/continuity/OPERATIONAL_DASHBOARD.md** — Operational health & metrics (10 min)
4. **docs/continuity/NEXT_SESSION.md** — Session initialization (5 min)
5. **docs/README.md** — Development setup (10 min)
6. **docs/development/INSTALLATION_AND_QUICKSTART.md** — Install `sim-retire` & run first study (10 min)
7. **docs/development/CLI_USAGE.md** — CLI command reference (10 min)
8. **docs/development/ARCHITECTURE_OVERVIEW.md** — System design walkthrough

### Quality Gates

**Before starting work:**

- [ ] Read `docs/continuity/AI_ARCHITECT_GUIDE.md`
- [ ] Read `docs/continuity/PROJECT_CONTEXT.md`
- [ ] Read `docs/continuity/OPERATIONAL_DASHBOARD.md`
- [ ] Read `docs/continuity/NEXT_SESSION.md`
- [ ] Run tests: `pytest tests/ -v`
- [ ] Find your task in `docs/continuity/NEXT_SESSION.md`
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
- ✅ All 808 tests still passing
- ✅ 0 mypy errors in v0.4 infrastructure modules
- ✅ All specifications frozen and approved
- ✅ Clear separation of frozen vs. active documentation
- ✅ Excellent onboarding capability for new AI developers

---

## 13. Contact

For questions about documentation governance, consult the Chief Architect.

---

**Document Status:** Complete & Accurate  
**Last Updated:** 2026-08-08
**Maintainer:** Chief Architect