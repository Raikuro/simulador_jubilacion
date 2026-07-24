# `CohortGenerator` Public API Review

## Purpose

This document defines and freezes the public API contract for `CohortGenerator`, the temporal windowing utility of the Research Layer (`v0.2-research-layer`).

After approval, implementation proceeds strictly against this frozen public interface.

---

## 1. Module Placement & Export Interface

### Canonical File Location
```text
src/research/domain/cohort/generator.py
```

### Public Export Contract

```python
# src/research/domain/cohort/__init__.py
from research.domain.cohort.specification import CohortSpecification
from research.domain.cohort.generator import CohortGenerator

# src/research/domain/__init__.py
from research.domain.cohort import CohortSpecification, CohortGenerator

# src/research/__init__.py
from research.domain import CohortSpecification, CohortGenerator

__all__ = [
    "CohortSpecification",
    "CohortGenerator",
    "ExperimentDefinition",
]
```

External consumers import via the stable public interface:
```python
from research import CohortGenerator
```

---

## 2. Class Declaration

`CohortGenerator` is a **stateless utility class**. It is never instantiated. All methods are `@staticmethod`. The class body contains no fields, no `__init__`, and no instance state.

```python
from datetime import date
from typing import Sequence

from engine.domain.model.dataset import Dataset
from research.domain.cohort.specification import CohortSpecification


class CohortGenerator:
    """Stateless utility for generating horizon-feasible CohortSpecification sequences.

    Translates historical Dataset snapshots and a simulation horizon into
    chronologically ordered, validated CohortSpecification tuples.

    All methods are @staticmethod. This class is never instantiated.
    """
```

---

## 3. Public Method Signatures

### 3.1 `generate_rolling_monthly`

```python
@staticmethod
def generate_rolling_monthly(
    dataset: Dataset,
    horizon_months: int,
) -> tuple[CohortSpecification, ...]:
    """Generate all horizon-feasible cohorts from the full dataset history.

    Scans dataset.snapshots from the first to the last snapshot date.
    A snapshot at index i is included if and only if:

        len(dataset.snapshots) - i >= horizon_months

    Tail snapshots that cannot satisfy horizon_months are silently excluded.
    No error is raised when tail windows are infeasible.

    Args:
        dataset:        Valid non-null Dataset containing market snapshots.
        horizon_months: Strictly positive integer simulation horizon (> 0).

    Returns:
        Chronologically ordered tuple of CohortSpecification instances,
        one per feasible snapshot date. May be empty only if the entire
        dataset is shorter than horizon_months (in which case ValueError
        is raised on the dataset depth check first).

    Raises:
        ValueError: If dataset is None.
        ValueError: If dataset contains zero snapshots.
        ValueError: If horizon_months <= 0.
        ValueError: If len(dataset.snapshots) < horizon_months.
    """
```

### 3.2 `generate_range`

```python
@staticmethod
def generate_range(
    dataset: Dataset,
    horizon_months: int,
    start_date: date,
    end_date: date,
) -> tuple[CohortSpecification, ...]:
    """Generate feasible cohorts within the closed interval [start_date, end_date].

    Considers only snapshot dates D where start_date <= D <= end_date.
    Within that range, a snapshot at index i is included if and only if:

        len(dataset.snapshots) - i >= horizon_months

    Tail dates inside the range that cannot satisfy horizon_months are silently
    excluded. No error is raised for infeasible tail windows within the range.

    Args:
        dataset:        Valid non-null Dataset containing market snapshots.
        horizon_months: Strictly positive integer simulation horizon (> 0).
        start_date:     Inclusive lower bound of the cohort date range.
        end_date:       Inclusive upper bound of the cohort date range.

    Returns:
        Chronologically ordered tuple of CohortSpecification instances
        for feasible snapshot dates within [start_date, end_date].

    Raises:
        ValueError: If dataset is None.
        ValueError: If dataset contains zero snapshots.
        ValueError: If horizon_months <= 0.
        ValueError: If len(dataset.snapshots) < horizon_months.
        ValueError: If start_date > end_date.
        ValueError: If no snapshots in [start_date, end_date] satisfy horizon_months.
    """
```

### 3.3 `from_start_dates`

```python
@staticmethod
def from_start_dates(
    dataset: Dataset,
    horizon_months: int,
    start_dates: Sequence[date],
) -> tuple[CohortSpecification, ...]:
    """Generate CohortSpecifications for an explicit sequence of start dates.

    Every date in start_dates is strictly validated. Fail-fast semantics apply:
    if any requested date is missing from the dataset or has insufficient
    remaining history, a ValueError is raised immediately.

    This method is intended for reproducibility and exact-cohort use cases
    where partial results would corrupt a study's reproducibility contract.

    Args:
        dataset:        Valid non-null Dataset containing market snapshots.
        horizon_months: Strictly positive integer simulation horizon (> 0).
        start_dates:    Non-empty sequence of explicitly requested start dates.

    Returns:
        Chronologically ordered tuple of CohortSpecification instances,
        one per requested date, in ascending start_date order.

    Raises:
        ValueError: If dataset is None.
        ValueError: If dataset contains zero snapshots.
        ValueError: If horizon_months <= 0.
        ValueError: If len(dataset.snapshots) < horizon_months.
        ValueError: If start_dates is empty.
        ValueError: If any requested date does not exist in dataset.snapshots.
        ValueError: If any requested date exists but has fewer than
                    horizon_months remaining snapshots to dataset end.
    """
```

---

## 4. Method Contracts Summary

| Method                   | Candidate Scope             | Infeasible Tail Handling | Empty Result Allowed | Raises on Missing Date |
|--------------------------|-----------------------------|--------------------------|----------------------|------------------------|
| `generate_rolling_monthly` | All dataset snapshot dates | Silent exclusion         | No (depth guard)     | N/A                    |
| `generate_range`         | Dates in `[start, end]`     | Silent exclusion         | No (`ValueError`)    | N/A                    |
| `from_start_dates`       | Explicitly named dates      | `ValueError` (fail-fast) | No (`ValueError`)    | Yes (`ValueError`)     |

---

## 5. Output Contract

All three methods share an identical output type:

```python
tuple[CohortSpecification, ...]
```

### Guarantee 1 — Ordering

**Every public method returns cohorts ordered by canonical identity (`start_date`) in strict ascending order.**

This guarantee holds unconditionally:

- regardless of the order in which `start_dates` are supplied by the caller;
- regardless of which generation strategy is used;
- regardless of internal implementation details.

Consumers must **never** sort the returned tuple. The ordering guarantee is part of the frozen public contract, not an implementation convenience.

### Guarantee 2 — Uniqueness

**No two `CohortSpecification` objects in the returned tuple represent the same canonical identity (`start_date`).**

This guarantee holds unconditionally:

- regardless of how the caller constructs the input (e.g. duplicate dates in `start_dates` are deduplicated before construction);
- regardless of which generation strategy is used.

Uniqueness is evaluated strictly by `start_date`, consistent with the canonical identity of `CohortSpecification`. The external `id` field plays no role in uniqueness determination.

### Additional Output Invariants

3. **Horizon-Feasibility:** Every `CohortSpecification` in the returned tuple satisfies `horizon_months` remaining dataset history. No infeasible cohort is ever returned.
4. **Immutability:** The returned `tuple` is immutable. Each element is a `@dataclass(frozen=True)` `CohortSpecification`. Consumers cannot alter the sequence or its elements.
5. **Default `id` Assignment:** Each `CohortSpecification` is constructed with `start_date` only. The `id` field defaults to `start_date.isoformat()` via the `CohortSpecification` constructor. `CohortGenerator` never injects a custom `id`.

---

## 6. Validation & Fail-Fast Rules

The following `ValueError` conditions apply across all strategies (unless noted):

| # | Condition                                                      | Strategy Scope          | Error Message (illustrative)                                         |
|---|----------------------------------------------------------------|-------------------------|----------------------------------------------------------------------|
| 1 | `dataset` is `None`                                            | All                     | `"CohortGenerator dataset cannot be None."`                         |
| 2 | `dataset.snapshots` is empty                                   | All                     | `"CohortGenerator dataset contains no snapshots."`                  |
| 3 | `horizon_months <= 0`                                          | All                     | `"CohortGenerator horizon_months must be positive (> 0)."`          |
| 4 | `len(dataset.snapshots) < horizon_months`                      | All                     | `"CohortGenerator dataset is shorter than horizon_months."`         |
| 5 | `start_date > end_date`                                        | `generate_range` only   | `"CohortGenerator start_date must not be after end_date."`          |
| 6 | No snapshot in `[start, end]` satisfies `horizon_months`       | `generate_range` only   | `"CohortGenerator no feasible cohorts found in requested range."`   |
| 7 | `start_dates` is empty                                         | `from_start_dates` only | `"CohortGenerator start_dates cannot be empty."`                    |
| 8 | A requested date is absent from `dataset.snapshots`            | `from_start_dates` only | `"CohortGenerator requested date {D} not found in dataset."`        |
| 9 | A requested date has fewer than `horizon_months` remaining     | `from_start_dates` only | `"CohortGenerator requested date {D} has insufficient horizon."`    |

---

## 7. Determinism Contract

`CohortGenerator` is strictly deterministic:

- Given identical `dataset` snapshots and `horizon_months`, any method produces the same `CohortSpecification` tuple on every call.
- No random generators, system clocks, environment variables, or global state are consulted.
- Determinism is required for study reproducibility: research results must be fully reconstructible from the same inputs.

---

## 8. Explicit API Exclusions

The following are **explicitly excluded** from `CohortGenerator`'s public API:

1. **No `ExperimentDefinition` Parameter:** `CohortGenerator` methods never accept `ExperimentDefinition` as a parameter. `ResearchExecutor` extracts primitive arguments before calling `CohortGenerator`.
2. **No Sampling Strategies:** Random sub-sampling, CAPE-conditioned selection, recession-period filtering, or any study-specific selection criterion has no place in this API.
3. **No Financial Logic:** `CohortGenerator` does not compute returns, valuations, drawdowns, or any portfolio metric.
4. **No Instance Construction:** `CohortGenerator.__init__` is never called. The class is never instantiated.
5. **No I/O:** No file reads, database queries, or network access.

---

## 9. Public API Usage Examples

### Rolling Monthly (exploratory survey)

```python
from research import CohortGenerator

cohorts = CohortGenerator.generate_rolling_monthly(
    dataset=historical_dataset,
    horizon_months=360,
)

# cohorts is a tuple[CohortSpecification, ...] sorted by start_date ascending
# Tail windows shorter than 360 months are silently excluded
print(f"Generated {len(cohorts)} feasible 30-year cohorts")
print(f"First: {cohorts[0].start_date}, Last: {cohorts[-1].start_date}")
```

### Range-Bounded (era-specific study)

```python
from datetime import date
from research import CohortGenerator

cohorts = CohortGenerator.generate_range(
    dataset=historical_dataset,
    horizon_months=360,
    start_date=date(1960, 1, 1),
    end_date=date(1990, 12, 1),
)

# Only feasible cohorts within [1960-01, 1990-12] are returned
print(f"Generated {len(cohorts)} cohorts in the 1960-1990 era")
```

### Explicit Date Windowing (exact reproducibility)

```python
from datetime import date
from research import CohortGenerator

cohorts = CohortGenerator.from_start_dates(
    dataset=historical_dataset,
    horizon_months=360,
    start_dates=[
        date(1929, 9, 1),  # Pre-depression cohort
        date(1966, 1, 1),  # Stagflation-era cohort
        date(2000, 1, 1),  # Dot-com bust cohort
    ],
)

# ValueError is raised if any date is missing or infeasible
# On success, returns exactly 3 CohortSpecifications in ascending order
assert len(cohorts) == 3
assert cohorts[0].start_date == date(1929, 9, 1)
```

---

## 10. Approval Requirement

This document freezes the public API contract for `CohortGenerator`.

Implementation proceeds strictly against this frozen interface. No method signature, output contract, or validation rule may be altered during implementation without returning to this review step.
