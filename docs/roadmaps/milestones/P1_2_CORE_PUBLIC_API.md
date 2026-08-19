# P1.2 — Core Public API and Dependency Boundary Specification

**Document Type:** Architectural Decision Document (Milestone Specification)  
**Status:** APPROVED WITH ARCHITECTURAL MODIFICATIONS (2026-08-19)  
**Date:** 2026-08-19  
**Workstream:** Repository Separation & Documentation Audit  
**Task:** Phase 1 / P1.2 (Define the CORE Public API)  
**Prerequisites:** P1.1 (Repository & Dependency Baseline) COMPLETE  
**Successor:** P1.3 (Define the Core Boundary & Internal Layout)  

---

## 1. Executive Summary

This document establishes the official architectural specification for the **Public API** and **Dependency Boundary** of the future standalone `fbf/core` repository.

Following the empirical findings of task P1.1 and architectural review, this specification formalizes the separation between:
1. **The Core Public API:** A small, deliberate, framework-neutral application surface consumed by external frontends (the CLI, future UI, Python scripts, and test harnesses).
2. **Core Internal Capabilities:** High-performance execution strategies (Reference Horizon Chaining, Closed-Form Fast Path), simulation pipeline steps, persistence mechanics, and domain algorithms that reside physically in Core but remain internal implementation details.

### Key Approved Principles
- **Capability-Oriented Surface:** Core exposes high-level application capabilities (defining a study, building an execution plan, running a simulation, optimizing SWR, comparing strategies, persisting results) rather than low-level execution machinery.
- **Unidirectional Dependency:** Dependencies flow strictly `CLI → CORE` and `UI → CORE`. `CORE → CLI` and `CORE → UI` are strictly forbidden.
- **Internal Implementation Freedom:** P1.2 defines public capabilities and boundary invariants without freezing the internal package tree. P1.3 is explicitly empowered to reorganize internal packages to achieve the cleanest possible dependency graph.
- **No Legacy Compatibility Aliases:** No artificial compatibility layers or legacy alias paths (`engine.*`, `research.*`, `infrastructure.*`) will be retained in Core. The codebase and tests will migrate cleanly to the new namespace.
- **Behavioral, Not Textual, Invariance:** The Decimal reference engine and its observable mathematical behavior are canonical. Architectural refactoring is permitted where necessary, provided the reference behavior is proven identical by the oracle matrix and regression test suite.

---

## 2. Verified Current Architecture

An empirical re-audit of the repository confirms the baseline established in P1.1:

1. **Pure Domain Core (`src/engine/`):**  
   Contains `Money`, `Portfolio`, `AssetClass`, `Dataset`, `MarketSnapshot`, `SimulationRunner`, `SimulationPipeline`, and monthly step implementations. Pure mathematical domain logic.
2. **Research Orchestration (`src/research/`):**  
   Contains `CohortGenerator`, `ParameterAxis`, `ParameterSweepEngine`, `ExperimentDefinition`, `ResearchPlan`, `materialize_research_plan`, and `SWROptimizer`.
3. **Execution & Persistence Infrastructure (`src/infrastructure/`):**  
   - `parallel_executor.py`: Parallel worker pool for batch simulation execution.
   - `reference_chaining.py`: Default reference execution engine utilizing longest-horizon run derivation for prefix-consistent families. *Contains the leak:* `from cli.policies import ConstantAllocationPolicy, FixedRealWithdrawalPolicy` (line 15).
   - `persistence/`: Generic SQLite schema, repository, serializers, and entity `codecs.py`.
4. **Accidental Domain & Application Logic in CLI (`src/cli/`):**  
   - `policies.py`: Concrete implementations of `AllocationPolicy` and `WithdrawalPolicy`.
   - `builders.py`: `StudyConfiguration` dataclass, YAML loader, policy resolvers, Cartesian sweep builders, and `build_study_plan()`.
   - `fast_path.py`: Closed-form analytical recurrence solver and F7 stratified validation.
   - `commands/optimize_command.py`: Houses `_SWREvaluator` which bridges `SWROptimizer` to `build_study_plan` and execution.

---

## 3. Public API Principles

The Core Public API is governed by six foundational principles:

1. **Capability-Oriented, Not File-Oriented:** The public API reflects what external callers need to accomplish (define study, run simulation, optimize SWR, query past studies), not the internal physical module layout.
2. **Strict Unidirectional Flow:** Core must have 0 imports of `cli` or `ui`.
3. **Internalized Execution & Process Mechanics:** Callers specify execution semantics via `ExecutionOptions` (e.g. `workers=4`, `mode=ExecutionMode.FAST`). A caller is never required to know whether Core executes a study in-process, through threads, through processes, through horizon-chained batches, or through a future execution backend.
4. **Framework Neutrality:** Core accepts and returns standard Python types (`dict`, `str`, `int`, `Decimal`, `Path`, immutable dataclasses). Core has 0 awareness of terminal formatting, ANSI escape codes, `argparse`, CLI exit codes, or GUI widget toolkits.
5. **Two-Tier Public Namespace:** The top-level `fbf.core` exports only the small primary application surface. Detailed domain, policy, and persistence contracts reside in dedicated public submodules (`fbf.core.study`, `fbf.core.domain`, etc.).
6. **Deterministic & Verifiable:** Identical inputs produce deterministic results. Numerical equivalence requirements are execution-mode-specific and defined by the reference oracle acceptance criteria.

---

## 4. Two-Tier Public Core API Surface

### 4.1 Primary Application API (`fbf.core`)
A minimal, highly ergonomic root surface covering the primary user workflows:

```python
# Primary Application Entry Points
from fbf.core import (
    StudyConfiguration,      # Core study specification (v0.6 values-only)
    build_study_plan,        # Application service: StudyConfiguration -> StudyPlanResult / Plan
    execute_study_plan,      # Application service: executes study plan with ExecutionOptions
    optimize_study_swr,      # Application service: binary-search SWR solver
    ExecutionOptions,        # Execution configuration (workers, mode, progress_callback, summary_only)
    ExecutionMode,           # Execution mode enum: REFERENCE, FAST, AUTO
)
```

### 4.2 Stable Public Submodule APIs
Specific domain, policy, and persistence contracts are accessible via explicit submodules:

- **Study & Planning (`fbf.core.study`):**
  - `StudyConfiguration`, `StudyPlanResult`, `build_study_plan`
- **Execution Services (`fbf.core.execution`):**
  - `execute_study_plan`, `ExecutionOptions`, `ExecutionMode`, `ProgressCallback`, `ProgressEvent`
- **Optimization & Analytics (`fbf.core.optimization`):**
  - `optimize_study_swr`, `SWROptimizationResult`, `StrategyComparator`, `StrategyComparisonReport`, `GroupingDimension`, `RankingRule`
- **Persistence Contracts (`fbf.core.persistence`):**
  - `StudyRepository` (Protocol), `PersistedStudySummary`, `PersistedStudyExport`, `ExperimentIdentity`
  - *(Infrastructure adapter `SQLiteStudyRepository` importable from persistence adapter module, not root application surface)*
- **Domain Primitives & Results (`fbf.core.domain`):**
  - `Money`, `Currency`, `Portfolio`, `AssetHolding`, `Dataset`, `MarketSnapshot`, `AssetClass`, `SimulationResult`, `SimulationStatistics`, `ResearchExecutionResult`, `ResearchPlan`
- **Concrete & Base Policies (`fbf.core.policies`):**
  - `AllocationPolicy`, `WithdrawalPolicy`, `ConstantAllocationPolicy`, `ConstantWithdrawalPolicy`, `FixedRealWithdrawalPolicy`
- **Core Exceptions (`fbf.core.errors`):**
  - `CoreError`, `StudyConfigurationError`, `DatasetNotFoundError`, `ExecutionError`, `PersistenceError`, `DuplicateStudyError`, `OptimizationError`

---

## 5. Core Public vs. Internal API Classification

| Capability | Candidate API | Scope | Tier / Location | Rationale |
| :--- | :--- | :---: | :--- | :--- |
| **Study Configuration** | `StudyConfiguration` | **PUBLIC** | Primary (`fbf.core`) | Core data model required to define any study. |
| **Dict Config Validation** | `StudyConfiguration.from_dict` | **PUBLIC** | Submodule (`fbf.core.study`) | Validates raw dictionary inputs from any frontend. |
| **YAML File Loading** | `load_yaml` | **INTERNAL (CLI)** | `cli.loaders` | File I/O and YAML text parsing is a CLI adapter concern. |
| **Plan Construction** | `build_study_plan` | **PUBLIC** | Primary (`fbf.core`) | High-level application service translating config to plan. |
| **Plan Materialization** | `materialize_research_plan` | **INTERNAL** | `core.internal.research` | Low-level engine pipeline; encapsulated by `build_study_plan`. |
| **Parameter Sweep Engine**| `ParameterSweepEngine` | **INTERNAL** | `core.internal.research` | Cartesian sweep logic encapsulated by `build_study_plan`. |
| **Research Plan Model** | `ResearchPlan` | **PUBLIC** | Submodule (`fbf.core.domain`) | Immutable model representing simulation units. |
| **Unified Execution** | `execute_study_plan` | **PUBLIC** | Primary (`fbf.core`) | Single entry point for executing simulations across workers. |
| **Execution Options** | `ExecutionOptions` | **PUBLIC** | Primary (`fbf.core`) | Configures workers, mode (REFERENCE/FAST), and callbacks. |
| **Execution Mode Enum** | `ExecutionMode` | **PUBLIC** | Primary (`fbf.core`) | Semantic execution selector (`REFERENCE`, `FAST`, `AUTO`). |
| **Reference Chaining** | `execute_reference_chained` | **INTERNAL** | `core.internal.execution` | Default reference engine; encapsulated in `execute_study_plan`. |
| **Parallel Process Pool** | `parallel_execute` | **INTERNAL** | `core.internal.execution` | Process dispatch logic; encapsulated in `execute_study_plan`. |
| **Fast Path Engine** | `FastPathSimulationExecutor` | **INTERNAL** | `core.internal.execution` | Closed-form recurrence solver; encapsulated in `execute_study_plan`. |
| **Fast Path Equivalence** | Equivalence verification | **INTERNAL / TEST** | `core.tests.validation` | Verification facility; not a standard frontend application API. |
| **Concrete Policies** | `ConstantAllocationPolicy`, etc. | **PUBLIC** | Submodule (`fbf.core.policies`)| Simulation policies required for custom scripting. |
| **SWR Optimization** | `optimize_study_swr` | **PUBLIC** | Primary (`fbf.core`) | High-level SWR solver; encapsulates evaluator adapter. |
| **Strategy Comparator** | `StrategyComparator` | **PUBLIC** | Submodule (`fbf.core.optimization`)| Public comparative analytics engine for strategy evaluations. |
| **Persistence Protocol** | `StudyRepository` | **PUBLIC** | Submodule (`fbf.core.persistence`)| Abstract interface for study storage and retrieval. |
| **SQLite Adapter** | `SQLiteStudyRepository` | **PUBLIC ADAPTER** | `fbf.core.persistence.sqlite` | Concrete infrastructure repository implementation. |
| **Persistence Codecs** | `codecs.py`, `schema.py` | **INTERNAL** | `core.internal.persistence`| Low-level serialization mechanics; hidden behind repository. |
| **Dataset Resolution** | `DatasetResolver` | **PUBLIC** | Submodule (`fbf.core.dataset`)| Service protocol for resolving dataset identifiers. |
| **Core Exceptions** | `CoreError`, etc. | **PUBLIC** | Submodule (`fbf.core.errors`)| Standard error hierarchy raised by Core services. |

---

## 6. Detailed Architectural Decisions

### 6.1 StudyConfiguration & YAML Boundary
- **StudyConfiguration Model:** A frozen dataclass implementing the v0.6 values-only specification. Owned by Core Application.
- **YAML Responsibility:** 
  - The CLI owns reading files from disk and converting YAML strings to Python dictionaries using `yaml.safe_load()`.
  - Core provides semantic validation and instantiation via `StudyConfiguration.from_dict(data: Mapping[str, Any])`.
  - Core may provide a convenience helper `StudyConfiguration.from_yaml_str(yaml_str: str)`, keeping `pyyaml>=6.0` as a lightweight Core dependency.
  - Future UI clients (HTTP/JSON or native forms) pass dictionaries directly to `StudyConfiguration.from_dict(...)` without interacting with YAML.

### 6.2 Plan-Building API & `BuiltStudy` Reconsideration
- **Public Entry Point:** `build_study_plan(config: StudyConfiguration, ...)`.
- **Public Output:** Rather than exposing internal Cartesian materialization internals (`ExperimentDefinition`, `CohortSpecification`, `ParameterConfiguration`), Core will return an explicit application result (e.g., `StudyPlanResult` containing the executable `ResearchPlan` and summary metadata needed for CLI dry-runs).
- **P1.3 Action:** P1.3 will determine the precise, minimal attributes of `StudyPlanResult` to ensure zero leakage of internal planning stages.

### 6.3 Execution API & ExecutionMode Contract
- **Semantic Execution Mode:** Rather than a fragile boolean flag (`fast_path: bool`), execution semantics are governed by an enum:
  ```python
  class ExecutionMode(Enum):
      REFERENCE = "reference"  # Canonical Decimal reference engine with horizon chaining
      FAST = "fast"            # Closed-form float recurrence optimization
      AUTO = "auto"            # Uses Fast Path if strategy is eligible, else Reference
  ```
- **Unified Service:** `execute_study_plan(plan, options=ExecutionOptions(mode=ExecutionMode.REFERENCE, workers=4, ...))`.
- **Invariance:** `ExecutionMode.AUTO` must never silently sacrifice reference correctness. If an unsupported policy is encountered in `FAST` mode, Core raises an explicit `ExecutionError`.

### 6.4 Policy Rehoming
- **Resolution of Leak:** `ConstantAllocationPolicy`, `ConstantWithdrawalPolicy`, and `FixedRealWithdrawalPolicy` move from `src/cli/policies.py` into Core domain/policies, permanently resolving the `reference_chaining.py → cli.policies` dependency leak.
- **Submodule Placement:** Concrete policies are exportable from `fbf.core.policies`.

### 6.5 Persistence Boundary
- **Application Interface:** Core application logic interacts with persistence via the `StudyRepository` protocol.
- **Infrastructure Adapter:** `SQLiteStudyRepository` provides the default SQLite implementation, encapsulating schema management, migrations, and codecs.
- **Decoupling:** Future backends (PostgreSQL, in-memory, remote API) can implement `StudyRepository` without modifying Core application services.

### 6.6 SWR Optimization Service
- **Core Service:** The SWR evaluator adapter previously embedded in `optimize_command.py` is formalized into `optimize_study_swr(config, target_success_rate, ...)` in `fbf.core.optimization`.
- **CLI Role:** `OptimizeCommand` becomes a thin adapter that calls `optimize_study_swr` and renders iteration progress to the terminal.

### 6.7 Dataset Loading, Identity & Batching Invariant
- **Architectural Rule:** Dataset resolution and materialization must occur at the highest practical scope and must not be repeated per cohort, unit, or month.
- **Identity Preservation:** Reference Horizon Chaining relies on snapshot identity and prefix consistency. Caching and preloading mechanisms remain internal implementation details that satisfy this rule.

### 6.8 Progress Reporting Boundary
- **Framework Neutrality:** Core execution dispatches progress notifications without referencing terminal streams or GUI frameworks.
- **Event Protocol:** Core supports progress callbacks receiving progress metrics (completed units, total units, optional phase/elapsed). Frontends adapt these events to their specific UI (CLI progress bars, WebSockets, GUI widgets).

### 6.9 Error Hierarchy
- Core services raise explicit subclasses of `CoreError` (`StudyConfigurationError`, `ExecutionError`, `PersistenceError`). Core never invokes `sys.exit()` or references CLI exit codes.

---

## 7. Public API Validation Against Use Cases

| Client Use Case | Primary Interaction with Core Public API | Encapsulated Core Internals |
| :--- | :--- | :--- |
| **CLI Commands** | Calls `StudyConfiguration.from_dict`, `build_study_plan`, `execute_study_plan`, `optimize_study_swr`, `SQLiteStudyRepository`. | Process pools, batch slicing (`_CHAINED_MAX_UNITS_PER_WORKER`), codecs, closed-form formulas. |
| **Python Script / Notebook** | Instantiates `StudyConfiguration` dataclass, calls `build_study_plan` and `execute_study_plan`, directly inspects `ResearchExecutionResult`. | Multiprocessing queues, internal step pipelines. |
| **Future HTTP / UI Backend** | Deserializes JSON to dict, validates via `StudyConfiguration.from_dict`, passes WebSocket callback to `execute_study_plan`, queries `StudyRepository`. | Terminal formatting, CLI config precedence, filesystem YAML loading. |
| **Test & Benchmark Harness** | Imports domain contracts and internal modules directly from Core tests to benchmark reference vs fast-path execution and verify oracle equivalence. | None (testing harness has legitimate internal access within Core). |

---

## 8. Target Dependency Graph & Forbidden Dependencies

```
                    ┌────────────────────────┐
                    │      FRONTENDS         │
                    │   fbf/cli, fbf/ui      │
                    └───────────┬────────────┘
                                │
                         Core Public API
                                │
                                ▼
                    ┌────────────────────────┐
                    │   fbf/core (PUBLIC)    │
                    │  Application Services  │
                    │  & Domain Contracts    │
                    └───────────┬────────────┘
                                │
                         Internal Calls
                                │
                                ▼
                    ┌────────────────────────┐
                    │   fbf/core (INTERNAL)  │
                    │  - Execution Engines   │
                    │  - Monthly Pipeline    │
                    │  - Persistence Codecs  │
                    │  - Domain Algorithms   │
                    └────────────────────────┘
```

### Strictly Forbidden Dependencies
1. **`CORE → CLI`:** Core must NEVER import anything from CLI packages.
2. **`CORE → UI`:** Core must NEVER import anything from UI packages.
3. **`DOMAIN → INFRASTRUCTURE`:** Pure domain models must never import persistence or process execution modules.
4. **`DOMAIN → APPLICATION`:** Domain models must never depend on application orchestration services.

---

## 9. Public API Stability Policy

1. **Public API (`fbf.core` and public submodules):** Fully supported, semantically versioned contract. Breaking changes require a major/minor version bump.
2. **Internal API (`core.internal.*` or private modules):** Implementation details subject to change and refactoring without compatibility guarantees.
3. **Experimental Capabilities:** Any experimental execution modes or optimizers must be explicitly documented and flagged.

---

## 10. Contract Testing Requirements (Input to P1.7)

P1.7 will establish dedicated Core Public API contract tests verifying:
- Clean imports from documented public submodules.
- Static enforcement that Core contains 0 imports from CLI or UI.
- End-to-end execution of study configuration, planning, simulation, optimization, and persistence strictly through the public API.
- Bit-exact / numerical equivalence preservation for the Decimal reference engine and 180-cell ERN oracle table.

---

## 11. Handoff & Migration Scope for P1.3–P1.8

| Task | Responsibilities Established by P1.2 | Implementation Work Delegated to Task |
| :--- | :--- | :--- |
| **P1.3 (Core Boundary & Internal Layout)** | Invariants, public capabilities, and boundary constraints. | Determine exact physical file placement, internal module hierarchy, and internal package reorganization. |
| **P1.4 (CLI Boundary Finalization)** | Standard for CLI as a thin presentation layer over Core Public API. | Refactor CLI commands to consume `fbf.core` services exclusively. |
| **P1.5 (Dependency & Import Audit)** | Forbidden dependency rules and target public import paths. | Audit all imports across all 199 files and eliminate `reference_chaining → cli.policies`. |
| **P1.6 (Packaging Design)** | `fbf-core` and `fbf-cli` distribution specifications. | Create independent `pyproject.toml` configurations. |
| **P1.7 (Test Separation Design)** | Public API contract testing requirements and suite partition. | Allocate 978 tests into Core vs CLI repositories. |
| **P1.8 (Git Migration Strategy)** | Linear commit history preservation for Core. | Draft Git extraction execution script. |
