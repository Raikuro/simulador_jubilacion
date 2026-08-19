# v0.4 Infrastructure & Deployment — Milestone Architecture

**Document Type:** Architectural Specification (Frozen)  
**Status:** APPROVED & FROZEN  
**Baseline:** v0.1 Execution Engine, v0.2.3 Research Infrastructure, v0.3 Optimization Layer (all frozen)  
**Milestone Objective:** Production-Ready Persistence, CLI Interface, and Parallel Execution  
**Target Version:** `v0.4-infrastructure-deployment`

---

## Executive Summary

v0.4 is the **Infrastructure & Deployment** milestone. It transforms the FIRE Backtesting Framework from a research-grade Python library into a production-ready application by adding:

1. **Persistence Layer** — SQLite-based storage of research definitions and results
2. **CLI Interface** — Command-line tool for batch experiment execution
3. **Parallel Execution** — Multi-core support for large-scale studies

This milestone **introduces no new domain logic**. All domain components (Engine v0.1, Research v0.2.3, Optimization v0.3) remain frozen and unchanged. v0.4 adds **infrastructure-only** capabilities aligned with the clean architecture principle that domain logic never depends on external systems.

---

## 1. Architectural Context

### 1.1 Layer Architecture Alignment

The FIRE Framework follows strict Clean Architecture principles:

```
┌─────────────────────────────────────────────────────────┐
│         Presentation Layer (v0.4 NEW)                   │
│  CLI Commands | Output Formatting | User Interaction    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│       Application Layer (v0.2.3 FROZEN)                 │
│  ResearchExecutor | SimulationExecutor | Orchestration  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│         Domain Layer (v0.1 + v0.2.3 + v0.3 FROZEN)      │
│  Engine | Research | Optimization | Pure Business Logic │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│     Infrastructure Layer (v0.4 NEW)                     │
│  SQLite | Serialization | I/O | Parallelization         │
└─────────────────────────────────────────────────────────┘
```

**Critical Invariant:** Domain layer (v0.1 + v0.2.3 + v0.3) has **zero dependencies** on v0.4 infrastructure code. All dependencies flow unidirectionally downward: CLI → Research → Domain → Infrastructure (external dependencies).

### 1.2 Frozen Dependencies

All components v0.4 depends on are permanently frozen:

| Component | Version | Status | Responsibility |
|-----------|---------|--------|-----------------|
| **SimulationRunner** | v0.1 | FROZEN | Executes one deterministic simulation |
| **SimulationExecutor** | v0.1 | FROZEN | Batch coordinates multiple simulations |
| **ResearchExecutor** | v0.2.3 | FROZEN | Orchestrates research studies |
| **SWROptimizer** | v0.3 | FROZEN | Solves for safe withdrawal rates |
| **StrategyComparator** | v0.3 | FROZEN | Comparative strategy analysis |
| **ExperimentDefinition** | v0.2.1 | FROZEN | Declarative study schema |
| **ResearchPlan** | v0.2.3 | FROZEN | Immutable materialized study plan |

**Implementation Implication:** v0.4 must use only the frozen public APIs of these components. No internal implementation details are visible or usable.

---

## 2. Milestone Objective & Rationale

### 2.1 Why v0.4 Now?

**Readiness Criteria:**

✅ **Domain logic complete** — All v0.1, v0.2.3, v0.3 components are production-grade, frozen, fully tested.

✅ **Research infrastructure stable** — Study definition, cohort generation, parameter sweeps, and result aggregation are proven and immutable.

✅ **Optimization algorithms proven** — SWROptimizer and StrategyComparator implement reproducible research patterns.

✅ **External API contracts frozen** — All public API boundaries defined and approved for infrastructure integration.

✅ **Demonstrated business value** — Framework successfully reproduces ERN studies; next step is democratizing access through CLI and persistence.

### 2.2 v0.4 Business Objectives

| Objective | Capability | Rationale |
|-----------|-----------|-----------|
| **Reproducibility** | Persist experiment definitions, execution plans, and results | Enable independent verification and long-term audit trails |
| **Usability** | CLI interface for batch studies | Reduce friction for researchers without Python knowledge |
| **Performance** | Parallel study execution | Enable large-scale parameter sweeps in reasonable time |
| **Integration** | Export results (CSV, JSON) | Enable downstream analysis and visualization tools |

---

## 3. Architectural Decisions

### 3.1 Persistence Architecture Decision

#### Decision: Domain-First Serialization

**Principle:** Infrastructure layer serializes domain objects; domain objects never know about serialization formats.

**Implementation Pattern:**

```
Domain Object (e.g., ResearchPlan)
         │
         ▼
Infrastructure Serializer (SQLite adapter)
         │
         ▼
SQLite Schema (derived from domain structure)
```

**Rationale:**

- Domain remains decoupled from persistence mechanism
- Easy to support multiple storage formats (SQLite, JSON, Parquet) without changing domain
- Testing domain logic requires no database setup
- Serialization logic isolated in infrastructure layer

**Anti-Pattern (Prohibited):**

```
❌ Domain objects with @orm_decorators
❌ Domain __init__ methods calling database
❌ Domain classes inheriting from ORM base classes
❌ Domain classes aware of table names or column mappings
```

#### Decision: Value Object Serialization Contract

**What Gets Persisted:**

| Type | Persist? | Rationale | Format |
|------|----------|-----------|--------|
| **ExperimentDefinition** | ✅ YES | User-defined study schema | Normalized (foreign key to ExperimentDefinition table) |
| **ResearchPlan** | ✅ YES | Pre-materialized execution plan | Normalized (Plan → PlannedUnit records) |
| **PlannedSimulationUnit** | ✅ YES | Individual unit metadata | Immutable record (cohort identity, parameters, policies) |
| **ResearchExecutionResult** | ✅ YES | Aggregated study results | Normalized result tables (one record per unit) |
| **SimulationResult** | ✅ YES | Monthly trajectories | Fact table (one record per month per simulation) |
| **Portfolio** | ⚠️ CONDITIONAL | Only when required by result aggregation | Nested JSON or denormalized record |
| **MonthlyResult** | ✅ YES | Monthly snapshots | Fact table (one record per month per simulation) |

**Non-Persisted (Infrastructure Concern):**

- `AllocationPolicy` / `WithdrawalPolicy` — Persisted as policy type + parameters, not object serialization
- `MarketDataset` — Loaded from external source, not persisted
- `CohortSpecification** — Identity persisted (start_date), definition loaded from MarketDataset
- `ParameterConfiguration** — Persisted as key-value pairs

#### Decision: Policy Serialization Strategy

**Policy Representation:**

Policies are **NOT** persisted as Python objects. Instead, persist:

```python
# ✅ CORRECT: Persist policy type + parameters
PolicyRecord = {
    "policy_type": "ConstantAllocationPolicy",
    "parameters": {
        "equity_allocation": "0.75",
        "bond_allocation": "0.25"
    }
}

# ❌ INCORRECT: Do not pickle policy objects
pickle.dumps(allocation_policy)
```

**Rationale:**

- Pickled Python objects are fragile across versions
- Policy parameters are the actual business data
- Policy type string allows re-instantiation in future versions
- Enables policy parameter auditing and reproducibility

### 3.2 CLI Architecture Decision

#### Decision: Command Hierarchy & Responsibility

**CLI Structure:**

```
sim-retire [global-options] COMMAND [command-options]
├── run              — Execute research study
│   ├── --study FILE
│   ├── --output-dir DIR
│   ├── --workers N
│   └── --format (csv|json|sqlite)
├── list             — List stored studies
├── validate         — Validate experiment definition
├── export           — Export results
│   ├── --study-id ID
│   ├── --format (csv|json|parquet)
│   └── --output FILE
├── optimize         — Run SWROptimizer
│   ├── --target-success-rate RATE
│   └── --initial-capital AMOUNT
└── compare          — Run StrategyComparator
    ├── --strategy1 POLICY
    ├── --strategy2 POLICY
    └── --metrics (stats|drawdown|quantiles)
```

**Responsibility Boundary:**

| Layer | Responsibility |
|-------|-----------------|
| **CLI** | Argument parsing, user I/O, output formatting |
| **Application** | Study orchestration, command routing |
| **Domain** | Business logic (unchanged) |

**Anti-Pattern (Prohibited):**

```
❌ Business logic in CLI commands
❌ Domain objects constructed in CLI layer
❌ Direct database access from CLI
❌ Hard-coded file paths or formats
```

### 3.3 Parallel Execution Architecture Decision

#### Decision: ProcessPoolExecutor Isolation

**Model:** Each worker process executes simulations in isolation.

**Constraints:**

1. **No Shared Mutable State** — All communication through immutable value objects
2. **Work Unit Granularity** — Work assigned by **PlannedSimulationUnit** (not by simulation step)
3. **Result Aggregation** — Worker results combined deterministically after all complete
4. **Error Isolation** — One worker failure doesn't stop others

**Implementation Pattern:**

```python
# Worker: Executes one or more simulation units
def execute_units(units: Sequence[PlannedSimulationUnit]) -> Sequence[SimulationResult]:
    """Pure function: units → results. No side effects."""
    # Units are immutable value objects
    # No database access
    # No inter-process communication
    # Return results in same order as input units
    return [SimulationRunner.execute(unit) for unit in units]

# Coordinator: Distributes work and collects results
def parallel_execute(
    plan: ResearchPlan, 
    max_workers: int
) -> ResearchExecutionResult:
    """Distribute units across workers, collect results."""
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        # Each batch is independent
        batches = chunk_plan_units(plan)
        results = pool.map(execute_units, batches)
        return aggregate_results(plan, results)
```

**Critical Constraint:** `ProcessPoolExecutor` requires serializable (picklable) objects. This means:

- All domain objects must be frozen dataclasses (already true)
- No file handles, thread locks, or network connections in units
- Policies must be serializable (they are frozen dataclasses)

#### Decision: No Process-Level Caching

**Rule:** No caching across process boundaries. Each worker computes results independently.

**Rationale:**

- Eliminates inter-process synchronization complexity
- Guarantees reproducibility (no cache coherency bugs)
- Simplifies testing (no mock caches needed)
- For large studies, I/O cost dominated anyway

### 3.4 Configuration Management Decision

#### Decision: Three-Level Configuration

**Levels:**

1. **User Configuration** (CLI arguments / config file)
   - Study location, output format, worker count, cache settings
2. **Study Configuration** (ExperimentDefinition)
   - Cohorts, policies, parameters, dataset selection
3. **System Configuration** (application defaults)
   - Default output directory, default worker count, file format defaults

**Hierarchy:**

```
User CLI args (highest priority)
    ↓
Config file (if specified)
    ↓
Study definition (ExperimentDefinition)
    ↓
System defaults (lowest priority)
```

**Anti-Pattern (Prohibited):**

```
❌ Hard-coded paths in domain logic
❌ Environment variable parsing in domain layer
❌ Magic strings for file names or formats
```

---

## 4. Component Architecture

### 4.1 Infrastructure Layer Components

```
src/infrastructure/
├── persistence/
│   ├── __init__.py
│   ├── repository.py              # Abstract repository interface
│   ├── sqlite_adapter.py           # SQLite implementation
│   └── schema.py                   # SQLite schema definitions
├── serialization/
│   ├── __init__.py
│   ├── value_object_encoder.py    # Domain object serialization
│   ├── csv_exporter.py            # CSV export
│   └── json_exporter.py           # JSON export
├── execution/
│   ├── __init__.py
│   ├── parallel_executor.py        # ProcessPoolExecutor wrapper
│   └── result_aggregator.py        # Result collection & combination
├── configuration/
│   ├── __init__.py
│   └── settings.py                # Configuration objects
└── logging/
    ├── __init__.py
    └── structured_logger.py        # Structured logging
```

### 4.2 CLI Layer Components

```
src/cli/
├── __init__.py
├── main.py                        # Entry point
├── commands/
│   ├── __init__.py
│   ├── run_command.py             # Execute study
│   ├── list_command.py            # List studies
│   ├── validate_command.py        # Validate definition
│   ├── export_command.py          # Export results
│   ├── optimize_command.py        # Run optimizer
│   └── compare_command.py         # Run comparator
├── output_formatters/
│   ├── __init__.py
│   ├── table_formatter.py         # Pretty-print tables
│   ├── csv_formatter.py           # CSV output
│   └── json_formatter.py          # JSON output
└── error_handlers.py              # User-facing error messages
```

### 4.3 Application Layer Components (New)

```
src/research/application/
├── __init__.py
├── study_runner.py                # High-level study orchestration
├── optimization_runner.py         # SWROptimizer orchestration
└── comparison_runner.py           # StrategyComparator orchestration
```

---

## 5. Public API Contracts

### 5.1 Persistence API Contract

#### Repository Interface

```python
# src/infrastructure/persistence/repository.py

from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Sequence

@dataclass(frozen=True)
class StoredStudy:
    """Immutable record of a stored research study."""
    study_id: str
    experiment_definition: ExperimentDefinition
    created_at: datetime
    updated_at: datetime
    status: str  # "pending" | "running" | "completed" | "failed"
    result_count: int


class StudyRepository(ABC):
    """Abstract interface for persisting and retrieving research studies."""
    
    @abstractmethod
    def save_study(
        self, 
        experiment_definition: ExperimentDefinition
    ) -> str:
        """
        Persist an experiment definition.
        
        Args:
            experiment_definition: Immutable study schema
        
        Returns:
            study_id: Unique identifier for later retrieval
        
        Raises:
            RepositoryError: If persistence fails
        """
        pass
    
    @abstractmethod
    def load_study(self, study_id: str) -> StoredStudy:
        """
        Retrieve a stored experiment definition by ID.
        
        Raises:
            StudyNotFoundError: If study_id doesn't exist
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    def list_studies(self) -> Sequence[StoredStudy]:
        """List all stored studies with metadata."""
        pass
    
    @abstractmethod
    def save_results(
        self,
        study_id: str,
        plan: ResearchPlan,
        result: ResearchExecutionResult
    ) -> None:
        """
        Persist execution results for a completed study.
        
        Args:
            study_id: Study identifier
            plan: The executed research plan
            result: Aggregated execution results
        
        Raises:
            RepositoryError: If persistence fails
        """
        pass
    
    @abstractmethod
    def load_results(self, study_id: str) -> ResearchExecutionResult:
        """
        Retrieve execution results for a study.
        
        Raises:
            ResultsNotFoundError: If results not persisted
            RepositoryError: If retrieval fails
        """
        pass
```

### 5.2 Parallel Execution API Contract

```python
# src/infrastructure/execution/parallel_executor.py

from dataclasses import dataclass
from typing import Optional, Callable

@dataclass(frozen=True)
class ExecutionConfig:
    """Configuration for parallel execution."""
    max_workers: Optional[int] = None  # None = CPU count
    timeout_seconds: Optional[float] = None
    use_processes: bool = True  # vs. threads


class ParallelExecutor:
    """Execute research studies with multi-core support."""
    
    def __init__(self, config: ExecutionConfig):
        """Initialize executor with configuration."""
        pass
    
    def execute_plan(
        self,
        plan: ResearchPlan,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ResearchExecutionResult:
        """
        Execute a research plan in parallel.
        
        Args:
            plan: Immutable research plan to execute
            progress_callback: Optional callback(completed, total) for progress updates
        
        Returns:
            Aggregated execution results
        
        Raises:
            ExecutionError: If execution fails
            ExecutionTimeout: If timeout exceeded
        """
        pass
```

### 5.3 CLI API Contract

```python
# src/cli/commands/run_command.py

@dataclass(frozen=True)
class RunCommandArgs:
    """Arguments for the 'run' command."""
    study_file: Path                    # Path to YAML experiment definition
    output_dir: Path                    # Where to store results
    workers: int = 1                    # Number of parallel workers
    format: str = "csv"                 # Output format (csv|json|sqlite)
    persist_study: bool = True          # Save study definition


class RunCommand:
    """Execute a research study from CLI."""
    
    def execute(self, args: RunCommandArgs) -> int:
        """
        Run study and return exit code.
        
        Returns:
            0 if successful
            1 if failed
            2 if validation error
        """
        pass
```

---

## 6. Behavioral Specifications (Outline)

v0.4 requires three detailed behavioral specifications to be completed before implementation begins:

### 6.1 SQLite Persistence Specification

**Title:** `INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md`

**Responsibility:** Define exactly:

- Schema design (tables, relationships, constraints)
- Serialization contracts (how domain objects map to schemas)
- Migration strategy (backward compatibility)
- Query patterns (how CLI retrieves data)
- Concurrency model (transaction semantics)

**Acceptance Criteria:**

- [ ] Schema supports all required domain objects
- [ ] All domain values preserved losslessly
- [ ] Schema normalized to 3NF (no denormalization without justification)
- [ ] Transaction semantics guarantee consistency
- [ ] Migration path defined for v0.5 changes

### 6.2 CLI Interface Specification

**Title:** `CLI_INTERFACE_SPECIFICATION.md`

**Responsibility:** Define exactly:

- Command syntax and argument contracts
- Exit codes and error messages
- Input/output formats (YAML definitions, CSV results, JSON output)
- Help text and user interaction patterns
- Configuration file format

**Acceptance Criteria:**

- [ ] All commands defined with argument validation
- [ ] Exit codes consistent across commands
- [ ] Error messages actionable for users
- [ ] Help text comprehensive and discoverable

### 6.3 Parallel Execution Specification

**Title:** `PARALLEL_EXECUTION_SPECIFICATION.md`

**Responsibility:** Define exactly:

- Work distribution strategy (how units assigned to workers)
- Result aggregation semantics (ordering guarantee, duplicate detection)
- Error handling (partial failure recovery)
- Determinism guarantee (same results as sequential execution)
- Resource constraints (memory, file descriptors, timeouts)

**Acceptance Criteria:**

- [ ] Results deterministically identical to sequential execution
- [ ] Failure isolation prevents cascade failures
- [ ] Resource usage bounded and predictable
- [ ] Progress tracking implemented

---

## 7. Dependencies & Integration Points

### 7.1 Integration with Frozen Components

| Component | Integration Point | Data Flow |
|-----------|------------------|-----------|
| **ResearchExecutor** | CLI → study_runner → ResearchExecutor | ResearchPlan → ResearchExecutionResult |
| **SWROptimizer** | CLI optimize-command → SWROptimizer | WithdrawalRate → OptimizationResult |
| **StrategyComparator** | CLI compare-command → StrategyComparator | Strategy pair → ComparativeMetrics |
| **SimulationExecutor** | Parallel executor batches units | PlannedSimulationUnit → SimulationResult |
| **ExperimentDefinition** | CLI loads YAML → deserialized definition | YAML file → ExperimentDefinition object |

### 7.2 External Dependencies (Infrastructure Only)

**Allowed (Infrastructure Layer):**

- `sqlite3` — Standard library, SQLite database
- `click` — CLI framework (not required in domain layer)
- `pyyaml` — Study definition serialization (infrastructure layer only)
- `dataclasses-json` — Domain object serialization (infrastructure layer only)

**Prohibited (Domain Layer):**

- ❌ No database libraries in domain
- ❌ No CLI frameworks in domain
- ❌ No I/O libraries in domain
- ❌ No process/threading libraries in domain

---

## 8. Known Constraints & Architectural Decisions

### 8.1 Determinism Guarantee

**Constraint:** Parallel execution must produce identical results to sequential execution (within numerical precision).

**Why:** Scientific reproducibility requires deterministic results.

**Implementation Requirement:** 

- No randomness in work assignment
- Deterministic ordering of result aggregation
- Results combined in same sequence regardless of worker completion order

### 8.2 Immutability Preservation

**Constraint:** All domain objects remain frozen dataclasses. v0.4 infrastructure must not require mutable wrappers.

**Why:** Mutability is a major source of bugs and makes parallelization unsafe.

**Implication:** No `ORMBase` classes or mutable proxies. Serialization logic lives entirely in infrastructure layer.

### 8.3 No Domain Changes

**Constraint:** v0.4 introduces zero new domain logic. All domain components (v0.1, v0.2.3, v0.3) remain unchanged.

**Why:** Changing domain logic while adding infrastructure would conflate two independent concerns.

**Verification:** All existing domain tests must pass unchanged.

### 8.4 Backward Compatibility

**Constraint:** CLI and persistence interfaces must not break existing frozen APIs (v0.1–v0.3).

**Why:** Other projects may depend on frozen public APIs.

**Implication:** CLI is an additional interface, not a replacement for Python library usage.

---

## 9. Testing Strategy

### 9.1 Persistence Tests

```python
# tests/infrastructure/test_sqlite_persistence.py

def test_roundtrip_experiment_definition():
    """Verify ExperimentDefinition can be persisted and retrieved losslessly."""
    pass

def test_roundtrip_research_execution_result():
    """Verify ResearchExecutionResult persisted and retrieved losslessly."""
    pass

def test_concurrent_writes():
    """Verify SQLite handles concurrent writes without corruption."""
    pass
```

### 9.2 CLI Tests

```python
# tests/cli/test_run_command.py

def test_run_command_with_yaml_study():
    """Verify CLI parses study YAML and executes."""
    pass

def test_run_command_exit_codes():
    """Verify correct exit codes for success/failure."""
    pass

def test_run_command_output_formats():
    """Verify CLI produces valid CSV/JSON output."""
    pass
```

### 9.3 Parallel Execution Tests

```python
# tests/infrastructure/test_parallel_execution.py

def test_parallel_results_identical_to_sequential():
    """Verify determinism: parallel ≡ sequential execution."""
    pass

def test_error_isolation():
    """Verify one worker failure doesn't stop others."""
    pass

def test_progress_callback():
    """Verify progress updates reported correctly."""
    pass
```

---

## 10. Quality Gates

### Pre-Implementation Checklist

Before implementation begins, these artifacts must be frozen:

- [ ] `INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md` — Approved & Frozen
- [ ] `CLI_INTERFACE_SPECIFICATION.md` — Approved & Frozen
- [ ] `PARALLEL_EXECUTION_SPECIFICATION.md` — Approved & Frozen
- [ ] SQLite schema design reviewed
- [ ] Data serialization contracts defined
- [ ] CLI command hierarchy approved
- [ ] Parallel work distribution model approved
- [ ] Error handling strategy defined
- [ ] Configuration management approach approved

### Quality Standards (No Exceptions)

Every v0.4 component must:

- ✅ Pass 100% of infrastructure-specific tests
- ✅ Achieve 0 mypy errors
- ✅ Maintain clean architecture boundaries (domain ↔ infrastructure)
- ✅ Preserve determinism of frozen domain components
- ✅ Have comprehensive docstrings
- ✅ Match specifications exactly
- ✅ Include architecture review comment linking to this document

---

## 11. Implementation Roadmap

### Architectural Rationale for Phase Ordering

The sequence of implementation phases is structured to respect internal architectural dependencies and minimize implementation risk:

1. **Phase 1 (Parallel Execution)** precedes Persistence because it is pure algorithmic code without external system dependencies (I/O or database). It establishes and validates the concrete batch execution data structures and eliminates determinism/process-pool risks prior to adding storage complexity.
2. **Phase 2 (Persistence Layer)** directly builds upon the validated execution data structures established in Phase 1 to design and verify SQLite schemas, serialization contracts, and repository patterns.
3. **Phase 3 (CLI Interface)** integrates the parallel execution engine (Phase 1) and persistence layer (Phase 2) into user-facing command handlers.
4. **Phase 4 (Integration & Acceptance)** validates end-to-end workflows across all integrated components.

---

### Phase 1: Parallel Execution (Implementation 1) ⭐ START HERE

**Components:** `ParallelExecutor`, work distribution, result aggregation, error isolation

**Architectural Focus:** Algorithmic concurrency, determinism verification, process pool management (zero database dependency)

**Deliverables:**
- `ProcessPoolExecutor` integration complete
- Deterministic work batching implemented
- Ordered result collection implemented
- Error isolation and progress tracking verified

**Exit Criteria:**
- Parallel results identical to sequential (bit-for-bit determinism)
- Error isolation working (one worker failure does not crash pool)
- Speedup target achieved (speedup ≥ 0.8 × worker count)
- 0 mypy errors in execution module

### Phase 2: Persistence Layer (Implementation 2)

**Components:** SQLite adapter, schema, repository implementation (informed by Phase 1 output structures)

**Deliverables:**
- SQLite schema created (9 tables with relationships)
- Repository interface implemented
- Lossless round-trip serialization tests passing (100%)
- Concurrent read and lock retry handling verified

**Exit Criteria:**
- 100% of persistence tests passing
- Round-trip tests validate all Decimal and date precision preserved
- Schema documented and verified
- 0 mypy errors in persistence module

### Phase 3: CLI Interface (Implementation 3)

**Components:** Command implementations (`sim-retire`), argument parsing, output formatters, error handlers

**Deliverables:**
- All 6 CLI commands implemented (`run`, `list`, `validate`, `export`, `optimize`, `compare`)
- Help text, exit codes, and output formatters (CSV, JSON) complete

**Exit Criteria:**
- All CLI tests passing
- Help text generated correctly
- Exit codes consistent
- 0 mypy errors in CLI module

### Phase 4: Integration & Acceptance (Final)

**Components:** End-to-end integration tests, performance validation, complete milestone handoff

**Deliverables:**
- End-to-end workflows working (study load → parallel execution → persistence → CLI export)
- Performance profile established
- Acceptance criteria 100% satisfied

**Exit Criteria:**
- 100% of tests passing (including integration and all frozen v0.1-v0.3 tests)
- 0 mypy errors across entire codebase
- Acceptance tests passing

---

## 12. Handoff to Implementation Engineer

### 12.1 What Is Frozen

The following components are ready for implementation:

| Artifact | Status | Location |
|----------|--------|----------|
| This milestone architecture | ✅ FROZEN | This document |
| Parallel Execution Spec | ✅ FROZEN | `docs/specifications/infrastructure/PARALLEL_EXECUTION_SPECIFICATION.md` |
| SQLite Persistence Spec | ✅ FROZEN | `docs/specifications/infrastructure/INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md` |
| CLI Interface Spec | ✅ FROZEN | `docs/specifications/infrastructure/CLI_INTERFACE_SPECIFICATION.md` |
| v0.1 Execution Engine API | ✅ FROZEN | v0.1 public APIs (unchanged) |
| v0.2.3 Research Layer API | ✅ FROZEN | v0.2.3 public APIs (unchanged) |
| v0.3 Optimization Layer API | ✅ FROZEN | v0.3 public APIs (unchanged) |

### 12.2 Behavioral Specifications (Approved)

All behavioral specifications have been approved and frozen:

| Specification | Status | Responsibility |
|---------------|--------|-----------------|
| `PARALLEL_EXECUTION_SPECIFICATION.md` | ✅ FROZEN | Work distribution, determinism, error isolation |
| `INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md` | ✅ FROZEN | Schema design, serialization, repository pattern |
| `CLI_INTERFACE_SPECIFICATION.md` | ✅ FROZEN | Command syntax, argument handling, exit codes |

### 12.3 Implementation Guardrails

**MUST:**

- ✅ Never modify any domain code (v0.1, v0.2.3, v0.3)
- ✅ Keep infrastructure tests independent (no database setup required for domain tests)
- ✅ Preserve all frozen public API contracts
- ✅ Match specifications exactly
- ✅ Achieve 0 mypy errors
- ✅ Pass 100% of tests
- ✅ Create atomic commits ONLY after an implementation phase has successfully completed all validation gates (tests, type checks, traceability review, self-audit, and acceptance criteria)

**MUST NOT:**

- ❌ Add dependencies to domain layer
- ❌ Modify frozen domain objects
- ❌ Create mutable wrappers around immutable objects
- ❌ Skip any specification requirement
- ❌ Assume infrastructure patterns from other projects
- ❌ Create progress or intermediate commits prior to phase gate validation

---

## 13. Success Criteria

v0.4 is complete when:

1. ✅ Parallel execution produces deterministic results
2. ✅ SQLite persistence working end-to-end for all domain objects
3. ✅ CLI commands execute studies and export results
4. ✅ All infrastructure tests passing (100%)
5. ✅ All domain tests still passing (100%)
6. ✅ Zero mypy errors
7. ✅ Clean architecture boundaries maintained
8. ✅ All frozen APIs unchanged and working
9. ✅ Documentation complete and accurate
10. ✅ Performance profile acceptable (parallel speedup achieved)

---

## 14. Related Documents

**Frozen Baseline:**
- [CURRENT_STATE.md](../../continuity/CURRENT_STATE.md) — v0.1–v0.3 status
- [PROJECT_CONTEXT.md](../../continuity/PROJECT_CONTEXT.md) — Long-term vision
- [RESEARCH_LAYER_FINAL_ROADMAP.md](./RESEARCH_LAYER_FINAL_ROADMAP.md) — v0.2–v0.3 architecture

**Behavioral Specifications (Frozen):**
- [PARALLEL_EXECUTION_SPECIFICATION.md](../../specifications/infrastructure/PARALLEL_EXECUTION_SPECIFICATION.md) — Parallel execution contract
- [INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md](../../specifications/infrastructure/INFRASTRUCTURE_SQLITE_PERSISTENCE_SPECIFICATION.md) — Persistence contract
- [CLI_INTERFACE_SPECIFICATION.md](../../specifications/infrastructure/CLI_INTERFACE_SPECIFICATION.md) — CLI command specification

---

## 15. Approval & Status

| Role | Approval | Date |
|------|----------|------|
| **Chief Architect** | FROZEN | 2026-07-25 |
| **Approved for Implementation** | YES | 2026-07-25 |

**Next Step:** Implementation Engineer begins Phase 1 (Parallel Execution Engine) following `V0.4_IMPLEMENTATION_HANDOFF.md`.

---

## Appendix A: Clean Architecture Reminder

```
Don't let this happen:

❌ BAD: Domain logic depends on SQLite
     class AllocationPolicy(SQLAlchemy):
         __tablename__ = "policies"
         equity_allocation = Column(Decimal)

❌ BAD: CLI imports domain classes
     from engine.domain.portfolio import Portfolio
     p = Portfolio()  # Wrong layer

✅ GOOD: Infrastructure adapts domain objects
     @dataclass(frozen=True)
     class AllocationPolicy:
         equity_allocation: Decimal
     
     # Adapter in infrastructure
     class PolicySQLiteAdapter:
         def serialize(policy: AllocationPolicy) -> Row
         def deserialize(row: Row) -> AllocationPolicy

✅ GOOD: CLI uses application layer
     from research.application.study_runner import StudyRunner
     runner = StudyRunner()
     runner.execute_study(study_id, output_dir)
```

---

**Document Status:** APPROVED AND FROZEN  
**Implementation Ready:** YES  
**Next Gate:** Three detailed specifications required before code begins
