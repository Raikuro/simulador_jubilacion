# P1.4 — CLI Boundary Finalization & Extraction Map

**Document Type:** Architectural Design & Extraction Specification  
**Status:** REVISED SPECIFICATION (2026-08-19)  
**Date:** 2026-08-19  
**Workstream:** Repository Separation & Documentation Audit  
**Task:** Phase 1 / P1.4 (Define the CLI Boundary & Extraction Map)  
**Prerequisites:** P1.1 (Repository Baseline) COMPLETE, P1.2 (Core Public API) APPROVED, P1.3 (Core Boundary) APPROVED  
**Successor:** P1.5 (Dependency Inversion / Import Audit)  

---

## 1. Executive Summary

This document establishes the official architectural boundary, complete module disposition, and concrete extraction mapping for the standalone `fbf/cli` repository.

Building directly upon the approved P1.3 Core Boundary specification, P1.4 transforms the CLI from a mixed-responsibility package containing accidental domain models, solver algorithms, and execution dispatchers into a **thin presentation and adapter layer** over the `fbf.core` Public API.

### Core Architectural Invariant
$$\text{fbf/cli} \xrightarrow{\quad\text{Public API only}\quad} \text{fbf.core}$$
$$\text{fbf.core} \centernot\longrightarrow \text{fbf/cli} \quad\text{and}\quad \text{fbf/cli} \centernot\longrightarrow \text{fbf.core (Internal Implementations)}$$

### Key Architectural Results
1. **Pure Presentation & CLI Orchestration Role:** `fbf/cli` is exclusively responsible for CLI argument parsing, terminal I/O, file loading, ASCII/ANSI rendering, exit codes, and CLI-specific user configuration.
2. **Elimination of Accidental Core Code in CLI:**  
   - `src/cli/policies.py` moves to `fbf.core.domain.policies.concrete`.
   - `src/cli/fast_path.py` moves to `fbf.core.execution.strategies.fast_path`.
   - `StudyConfiguration` and `build_study_plan()` in `src/cli/builders.py` move to `fbf.core.study`.
   - `_SWREvaluator` in `src/cli/commands/optimize_command.py` moves to `fbf.core.optimization.swr_service`.
3. **Decoupled Study Planning vs. Dataset Acquisition:**  
   The CLI loader reads YAML files into Python dictionaries (`yaml.safe_load()`), passes them to Core via `StudyConfiguration.from_dict()`, and obtains a `StudyPlanResult` (containing `ResearchPlan` with dataset references/identifiers) via `build_study_plan()`. Study planning does **not** acquire or materialize datasets.
4. **Encapsulated Execution Dispatch:**  
   CLI commands no longer import `parallel_executor`, `reference_chaining`, or `FastPathSimulationExecutor`. They call `execute_study_plan(plan, options=ExecutionOptions(mode=..., workers=..., progress_callback=...))`.
5. **Persistence Abstraction:**  
   CLI persistence interactions go through the high-level `StudyRepository` contract (instantiated via Core's `create_study_repository()` factory), keeping SQLite schema, connections, and codecs completely internal to Core.

---

## 2. Current CLI Architecture & Empirical Baseline

The current `src/cli/` tree comprises 16 Python files across 4 functional areas:

```
src/cli/
├── __init__.py                # Package root & convenience imports
├── main.py                    # Argument parser & top-level command dispatch
├── error_handling.py          # ExitCode enum & exception formatting
├── progress.py                # Terminal progress bar (ProgressDisplay)
│
├── builders.py (MONOLITH)     # 424 lines: StudyConfiguration, YAML loader, Cartesian sweeps, build_study_plan
├── policies.py (LEAK)         # 101 lines: ConstantAllocationPolicy, FixedRealWithdrawalPolicy
├── fast_path.py (LEAK)        # 931 lines: Closed-form recurrence solver, Float/Decimal validation
│
└── commands/                  # Command implementations
    ├── __init__.py            # Command registry
    ├── base.py                # BaseCommand protocol & ExecutionContext
    ├── run_command.py         # 520 lines: Run orchestration, strategy selection, persistence
    ├── validate_command.py    # 173 lines: Study YAML validation & dry-run reporting
    ├── optimize_command.py    # 384 lines: SWR binary search evaluation & reporting
    ├── compare_command.py     # 358 lines: Multi-strategy execution, filtering, ranking
    ├── list_command.py        # 191 lines: Study history listing from SQLite repository
    ├── export_command.py      # 198 lines: Exporting results to CSV/JSON
    └── config_command.py      # 345 lines: CLI default settings file management
```

### Empirical Import Audit of Current CLI
An inspection of `src/cli/` reveals massive dependency coupling to engine, research, and infrastructure internals:
- `cli.commands.run_command`: Imports `reference_chaining.py`, `parallel_executor.py`, `cli.fast_path`, `cli.builders`, `infrastructure.persistence.sqlite_repository`.
- `cli.commands.compare_command`: Imports `StrategyComparator`, `sequential_execute`, `parallel_execute`, `SQLiteRepository`.
- `cli.commands.optimize_command`: Imports `SWROptimizer`, `sequential_execute`, `parallel_execute`, `SQLiteRepository`.
- `cli.builders`: Imports `CohortGenerator`, `ParameterSweepEngine`, `ParameterAxis`, `DefaultDatasetResolver`.
- `cli.fast_path`: Imports `SimulationExecutor`, `parallel_executor.py`, `ResearchPlan`.

---

## 3. Target CLI Architecture (`fbf/cli`)

The standalone `fbf/cli` repository is organized into a clean, presentation-focused structure:

```
fbf-cli/
├── pyproject.toml             # CLI packaging (depends on fbf-core)
├── README.md
├── AGENTS.md
├── src/
│   └── fbf/
│       └── cli/
│           ├── __init__.py            # CLI package entry
│           ├── main.py                # argparse entry point & command router
│           ├── error_handling.py      # CLI exit codes & user-facing error formatting
│           ├── context.py             # CLI ExecutionContext & runtime options
│           │
│           ├── loaders/               # CLI File & Configuration Loaders
│           │   ├── __init__.py
│           │   ├── yaml_loader.py     # Filesystem YAML file reader (safe_load -> dict)
│           │   └── user_config.py     # ~/.config/fbf/config.yaml user settings
│           │
│           ├── presentation/          # Terminal Formatting & Progress Display
│           │   ├── __init__.py
│           │   ├── progress.py        # Terminal ASCII progress bar & ETA estimator
│           │   ├── tables.py          # Tabular ASCII summary formatters
│           │   └── formatters.py      # Currency, percentage, and date string formatters
│           │
│           └── commands/              # Thin Presentation Commands
│               ├── __init__.py
│               ├── base.py            # BaseCommand abstract contract
│               ├── run.py             # 'run' command: parses args -> execute_study_plan -> prints table
│               ├── validate.py        # 'validate' command: loads YAML -> build_study_plan -> prints preview
│               ├── optimize.py        # 'optimize' command: parses args -> optimize_study_swr -> prints iterations
│               ├── compare.py         # 'compare' command: runs plan -> StrategyComparator -> prints comparison
│               ├── list.py            # 'list' command: queries StudyRepository -> prints summary table
│               ├── export.py          # 'export' command: exports study results to CSV / JSON / stdout
│               └── config.py          # 'config' command: get/set CLI user defaults
│
└── tests/                             # CLI test suite (~275 tests)
```

---

## 4. Public Core API Consumption Rules for CLI

The CLI is strictly restricted to importing from the approved two-tier Public Core API:

```python
# Primary Application API Surface (Recommended)
from fbf.core import (
    StudyConfiguration,       # Core study specification
    StudyPlanResult,          # Built study metadata & plan
    build_study_plan,         # Application service: config -> StudyPlanResult
    ExecutionOptions,         # Execution options (workers, mode, callback)
    ExecutionMode,            # Execution mode enum: REFERENCE, FAST, AUTO
    execute_study_plan,       # Application service: executes simulation plan
    optimize_study_swr,       # Application service: SWR binary search solver
)

# Documented Public Submodules (When explicit domain or storage contracts are needed)
from fbf.core.domain import Money, Currency
from fbf.core.execution import ResearchExecutionResult, ProgressCallback, ProgressEvent
from fbf.core.domain.policies import ConstantAllocationPolicy, FixedRealWithdrawalPolicy
from fbf.core.optimization import StrategyComparator, StrategyComparisonReport, GroupingDimension, RankingRule
from fbf.core.persistence import StudyRepository, create_study_repository, PersistedStudySummary, PersistedStudyExport
from fbf.core.errors import CoreError, StudyConfigurationError, ExecutionError, PersistenceError
```

### Strictly Forbidden CLI Imports
The CLI must **NEVER** import:
- `fbf.core.execution.pipeline.*` (`SimulationRunner`, `SimulationPipeline`, step classes)
- `fbf.core.execution.strategies.*` (`reference_chaining`, `fast_path`, `worker_pool`)
- `fbf.core.study.internal.*` (`ParameterSweepEngine`, `ParameterAxis`, `CohortGenerator`, `ExperimentDefinition`)
- `fbf.core.persistence.studies.sqlite.*` (SQLite schema DDL, connection pools, codecs)
- `fbf.core.persistence.datasets.*` (DatasetCache, DefaultDatasetResolver)

---

## 5. CLI Orchestration vs. Core Application Orchestration

To maintain a clean separation of concerns, the boundary between CLI orchestration and Core application orchestration is explicitly codified:

| Layer | Permitted Responsibilities (IN SCOPE) | Forbidden Responsibilities (OUT OF SCOPE) |
| :--- | :--- | :--- |
| **CLI Layer (`fbf/cli`)** | • Parse command-line flags and positional arguments.<br>• Read YAML files from filesystem into `dict`.<br>• Instantiate `StudyConfiguration` via `from_dict`.<br>• Invoke Core application services (`build_study_plan`, `execute_study_plan`, `optimize_study_swr`).<br>• Adapt Core progress events to terminal progress bars.<br>• Format returned domain results as ASCII tables / JSON / CSV.<br>• Map `CoreError` exceptions to exit codes. | • Resolve or materialize historical datasets.<br>• Construct `SimulationContext` objects.<br>• Execute pipeline simulation steps.<br>• Manage multiprocessing workers or batch sizes.<br>• Perform Cartesian sweeps or cohort generation.<br>• Implement SWR search recurrence formulas.<br>• Execute raw SQLite schema queries or DDL. |
| **Core Layer (`fbf/core`)** | • Validate study configuration semantics.<br>• Perform Cartesian sweeps and generate cohort plans.<br>• Resolve and materialize historical datasets.<br>• Select execution strategy based on `ExecutionMode`.<br>• Orchestrate worker pools, batching, and IPC.<br>• Execute 9-step monthly reference pipeline.<br>• Perform binary-search SWR optimization.<br>• Manage SQLite schema, transactions, and codecs. | • Inspect CLI arguments (`sys.argv`, `argparse`).<br>• Emit terminal ANSI escape sequences.<br>• Call `sys.exit()` or define CLI exit codes.<br>• Read configuration files from user home (`~/.config`). |

---

## 6. Command-by-Command Extraction & Interaction Flow

### 6.1 `validate` Command
- **Target Flow:**
  1. `loaders.yaml_loader.load_yaml(file_path)` reads file from disk $\to$ `dict`.
  2. `StudyConfiguration.from_dict(data)` validates schema $\to$ `StudyConfiguration`.
  3. `build_study_plan(config)` $\to$ `StudyPlanResult` (containing `ResearchPlan` with dataset reference/identifier).
  4. `presentation.tables.render_study_plan_preview(plan_result)` outputs summary to stdout.
- **Coupling Status:** Cleanly decoupled (zero dataset materialization in planning).

### 6.2 `run` Command
- **Target Flow:**
  1. Parse CLI arguments (`--mode reference|fast|auto`, `--workers N`, `--database DB_PATH`, `--dry-run`).
  2. Load YAML $\to$ `StudyConfiguration.from_dict(data)` $\to$ `build_study_plan(config)`.
  3. If `--dry-run`: render dry-run table and exit.
  4. Build `ExecutionOptions(mode=ExecutionMode(args.mode), workers=args.workers, progress_callback=progress_display.update)`.
  5. Call `result = execute_study_plan(plan_result.plan, options=options)`.
  6. If persistence configured: obtain repository via `repo = create_study_repository(db_path)` and call `repo.save_study(identity, plan_result, result, elapsed)`.
  7. Render result statistics table to terminal.
- **Coupling Status:** Transformed from deeply coupled engine orchestrator to thin application caller.

### 6.3 `optimize` Command
- **Target Flow:**
  1. Parse CLI arguments (`--target-success-rate`, `--tolerance`, `--max-iterations`, `--equity-allocation`, `--horizon-years`).
  2. Load YAML $\to$ `StudyConfiguration.from_dict(data)`.
  3. Call `opt_result = optimize_study_swr(config, target_success_rate=..., tolerance=..., max_iterations=..., options=ExecutionOptions(...), progress_callback=...)`.
  4. Render iteration steps and final optimum SWR table to terminal.
- **Coupling Status:** Fully decoupled (`_SWREvaluator` logic moved to Core Application Service `fbf.core.optimization.swr_service`).

### 6.4 `compare` Command
- **Target Flow:**
  1. Parse CLI arguments (`--strategy`, `--group-by`, `--rank-by`, `--database`).
  2. Load YAML $\to$ `build_study_plan(config)` $\to$ `execute_study_plan(plan)`.
  3. Instantiate `StrategyComparator()` and run comparative analytics: `report = comparator.compare(result, group_by=..., rank_by=...)`.
  4. Render formatted comparison table to terminal.
- **Coupling Status:** Cleanly decoupled.

### 6.5 `list` Command
- **Target Flow:**
  1. Parse CLI arguments (`--database`, `--status`, `--limit`).
  2. Instantiate repository: `repo = create_study_repository(db_path)`.
  3. Call `studies: list[PersistedStudySummary] = repo.list_studies(...)`.
  4. Render tabular study summary list to terminal.
- **Coupling Status:** Consumes high-level persistence models without private codec imports.

### 6.6 `export` Command
- **Target Flow:**
  1. Parse CLI arguments (`--database`, `STUDY_ID`, `--format csv|json`, `--output FILE`).
  2. Instantiate repository: `repo = create_study_repository(db_path)`.
  3. Call `export_data: PersistedStudyExport = repo.get_export_data(study_id)`.
  4. Format export payload (CSV / JSON) and write to file/stdout.
- **Coupling Status:** Cleanly decoupled.

### 6.7 `config` Command
- **Target Flow:** Reads/writes user defaults in `~/.config/fbf/config.yaml`.
- **Coupling Status:** 100% self-contained CLI code.

---

## 7. Complete Extraction & Migration Map

| Current File Path | Responsibility | Target Path | Action | Post-P1.4 Dependency | Tests Affected |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `src/cli/main.py` | CLI entry point & routing | `fbf/cli/main.py` | **KEEP IN CLI** | Imports `fbf.cli.commands.*` | `tests/cli/test_main.py` |
| `src/cli/error_handling.py` | Exit codes & exception formatting | `fbf/cli/error_handling.py` | **KEEP IN CLI** | Imports `fbf.core.errors.CoreError` | `tests/cli/test_error_handling.py` |
| `src/cli/progress.py` | Terminal progress display | `fbf/cli/presentation/progress.py`| **REFACTOR IN CLI** | Conforms to `ProgressCallback` | `tests/cli/test_run_command.py` |
| `src/cli/builders.py:StudyConfiguration` | Study config data model | `fbf/core/study/configuration.py` | **MOVE TO CORE** | None (Core model) | `tests/cli/test_builders.py` |
| `src/cli/builders.py:build_study_plan` | Application planning service | `fbf/core/study/builder.py` | **MOVE TO CORE** | None (Core service) | `tests/cli/test_builders.py` |
| `src/cli/builders.py:load_yaml` | File I/O YAML loader | `fbf/cli/loaders/yaml_loader.py` | **REMAIN IN CLI** | `yaml.safe_load()` | `tests/cli/test_builders.py` |
| `src/cli/policies.py` | Concrete simulation policies | `fbf/core/domain/policies/concrete.py`| **MOVE TO CORE** | None (Core domain) | `tests/cli/test_policies.py` |
| `src/cli/fast_path.py` | Closed-form solver & validation | `fbf/core/execution/strategies/fast_path.py`| **MOVE TO CORE** | None (Core strategy) | `tests/cli/test_fast_path*.py` |
| `src/cli/commands/base.py` | Base command class & context | `fbf/cli/commands/base.py` | **KEEP IN CLI** | None | `tests/cli/test_command_base.py` |
| `src/cli/commands/run_command.py` | Run command execution & display | `fbf/cli/commands/run.py` | **REFACTOR IN CLI** | `fbf.core.{build_study_plan, execute_study_plan}` | `tests/cli/test_run_command.py` |
| `src/cli/commands/validate_command.py`| Validate command | `fbf/cli/commands/validate.py` | **REFACTOR IN CLI** | `fbf.core.{StudyConfiguration, build_study_plan}` | `tests/cli/test_validate_command.py` |
| `src/cli/commands/optimize_command.py`| Optimize command | `fbf/cli/commands/optimize.py` | **REFACTOR IN CLI** | `fbf.core.optimize_study_swr` | `tests/cli/test_optimize_command.py` |
| `src/cli/commands/compare_command.py` | Compare command | `fbf/cli/commands/compare.py` | **REFACTOR IN CLI** | `fbf.core.optimization.StrategyComparator` | `tests/cli/test_compare_command.py` |
| `src/cli/commands/list_command.py` | List past studies | `fbf/cli/commands/list.py` | **REFACTOR IN CLI** | `fbf.core.persistence.StudyRepository` | `tests/cli/test_list_command.py` |
| `src/cli/commands/export_command.py`| Export study data | `fbf/cli/commands/export.py` | **REFACTOR IN CLI** | `fbf.core.persistence.StudyRepository` | `tests/cli/test_export_command.py` |
| `src/cli/commands/config_command.py`| User defaults config manager | `fbf/cli/commands/config.py` | **KEEP IN CLI** | None (CLI local) | `tests/cli/test_config_command.py` |

---

## 8. Persistence & Dataset Access Audit

| Area | Current CLI Behavior | Architectural Violation | Target Resolution |
| :--- | :--- | :--- | :--- |
| **Persistence Factory** | Directly instantiates `SQLiteRepository(db_path)` | Direct coupling to SQLite backend | CLI calls `create_study_repository(db_path)` returning `StudyRepository` protocol instance. |
| **Schema & Migrations**| Leaked via direct DB operations | Leaking schema DDL to CLI | Schema management is 100% encapsulated inside Core persistence. CLI never touches `schema.py`. |
| **Codecs & Serialization**| Directly referenced in some test helpers | Leaking codec internals | Codecs are private to `fbf.core.persistence.studies.sqlite.codecs`. CLI receives flat DTOs (`PersistedStudySummary`, `PersistedStudyExport`). |
| **Dataset Resolution**| `resolve_dataset()` helper in `builders.py` | Mixed persistence in builder | Study planning does not resolve datasets; dataset acquisition is performed by Core during simulation execution. |

---

## 9. Test Architecture & Boundary Enforcement

The test suite will be partitioned and augmented with strict architectural enforcement tests:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          CLI TEST SUITE                                │
│ (cli/tests/ - ~275 tests)                                              │
│                                                                        │
│ 1. Command Unit & Functional Tests:                                    │
│    - test_main.py (argument routing, exit codes)                       │
│    - test_run_command.py (CLI flag parsing, table output, dry-run)     │
│    - test_validate_command.py (validation error messages)              │
│    - test_optimize_command.py (terminal iteration tables)              │
│    - test_compare_command.py (comparison tables, strategy filters)     │
│    - test_list_command.py & test_export_command.py                     │
│                                                                        │
│ 2. Black-box E2E Tests:                                                │
│    - tests/e2e/ern/ (runs CLI binary via subprocess against fixtures)  │
│                                                                        │
│ 3. CLI Architectural Boundary Tests (NEW):                             │
│    - test_cli_imports.py: Static AST test verifying fbf/cli NEVER     │
│      imports from fbf.core.*.internal or fbf.core.execution.pipeline.* │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Architectural Migration Risks & Mitigations

1. **Risk: Breaking CLI Option Parsing & Precedence:**  
   *Mitigation:* Retain all existing CLI flags (`--fast-path`, `--workers`, `--database`, `--initial-capital`, `--currency`) and map them directly into `ExecutionOptions` and `build_study_plan` arguments.
2. **Risk: Progress Bar Coupling to Multiprocessing:**  
   *Mitigation:* Standardize on `ProgressCallback = Callable[[int, int], None]` event protocol. Core execution fires callback events; `fbf.cli.presentation.progress.ProgressDisplay` renders them without Core knowing about terminal streams.
3. **Risk: CLI Error Handling Masking Core Exceptions:**  
   *Mitigation:* Standardize on `CoreError` hierarchy. CLI `error_handling.py` catches `CoreError` subclasses and maps them to human-readable error messages and explicit `ExitCode` values (e.g. `ExitCode.CONFIG_ERROR`, `ExitCode.EXECUTION_ERROR`).

---

## 11. Implementation Sequencing (Handoff to P1.5–P1.10)

1. **P1.5 (Dependency Inversion / Import Audit):** Perform a static AST verification of all repository imports to ensure 100% compliance with P1.2/P1.3/P1.4 boundaries before physical extraction.
2. **P1.6 (Packaging Design):** Write independent `pyproject.toml` files for `fbf-core` and `fbf-cli`.
3. **P1.7 (Test Separation Design):** Formally partition tests between `fbf-core` and `fbf-cli`.
4. **P1.8 (Git Migration Strategy):** Design Git extraction script with linear history preservation.
5. **P1.9 (Core Extraction):** Extract `fbf/core` and verify all Core tests pass.
6. **P1.10 (CLI Extraction):** Refactor `fbf/cli` to consume `fbf.core` and verify all CLI tests pass.

---

## 12. Acceptance Criteria for P1.4

- [x] Complete module disposition table classifying every file in `src/cli/`.
- [x] Full command-by-command trace from entry point to Core Public API call to terminal presentation.
- [x] Explicit list of forbidden Core internal imports for CLI commands.
- [x] Verified decoupling of YAML file loading (`dict`) from study configuration validation (`StudyConfiguration`).
- [x] Dataset acquisition completely removed from study-plan construction.
- [x] Zero changes made to production code, tests, packaging, or Git branches during P1.4.

---

## 13. Architectural Decision

**APPROVE DESIGN**

The CLI Boundary & Extraction Map is fully aligned with P1.3, responsibility-based, and ready for static import verification in P1.5.
