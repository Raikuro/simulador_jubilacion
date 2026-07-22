# `ExperimentDefinition` Public API Review

## Purpose

This document defines and freezes the public API contract for `ExperimentDefinition` and `CohortSpecification`, forming the **Public Research Domain Contract** of the Research Layer (`v0.2-research-layer`).

---

## 1. Module Placement & Export Interface

### Canonical File Locations
```text
src/research/domain/cohort/specification.py
src/research/domain/experiment/definition.py
```

### Public Export Contract
```python
# src/research/__init__.py
from research.domain.cohort.specification import CohortSpecification
from research.domain.experiment.definition import ExperimentDefinition

__all__ = [
    "CohortSpecification",
    "ExperimentDefinition",
]
```

External consumers (CLI, notebooks, YAML loaders in `infrastructure`, `ResearchExecutor`, and `v0.3` optimizers) import `CohortSpecification` and `ExperimentDefinition` directly from the top-level `research` package:
```python
from research import CohortSpecification, ExperimentDefinition
```

---

## 2. Public Classes & Signatures

### 2.1 `CohortSpecification` Value Object

```python
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CohortSpecification:
    """Immutable value object representing the specification of a single historical cohort window."""

    start_date: date
    id: str | None = None

    def __post_init__(self) -> None:
        """Validates cohort invariants and generates default ID if omitted."""
        if self.start_date is None:
            raise ValueError("CohortSpecification start_date cannot be None.")
        if self.id is None:
            object.__setattr__(self, "id", self.start_date.isoformat())
        elif not self.id.strip():
            raise ValueError("CohortSpecification id cannot be empty or whitespace.")
```

#### Canonical Identity vs External Identifier
- **Canonical Identity:** The canonical identity of a cohort is strictly its **`start_date`**.
- **Chronological Ordering:** Consumers must **never** rely on `id` for ordering or chronology. Chronological ordering is always determined strictly by `start_date`.
- **Role of `id`:** The `id` is a stable external identifier used exclusively for:
  - Reporting and logging;
  - Data serialization (JSON, YAML, Parquet);
  - Experiment reproducibility and hash auditing;
  - User-facing references.
- **Default Behavior:** If `id` is omitted at construction, it is deterministically derived from `start_date` (`start_date.isoformat()`, e.g. `"1871-01-01"`).

---

### 2.2 `ExperimentDefinition` Blueprint

```python
from dataclasses import dataclass
from typing import Sequence

from engine.domain import AllocationPolicy, Dataset, Money, WithdrawalPolicy


@dataclass(frozen=True)
class ExperimentDefinition:
    """Immutable declarative specification of a quantitative research study.
    
    Serves as the public contract of the Research Layer.
    """

    name: str
    description: str
    dataset: Dataset
    horizon_months: int
    initial_wealth: Money
    cohorts: tuple[CohortSpecification, ...]
    allocation_policies: tuple[AllocationPolicy, ...]
    withdrawal_policies: tuple[WithdrawalPolicy, ...]

    def __post_init__(self) -> None:
        """Coerces sequence inputs to immutable tuples and validates local intrinsic invariants."""
        ...
```

---

## 3. Detailed Field Specifications & Invariants

### `ExperimentDefinition` Fields

| Field Name | Type | Mandatory / Optional | Allowed Value Constraints |
| :--- | :--- | :--- | :--- |
| `name` | `str` | Mandatory | Non-empty string; `name.strip()` must not be empty. |
| `description` | `str` | Mandatory | Non-empty string; `description.strip()` must not be empty. |
| `dataset` | `Dataset` | Mandatory | Valid, non-null `Dataset` reference. |
| `horizon_months` | `int` | Mandatory | Strictly positive integer ($> 0$). |
| `initial_wealth` | `Money` | Mandatory | Valid, non-null `Money` object with positive amount ($> 0$). |
| `cohorts` | `tuple[CohortSpecification, ...]` | Mandatory | Non-empty tuple of unique `CohortSpecification` instances (unique `start_date`). |
| `allocation_policies` | `tuple[AllocationPolicy, ...]` | Mandatory | Non-empty tuple of non-null `AllocationPolicy` instances. |
| `withdrawal_policies` | `tuple[WithdrawalPolicy, ...]` | Mandatory | Non-empty tuple of non-null `WithdrawalPolicy` instances. |

---

## 4. Initialization & Coercion Contract

When initializing an `ExperimentDefinition`:

1. **Defensive Sequence Coercion:** Any sequence (e.g. `list` or `Set`) passed to constructor for `cohorts`, `allocation_policies`, or `withdrawal_policies` must be automatically converted to an immutable `tuple` inside `__post_init__` via `object.__setattr__`:
   ```python
   object.__setattr__(self, "cohorts", tuple(self.cohorts))
   object.__setattr__(self, "allocation_policies", tuple(self.allocation_policies))
   object.__setattr__(self, "withdrawal_policies", tuple(self.withdrawal_policies))
   ```

2. **Intrinsic Local Validation:**
   - Raises `ValueError("ExperimentDefinition name cannot be empty or whitespace.")` if `name` is blank.
   - Raises `ValueError("ExperimentDefinition description cannot be empty or whitespace.")` if `description` is blank.
   - Raises `ValueError("ExperimentDefinition dataset cannot be None.")` if `dataset` is `None`.
   - Raises `ValueError("ExperimentDefinition horizon_months must be positive (> 0).")` if `horizon_months` $\le 0$.
   - Raises `ValueError("ExperimentDefinition initial_wealth must be positive (> 0).")` if `initial_wealth` is `None` or $\le 0$.
   - Raises `ValueError("ExperimentDefinition cohorts cannot be empty.")` if `cohorts` is empty.
   - Raises `ValueError("ExperimentDefinition cohorts contain invalid elements.")` if any element of `cohorts` is not a `CohortSpecification` or is `None`.
   - Raises `ValueError("ExperimentDefinition cohorts contain duplicate start dates.")` if `len(set(c.start_date for c in cohorts)) != len(cohorts)`.
   - Raises `ValueError("ExperimentDefinition allocation_policies cannot be empty.")` if `allocation_policies` is empty or contains `None`.
   - Raises `ValueError("ExperimentDefinition withdrawal_policies cannot be empty.")` if `withdrawal_policies` is empty or contains `None`.

---

## 5. Explicit Contract Exclusions

Per approved architectural reviews:

1. **NO `targets` Field:**
   - The generic `targets` field is **REMOVED**.
   *(Reason: Target objectives belong to consumers like optimizers or analyzers in `v0.3`, not to the execution blueprint.)*

2. **NO Primitive Cohort Strings:**
   - Raw `str` cohort identifiers are replaced by `CohortSpecification` value objects.

3. **NO Derived Execution Metrics:**
   - `total_simulations` property is **EXCLUDED**.
   - `is_single_simulation` property is **EXCLUDED**.

4. **NO Dataset Snapshot Completeness Checks:**
   - Dataset snapshot count verification is **EXCLUDED**.

---

## 6. Structural Equality & Hash Contract

- Both `CohortSpecification` and `ExperimentDefinition` are `@dataclass(frozen=True)` value objects.
- `__eq__(other)`: Evaluates value equality across all fields.
- `__hash__()`: Evaluates deterministic hash for usage as dictionary keys, set elements, and caching entries.

---

## 7. Public API Usage Example

```python
from datetime import date
from engine.domain import Dataset, Money
from engine.domain.policies import StaticAllocationPolicy, ConstantWithdrawalPolicy
from research import CohortSpecification, ExperimentDefinition

# Define explicit cohorts
cohort_1 = CohortSpecification(start_date=date(1871, 1, 1))
cohort_2 = CohortSpecification(start_date=date(1871, 2, 1))

# Construct experiment definition
study = ExperimentDefinition(
    name="ERN Part 19 Reproduction",
    description="Reproduction of Equity Glidepaths vs Static Allocations",
    dataset=historical_dataset,
    horizon_months=360,
    initial_wealth=Money(1_000_000, "USD"),
    cohorts=[cohort_1, cohort_2],
    allocation_policies=[
        StaticAllocationPolicy(equity_ratio=0.6),
        StaticAllocationPolicy(equity_ratio=0.8),
    ],
    withdrawal_policies=[
        ConstantWithdrawalPolicy(annual_rate=0.04),
    ],
)

# Inspect blueprint
assert study.name == "ERN Part 19 Reproduction"
assert isinstance(study.cohorts, tuple)
assert isinstance(study.cohorts[0], CohortSpecification)
assert study.cohorts[0].start_date == date(1871, 1, 1)
assert study.cohorts[0].id == "1871-01-01"
```

---

## Approval Requirement

This document freezes the public API contract for `ExperimentDefinition` and `CohortSpecification`. Implementation is executed strictly against this frozen public interface.
