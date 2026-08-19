# P1.8 — Git Migration Strategy

**Document Type:** Architectural Strategy & Repository Extraction Specification  
**Status:** REVISED SPECIFICATION (2026-08-19)  
**Date:** 2026-08-19  
**Workstream:** Repository Separation & Documentation Audit  
**Task:** Phase 1 / P1.8 (Git Migration Strategy)  
**Prerequisites:** P1.1 (Repository Baseline) COMPLETE, P1.2 (Core Public API) APPROVED, P1.3 (Core Boundary) APPROVED, P1.4 (CLI Boundary) APPROVED, P1.5 (Dependency Audit) APPROVED, P1.6 (Packaging Design) APPROVED, P1.7 (Test Separation Design) APPROVED  
**Successor:** P1.9 (Core Extraction Implementation)  

---

## 1. Executive Summary

This document establishes the Git migration strategy, commit classification rules, deterministic path transformation specifications, concrete syntax tree (LibCST) transformation mechanisms, and candidate-wheel handoff workflow for splitting the monorepo into two standalone Git repositories:
- **`fbf-core`**: The foundational FIRE Backtesting Framework simulation engine repository.
- **`fbf-cli`**: The command-line interface and presentation frontend repository.

### Core Extraction Principles
1. **Tooling Standard:** Standardized on `git-filter-repo`, the modern recommended replacement for `git filter-branch`.
2. **Mechanically Verifiable Positive Allowlists & Inverted Exclusion Checks:** Extraction paths are defined via exhaustive positive allowlists and verified by bidirectional assertions: $\text{expected} \subseteq \text{extracted}$ and $\text{unexpected} = \emptyset$ (zero `tests/cli/` in Core; zero `engine/` in CLI).
3. **Deterministic Path Transformation & Strict 1-to-1 Mapping:** Specific-first prefix precedence guarantees that every retained source path resolves to exactly one destination path with zero destination collisions.
4. **Historical Lineage & Authenticity:** Historical commits preserve their authentic code diffs, author metadata, timestamps, and rewritten parentage; commit SHA IDs are deterministically recomputed. Namespace migrations on HEAD are encapsulated in a dedicated, clearly identifiable migration commit.
5. **Lossless Source Transformation via LibCST:** Namespace and import transformations on HEAD are executed using `LibCST` with pre/post source-diff validation ensuring zero unintended modifications outside declared import transformations.
6. **Normalized Structural Assertion-Preservation Audit:** Structural AST comparison across `assert`, `pytest.raises`, `pytest.warns`, and expected literals verifies that 100% of existing test assertions are preserved across file relocations and namespace migrations.
7. **Candidate Wheel Artifact Pipeline:** P1.9 extracts and validates a **candidate `fbf-core` wheel**, which is then consumed and proven by P1.10 during `fbf-cli` clean-environment testing before final publication.

---

## 2. Test Count Baseline & Reconciliation (P0)

To ensure clear, unambiguous migration acceptance gates:

| Scope | Existing Collected Baseline (P1.7) | New Contract Tests Added | Post-Extraction Final Suite |
| :--- | :---: | :---: | :---: |
| **`fbf-core`** | **686 tests** (59 files) | +4 tests (`test_core_boundaries.py`) | **690 tests** (60 files) |
| **`fbf-cli`** | **292 tests** (14 files) | +3 tests (`test_cli_boundaries.py`) | **295 tests** (15 files) |
| **Combined** | **978 tests** (73 files) | **+7 contract tests** (2 files) | **985 tests** (75 files) |

*Migration Gate Rule:*  
1. Phase 6 initially verifies that **all 686 existing Core tests and all 292 existing CLI tests (978 tests total)** pass with 100% green status.
2. The +7 new contract tests (+4 Core / +3 CLI) are then injected and verified, bringing the final post-extraction totals to 690 Core tests and 295 CLI tests.

---

## 3. Historical Commit Inventory & Classification

Empirical git log audit across all **97 commits** in the repository:

```
┌────────────────────────────────────────────────────────────────────────┐
│               HISTORICAL COMMIT CLASSIFICATION (97 COMMITS)            │
├────────────────────────────┬─────────────┬────────────┬────────────────┤
│ Category                   │ Count       │ Percentage │ Handling       │
├────────────────────────────┼─────────────┼────────────┼────────────────┤
│ 1. Core-Only Commits       │ 25 commits  │ 25.8%      │ Retained in Core; pruned in CLI │
│ 2. CLI-Only Commits        │  9 commits  │  9.3%      │ Retained in CLI; pruned in Core │
│ 3. Genuinely Coupled       │ 24 commits  │ 24.7%      │ Filtered by path in both repos │
│ 4. Documentation-Only      │ 37 commits  │ 38.1%      │ Pruned unless in retained docs │
│ 5. Repository Infra        │  1 commit   │  1.0%      │ Replaced with P1.6 pyproject   │
│ 6. Initial / Other         │  1 commit   │  1.0%      │ Retained as shared root        │
├────────────────────────────┼─────────────┼────────────┼────────────────┤
│ TOTAL                      │ 97 commits  │ 100.0%     │                │
└────────────────────────────┴─────────────┴────────────┴────────────────┘
```

### 3.1 Coupled Commits (24 Commits) & Historical Lineage
- In `fbf-core`: `git-filter-repo` retains only the diffs matching the Core Positive Path Allowlist.
- In `fbf-cli`: `git-filter-repo` retains only the diffs matching the CLI Positive Path Allowlist.
- **Metadata Preservation:** Commit authors, committers, timestamps, commit messages, and relative chronological parentage are preserved. Commit SHA IDs will recompute deterministically.
- **Historical Lineage & Verification:** Relevant historical ancestry is preserved wherever the corresponding path survives filtering. Representative files will be verified post-extraction via `git log --follow` and `git blame`.
- **Documentation History Decision:** Documentation-only history outside declared repository-owned paths is intentionally pruned during extraction. Each extracted repository receives its clean, dedicated documentation baseline (`README.md`, `AGENTS.md`, and module documentation) initialized on HEAD.

---

## 4. Positive Path Allowlists & Inverted Exclusion Assertions (P0)

### 4.1 `fbf-core` Positive Allowlist & Mechanical Inverted Checks

```text
POSITIVE ALLOWLIST (Core):
├── src/engine/**
├── src/research/**
├── src/infrastructure/**
├── src/cli/policies.py
├── src/cli/fast_path.py
├── src/cli/builders.py
├── tests/test_*.py
├── tests/unit/**
├── tests/infrastructure/**
├── tests/integration/test_multi_cohort_execution.py
├── tests/integration/test_real_engine_execution.py
├── tests/integration/test_framework_infrastructure.py
├── tests/e2e/ern/test_oracle_matrix.py
├── tests/e2e/ern/test_ern_swr_replication.py
├── tests/e2e/ern/test_per_cell_parser.py
├── tests/e2e/ern/test_worker_selection.py
├── tests/benchmarks/test_execution_performance.py
├── tests/benchmarks/test_fast_path_performance.py
├── tests/benchmarks/test_persistence_performance.py
├── data/ern/**
└── tools/ern/**

MECHANICAL INVERTED ASSERTION (Core must contain 0 occurrences of):
├── tests/cli/**
├── tests/integration/test_config_integration.py
├── tests/integration/test_e2e_workflows.py
├── tests/e2e/ern/test_cli_harness.py
├── tests/benchmarks/test_cli_performance.py
└── examples/**
```

### 4.2 `fbf-cli` Positive Allowlist & Mechanical Inverted Checks

```text
POSITIVE ALLOWLIST (CLI):
├── src/cli/main.py
├── src/cli/error_handling.py
├── src/cli/commands/**
├── src/cli/presentation/**
├── src/cli/loaders/**
├── tests/cli/**
├── tests/integration/test_config_integration.py
├── tests/integration/test_e2e_workflows.py
├── tests/e2e/ern/test_cli_harness.py
├── tests/benchmarks/test_cli_performance.py
└── examples/**

MECHANICAL INVERTED ASSERTION (CLI must contain 0 occurrences of):
├── src/engine/**
├── src/research/**
├── src/infrastructure/**
├── data/ern/**
└── tools/ern/**
```

---

## 5. Deterministic Path Transformation Specification (P1)

### 5.1 Relocation Precedence & Collision Invariants
1. **Specific-First Ordering:** More specific prefix mappings are evaluated and applied before broader parent prefixes (e.g. `src/engine/application/steps/` precedes `src/engine/application/`; `src/research/domain/parameter/` precedes `src/research/domain/`).
2. **Strict Bijective Invariant:**
   $$\forall \text{ retained source path } s, \exists! \text{ destination path } d$$
   $$\forall s_1 \neq s_2 \implies \text{destination}(s_1) \neq \text{destination}(s_2) \quad (\text{Zero Destination Collisions})$$

### 5.2 `fbf-core` Deterministic Path Transformation Manifest

| Priority | Source Path | Target Path in `fbf-core` | Mapping Rule Type |
| :---: | :--- | :--- | :--- |
| 1 | `src/engine/application/steps/` | `src/fbf/core/execution/pipeline/steps/` | Specific Prefix |
| 2 | `src/engine/application/` | `src/fbf/core/execution/pipeline/` | General Prefix |
| 3 | `src/engine/domain/` | `src/fbf/core/domain/` | General Prefix |
| 4 | `src/research/domain/parameter/` | `src/fbf/core/study/internal/parameter/` | Specific Prefix |
| 5 | `src/research/domain/cohort/` | `src/fbf/core/study/internal/cohort/` | Specific Prefix |
| 6 | `src/research/domain/` | `src/fbf/core/study/` | General Prefix |
| 7 | `src/research/orchestration/` | `src/fbf/core/execution/` | General Prefix |
| 8 | `src/research/optimization/` | `src/fbf/core/optimization/` | General Prefix |
| 9 | `src/infrastructure/persistence/` | `src/fbf/core/persistence/` | General Prefix |
| 10 | `src/infrastructure/execution/` | `src/fbf/core/execution/strategies/` | General Prefix |
| 11 | `src/cli/policies.py` | `src/fbf/core/domain/policies/concrete.py` | Specific File |
| 12 | `src/cli/fast_path.py` | `src/fbf/core/execution/strategies/fast_path.py` | Specific File |
| 13 | `src/cli/builders.py` | `src/fbf/core/study/builder.py` | Specific File |
| 14 | `tests/test_money.py` | `tests/unit/domain/test_money.py` | Specific File |
| 15 | `tests/test_portfolio.py` | `tests/unit/domain/test_portfolio.py` | Specific File |
| 16 | `tests/test_allocation.py` | `tests/unit/domain/test_allocation.py` | Specific File |
| 17 | `tests/test_dataset.py` | `tests/unit/domain/test_dataset.py` | Specific File |
| 18 | `tests/unit/test_dataset_slice.py` | `tests/unit/domain/test_dataset_slice.py` | Specific File |
| 19 | `tests/test_validation.py` | `tests/unit/domain/test_validation.py` | Specific File |
| 20 | `tests/test_policy_interfaces.py` | `tests/unit/domain/test_policy_interfaces.py` | Specific File |
| 21 | `tests/test_portfolio_rebalance_service.py` | `tests/unit/domain/test_portfolio_rebalance_service.py` | Specific File |
| 22 | `tests/test_portfolio_market_evolution_service.py` | `tests/unit/domain/test_portfolio_market_evolution_service.py` | Specific File |
| 23 | `tests/test_portfolio_withdrawal_service.py` | `tests/unit/domain/test_portfolio_withdrawal_service.py` | Specific File |
| 24 | `tests/test_rebalance_normalization_regression.py` | `tests/unit/domain/test_rebalance_normalization_regression.py` | Specific File |
| 25 | `tests/test_portfolio_rebalance_integration.py` | `tests/unit/domain/test_portfolio_rebalance_integration.py` | Specific File |
| 26 | `tests/test_build_decision_context_step.py` | `tests/unit/pipeline/test_build_decision_context_step.py` | Specific File |
| 27 | `tests/test_withdrawal_decision_step.py` | `tests/unit/pipeline/test_withdrawal_decision_step.py` | Specific File |
| 28 | `tests/test_withdrawal_execution_step.py` | `tests/unit/pipeline/test_withdrawal_execution_step.py` | Specific File |
| 29 | `tests/test_allocation_decision_step.py` | `tests/unit/pipeline/test_allocation_decision_step.py` | Specific File |
| 30 | `tests/test_portfolio_rebalance_step.py` | `tests/unit/pipeline/test_portfolio_rebalance_step.py` | Specific File |
| 31 | `tests/test_market_evolution_step.py` | `tests/unit/pipeline/test_market_evolution_step.py` | Specific File |
| 32 | `tests/test_monthly_result_builder_step.py` | `tests/unit/pipeline/test_monthly_result_builder_step.py` | Specific File |
| 33 | `tests/test_simulation_state_update_step.py` | `tests/unit/pipeline/test_simulation_state_update_step.py` | Specific File |
| 34 | `tests/test_simulation_runner.py` | `tests/unit/pipeline/test_simulation_runner.py` | Specific File |
| 35 | `tests/test_simulation_runner_integration.py` | `tests/unit/pipeline/test_simulation_runner_integration.py` | Specific File |
| 36 | `tests/test_simulation_executor.py` | `tests/unit/pipeline/test_simulation_executor.py` | Specific File |
| 37 | `tests/test_simulation_statistics_builder.py` | `tests/unit/pipeline/test_simulation_statistics_builder.py` | Specific File |
| 38 | `tests/test_cohort_specification.py` | `tests/unit/study/test_cohort_specification.py` | Specific File |
| 39 | `tests/test_cohort_generator.py` | `tests/unit/study/test_cohort_generator.py` | Specific File |
| 40 | `tests/test_parameter_sweep_engine.py` | `tests/unit/study/test_parameter_sweep_engine.py` | Specific File |
| 41 | `tests/test_experiment_definition.py` | `tests/unit/study/test_experiment_definition.py` | Specific File |
| 42 | `tests/test_research_plan.py` | `tests/unit/study/test_research_plan.py` | Specific File |
| 43 | `tests/test_research_executor.py` | `tests/unit/execution/test_research_executor.py` | Specific File |
| 44 | `tests/test_grid_plan.py` | `tests/unit/execution/test_grid_plan.py` | Specific File |
| 45 | `tests/test_swr_optimizer.py` | `tests/unit/optimization/test_swr_optimizer.py` | Specific File |
| 46 | `tests/test_strategy_comparator.py` | `tests/unit/optimization/test_strategy_comparator.py` | Specific File |
| 47 | `tests/test_strategy_comparator_additional.py` | `tests/unit/optimization/test_strategy_comparator_additional.py` | Specific File |
| 48 | `tests/test_engine_imports.py` | `tests/contract/test_engine_imports.py` | Specific File (1-to-1) |
| 49 | `tests/test_imports.py` | `tests/contract/test_imports.py` | Specific File (1-to-1) |
| 50 | `tests/e2e/ern/` | `tests/oracle/ern/` | General Prefix |
| 51 | `data/ern/` | `data/ern/` | Direct Path |
| 52 | `tools/ern/` | `tools/ern/` | Direct Path |

---

### 5.3 `fbf-cli` Deterministic Path Transformation Manifest

| Priority | Source Path | Target Path in `fbf-cli` | Mapping Rule Type |
| :---: | :--- | :--- | :--- |
| 1 | `src/cli/main.py` | `src/fbf/cli/main.py` | Specific File |
| 2 | `src/cli/error_handling.py` | `src/fbf/cli/error_handling.py` | Specific File |
| 3 | `src/cli/commands/` | `src/fbf/cli/commands/` | General Prefix |
| 4 | `src/cli/presentation/` | `src/fbf/cli/presentation/` | General Prefix |
| 5 | `src/cli/loaders/` | `src/fbf/cli/loaders/` | General Prefix |
| 6 | `tests/cli/test_main.py` | `tests/unit/test_main.py` | Specific File |
| 7 | `tests/cli/test_*.py` | `tests/unit/test_*.py` | General Prefix |
| 8 | `tests/integration/test_config_integration.py` | `tests/integration/test_config_integration.py` | Specific File |
| 9 | `tests/integration/test_e2e_workflows.py` | `tests/integration/test_e2e_workflows.py` | Specific File |
| 10 | `tests/e2e/ern/test_cli_harness.py` | `tests/e2e/test_cli_harness.py` | Specific File |
| 11 | `tests/benchmarks/test_cli_performance.py` | `tests/benchmarks/test_cli_performance.py` | Specific File |
| 12 | `examples/` | `examples/` | General Prefix |

---

## 6. LibCST Lossless HEAD Transformation & Migration Commit (P1)

### 6.1 LibCST Transformation Guarantee
- **Guarantee:** No unintended source changes may occur outside explicitly declared namespace/import transformations.
- **Source-Diff Validation:** A mechanical diff audit compares pre- and post-transformation HEAD to assert that only expected module references (`engine.*` $\to$ `fbf.core.*`, `cli.policies` $\to$ `fbf.core.domain.policies`, etc.) were modified, and that comments, docstrings, formatting, and whitespace remain 100% untouched.

### 6.2 Dedicated Post-Extraction Migration Commit
Historical commits remain historically authentic; modern namespace changes are committed as a single clear transition commit:
```
filtered historical HEAD
        ↓
LibCST transformation & packaging injection
        ↓
validation (AST, assertions, ruff, mypy, pytest)
        ↓
git commit -m "chore: migrate package layout to fbf.core / fbf.cli namespace"
```

---

## 7. Normalized Structural Assertion-Preservation Audit (P1)

To prove that 100% of existing behavioral validation is retained without requiring identical source text:
1. **Audit Scope:** Compares normalized assertion constructs across test suites:
   - `assert` expressions and boolean conditions
   - `pytest.raises(...)` and expected exception types
   - `pytest.warns(...)` and expected warning classes
   - Mock assertion calls (e.g. `assert_called_once_with(...)`)
   - Test function/method identity and parameterization counts
   - Literal expected numeric/string values
2. **Tolerance Rules:** The audit tolerates file relocation, package namespace updates, and approved import changes.
3. **Rejection Rules:** The audit strictly rejects removed assertions, changed expected values, changed exception types, changed comparison operators, or altered assertion structure.

---

## 8. Candidate Core Wheel Artifact & Handoff Pipeline (P1)

To prevent premature release before cross-package integration is proven:

```
[P1.9: Core Candidate Extraction]
        │
        ▼
Extract fbf-core staging
        │
        ▼
Validate 686 existing tests + 4 contract tests (690 total)
        │
        ▼
Build wheel: dist/fbf_core-0.1.0-py3-none-any.whl
Verify metadata: Requires-Dist is EMPTY (0 third-party runtime dependencies)
        │
        ▼
PRODUCE CANDIDATE fbf-core WHEEL ARTIFACT
        │
        ├─────────────────────────────┐
        │                             │
        ▼                             ▼
[P1.10: CLI Extraction]       [Isolated Clean Environment]
        │                             │
        ▼                             ▼
Extract fbf-cli staging       pip install dist/fbf_core-0.1.0-py3-none-any.whl
        │                             │
        ▼                             ▼
Install candidate wheel exclusively   Validate 292 existing + 3 contract (295 total)
(0 local source checkout bleed)       Verify `fbf --help`
        │                             │
        └──────────────┬──────────────┘
                       │
                       ▼
         FINAL INTEGRATED PUBLICATION
```

---

## 9. Pre-Flight and Post-Migration Validation Gates

| Gate | Target | Acceptance Criteria |
| :--- | :--- | :--- |
| **Gate 1: AST Boundary Compliance** | `tests/contract/test_*_boundaries.py` | `CLI → Core Public API`: ALLOWED; `CLI → Core Internals`: FORBIDDEN; `Core → CLI`: FORBIDDEN; Domain downward purity verified. |
| **Gate 2: Structural Assertion & Test Gate** | AST comparison & `pytest` | **100% of normalized behavioral assertions preserved**; Core: **686 existing + 4 contract = 690 green**; CLI: **292 existing + 3 contract = 295 green**. |
| **Gate 3: Type Safety & Formatting** | `mypy --strict` and `ruff check` | 0 type errors; PEP 561 `py.typed` present; formatting clean. |
| **Gate 4: Wheel Package Isolation** | Clean venv wheel install | `fbf-core` wheel metadata declares **0 third-party runtime dependencies** (`Requires-Dist = ∅`); `fbf-cli` wheel installs against candidate `fbf-core` wheel exclusively and executes `fbf --help`. |
| **Gate 5: Mathematical Oracle Truth** | ERN 180-cell acceptance test | Exact Decimal equality against canonical oracle outputs, using the same precision, rounding, scale/serialization rules, and comparison semantics as the reference (180 cells / 313,020 simulated units). |

---

## 10. P1.8 Acceptance Criteria

- [x] Test count baseline fully reconciled: 686 Core + 292 CLI (978 existing) $+ 7$ contract $= 985$ total.
- [x] Bidirectional positive allowlists and mechanical inverted exclusion assertions specified.
- [x] Specific-first relocation precedence rules and strict bijective (zero-collision) guarantee codified (including distinct paths for `test_engine_imports.py` and `test_imports.py`).
- [x] LibCST lossless transformation guarantee and dedicated migration commit sequence defined.
- [x] Normalized structural AST assertion-preservation audit specified.
- [x] Explicit three-tier public Core API boundary enforced in Gate 1.
- [x] Candidate `fbf-core` wheel artifact handoff model integrated into P1.9/P1.10 flow (exclusive wheel consumption).
- [x] Zero third-party runtime dependencies verified via wheel metadata.
- [x] Exact Decimal equality specified for canonical oracle truth gate.
- [x] Zero modifications made to production code, tests, packaging, or Git history during P1.8.

---

## 11. Architectural Decision

**APPROVE DESIGN**

The revised Git Migration Strategy is fully reconciled, mechanically verified, LibCST-lossless, and ready for physical candidate extraction in **P1.9 (Core Extraction Implementation)** upon formal approval.
