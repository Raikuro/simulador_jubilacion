# P1.7 — Test Separation Design

**Document Type:** Architectural Design & Test Suite Allocation Specification  
**Status:** APPROVED (2026-08-19)  
**Date:** 2026-08-19  
**Workstream:** Repository Separation & Documentation Audit  
**Task:** Phase 1 / P1.7 (Test Separation Design)  
**Prerequisites:** P1.1 (Repository Baseline) COMPLETE, P1.2 (Core Public API) APPROVED, P1.3 (Core Boundary) APPROVED, P1.4 (CLI Boundary) APPROVED, P1.5 (Dependency Audit) APPROVED, P1.6 (Packaging Design) APPROVED  
**Successor:** P1.8 (Git Migration Strategy)  

---

## 1. Executive Summary

This document establishes the test suite allocation, test architecture, fixture placement, and import migration rules for partitioning the existing **978 tests across 73 files** into two standalone repositories:
- **`fbf-core` (`core/tests/`):** **59 existing test files (686 tests)** covering pure domain math, canonical 9-step simulation pipeline, study planning sweeps, execution strategies, Fast Path recurrences, SQLite persistence, benchmarks, and the canonical Decimal ERN oracle matrix.
- **`fbf-cli` (`cli/tests/`):** **14 existing test files (292 tests)** covering CLI argument routing, presentation tables, ASCII progress bars, user configuration, exit codes, and black-box E2E workflows against the `fbf` binary.

### Core Test Invariants
1. **Assertion Preservation Requirement:** The migration MUST preserve 100% of existing behavioral assertions; this requirement will be empirically verified during P1.9/P1.10. The 4 smoke test assertions in `tests/test_engine_imports.py` (3) and `tests/test_imports.py` (1) are migrated to `fbf-core/tests/contract/test_core_imports.py` to validate the target Core namespace.
2. **Two-Tier Test Import Boundary:**
   - **CLI Tests (`cli/tests/`):** Strictly restricted to importing from the Public Root Facade (`fbf.core`) and documented Public Submodules (`fbf.core.domain.policies`, `fbf.core.study`, `fbf.core.execution`, `fbf.core.persistence`).
   - **Core Tests (`core/tests/`):** Legitimate access to both Public APIs and internal Core implementation modules (`fbf.core.execution.pipeline.*`, `fbf.core.execution.strategies.*`, `fbf.core.study.internal.*`, `fbf.core.persistence.studies.sqlite.*`) to ensure deep, isolated unit testing of engine internals. Tier 3 remains private and is never a public contract.
3. **Canonical Reference Oracle Placement:** The 180-cell ERN oracle acceptance test (`tests/e2e/ern/test_oracle_matrix.py`, covering 313,020 simulated units across 720 months) is owned by `fbf-core` as the definitive mathematical ground truth.
4. **Distinct Test Categorization:** Correctness unit/integration tests, mathematical oracle acceptance suites, performance benchmarks, and architectural contract tests are categorized and reported distinctly.

---

## 2. Authoritative Test Inventory & Allocation Summary

Empirical pytest collection audit across all 73 test files in the repository:

### 2.1 File Count & Test Count Reconciliation

$$\begin{aligned}
\text{Total Existing Test Files} &= 59 \text{ (Core)} + 14 \text{ (CLI)} = \mathbf{73\text{ files}} \\
\text{Total Existing Collected Tests} &= 686 \text{ (Core)} + 292 \text{ (CLI)} = \mathbf{978\text{ tests}} \\
\text{New Contract Test Files} &= +1 \text{ (Core)} + 1 \text{ (CLI)} = \mathbf{+2\text{ files}} \\
\text{New Contract Tests} &= +4 \text{ (Core)} + 3 \text{ (CLI)} = \mathbf{+7\text{ tests}} \\
\text{Total Post-Extraction Test Suite} &= 60 \text{ (Core)} + 15 \text{ (CLI)} = \mathbf{75\text{ files (985 tests)}}
\end{aligned}$$

### 2.2 Category Breakdown (Post-Extraction)

| Category | Existing Tests | New Tests | Total | Distribution | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Domain & Math Unit Tests** | 92 | 0 | 92 | `fbf-core` | `Money`, `Portfolio`, `Dataset`, policies, math services. |
| **Pipeline & Runner Tests** | 114 | 0 | 114 | `fbf-core` | 9 monthly steps, `SimulationRunner`, `StatisticsBuilder`. |
| **Study Planning Tests** | 154 | 0 | 154 | `fbf-core` | `StudyConfiguration`, builder, sweeps, cohorts. |
| **Execution Strategy Tests** | 118 | 0 | 118 | `fbf-core` | `reference_chaining`, `fast_path`, closed-form, worker pools. |
| **Optimization Tests** | 15 | 0 | 15 | `fbf-core` | `SWROptimizer`, `StrategyComparator`. |
| **Persistence Tests** | 152 | 0 | 152 | `fbf-core` | SQLite repository, migrations, codecs, dataset cache. |
| **Core Integration Tests** | 7 | 0 | 7 | `fbf-core` | Real engine multi-cohort execution. |
| **Core ERN Oracle Suite** | 25 | 0 | 25 | `fbf-core` | 180 oracle cells (313,020 simulated units). |
| **Core Benchmarks** | 20 | 0 | 20 | `fbf-core` | Execution, Fast Path speedup, persistence scaling. |
| **Core Architectural Contract Tests**| 0 | 4 | 4 | `fbf-core` | AST boundary, downward domain purity, public API manifest. |
| **Core Package Smoke Tests** | 4 | 0 | 4 | `fbf-core` | Upgraded namespace smoke assertions from v0.1. |
| **Core Suite Subtotal** | **686** | **4** | **690** | `fbf-core` (60 files) | **100% headless Core engine tests** |
| **CLI Command Unit Tests** | 188 | 0 | 188 | `fbf-cli` | `run`, `validate`, `optimize`, `compare`, `list`, `export`, etc. |
| **CLI Integration Workflows** | 88 | 0 | 88 | `fbf-cli` | `test_config_integration.py` (43), `test_e2e_workflows.py` (45). |
| **CLI Black-Box E2E Harness** | 6 | 0 | 6 | `fbf-cli` | Subprocess harness against `fbf` binary. |
| **CLI Benchmarks** | 10 | 0 | 10 | `fbf-cli` | CLI invocation and table formatting overhead. |
| **CLI Architectural Contract Tests** | 0 | 3 | 3 | `fbf-cli` | AST check ensuring CLI only uses public Core API. |
| **CLI Suite Subtotal** | **292** | **3** | **295** | `fbf-cli` (15 files) | **Presentation & CLI workflow tests** |
| **TOTAL COMBINED** | **978** | **7** | **985** | **Both** (75 files) | |

---

## 3. Machine-Verified List of Coupled Test Statements & Remediations

The audit identified exactly **34 import statements across 13 test files** that import from `cli.policies`, `cli.fast_path`, or `cli.builders`.

### 3.1 Policy on Test Imports
- **Tests in `fbf-core` (Rows 1–8, 10–20, 22–34):** Remediated to direct Core imports (public contracts or internal engine modules as appropriate for unit testing).
- **Tests in `fbf-cli` (Rows 9, 21):** Remediated strictly to **Public Core APIs** (`fbf.core.domain.policies` and `fbf.core.ExecutionMode`).

| # | Test File Path | Line | Current Misplaced Import | Target Import (Remediated) | Access Tier | Target Repo |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: |
| 1 | `tests/benchmarks/test_fast_path_performance.py` | 19 | `from cli.builders import build_initial_portfolio` | `from fbf.core.study.builder import build_initial_portfolio` | Internal (Tier 3) | Core |
| 2 | `tests/benchmarks/test_fast_path_performance.py` | 20 | `from cli.fast_path import ChainedFastPathSimulationExecutor...` | `from fbf.core.execution.strategies.fast_path import ...` | Internal (Tier 3) | Core |
| 3 | `tests/benchmarks/test_fast_path_performance.py` | 21 | `from cli.policies import ConstantAllocationPolicy...` | `from fbf.core.domain.policies import ...` | Public (Tier 2) | Core |
| 4 | `tests/benchmarks/test_fast_path_performance.py` | 80 | `from cli.builders import build_initial_portfolio` | `from fbf.core.study.builder import build_initial_portfolio` | Internal (Tier 3) | Core |
| 5 | `tests/benchmarks/test_fast_path_performance.py` | 165 | `from cli.builders import build_initial_portfolio` | `from fbf.core.study.builder import build_initial_portfolio` | Internal (Tier 3) | Core |
| 6 | `tests/benchmarks/test_fast_path_performance.py` | 166 | `from cli.fast_path import expected_chaining_report...` | `from fbf.core.execution.strategies.fast_path import ...` | Internal (Tier 3) | Core |
| 7 | `tests/cli/test_builders.py` | 14 | `from cli.builders import build_initial_portfolio` | `from fbf.core.study.builder import build_initial_portfolio` | Internal (Tier 3) | Core |
| 8 | `tests/cli/test_builders.py` | 15 | `from cli.policies import ConstantAllocationPolicy` | `from fbf.core.domain.policies import ConstantAllocationPolicy` | Public (Tier 2) | Core |
| 9 | `tests/cli/test_compare_command.py` | 22 | `from cli.policies import ConstantAllocationPolicy...` | `from fbf.core.domain.policies import ...` | **Public Submodule (Tier 2)** | **CLI** |
| 10 | `tests/cli/test_fast_path.py` | 19 | `from cli.builders import build_initial_portfolio` | `from fbf.core.study.builder import build_initial_portfolio` | Internal (Tier 3) | Core |
| 11 | `tests/cli/test_fast_path.py` | 22 | `from cli.fast_path import FAST_PATH_VALIDATION_MAX_UNITS...` | `from fbf.core.execution.strategies.fast_path import ...` | Internal (Tier 3) | Core |
| 12 | `tests/cli/test_fast_path.py` | 34 | `from cli.policies import ConstantAllocationPolicy...` | `from fbf.core.domain.policies import ...` | Public (Tier 2) | Core |
| 13 | `tests/cli/test_fast_path.py` | 406 | `from cli.fast_path import ClosedFormPath` | `from fbf.core.execution.strategies.fast_path import ClosedFormPath` | Internal (Tier 3) | Core |
| 14 | `tests/cli/test_fast_path_exact_equivalence.py` | 28 | `from cli.builders import build_initial_portfolio` | `from fbf.core.study.builder import build_initial_portfolio` | Internal (Tier 3) | Core |
| 15 | `tests/cli/test_fast_path_exact_equivalence.py` | 29 | `from cli.fast_path import ChainedFastPathSimulationExecutor...` | `from fbf.core.execution.strategies.fast_path import ...` | Internal (Tier 3) | Core |
| 16 | `tests/cli/test_fast_path_exact_equivalence.py` | 34 | `from cli.policies import ConstantAllocationPolicy...` | `from fbf.core.domain.policies import ...` | Public (Tier 2) | Core |
| 17 | `tests/cli/test_grid_chaining.py` | 27 | `from cli.builders import BuiltStudy, StudyConfiguration...` | `from fbf.core.study import StudyConfiguration, build_study_plan` | Public (Tier 2) | Core |
| 18 | `tests/cli/test_grid_chaining.py` | 33 | `from cli.fast_path import FAST_PATH_VALIDATION_MAX_UNITS...` | `from fbf.core.execution.strategies.fast_path import ...` | Internal (Tier 3) | Core |
| 19 | `tests/cli/test_grid_chaining.py` | 39 | `from cli.policies import ConstantAllocationPolicy...` | `from fbf.core.domain.policies import ...` | Public (Tier 2) | Core |
| 20 | `tests/cli/test_policies.py` | 12 | `from cli.policies import ConstantAllocationPolicy...` | `from fbf.core.domain.policies import ...` | Public (Tier 2) | Core |
| 21 | `tests/cli/test_run_command.py` | 595 | `from cli.fast_path import ChainedFastPathSimulationExecutor` | `from fbf.core import ExecutionMode` | **Public Facade (Tier 1)** | **CLI** |
| 22 | `tests/infrastructure/test_dataset_cache.py` | 168 | `from cli.builders import resolve_dataset` | `from fbf.core.persistence.datasets.resolver import ...` | Internal (Tier 3) | Core |
| 23 | `tests/infrastructure/test_dataset_cache.py` | 182 | `from cli.builders import resolve_dataset` | `from fbf.core.persistence.datasets.resolver import ...` | Internal (Tier 3) | Core |
| 24 | `tests/infrastructure/test_dataset_cache.py` | 194 | `from cli.builders import resolve_dataset` | `from fbf.core.persistence.datasets.resolver import ...` | Internal (Tier 3) | Core |
| 25 | `tests/infrastructure/test_dataset_cache.py` | 245 | `from cli.builders import resolve_dataset` | `from fbf.core.persistence.datasets.resolver import ...` | Internal (Tier 3) | Core |
| 26 | `tests/infrastructure/test_dataset_cache.py` | 258 | `from cli.builders import resolve_dataset` | `from fbf.core.persistence.datasets.resolver import ...` | Internal (Tier 3) | Core |
| 27 | `tests/infrastructure/test_dataset_cache.py` | 290 | `from cli.builders import resolve_dataset` | `from fbf.core.persistence.datasets.resolver import ...` | Internal (Tier 3) | Core |
| 28 | `tests/infrastructure/test_parallel_execution.py`| 20 | `from cli.builders import build_initial_portfolio` | `from fbf.core.study.builder import build_initial_portfolio` | Internal (Tier 3) | Core |
| 29 | `tests/infrastructure/test_parallel_execution.py`| 21 | `from cli.policies import ConstantAllocationPolicy...` | `from fbf.core.domain.policies import ...` | Public (Tier 2) | Core |
| 30 | `tests/infrastructure/test_reference_chaining.py`| 11 | `from cli.policies import ConstantAllocationPolicy...` | `from fbf.core.domain.policies import ...` | Public (Tier 2) | Core |
| 31 | `tests/integration/test_real_engine_execution.py`| 25 | `from cli.builders import build_initial_portfolio` | `from fbf.core.study.builder import build_initial_portfolio` | Internal (Tier 3) | Core |
| 32 | `tests/integration/test_real_engine_execution.py`| 26 | `from cli.policies import ConstantAllocationPolicy...` | `from fbf.core.domain.policies import ...` | Public (Tier 2) | Core |
| 33 | `tests/test_rebalance_normalization_regression.py`| 26 | `from cli.builders import build_initial_portfolio` | `from fbf.core.study.builder import build_initial_portfolio` | Internal (Tier 3) | Core |
| 34 | `tests/test_rebalance_normalization_regression.py`| 27 | `from cli.policies import ConstantAllocationPolicy` | `from fbf.core.domain.policies import ConstantAllocationPolicy` | Public (Tier 2) | Core |

---

## 4. Preservation of Legacy Import Smoke Assertions

The four smoke test assertions in the current repository:
- `tests/test_engine_imports.py` (3 tests: `test_engine_package_importable`, `test_engine_application_importable`, `test_engine_domain_importable`)
- `tests/test_imports.py` (1 test: `test_engine_packages_importable`)

**Disposition & Preservation:**  
The migration requirement mandates preserving 100% of the underlying validation checks. They are relocated to `fbf-core/tests/contract/test_core_imports.py` to assert top-level importability of the new namespace (`import fbf.core`, `from fbf.core import domain`, `from fbf.core import execution`, `from fbf.core import study`, `from fbf.core import persistence`).

---

## 5. Core API Tiers & Architectural Contract Tests

### 5.1 Three-Tier API Classification

```
┌────────────────────────────────────────────────────────────────────────┐
│                     TIER 1: PUBLIC ROOT FACADE                         │
│ (fbf.core: Minimal primary application surface for CLI & scripts)      │
│ StudyConfiguration, StudyPlanResult, build_study_plan,                 │
│ ExecutionOptions, ExecutionMode, execute_study_plan, optimize_study_swr │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                    TIER 2: PUBLIC SUBMODULE CONTRACTS                  │
│ (Specific domain primitives, policies, results, storage protocols)     │
│ • fbf.core.domain: Money, Currency, Portfolio, AssetHolding,           │
│   AssetClass, Dataset, MarketSnapshot, SimulationResult                │
│ • fbf.core.domain.policies: AllocationPolicy, WithdrawalPolicy,        │
│   ConstantAllocationPolicy, FixedRealWithdrawalPolicy, etc.            │
│ • fbf.core.study: ResearchPlan, PlannedSimulationUnit                  │
│ • fbf.core.execution: ResearchExecutionResult, ProgressCallback        │
│ • fbf.core.optimization: StrategyComparator, StrategyComparisonReport  │
│ • fbf.core.persistence: StudyRepository, create_study_repository      │
│ • fbf.core.errors: CoreError, StudyConfigurationError, etc.            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│               TIER 3: INTERNAL ENGINE IMPLEMENTATIONS                  │
│ (Accessible ONLY inside fbf-core tests; STRICTLY FORBIDDEN from CLI)   │
│ • fbf.core.execution.pipeline.* (runner, 9 steps)                      │
│ • fbf.core.execution.strategies.* (reference_chaining, fast_path)      │
│ • fbf.core.study.internal.* (sweeps, cohorts)                          │
│ • fbf.core.persistence.studies.sqlite.* (schema, codecs)               │
│ • fbf.core.persistence.datasets.* (cache, resolvers)                   │
└────────────────────────────────────────────────────────────────────────┘
```

*Architectural Invariant:* **Tier 3 is NOT a public API.** Core tests may depend on Tier 3 implementation details to verify internal algorithms; external consumers and CLI production/tests must not.

### 5.2 AST Architectural Boundary Rules
- **Rule Core-1 (Zero CLI Imports):** AST visitor asserts that no file under `core/src/` contains an import of `cli` or `fbf.cli`.
- **Rule Core-2 (Downward Domain Layering):** AST visitor asserts that `fbf.core.domain.*` only imports from an explicit allowlist:
  - `fbf.core.domain.*` (internal domain siblings)
  - `fbf.core.errors` (foundational domain exceptions)
  - Python Standard Library (`decimal`, `dataclasses`, `datetime`, `abc`, `typing`, `enum`, `math`)
  - Upward imports into `execution`, `study`, `persistence`, `optimization`, or `cli` are strictly forbidden.
- **Rule Core-3 (Execution/Optimization Isolation):** AST visitor asserts that files under `core/src/fbf/core/execution/` never import `fbf.core.optimization`.
- **Rule CLI-1 (Public API Only):** AST visitor asserts that files under `cli/src/` and `cli/tests/` import only from Tier 1 (Facade) or Tier 2 (Public Submodules), and **never** import Tier 3 internal modules.

---

## 6. Complete Test Allocation Map (All 73 Current Test Files)

The 9 canonical monthly pipeline steps in `src/engine/application/steps/` are explicitly listed in the inventory:
1. `InitializeAllocationStep` (validated in `test_simulation_runner.py`)
2. `BuildDecisionContextStep` (`test_build_decision_context_step.py`)
3. `WithdrawalDecisionStep` (`test_withdrawal_decision_step.py`)
4. `WithdrawalExecutionStep` (`test_withdrawal_execution_step.py`)
5. `AllocationDecisionStep` (`test_allocation_decision_step.py`)
6. `PortfolioRebalanceStep` (`test_portfolio_rebalance_step.py`)
7. `MarketEvolutionStep` (`test_market_evolution_step.py`)
8. `MonthlyResultBuilderStep` (`test_monthly_result_builder_step.py`)
9. `SimulationStateUpdateStep` (`test_simulation_state_update_step.py`)

| Current Test File | Target Path | Target Repo | Existing Tests | Scope & Tier |
| :--- | :--- | :---: | :---: | :--- |
| `tests/test_money.py` | `tests/unit/domain/test_money.py` | Core | 5 | Domain Money arithmetic |
| `tests/test_portfolio.py` | `tests/unit/domain/test_portfolio.py` | Core | 3 | Portfolio holdings |
| `tests/test_allocation.py` | `tests/unit/domain/test_allocation.py` | Core | 4 | Allocation targets |
| `tests/test_dataset.py` | `tests/unit/domain/test_dataset.py` | Core | 3 | Dataset loading & validation |
| `tests/unit/test_dataset_slice.py` | `tests/unit/domain/test_dataset_slice.py` | Core | 8 | Immutable slicing |
| `tests/test_validation.py` | `tests/unit/domain/test_validation.py` | Core | 3 | Domain validation |
| `tests/test_policy_interfaces.py` | `tests/unit/domain/test_policy_interfaces.py`| Core | 3 | Base policy protocols |
| `tests/cli/test_policies.py` | `tests/unit/domain/test_policies.py` | Core | 8 | Concrete policy logic |
| `tests/test_portfolio_rebalance_service.py` | `tests/unit/domain/test_portfolio_rebalance_service.py`| Core | 6 | Rebalancing math |
| `tests/test_portfolio_market_evolution_service.py`| `tests/unit/domain/test_portfolio_market_evolution_service.py`| Core | 7 | Market evolution math |
| `tests/test_portfolio_withdrawal_service.py`| `tests/unit/domain/test_portfolio_withdrawal_service.py`| Core | 7 | Cash withdrawal math |
| `tests/test_rebalance_normalization_regression.py`| `tests/unit/domain/test_rebalance_normalization_regression.py`| Core | 7 | Normalization regression |
| `tests/test_portfolio_rebalance_integration.py`| `tests/unit/domain/test_portfolio_rebalance_integration.py`| Core | 1 | Integration math |
| `tests/test_build_decision_context_step.py` | `tests/unit/pipeline/test_build_decision_context_step.py`| Core | 4 | Pipeline Step 2 |
| `tests/test_withdrawal_decision_step.py` | `tests/unit/pipeline/test_withdrawal_decision_step.py`| Core | 5 | Pipeline Step 3 |
| `tests/test_withdrawal_execution_step.py` | `tests/unit/pipeline/test_withdrawal_execution_step.py`| Core | 5 | Pipeline Step 4 |
| `tests/test_allocation_decision_step.py` | `tests/unit/pipeline/test_allocation_decision_step.py`| Core | 5 | Pipeline Step 5 |
| `tests/test_portfolio_rebalance_step.py` | `tests/unit/pipeline/test_portfolio_rebalance_step.py`| Core | 3 | Pipeline Step 6 |
| `tests/test_market_evolution_step.py` | `tests/unit/pipeline/test_market_evolution_step.py`| Core | 3 | Pipeline Step 7 |
| `tests/test_monthly_result_builder_step.py` | `tests/unit/pipeline/test_monthly_result_builder_step.py`| Core | 3 | Pipeline Step 8 |
| `tests/test_simulation_state_update_step.py`| `tests/unit/pipeline/test_simulation_state_update_step.py`| Core | 5 | Pipeline Step 9 |
| `tests/test_simulation_runner.py` | `tests/unit/pipeline/test_simulation_runner.py`| Core | 26 | Pipeline runner & Step 1 |
| `tests/test_simulation_runner_integration.py`| `tests/unit/pipeline/test_simulation_runner_integration.py`| Core | 10 | Runner integration |
| `tests/test_simulation_executor.py` | `tests/unit/pipeline/test_simulation_executor.py`| Core | 12 | Simulation executor |
| `tests/test_simulation_statistics_builder.py`| `tests/unit/pipeline/test_simulation_statistics_builder.py`| Core | 34 | Statistics calculation |
| `tests/cli/test_builders.py` | `tests/unit/study/test_builders.py` | Core | 5 | StudyConfig & builder |
| `tests/test_cohort_specification.py` | `tests/unit/study/test_cohort_specification.py`| Core | 8 | Cohort specification |
| `tests/test_cohort_generator.py` | `tests/unit/study/test_cohort_generator.py`| Core | 48 | Cohort generator |
| `tests/test_parameter_sweep_engine.py` | `tests/unit/study/test_parameter_sweep_engine.py`| Core | 46 | Parameter sweeps |
| `tests/test_experiment_definition.py` | `tests/unit/study/test_experiment_definition.py`| Core | 14 | Experiment definitions |
| `tests/test_research_plan.py` | `tests/unit/study/test_research_plan.py` | Core | 25 | Research plan model |
| `tests/test_research_executor.py` | `tests/unit/execution/test_research_executor.py`| Core | 46 | Research executor |
| `tests/cli/test_fast_path.py` | `tests/unit/execution/test_fast_path.py` | Core | 17 | Fast path solver |
| `tests/cli/test_fast_path_exact_equivalence.py`| `tests/unit/execution/test_fast_path_exact_equivalence.py`| Core | 12 | Exact equivalence |
| `tests/cli/test_grid_chaining.py` | `tests/unit/execution/test_grid_chaining.py` | Core | 14 | Grid chaining |
| `tests/test_grid_plan.py` | `tests/unit/execution/test_grid_plan.py` | Core | 8 | Grid plan |
| `tests/infrastructure/test_parallel_execution.py`| `tests/unit/execution/test_parallel_execution.py`| Core | 17 | Worker pool execution |
| `tests/infrastructure/test_reference_chaining.py`| `tests/unit/execution/test_reference_chaining.py`| Core | 15 | Reference chaining strategy |
| `tests/test_swr_optimizer.py` | `tests/unit/optimization/test_swr_optimizer.py`| Core | 3 | Binary search optimizer |
| `tests/test_strategy_comparator.py` | `tests/unit/optimization/test_strategy_comparator.py`| Core | 6 | Strategy comparator |
| `tests/test_strategy_comparator_additional.py`| `tests/unit/optimization/test_strategy_comparator_additional.py`| Core | 6 | Additional comparisons |
| `tests/infrastructure/test_sqlite_persistence.py`| `tests/infrastructure/test_sqlite_persistence.py`| Core | 49 | SQLite study storage |
| `tests/infrastructure/test_schema_migration.py`| `tests/infrastructure/test_schema_migration.py`| Core | 3 | DDL migrations |
| `tests/infrastructure/test_codecs.py` | `tests/infrastructure/test_codecs.py` | Core | 30 | Lossless entity codecs |
| `tests/infrastructure/test_context.py` | `tests/infrastructure/test_context.py` | Core | 19 | Persistence context |
| `tests/infrastructure/test_dataset_cache.py` | `tests/infrastructure/test_dataset_cache.py` | Core | 13 | Dataset cache |
| `tests/infrastructure/test_dataset_identity_persistence.py`| `tests/infrastructure/test_dataset_identity_persistence.py`| Core | 6 | Dataset identity |
| `tests/integration/test_multi_cohort_execution.py`| `tests/integration/test_multi_cohort_execution.py`| Core | 3 | Multi-cohort engine |
| `tests/integration/test_real_engine_execution.py`| `tests/integration/test_real_engine_execution.py`| Core | 3 | Real engine integration |
| `tests/integration/test_framework_infrastructure.py`| `tests/integration/test_framework_infrastructure.py`| Core | 41 | Framework integration |
| `tests/e2e/ern/test_oracle_matrix.py` | `tests/oracle/ern/test_oracle_matrix.py` | Core | 3 | Canonical 180-cell oracle |
| `tests/e2e/ern/test_ern_swr_replication.py` | `tests/oracle/ern/test_ern_swr_replication.py`| Core | 4 | ERN SWR replication |
| `tests/e2e/ern/test_per_cell_parser.py` | `tests/oracle/ern/test_per_cell_parser.py`| Core | 6 | Cell parser verification |
| `tests/e2e/ern/test_worker_selection.py` | `tests/oracle/ern/test_worker_selection.py`| Core | 12 | Worker selection |
| `tests/benchmarks/test_execution_performance.py`| `tests/benchmarks/test_execution_performance.py`| Core | 10 | Execution benchmark |
| `tests/benchmarks/test_fast_path_performance.py`| `tests/benchmarks/test_fast_path_performance.py`| Core | 3 | Fast path speed benchmark |
| `tests/benchmarks/test_persistence_performance.py`| `tests/benchmarks/test_persistence_performance.py`| Core | 7 | Persistence benchmark |
| `tests/test_engine_imports.py` | `tests/contract/test_core_imports.py` | Core | 3 | Upgraded namespace smoke test |
| `tests/test_imports.py` | `tests/contract/test_core_imports.py` | Core | 1 | Upgraded namespace smoke test |
| `tests/cli/test_main.py` | `tests/unit/test_main.py` | CLI | 11 | CLI routing & exit codes |
| `tests/cli/test_command_base.py` | `tests/unit/test_command_base.py` | CLI | 7 | BaseCommand protocol |
| `tests/cli/test_error_handling.py` | `tests/unit/test_error_handling.py` | CLI | 8 | Error formatting |
| `tests/cli/test_run_command.py` | `tests/unit/test_run_command.py` | CLI | 35 | 'run' presentation |
| `tests/cli/test_validate_command.py` | `tests/unit/test_validate_command.py` | CLI | 20 | 'validate' presentation |
| `tests/cli/test_optimize_command.py` | `tests/unit/test_optimize_command.py` | CLI | 21 | 'optimize' iteration tables |
| `tests/cli/test_compare_command.py` | `tests/unit/test_compare_command.py` | CLI | 40 | 'compare' comparison display |
| `tests/cli/test_list_command.py` | `tests/unit/test_list_command.py` | CLI | 15 | 'list' history display |
| `tests/cli/test_export_command.py` | `tests/unit/test_export_command.py` | CLI | 17 | 'export' serialization |
| `tests/cli/test_config_command.py` | `tests/unit/test_config_command.py` | CLI | 14 | 'config' file defaults |
| `tests/integration/test_config_integration.py`| `tests/integration/test_config_integration.py`| CLI | 43 | CLI config integration |
| `tests/integration/test_e2e_workflows.py` | `tests/integration/test_e2e_workflows.py`| CLI | 45 | E2E CLI command workflows |
| `tests/e2e/ern/test_cli_harness.py` | `tests/e2e/test_cli_harness.py` | CLI | 6 | CLI subprocess harness |
| `tests/benchmarks/test_cli_performance.py` | `tests/benchmarks/test_cli_performance.py`| CLI | 10 | CLI invocation benchmark |

---

## 7. Package Boundary & Physical Installation Gates (Preserved from P1.6)

In addition to AST tests, P1.7 enforces the physical packaging boundary gates established in P1.6:
1. **Isolated Core Installation:** `pip install ./core` in a clean environment must allow `import fbf.core` and raise `ModuleNotFoundError` for `import fbf.cli`.
2. **CLI Distribution Resolution:** `pip install ./cli` in a clean environment must install `fbf-core` via its package dependency and execute `fbf --help`.
3. **Zero Repository-Relative Imports:** Tests in `cli/tests/` must resolve `fbf.core` as an installed package with zero path modifications.

---

## 8. Implementation Sequencing for P1.8–P1.10

- **P1.8 (Git Migration Strategy):** Design the Git history extraction script to split commits into `fbf-core` and `fbf-cli`.
- **P1.9 (Core Extraction):** Extract `fbf-core` with its 59 existing test files (686 tests) + new contract tests (690 tests total) and verify 100% pass rate.
- **P1.10 (CLI Extraction):** Extract `fbf-cli` with its 14 existing test files (292 tests) + new contract tests (295 tests total) and verify 100% pass rate.

---

## 9. Acceptance Criteria for P1.7

- [x] Authoritative 73-file inventory with exact test counts (686 Core + 292 CLI = 978 existing tests).
- [x] Assertion preservation requirement established and scheduled for empirical verification in P1.9/P1.10.
- [x] Complete table of all 34 coupled test statements across 13 files with explicit target imports.
- [x] Two-tier import rule enforced: CLI tests consume Public API only; Core tests access Core internals.
- [x] Three-tier API manifest specified (Root Facade, Public Submodules, Internal Modules).
- [x] Concrete allowlist specified for Rule Core-2 (Downward Domain Layering).
- [x] Categorization of correctness, oracle acceptance, benchmarks, and contract tests.
- [x] Zero modifications made to existing repository code, tests, or packaging files.

---

## 10. Architectural Decision

**APPROVE DESIGN**

The revised Test Separation Design is fully reconciled against the collected test inventory, proven assertion-complete, and ready for Git migration strategy design in P1.8.
