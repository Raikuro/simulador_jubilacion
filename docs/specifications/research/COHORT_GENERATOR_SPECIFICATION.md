# CohortGenerator Behavioural Specification

## Purpose

`CohortGenerator` is a Research Layer component responsible for generating sequences of immutable `CohortSpecification` value objects across historical financial market datasets (`Dataset`).

It translates temporal windowing strategies into concrete, chronologically ordered, validated `CohortSpecification` tuples for use in research studies.

It acts as the feasibility boundary for dataset temporal depth relative to requested simulation horizons (`horizon_months`).

---

## Responsibilities & Scope Boundaries

### Core Responsibilities
`CohortGenerator` owns exclusively:

- **Candidate Generation:** Constructing `CohortSpecification` value objects from dataset snapshots.
- **Chronological Ordering:** Sorting generated cohort sequences strictly in ascending order by canonical `start_date`.
- **Validation of Explicit Requests:** Verifying that user-specified explicit start dates exist in the dataset and have sufficient horizon depth.
- **Horizon Feasibility Filtering:** Identifying which historical snapshot dates possess at least `horizon_months` of remaining market history to complete a simulation.

### Explicit Scope Boundaries
- **No Research Sampling:** `CohortGenerator` does **not** implement higher-level research sampling strategies (e.g. random sub-sampling, recession-only cohorts, CAPE-conditioned sampling, or stress-period filtering). Higher-level research components construct custom studies on top of `CohortGenerator` output.

---

## Forbidden Responsibilities

`CohortGenerator` must not:

- execute simulations or invoke `SimulationRunner` / `SimulationExecutor` / `ResearchExecutor`;
- create `SimulationContext` or `ExperimentDefinition` objects;
- mutate `Dataset` instances or market snapshots;
- calculate financial returns, portfolio valuations, or policy decisions;
- perform file I/O, database access, or environment configuration loading;
- alter dataset snapshot ordering or filter market data beyond horizon feasibility.

---

## Strategy Specifications & Filtering Semantics

### 1. Rolling Monthly Generation (`generate_rolling_monthly`)
- **Behavior:** Scans `dataset.snapshots` sequentially from start date to end date.
- **Filtering Rule (Silent Tail Exclusion):** A snapshot at index $i$ with date $D_i$ is included as a valid cohort if and only if the remaining number of snapshots from index $i$ to the dataset end is $\ge \text{horizon\_months}$:
  $$\text{len}(\text{dataset.snapshots}) - i \ge \text{horizon\_months}$$
- **Error Behavior:** Does **not** raise an error when tail snapshots lack remaining history; tail snapshots are naturally excluded.
- **Ordering:** Returned tuple is sorted strictly in ascending order of `start_date`.

### 2. Range-Bounded Generation (`generate_range`)
- **Behavior:** Generates cohorts for snapshot dates falling within the closed interval $[\text{start\_date}, \text{end\_date}]$.
- **Filtering Rule (Feasibility Exclusion):** Candidates within the range that satisfy $\text{len}(\text{dataset.snapshots}) - i \ge \text{horizon\_months}$ are included. Tail dates in the range that cannot satisfy `horizon_months` are silently excluded.
- **Error Behavior:** Raises `ValueError` if `start_date > end_date` or if no snapshots in the range satisfy `horizon_months`.

### 3. Explicit Date Windowing (`from_start_dates`)
- **Behavior:** Accepts an explicit sequence of user-requested `date` objects (`start_dates`).
- **Validation Rule (Fail-Fast Validation):**
  - Every explicitly requested date $D$ in `start_dates` is strictly validated.
  - If any date $D$ does not exist in `dataset`, raise `ValueError`.
  - If any date $D$ has fewer than `horizon_months` remaining snapshots to dataset end, raise `ValueError`.
- **Ordering:** Returned tuple is sorted strictly in ascending order of `start_date`.

---

## Input & Output Contracts

### Inputs
- `dataset: Dataset`: Valid non-null domain `Dataset` object.
- `horizon_months: int`: Strictly positive integer ($> 0$).
- Strategy-specific parameters (e.g. `start_dates: Sequence[date]`, or range bounds `start_date: date`, `end_date: date`).

### Output
- `tuple[CohortSpecification, ...]`: Chronologically sorted, immutable tuple of valid `CohortSpecification` instances.

---

## Fail-Fast & Validation Rules

`CohortGenerator` raises a `ValueError` with a descriptive message in the following cases:

1. **Null Dataset:** `dataset` is `None`.
2. **Empty Dataset:** `dataset` contains zero market snapshots.
3. **Invalid Horizon:** `horizon_months` $\le 0$.
4. **Insufficient Total Dataset Depth:** `len(dataset.snapshots) < horizon_months`.
5. **No Feasible Cohorts:** No snapshot in the dataset satisfies `horizon_months` for the requested strategy/range.
6. **Explicit Date Missing (for `from_start_dates`):** An explicitly requested date is not found in `dataset.snapshots`.
7. **Explicit Date Infeasible (for `from_start_dates`):** An explicitly requested date exists in `dataset.snapshots`, but has fewer than `horizon_months` remaining snapshots.
8. **Invalid Date Range (for `generate_range`):** `start_date > end_date`.

---

## Behavioral Interface

```python
class CohortGenerator:
    """Generates and validates CohortSpecification sequences across historical Datasets."""

    @staticmethod
    def generate_rolling_monthly(
        dataset: Dataset,
        horizon_months: int,
    ) -> tuple[CohortSpecification, ...]:
        ...

    @staticmethod
    def from_start_dates(
        dataset: Dataset,
        horizon_months: int,
        start_dates: Sequence[date],
    ) -> tuple[CohortSpecification, ...]:
        ...

    @staticmethod
    def generate_range(
        dataset: Dataset,
        horizon_months: int,
        start_date: date,
        end_date: date,
    ) -> tuple[CohortSpecification, ...]:
        ...
```

---

## Determinism & Identity

`CohortGenerator` is strictly deterministic and side-effect free:
- Given identical `dataset` snapshots and `horizon_months`, calls produce identical `CohortSpecification` tuples.
- No random generators, system timestamps, or global state affect generation.

---

## Testing Requirements

### Unit Tests
The unit test suite for `CohortGenerator` must verify:

1. **Rolling Monthly Generation:**
   - Correctly excludes tail snapshots shorter than `horizon_months` without raising an error.
   - For a dataset of 100 snapshots and horizon of 36 months, produces exactly 65 cohorts.
   - Cohort dates match dataset snapshot dates in ascending order.
2. **Explicit Date Windowing:**
   - Valid requested dates produce corresponding `CohortSpecification` objects.
   - Requesting a date missing from dataset raises `ValueError`.
   - Requesting a date with insufficient remaining horizon raises `ValueError`.
3. **Range-Bounded Generation:**
   - Correctly includes valid cohorts in $[\text{start\_date}, \text{end\_date}]$ and excludes infeasible tail dates.
   - Raises `ValueError` when `start_date > end_date`.
4. **Boundary Validations:**
   - `dataset = None` or empty dataset raises `ValueError`.
   - `horizon_months <= 0` raises `ValueError`.
   - Dataset shorter than `horizon_months` raises `ValueError`.

---

## Approval Criteria

This specification is approved when `CohortGenerator` is defined as:

1. A stateless utility component producing immutable `CohortSpecification` tuples.
2. Differentiating between natural feasibility filtering (rolling/range generation) and strict fail-fast validation (explicit date requests).
3. Owning exclusively candidate generation, ordering, explicit validation, and horizon feasibility filtering.
4. Leaving higher-level research sampling strategies to upstream research components.
5. Fully decoupled from execution engines, financial models, and I/O infrastructure.
