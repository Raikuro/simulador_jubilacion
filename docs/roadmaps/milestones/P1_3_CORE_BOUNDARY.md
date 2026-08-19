# P1.3 — Core Boundary Finalization

**Document Type:** Architectural Design & Implementation Specification  
**Status:** APPROVED (2026-08-19)  
**Date:** 2026-08-19  
**Workstream:** Repository Separation & Documentation Audit  
**Task:** Phase 1 / P1.3 (Core Boundary Finalization)  
**Prerequisites:** P1.1 (Repository Baseline) COMPLETE, P1.2 (Core Public API) APPROVED  
**Successor:** P1.4 (CLI Boundary Finalization)  

---

## 1. Executive Summary

This document establishes the physical package architecture, complete module ownership classification, and internal dependency boundaries for the standalone `fbf/core` repository.

### Core Architectural Principle: Freeze Responsibilities, Not Performance Mechanisms
P1.3 permanently establishes **architectural responsibilities, semantic boundaries, and dependency directions**, while explicitly leaving lower-level performance mechanisms (materialization point, IPC transfer, worker preloading, batch sizing, caching topologies, and shared memory representations) open for empirical validation under the upcoming P4.11 IO and batching benchmark investigation.

### Key Architectural Results
1. **Cohesive Five-Package Core Layout:**  
   `src/fbf/core/` is organized into five distinct packages:
   - `domain/`: Pure financial models, services, base policies, and concrete policy implementations (zero upward dependencies).
   - `study/`: Study planning models (`StudyConfiguration`, `ResearchPlan`, `StudyPlanResult`), application builder (`build_study_plan`), and sweep generation machinery.
   - `execution/`: Execution application service (`execute_study_plan`), execution orchestration result (`ResearchExecutionResult`), canonical monthly pipeline, execution strategies, and worker dispatchers.
   - `optimization/`: SWR optimization service (`optimize_study_swr`), binary-search solver (`SWROptimizer`), and strategy comparative analytics (`StrategyComparator`).
   - `persistence/`: Distinct packages for study experiment storage (`persistence/studies/`) and dataset acquisition/caching (`persistence/datasets/`).
2. **Strict Domain Purity:**  
   The domain layer contains pure financial mathematics and models with zero dependencies on persistence, execution engines, multiprocessing, optimization, study planning, or external interfaces.
3. **Decoupled Study Planning vs. Dataset Acquisition:**  
   `ResearchPlan` contains simulation parameters and dataset identities/references. Dataset acquisition belongs to `persistence.datasets`. `SimulationContext` and monthly pipeline steps **receive** data; they **never acquire** data or access repositories.
4. **Layered Optimization & Execution Boundary:**  
   `optimization` depends strictly on the high-level execution application contract (`execute_study_plan`), never directly importing specific execution strategies, worker pools, or Fast Path engines. The reverse dependency (`execution → optimization`) is strictly forbidden.
5. **Permanent Resolution of `reference_chaining.py → cli.policies` Leak:**  
   Concrete policies (`ConstantAllocationPolicy`, `ConstantWithdrawalPolicy`, `FixedRealWithdrawalPolicy`) move to `fbf.core.domain.policies.concrete`, establishing a clean downward dependency direction (`execution → domain.policies`).

---

## 2. Target Physical Core Structure (`fbf/core`)

```
fbf-core/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── src/
│   └── fbf/
│       └── core/
│           ├── __init__.py                # Minimal primary application API surface
│           ├── errors.py                  # Standard Core error hierarchy
│           │
│           ├── domain/                    # Pure Domain Layer (Zero upward dependencies)
│           │   ├── __init__.py
│           │   ├── money.py               # Money, Currency value objects (Decimal arithmetic)
│           │   ├── asset.py               # AssetClass entity and metadata
│           │   ├── portfolio.py           # Portfolio, AssetHolding entities
│           │   ├── market_snapshot.py     # MarketSnapshot entity (prices, inflation indices)
│           │   ├── dataset.py             # Dataset entity and immutable slicing logic
│           │   ├── simulation.py          # SimulationResult, SimulationStatistics, SimulationTimeline
│           │   ├── policies/              # Policy contracts and financial decision implementations
│           │   │   ├── __init__.py
│           │   │   ├── base.py            # AllocationPolicy, WithdrawalPolicy, Decision objects
│           │   │   └── concrete.py        # ConstantAllocationPolicy, FixedRealWithdrawalPolicy, ConstantWithdrawalPolicy
│           │   └── services/              # Pure domain financial mathematics
│           │       ├── __init__.py
│           │       ├── valuation.py       # Portfolio valuation service
│           │       ├── rebalancing.py     # Monthly asset rebalancing service
│           │       ├── evolution.py       # Market return evolution service
│           │       └── withdrawal.py      # Monthly cash withdrawal service
│           │
│           ├── study/                     # Study Planning & Sweep Orchestration (Application Layer)
│           │   ├── __init__.py
│           │   ├── configuration.py       # StudyConfiguration (v0.6 values-only data model & dict validator)
│           │   ├── plan.py                # ResearchPlan, PlannedSimulationUnit, StudyPlanResult
│           │   ├── builder.py             # build_study_plan() application service
│           │   └── internal/              # Internal sweep and cohort generation machinery
│           │       ├── cohorts.py         # CohortGenerator, CohortSpecification
│           │       ├── sweeps.py          # ParameterAxis, ParameterSweepEngine, ParameterConfiguration
│           │       └── experiment.py      # ExperimentDefinition
│           │
│           ├── execution/                 # Simulation Execution & Strategies (Application/Execution Layer)
│           │   ├── __init__.py
│           │   ├── service.py             # execute_study_plan(), ExecutionOptions, ExecutionMode
│           │   ├── result.py              # ResearchExecutionResult (Orchestration output model)
│           │   ├── events.py              # ProgressCallback, ProgressEvent
│           │   ├── context.py             # SimulationContext (Receives pre-resolved inputs)
│           │   ├── pipeline/              # Canonical monthly reference pipeline (INTERNAL)
│           │   │   ├── __init__.py
│           │   │   ├── runner.py          # SimulationRunner
│           │   │   ├── pipeline.py        # SimulationPipeline
│           │   │   ├── statistics.py      # SimulationStatisticsBuilder
│           │   │   └── steps/             # Preserved monthly pipeline steps
│           │   │       ├── initialize_allocation.py
│           │   │       ├── build_decision_context.py
│           │   │       ├── withdrawal_decision.py
│           │   │       ├── withdrawal_execution.py
│           │   │       ├── allocation_decision.py
│           │   │       ├── portfolio_rebalance.py
│           │   │       ├── market_evolution.py
│           │   │       ├── monthly_result_builder.py
│           │   │       └── simulation_state_update.py
│           │   └── strategies/            # Execution strategies & worker dispatchers (INTERNAL)
│           │       ├── __init__.py
│           │       ├── reference_chaining.py  # Horizon-chaining reference strategy
│           │       ├── fast_path.py           # Closed-form analytical recurrence solver
│           │       └── worker_pool.py         # Worker/process execution backend (open for tuning)
│           │
│           ├── optimization/              # SWR Optimization & Analytics (Application Layer)
│           │   ├── __init__.py
│           │   ├── swr_service.py         # optimize_study_swr() high-level application service
│           │   ├── swr_solver.py          # SWROptimizer (stateless binary-search solver)
│           │   └── comparator.py          # StrategyComparator, StrategyComparisonReport, RankingRule
│           │
│           └── persistence/               # Storage & Data-Access Infrastructure Layer
│               ├── __init__.py
│               ├── studies/               # Study experiment/plan persistence
│               │   ├── __init__.py
│               │   ├── repository.py      # StudyRepository (Protocol), PersistedStudySummary, Export models
│               │   └── sqlite/            # SQLite repository implementation (INTERNAL ADAPTER)
│               │       ├── __init__.py
│               │       ├── adapter.py     # SQLiteStudyRepository
│               │       ├── schema.py      # SQLite DDL & migration scripts
│               │       ├── codecs.py      # Lossless entity codecs
│               │       └── serializers.py # JSON/raw serializers
│               └── datasets/              # Dataset resolution and materialization
│                   ├── __init__.py
│                   ├── resolver.py        # DatasetResolver (Protocol), DefaultDatasetResolver
│                   └── cache.py           # Dataset cache implementation (to be benchmarked)
│
└── tests/                                 # Core test suite
```

---

## 3. Production Module Ownership & Migration Classification

| Current Module Path | Proposed Core / CLI Path | Classification | Responsibility & Migration Action |
| :--- | :--- | :---: | :--- |
| `src/engine/domain/model/money.py` | `fbf/core/domain/money.py` | **MOVE TO CORE** | Move exact Decimal Money/Currency value objects. |
| `src/engine/domain/model/asset.py` | `fbf/core/domain/asset.py` | **MOVE TO CORE** | Move AssetClass entity. |
| `src/engine/domain/model/portfolio.py`| `fbf/core/domain/portfolio.py` | **MOVE TO CORE** | Move Portfolio, AssetHolding entities. |
| `src/engine/domain/model/market_snapshot.py`| `fbf/core/domain/market_snapshot.py`| **MOVE TO CORE**| Move MarketSnapshot entity. |
| `src/engine/domain/model/dataset.py`| `fbf/core/domain/dataset.py`| **MOVE TO CORE** | Move Dataset entity and immutable `Dataset.slice()`. |
| `src/engine/domain/model/simulation.py`| `fbf/core/domain/simulation.py`| **MOVE TO CORE**| Move SimulationResult, SimulationTimeline, SimulationStatistics. |
| `src/engine/domain/policies/allocation_policy.py`| `fbf/core/domain/policies/base.py`| **MOVE TO CORE**| Move AllocationPolicy base class. |
| `src/engine/domain/policies/withdrawal_policy.py`| `fbf/core/domain/policies/base.py`| **MOVE TO CORE**| Move WithdrawalPolicy base class. |
| `src/engine/domain/policies/decisions.py`| `fbf/core/domain/policies/base.py`| **MOVE TO CORE**| Move AllocationDecision, WithdrawalDecision dataclasses. |
| `src/cli/policies.py` | `fbf/core/domain/policies/concrete.py`| **MOVE TO CORE**| Move ConstantAllocationPolicy, FixedRealWithdrawalPolicy, ConstantWithdrawalPolicy. |
| `src/engine/domain/services/*` | `fbf/core/domain/services/*` | **MOVE TO CORE** | Move pure domain financial math services (valuation, rebalancing, evolution, withdrawal). |
| `src/engine/domain/optimizer/strategy_comparator.py`| `fbf/core/optimization/comparator.py`| **MOVE TO CORE**| Move StrategyComparator. |
| `src/engine/domain/optimizer/types.py`| `fbf/core/optimization/comparator.py`| **MOVE TO CORE**| Move GroupingDimension, RankingRule, StrategyComparisonReport. |
| `src/engine/domain/optimizer.py` | N/A | **DELETE / REPLACE** | Obsolete re-export stub; superseded by `optimization/comparator.py`. |
| `src/engine/domain/asset.py`, `dataset.py`, etc. (top-level)| N/A | **DELETE / REPLACE** | Delete top-level legacy re-export aliases in engine domain. |
| `src/engine/application/pipeline.py`| `fbf/core/execution/pipeline/pipeline.py`| **MOVE TO CORE**| Move SimulationPipeline. |
| `src/engine/application/runner.py`| `fbf/core/execution/pipeline/runner.py`| **MOVE TO CORE**| Move SimulationRunner. |
| `src/engine/application/statistics_builder.py`| `fbf/core/execution/pipeline/statistics.py`| **MOVE TO CORE**| Move SimulationStatisticsBuilder. |
| `src/engine/application/steps/*` | `fbf/core/execution/pipeline/steps/*` | **MOVE TO CORE** | Move monthly pipeline steps (preserving existing execution sequence). |
| `src/engine/application/simulation_context.py`| `fbf/core/execution/context.py`| **MOVE TO CORE**| Move SimulationContext. |
| `src/engine/application/executor.py`| `fbf/core/execution/service.py`| **REFACTOR INTO CORE**| Refactor into unified execution orchestration. |
| `src/research/domain/cohort/generator.py`| `fbf/core/study/internal/cohorts.py`| **MOVE TO CORE**| Move CohortGenerator. |
| `src/research/domain/cohort/specification.py`| `fbf/core/study/internal/cohorts.py`| **MOVE TO CORE**| Move CohortSpecification. |
| `src/research/domain/parameter/*` | `fbf/core/study/internal/sweeps.py`| **MOVE TO CORE**| Move ParameterAxis, ParameterSweepEngine, ParameterConfiguration. |
| `src/research/domain/experiment/definition.py`| `fbf/core/study/internal/experiment.py`| **MOVE TO CORE**| Move ExperimentDefinition. |
| `src/research/domain/plan.py` | `fbf/core/study/plan.py` | **MOVE TO CORE** | Move ResearchPlan, PlannedSimulationUnit. Add StudyPlanResult. |
| `src/research/orchestration/executor.py`| `fbf/core/execution/service.py`| **REFACTOR INTO CORE**| Refactor into unified execution dispatcher. |
| `src/research/orchestration/result.py`| `fbf/core/execution/result.py`| **MOVE TO CORE**| Move ResearchExecutionResult to execution package. |
| `src/research/optimization/swr_optimizer.py`| `fbf/core/optimization/swr_solver.py`| **MOVE TO CORE**| Move SWROptimizer binary search solver. |
| `src/research/optimization/strategy_comparator/*`| N/A | **DELETE / REPLACE** | Delete obsolete stub that raises NotImplementedError. |
| `src/research/experiments.py`, `src/research/experiment/*`| N/A | **DELETE / REPLACE** | Delete unused legacy re-export stubs. |
| `src/cli/builders.py` | Split: `study/` & CLI loaders | **SPLIT** | `StudyConfiguration`, `build_study_plan` move to `fbf/core/study/`. `load_yaml` remains in `fbf/cli/loaders/`. |
| `src/cli/fast_path.py` | `fbf/core/execution/strategies/fast_path.py`| **MOVE TO CORE**| Move Fast Path closed-form recurrence solver and internal validation. |
| `src/cli/commands/optimize_command.py:_SWREvaluator`| `fbf/core/optimization/swr_service.py`| **MOVE TO CORE**| Formalize `_SWREvaluator` into `optimize_study_swr()` application service. |
| `src/infrastructure/execution/reference_chaining.py`| `fbf/core/execution/strategies/reference_chaining.py`| **MOVE TO CORE**| Move Reference Chaining strategy (updates policy import to domain). |
| `src/infrastructure/execution/parallel_executor.py`| `fbf/core/execution/strategies/worker_pool.py`| **MOVE TO CORE**| Move worker pool backend. |
| `src/infrastructure/persistence/sqlite_repository.py`| `fbf/core/persistence/studies/sqlite/adapter.py`| **MOVE TO CORE**| Move SQLiteStudyRepository. |
| `src/infrastructure/persistence/codecs.py`| `fbf/core/persistence/studies/sqlite/codecs.py`| **MOVE TO CORE**| Move entity codecs and DefaultDatasetResolver. |
| `src/infrastructure/persistence/schema.py`| `fbf/core/persistence/studies/sqlite/schema.py`| **MOVE TO CORE**| Move DDL and migrations. |
| `src/infrastructure/persistence/serializers.py`| `fbf/core/persistence/studies/sqlite/serializers.py`| **MOVE TO CORE**| Move serializers. |
| `src/infrastructure/persistence/dataset_cache.py`| `fbf/core/persistence/datasets/cache.py`| **MOVE TO CORE**| Move DatasetCache. |
| `src/infrastructure/csv/`, `logging/`, `configuration/`| N/A | **DELETE / REPLACE** | Delete empty placeholder directories. |
| `src/cli/main.py` | `fbf/cli/main.py` | **REMAIN IN CLI** | Root CLI entry point. |
| `src/cli/progress.py` | `fbf/cli/progress.py` | **REMAIN IN CLI** | Terminal ASCII progress bar & ETA renderer. |
| `src/cli/error_handling.py` | `fbf/cli/error_handling.py` | **REMAIN IN CLI** | CLI exit codes & exception formatters. |
| `src/cli/commands/*` | `fbf/cli/commands/*` | **REMAIN IN CLI** | CLI command presentation & argument parsing. |

---

## 4. Study Planning vs. Dataset Materialization Lifecycle

To prevent premature coupling between study planning and physical dataset IO, the lifecycle is decoupled into explicit phases:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. STUDY PLANNING                               │
│  StudyConfiguration (v0.6 values-only)                                 │
│          ↓                                                             │
│  build_study_plan(config) -> StudyPlanResult                          │
│          ↓                                                             │
│  ResearchPlan:                                                         │
│    • simulation parameters (allocations, withdrawals, horizons)        │
│    • cohort date windows                                               │
│    • dataset identity / reference (e.g. "ern_real_returns_1871_2016")  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      2. DATASET ACQUISITION                            │
│  DatasetResolver (persistence.datasets)                                │
│          ↓                                                             │
│  MATERIALIZED DATASET (domain.dataset)                                 │
│  (Materialization point: parent preload, worker preload, process cache,│
│   or shared memory — to be determined empirically by P4.11 benchmark)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     3. SIMULATION EXECUTION                            │
│  execute_study_plan(plan, options)                                     │
│          ↓                                                             │
│  Scheduler / Worker Dispatchers (execution.strategies)                 │
│          ↓                                                             │
│  SimulationContext (Receives pre-resolved Dataset slices)              │
│          ↓                                                             │
│  Canonical Monthly Pipeline (execution.pipeline)                       │
│          ↓                                                             │
│  Domain Mathematics & Policies (domain.services, domain.policies)      │
└────────────────────────────────────────────────────────────────────────┘
```

### Dataset Slicing Invariant
- **Semantic Rule:** Dataset slicing must not implicitly trigger acquisition or unnecessary re-materialization of equivalent underlying market data.
- **Reference Behavior:** Slices conceptually behave as views/references over already materialized data whenever possible, avoiding redundant allocations.

---

## 5. Execution Architecture & Layering

The execution architecture cleanly decouples the high-level application service, execution strategies, worker dispatchers, and the canonical monthly simulation pipeline:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION SERVICE                            │
│           execute_study_plan(plan, options=ExecutionOptions(...))        │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                 Dispatches based on ExecutionMode
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌──────────────────────────────────┐   ┌──────────────────────────────────┐
│     REFERENCE CHAINED STRATEGY   │   │        FAST PATH STRATEGY        │
│ (reference_chaining.py)          │   │ (fast_path.py)                   │
│ - Longest-horizon grouping       │   │ - Closed-form recurrence solver  │
│ - Canonical Decimal derivation   │   │ - O(horizon) evaluation          │
│ - Bounded batch orchestration    │   │ - Float / Decimal modes          │
└────────────────┬─────────────────┘   └────────────────┬─────────────────┘
                 │                                      │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    EXECUTION SCHEDULER & WORKER POOL                     │
│ (worker_pool.py)                                                         │
│ - Worker / Process dispatch abstraction                                  │
│ - Progress event dispatching (ProgressCallback)                          │
│ - (Worker count, IPC, batching, caching open for benchmark tuning)       │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                   CANONICAL MONTHLY REFERENCE PIPELINE                   │
│ (pipeline/runner.py, pipeline/steps/*)                                   │
│ Step sequence and semantics preserved identically from existing engine: │
│ 1. InitializeAllocationStep     2. BuildDecisionContextStep              │
│ 3. WithdrawalDecisionStep       4. WithdrawalExecutionStep               │
│ 5. AllocationDecisionStep       6. PortfolioRebalanceStep                │
│ 7. MarketEvolutionStep          8. MonthlyResultBuilderStep              │
│ 9. SimulationStateUpdateStep    [Terminal: StatisticsBuilder]            │
└──────────────────────────────────────────────────────────────────────────┘
```

*Canonical Invariant:* P1.3 does not redefine the canonical monthly simulation sequence. Package extraction must preserve the existing sequence and semantics, verified by the existing tests and ERN oracle.

---

## 6. Decimal Reference Engine Preservation

1. **Canonical Reference Scope:**  
   `fbf.core.execution.pipeline` (pipeline steps, `SimulationRunner`, `SimulationPipeline`, and domain math services in `fbf.core.domain.services`) constitutes the canonical reference implementation.
2. **Behavioral Invariant:**  
   - Arithmetic must use `decimal.Decimal` with exact precision.
   - Monthly state transitions, ordering of decision and execution steps, and depletion criteria ($V_m < C$) are permanent domain semantics.
   - The 180-cell ERN oracle acceptance matrix (`data/ern/p49_oracle_table.csv`, 313,020 units) must match identically without a single discrepancy.
3. **Refactoring Permission:**  
   Architectural reorganization of pipeline files into the target namespace is permitted provided all existing unit, integration, and oracle tests continue to pass.

---

## 7. Dataset Lifecycle & Data Access Architecture

### 7.1 Design Boundaries vs. Implementation Facts
1. **Architectural Design Boundary (Frozen):**
   - Dataset acquisition and resolution belong behind the `fbf.core.persistence.datasets` boundary.
   - `Dataset` and `MarketSnapshot` are pure, immutable domain entities in `fbf.core.domain`.
   - `SimulationContext` receives pre-resolved data and **never** performs persistence, file access, or dataset loading.
   - Dataset slicing must not cause unnecessary re-materialization of equivalent underlying market data.
2. **Implementation & Performance Choices (Open for P4.11 Benchmarking):**
   - How often `DefaultDatasetResolver` is invoked across parent vs. worker processes.
   - Whether datasets are preloaded in the parent process, initialized per worker process, managed via a process-local cache, or shared via read-only memory.
   - The in-memory representation of dataset references inside `PlannedSimulationUnit` for multiprocessing IPC transfer.

---

## 8. Persistence Architecture

Persistence is decoupled into study experiment storage and dataset data access:

```
fbf.core.persistence/
├── studies/
│   ├── repository.py      # StudyRepository Protocol, PersistedStudySummary, Export models
│   └── sqlite/
│       ├── adapter.py     # SQLiteStudyRepository (Internal Adapter)
│       ├── schema.py      # DDL & schema migrations
│       ├── codecs.py      # Lossless Decimal & date codecs
│       └── serializers.py # JSON/raw serializers
│
└── datasets/
    ├── resolver.py        # DatasetResolver Protocol, DefaultDatasetResolver
    └── cache.py           # Dataset cache implementation (open for benchmark tuning)
```

*Decoupling Invariant:* `StudyRepository` is completely independent of `DatasetResolver`. Neither repository depends on domain execution or pipeline code.

---

## 9. Public API Surface vs. Internal Implementations

### 9.1 Primary Application API (`fbf.core`)
The top-level namespace exports only the primary application surface:

```python
from fbf.core import (
    StudyConfiguration,      # Core study specification (v0.6 values-only)
    StudyPlanResult,         # Plan construction result & summary metadata
    build_study_plan,        # Application service: StudyConfiguration -> StudyPlanResult
    ExecutionOptions,        # Execution configuration (workers, mode, callback, summary_only)
    ExecutionMode,           # Execution mode enum: REFERENCE, FAST, AUTO
    execute_study_plan,      # Application service: executes study plan
    optimize_study_swr,      # Application service: binary-search SWR solver
)
```

### 9.2 Stable Public Submodules
Domain, policy, and persistence contracts are accessible via explicit submodules:

- **Study Planning (`fbf.core.study`):** `StudyConfiguration`, `StudyPlanResult`, `build_study_plan`, `ResearchPlan`, `PlannedSimulationUnit`
- **Execution (`fbf.core.execution`):** `execute_study_plan`, `ResearchExecutionResult`, `ExecutionOptions`, `ExecutionMode`, `ProgressCallback`, `ProgressEvent`
- **Optimization (`fbf.core.optimization`):** `optimize_study_swr`, `SWROptimizationResult`, `StrategyComparator`, `StrategyComparisonReport`, `GroupingDimension`, `RankingRule`
- **Persistence (`fbf.core.persistence`):** `StudyRepository` (Protocol), `PersistedStudySummary`, `PersistedStudyExport`, `ExperimentIdentity`, `DatasetResolver`, `DefaultDatasetResolver`
  - *(Infrastructure adapter `SQLiteStudyRepository` importable from `fbf.core.persistence.studies.sqlite`)*
- **Domain Primitives (`fbf.core.domain`):** `Money`, `Currency`, `Portfolio`, `AssetHolding`, `AssetClass`, `Dataset`, `MarketSnapshot`, `SimulationResult`, `SimulationStatistics`
- **Policies (`fbf.core.domain.policies`):** `AllocationPolicy`, `WithdrawalPolicy`, `ConstantAllocationPolicy`, `FixedRealWithdrawalPolicy`, `ConstantWithdrawalPolicy`
- **Errors (`fbf.core.errors`):** `CoreError`, `StudyConfigurationError`, `DatasetNotFoundError`, `ExecutionError`, `PersistenceError`, `DuplicateStudyError`, `OptimizationError`

### 9.3 Explicitly Internal Implementation Layers
The following packages are internal implementation details and may evolve, be replaced, or be optimized without altering public contracts:
- `fbf.core.execution.pipeline.*` (SimulationRunner, SimulationPipeline, monthly steps)
- `fbf.core.execution.strategies.*` (reference chaining groups, fast path formulas, worker pools)
- `fbf.core.study.internal.*` (Cartesian sweep engines, cohort generator)
- `fbf.core.persistence.studies.sqlite.*` (SQLite DDL schema, codecs, serializers)
- `fbf.core.persistence.datasets.cache.*` (Dataset cache mechanisms)

---

## 10. Dependency DAG & Architectural Invariants

```
                        ┌────────────────────────┐
                        │      fbf/cli (CLI)     │
                        └───────────┬────────────┘
                                    │
                             Core Public API
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        fbf/core (PUBLIC API)                           │
│  fbf.core, fbf.core.study, fbf.core.execution, fbf.core.optimization,  │
│  fbf.core.persistence, fbf.core.domain, fbf.core.domain.policies       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         CORE INTERNAL LAYERS                           │
│                                                                        │
│   ┌───────────────────────┐            ┌───────────────────────────┐   │
│   │    fbf.core.study     │            │   fbf.core.optimization   │   │
│   │ (builder, sweeps)     │            │ (swr_service, comparator) │   │
│   └───────────┬───────────┘            └─────────────┬─────────────┘   │
│               │                                      │                 │
│               │    ┌─────────────────────────────────┘                 │
│               │    │ (uses execution application contract)             │
│               ▼    ▼                                                   │
│   ┌────────────────────────────────────┐                               │
│   │         fbf.core.execution         │                               │
│   │ (service, strategies, pipeline)    │                               │
│   └─────────────────┬──────────────────┘                               │
│                     │                                                  │
│         ┌───────────┴───────────┐                                      │
│         ▼                       ▼                                      │
│  ┌────────────────────┐   ┌─────────────────────────────────────────┐  │
│  │fbf.core.persistence│   │             fbf.core.domain             │  │
│  │(studies, datasets) │   │(money, asset, portfolio, dataset,       │  │
│  └────────────────────┘   │ policies, pure financial services)      │  │
│                           └─────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### Strictly Forbidden Dependency Rules
1. **`CORE → CLI` and `CORE → UI`:** Strictly forbidden.
2. **`domain → *`:** Pure domain models and policies must NEVER import persistence, execution engines, optimization, study builders, multiprocessing, or external packages.
3. **`optimization → execution strategies`:** Optimization services must interact strictly through the high-level execution application contract (`execute_study_plan`), never directly importing `reference_chaining.py`, `fast_path.py`, or worker pools.
4. **`execution → optimization`:** Execution engines and pipelines must NEVER import optimization services or types.
5. **`SimulationContext → persistence`:** SimulationContext must never load data or access repositories; it receives pre-resolved domain objects.
6. **`CLI → core.internal`:** CLI must never import internal execution pipeline steps, worker dispatchers, or sweep generators.

---

## 11. Deferred Optimization & Performance Decisions (P4.11 Mandate)

To satisfy the P4.11 mandate, the following performance decisions remain intentionally open and un-frozen until post-extraction benchmarking:

1. **Dataset Worker Preloading vs. Process-Local Cache:** Whether worker processes acquire datasets via parent preloading, worker initialization hooks, process-local memoization, or shared memory.
2. **IPC Serialization Strategy:** Optimal representation of `PlannedSimulationUnit` for multiprocessing dispatch to eliminate redundant snapshot serialization.
3. **Worker Pool Scheduling & Batch Sizing:** Tuning of worker pool mechanisms and dynamic batch slicing thresholds.
4. **Shared Memory Trajectory Storage:** Potential zero-copy shared memory representations for large multi-cohort market snapshots.

*Constraint:* The public Core API and application boundaries defined in P1.3 must remain 100% agnostic to these choices.

---

## 12. Test Architecture & Import Enforcement

Test suites will be structured to verify all architectural invariants:

1. **`core/tests/unit/`:** Pure domain unit tests (`Money`, `Portfolio`, `Dataset`, pipeline steps, `SimulationRunner`, policies).
2. **`core/tests/infrastructure/`:** SQLite study persistence, schema migrations, codecs, worker pools, and dataset resolution.
3. **`core/tests/integration/`:** Multi-cohort execution, real engine execution, and application services (`build_study_plan`, `execute_study_plan`, `optimize_study_swr`).
4. **`core/tests/benchmarks/`:** Execution performance, Fast Path equivalence benchmarks, memory bounds.
5. **`core/tests/contract/` (NEW Architecture Tests):**
   - Static AST test: Asserts `fbf-core` has 0 imports of `cli` or `ui`.
   - Static AST test: Asserts `fbf.core.domain` has 0 imports of persistence, execution, study, optimization, or multiprocessing.
   - Static AST test: Asserts `fbf.core.execution` has 0 imports of `fbf.core.optimization`.
   - Static AST test: Asserts `SimulationContext` and pipeline steps contain 0 calls to persistence or dataset resolvers.
   - Public API stability test: Asserts all documented public symbols are importable from documented paths.
   - Canonical Decimal reference equivalence test against `data/ern/p49_oracle_table.csv`.
6. **`cli/tests/`:** Command argument parsing, terminal formatting, progress bars, exit codes, and black-box CLI E2E tests (`tests/e2e/ern/`).

---

## 13. Concrete Migration Map (Current Files → Target Files)

```
CURRENT REPOSITORY                                  TARGET STANDALONE CORE (fbf/core)
-------------------------------------------------   -------------------------------------------------
src/engine/domain/model/money.py              ──►   src/fbf/core/domain/money.py
src/engine/domain/model/asset.py              ──►   src/fbf/core/domain/asset.py
src/engine/domain/model/portfolio.py          ──►   src/fbf/core/domain/portfolio.py
src/engine/domain/model/market_snapshot.py    ──►   src/fbf/core/domain/market_snapshot.py
src/engine/domain/model/dataset.py            ──►   src/fbf/core/domain/dataset.py
src/engine/domain/model/simulation.py         ──►   src/fbf/core/domain/simulation.py
src/engine/domain/policies/allocation_policy  ──►   src/fbf/core/domain/policies/base.py
src/engine/domain/policies/withdrawal_policy  ──►   src/fbf/core/domain/policies/base.py
src/engine/domain/policies/decisions.py       ──►   src/fbf/core/domain/policies/base.py
src/cli/policies.py                           ──►   src/fbf/core/domain/policies/concrete.py
src/engine/domain/services/*                  ──►   src/fbf/core/domain/services/*
src/engine/domain/optimizer/strategy_compare  ──►   src/fbf/core/optimization/comparator.py
src/engine/application/pipeline.py            ──►   src/fbf/core/execution/pipeline/pipeline.py
src/engine/application/runner.py              ──►   src/fbf/core/execution/pipeline/runner.py
src/engine/application/statistics_builder.py  ──►   src/fbf/core/execution/pipeline/statistics.py
src/engine/application/steps/*                ──►   src/fbf/core/execution/pipeline/steps/*
src/engine/application/simulation_context.py  ──►   src/fbf/core/execution/context.py
src/research/domain/cohort/*                  ──►   src/fbf/core/study/internal/cohorts.py
src/research/domain/parameter/*               ──►   src/fbf/core/study/internal/sweeps.py
src/research/domain/experiment/definition.py  ──►   src/fbf/core/study/internal/experiment.py
src/research/domain/plan.py                   ──►   src/fbf/core/study/plan.py
src/research/orchestration/result.py          ──►   src/fbf/core/execution/result.py
src/research/optimization/swr_optimizer.py    ──►   src/fbf/core/optimization/swr_solver.py
src/cli/builders.py (StudyConfig & Builder)   ──►   src/fbf/core/study/configuration.py & builder.py
src/cli/fast_path.py                          ──►   src/fbf/core/execution/strategies/fast_path.py
src/cli/commands/optimize_command.py (Eval)   ──►   src/fbf/core/optimization/swr_service.py
src/infrastructure/execution/reference_chain  ──►   src/fbf/core/execution/strategies/reference_chaining.py
src/infrastructure/execution/parallel_exec    ──►   src/fbf/core/execution/strategies/worker_pool.py
src/infrastructure/persistence/sqlite_repo    ──►   src/fbf/core/persistence/studies/sqlite/adapter.py
src/infrastructure/persistence/codecs.py      ──►   src/fbf/core/persistence/studies/sqlite/codecs.py
src/infrastructure/persistence/schema.py      ──►   src/fbf/core/persistence/studies/sqlite/schema.py
src/infrastructure/persistence/serializers.py ──►   src/fbf/core/persistence/studies/sqlite/serializers.py
src/infrastructure/persistence/dataset_cache  ──►   src/fbf/core/persistence/datasets/cache.py
```

---

## 14. Implementation Constraints for Subsequent Tasks (P1.4+)

1. **Strict Dependency Direction:** All modules and tests must import directly from `fbf.core.*`. No compatibility shims will be created.
2. **CLI Import Boundary:** CLI commands in `fbf/cli` must import solely from the documented public API (`from fbf.core import ...` or public submodules). CLI must never import internal execution pipeline steps, worker dispatchers, or sweep generators.
3. **Reference Invariant:** Extraction must preserve 100% test pass rate across the test suite, with `tests/e2e/ern/test_oracle_matrix.py` verifying the exact 180-cell ERN matrix.
