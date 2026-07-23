# `ResearchExecutor` Public API Review

## Purpose

This document defines and freezes the public API contract for:

- `ResearchPlan` & `PlannedSimulationUnit` — Public Research Domain Contracts (Immutable Value Objects)
- `ResearchExecutionResult` — Public Orchestration Output Contract
- `ResearchExecutor` — Stateless Research Execution Orchestration Service

of the Research Layer (`v0.2-research-layer`, Sub-Milestone `v0.2.3`).

After approval, implementation proceeds strictly against this frozen public interface.

**Baselines:**

- Behavioural specification: `RESEARCH_EXECUTOR_SPECIFICATION.md` (**Approved & Frozen**)
- Architectural review: `RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md` (**Approved & Frozen**)

---

## 1. Module Placement & Export Interface

### Canonical File Locations

```text
src/research/domain/plan.py               # ResearchPlan & PlannedSimulationUnit
src/research/orchestration/result.py     # ResearchExecutionResult
src/research/orchestration/executor.py   # ResearchExecutor
src/research/orchestration/errors.py     # ResearchExecutionError, InvalidResearchPlanError
```

### Public Export Contract

```python
# src/research/domain/__init__.py
from research.domain.cohort.specification import CohortSpecification
from research.domain.cohort.generator import CohortGenerator
from research.domain.experiment.definition import ExperimentDefinition
from research.domain.parameter.configuration import ParameterConfiguration
from research.domain.parameter.axis import ParameterAxis
from research.domain.parameter.engine import ParameterSweepEngine
from research.domain.plan import ResearchPlan, PlannedSimulationUnit

__all__ = [
    "CohortSpecification",
    "CohortGenerator",
    "ExperimentDefinition",
    "ParameterConfiguration",
    "ParameterAxis",
    "ParameterSweepEngine",
    "ResearchPlan",
    "PlannedSimulationUnit",
]

# src/research/orchestration/__init__.py
from research.orchestration.executor import ResearchExecutor
from research.orchestration.result import ResearchExecutionResult
from research.orchestration.errors import ResearchExecutionError, InvalidResearchPlanError

__all__ = [
    "ResearchExecutor",
    "ResearchExecutionResult",
    "ResearchExecutionError",
    "InvalidResearchPlanError",
]

# src/research/__init__.py — Top-level re-exports
from research.domain import (
    CohortSpecification,
    CohortGenerator,
    ExperimentDefinition,
    ParameterConfiguration,
    ParameterAxis,
    ParameterSweepEngine,
    ResearchPlan,
    PlannedSimulationUnit,
)
from research.orchestration import (
    ResearchExecutor,
    ResearchExecutionResult,
    ResearchExecutionError,
    InvalidResearchPlanError,
)

__all__ = [
    "CohortSpecification",
    "CohortGenerator",
    "ExperimentDefinition",
    "ParameterConfiguration",
    "ParameterAxis",
    "ParameterSweepEngine",
    "ResearchPlan",
    "PlannedSimulationUnit",
    "ResearchExecutor",
    "ResearchExecutionResult",
    "ResearchExecutionError",
    "InvalidResearchPlanError",
]
```

---

## 2. Public Domain Classes & Signatures

### 2.1 `PlannedSimulationUnit` (Public Domain Value Object)

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.domain.model.portfolio import Portfolio
    from engine.domain.policies.allocation_policy import AllocationPolicy
    from engine.domain.policies.withdrawal_policy import WithdrawalPolicy
    from research.domain.cohort.specification import CohortSpecification
    from research.domain.parameter.configuration import ParameterConfiguration

@dataclass(frozen=True, slots=True)
class PlannedSimulationUnit:
    """Immutable representation of one planned simulation run within a ResearchPlan.
    
    Canonical identity is the value tuple: (cohort.start_date, parameter_config).
    """

    cohort: CohortSpecification
    parameter_config: ParameterConfiguration
    allocation_policy: AllocationPolicy
    withdrawal_policy: WithdrawalPolicy
    initial_portfolio: Portfolio

    def __post_init__(self) -> None:
        if self.allocation_policy is None:
            raise ValueError("allocation_policy cannot be None")
        if self.withdrawal_policy is None:
            raise ValueError("withdrawal_policy cannot be None")
        if self.initial_portfolio is None:
            raise ValueError("initial_portfolio cannot be None")
```

> **Design Decision (Omission of `unit_id` from Public Contract):**
> `unit_id` is completely omitted from the public domain contract. The canonical identity of a `PlannedSimulationUnit` is strictly the value tuple `(cohort.start_date, parameter_config)`. Any string formatting or hashing used internally for duplicate detection or logging remains an unexposed implementation detail.

---

### 2.2 `ResearchPlan` (Public Research Domain Contract)

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Sequence, Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from research.domain.experiment.definition import ExperimentDefinition
    from research.domain.parameter.configuration import ParameterConfiguration
    from research.domain.plan import PlannedSimulationUnit

@dataclass(frozen=True, slots=True)
class ResearchPlan:
    """Immutable, fully materialised study plan ready for execution by ResearchExecutor."""

    experiment_definition: ExperimentDefinition
    units: tuple[PlannedSimulationUnit, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.units, tuple):
            object.__setattr__(self, "units", tuple(self.units))
        
        if not self.units:
            raise ValueError("ResearchPlan units tuple cannot be empty")
        
        # Verify unit uniqueness based on canonical value tuple (cohort.start_date, parameter_config)
        seen_keys: set[tuple[date, ParameterConfiguration]] = set()
        for idx, unit in enumerate(self.units):
            if not isinstance(unit, PlannedSimulationUnit):
                raise TypeError(f"Unit at index {idx} is not a PlannedSimulationUnit: {type(unit)}")
            key = (unit.cohort.start_date, unit.parameter_config)
            if key in seen_keys:
                raise ValueError(
                    f"Duplicate PlannedSimulationUnit identity detected in plan: "
                    f"cohort={unit.cohort.start_date.isoformat()}, parameter_config={unit.parameter_config}"
                )
            seen_keys.add(key)

    def __len__(self) -> int:
        return len(self.units)

    def __getitem__(self, index: int) -> PlannedSimulationUnit:
        return self.units[index]

    def __iter__(self) -> Iterator[PlannedSimulationUnit]:
        return iter(self.units)
```

---

### 2.3 `ResearchExecutionResult` (Orchestration Output Contract)

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.executor import ExperimentResult, SimulationResult
    from research.domain.plan import ResearchPlan, PlannedSimulationUnit

@dataclass(frozen=True, slots=True)
class ResearchExecutionResult:
    """Lossless execution result maintaining direct 1-to-1 index provenance."""

    plan: ResearchPlan
    experiment_result: ExperimentResult

    def __post_init__(self) -> None:
        if len(self.plan.units) != len(self.experiment_result.results):
            raise ValueError(
                f"Mismatch between plan units ({len(self.plan.units)}) and "
                f"engine results ({len(self.experiment_result.results)})"
            )

    @property
    def results(self) -> tuple[SimulationResult, ...]:
        """Ordered tuple of individual engine SimulationResults matching plan.units."""
        return self.experiment_result.results
```

> **Design Decision (Strictly Minimal Public Contract):**
> `ResearchExecutionResult` exposes **no redundant public representations** or derived pairing structures (such as `plan_unit_results` or custom zip iterators).
>
> 1. **Zero Redundancy:** The object contains only two core, immutable attributes: `plan: ResearchPlan` and `experiment_result: ExperimentResult` (plus a convenience `results` alias pointing to `experiment_result.results`).
> 2. **Positional Provenance Association:** Provenance is strictly index-aligned: `plan.units[i]` maps directly to `experiment_result.results[i]` for all $0 \le i < len(plan)$.
> 3. **Minimal API Surface:** Consumers requiring paired iteration can trivially perform `zip(result.plan.units, result.results)` in caller code. Omitting derived pairing methods keeps the public contract minimal, robust, and free of redundant APIs.

---

### 2.4 `ResearchExecutor` (Orchestration Service)

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.executor import SimulationExecutor
    from research.domain.plan import ResearchPlan
    from research.orchestration.result import ResearchExecutionResult

class ResearchExecutor:
    """Stateless Research Execution Orchestrator."""

    def __init__(self, simulation_executor: SimulationExecutor) -> None:
        if simulation_executor is None:
            raise ValueError("simulation_executor cannot be None")
        self._simulation_executor = simulation_executor

    def execute(self, plan: ResearchPlan) -> ResearchExecutionResult:
        """Executes an immutable ResearchPlan exactly once via SimulationExecutor."""
        if not isinstance(plan, ResearchPlan):
            raise InvalidResearchPlanError(f"Expected ResearchPlan, got {type(plan)}")

        # 1. Defensive structural validation of plan
        if len(plan) == 0:
            raise InvalidResearchPlanError("Cannot execute an empty ResearchPlan")

        # 2. Build frozen engine SimulationContexts in exact unit order
        contexts = []
        for idx, unit in enumerate(plan.units):
            try:
                context = self._create_context_for_unit(plan.experiment_definition, unit)
                contexts.append(context)
            except Exception as err:
                raise InvalidResearchPlanError(
                    f"Failed to translate plan unit {idx} (cohort={unit.cohort.start_date.isoformat()}) to SimulationContext: {err}"
                ) from err

        # 3. Delegate execution to SimulationExecutor
        try:
            exp_result = self._simulation_executor.execute(
                experiment_name=plan.experiment_definition.name,
                experiment_description=plan.experiment_definition.description,
                contexts=tuple(contexts),
            )
        except Exception as err:
            raise ResearchExecutionError(
                f"Execution failed during SimulationExecutor delegation for experiment '{plan.experiment_definition.name}': {err}"
            ) from err

        # 4. Wrap and return result with provenance
        return ResearchExecutionResult(plan=plan, experiment_result=exp_result)

    def _create_context_for_unit(self, experiment_def: ExperimentDefinition, unit: PlannedSimulationUnit) -> SimulationContext:
        """Translates a single PlannedSimulationUnit to a frozen engine SimulationContext."""
        ...
```

---

## 3. Exceptions

```python
class ResearchExecutionError(Exception):
    """Base exception for errors during research plan execution."""
    pass

class InvalidResearchPlanError(ResearchExecutionError):
    """Raised when a ResearchPlan fails structural or translation validation before execution."""
    pass
```

---

## 4. Summary of API Contracts

| Class | Type | Contract Status |
| :--- | :--- | :--- |
| `PlannedSimulationUnit` | Immutable Value Object | Public Research Domain Contract |
| `ResearchPlan` | Immutable Value Object | Public Research Domain Contract |
| `ResearchExecutionResult` | Immutable Value Object | Public Orchestration Output |
| `ResearchExecutor` | Application Service | Public Execution Orchestrator |
| `InvalidResearchPlanError` | Exception | Public Error Contract |
| `ResearchExecutionError` | Exception | Public Error Contract |

**Public API Review Status:** **APPROVED AND FROZEN**.
