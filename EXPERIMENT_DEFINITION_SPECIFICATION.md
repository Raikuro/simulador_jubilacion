# ExperimentDefinition Behavioural Specification

## Purpose

`ExperimentDefinition` is an immutable domain value object representing the pure declarative specification of a scientific research experiment or study in the Research Layer.

It defines **what** research parameters, policy matrices, datasets, and temporal cohort specifications (`CohortSpecification`) constitute a study (e.g., reproducing Early Retirement Now SWR studies).

It separates the declarative blueprint of a research study from execution mechanics and execution planning (which are orchestrated by `ResearchExecutor`), and from study optimization targets (which belong to `v0.3` consumers like `SWROptimizer`).

---

## Responsibilities

`ExperimentDefinition` is responsible for:

- encapsulating all declarative metadata describing a scientific study (name, description, version, metadata);
- referencing the underlying `Dataset` against which historical simulations will be evaluated;
- defining the simulation horizon in months (`horizon_months`);
- defining the base initial financial state for simulations in the study (`initial_wealth`, `initial_portfolio`);
- specifying the sequence of cohort specifications (`cohorts: tuple[CohortSpecification, ...]`);
- specifying the sequence of allocation policies to evaluate (`allocation_policies`);
- specifying the sequence of withdrawal policies to evaluate (`withdrawal_policies`);
- validating intrinsic local invariants at instantiation time to guarantee domain value integrity;
- providing strict value immutability and deterministic identity/equality semantics.

---

## Forbidden Responsibilities

`ExperimentDefinition` must not:

- hold optimization goals or target metrics (e.g., target success rate, target final wealth, target SWR, which belong to `v0.3` optimizers and analyzers);
- use raw primitive strings for cohorts (must use `CohortSpecification` value objects);
- calculate derived execution metrics (e.g., `total_simulations`, `is_single_simulation`, or matrix cross-products);
- execute simulations or invoke `SimulationRunner` / `SimulationExecutor` / `ResearchExecutor`;
- validate external dataset completeness or snapshot counts relative to cohort dates (which belong to `CohortGenerator` and execution planning);
- perform financial calculations, market updates, or portfolio operations;
- modify or mutate dataset snapshots or policy objects after instantiation;
- access external resources such as filesystems, databases, network endpoints, or environment variables;
- depend on infrastructure drivers, serialization libraries, CLI parsers, or plotting tools;
- contain transient runtime state (e.g., progress counters, execution timestamps, or result streams).

---

## Field Specifications & Invariants

| Field | Type | Constraint / Local Invariant | Rationale |
| :--- | :--- | :--- | :--- |
| `name` | `str` | Must be a non-empty, non-whitespace string. | Identifies the study in research catalogs and reports. |
| `description` | `str` | Must be a non-empty string. | Scientific documentation of research intent. |
| `dataset` | `Dataset` | Must be a valid non-null `Dataset` domain object reference. | Source financial market data reference. |
| `horizon_months` | `int` | Must be strictly positive ($> 0$). | Simulation evaluation window in months (e.g. 360 for 30 years). |
| `initial_wealth` | `Money` | Must be strictly positive ($> 0$). | Base starting portfolio balance for all cohorts. |
| `cohorts` | `tuple[CohortSpecification, ...]` | Must be a non-empty sequence of unique `CohortSpecification` instances. | Declarative specifications of temporal windows to backtest. |
| `allocation_policies` | `tuple[AllocationPolicy, ...]` | Must be a non-empty sequence of valid domain allocation policies. | Allocation strategies being evaluated (e.g. static, glidepath). |
| `withdrawal_policies` | `tuple[WithdrawalPolicy, ...]` | Must be a non-empty sequence of valid domain withdrawal policies. | Withdrawal rules being evaluated (e.g. constant, CAPE-based). |

---

## Validation Boundary & Fail-Fast Rules

Instantiation of `ExperimentDefinition` performs strict validation limited to **intrinsic local invariants** during initialization (`__post_init__`). It raises a `ValueError` with a descriptive message if any of the following local conditions are violated:

1. **Empty / Blank Name:** `name` is empty or consists solely of whitespace.
2. **Empty / Blank Description:** `description` is empty or consists solely of whitespace.
3. **Null Dataset Reference:** `dataset` is `None`.
4. **Invalid Horizon:** `horizon_months` $\le 0$.
5. **Invalid Initial Wealth:** `initial_wealth` is `None` or has an amount $\le 0$.
6. **Empty Cohorts:** `cohorts` sequence is empty ($len == 0$).
7. **Invalid Cohort Objects:** `cohorts` contains `None` or non-`CohortSpecification` objects.
8. **Duplicate Cohorts:** `cohorts` contains duplicate `id` entries.
9. **Empty Allocation Policies:** `allocation_policies` sequence is empty ($len == 0$) or contains `None` entries.
10. **Empty Withdrawal Policies:** `withdrawal_policies` sequence is empty ($len == 0$) or contains `None` entries.

### Explicit Validation Exclusions
- **No `targets` Field:** `targets` is removed.
- **No Execution Metrics Validation:** `ExperimentDefinition` does NOT calculate or validate simulation expansion counts.
- **No Dataset Completeness Validation:** `ExperimentDefinition` does NOT inspect snapshot counts or verify if the dataset contains sufficient historical depth for the requested cohorts/horizon. That responsibility is explicitly deferred to `CohortGenerator` and execution planning.

---

## Behavioral Interface

`ExperimentDefinition` provides a clean value object interface:

### 1. Immutability & Structural Equality
- Standard `@dataclass(frozen=True)` behavior.
- Implements `__eq__` based on structural value equality of all fields.
- Implements `__hash__` enabling usage as an immutable key in dictionaries, sets, and caching structures.

---

## Determinism & Identity

Two `ExperimentDefinition` instances created with identical constructor arguments are structurally equal (`exp1 == exp2`) and produce the exact same hash (`hash(exp1) == hash(exp2)`).

No external state, system clock, memory address, or random seeds influence equality or hash evaluation.

---

## Error Handling

Instantiation errors raise standard Python exceptions:
- `ValueError` for invalid local field values (negative horizon, empty policy sequences, blank strings, duplicate cohorts).
- `TypeError` for incorrect argument types.

Expected study construction with valid local parameters will never raise an exception.

---

## Testing Requirements

### Unit Tests
The test suite for `ExperimentDefinition` must verify:

1. **Successful Instantiation:**
   - Valid construction with minimal required fields and `CohortSpecification` instances.
2. **Immutability Enforcement:**
   - Attempting to mutate any attribute (e.g. `exp.horizon_months = 400`) raises `FrozenInstanceError`.
3. **Local Field Validation & Fail-Fast Behavior:**
   - Empty/whitespace `name` raises `ValueError`.
   - Empty/whitespace `description` raises `ValueError`.
   - Null `dataset` raises `ValueError`.
   - Zero or negative `horizon_months` raises `ValueError`.
   - Zero or negative `initial_wealth` raises `ValueError`.
   - Empty `cohorts` list raises `ValueError`.
   - Non-`CohortSpecification` elements in `cohorts` raise `ValueError`.
   - Duplicate `cohorts` IDs raise `ValueError`.
   - Empty `allocation_policies` list raises `ValueError`.
   - Empty `withdrawal_policies` list raises `ValueError`.
4. **Decoupling Verification:**
   - Verify that `ExperimentDefinition` has **no** `targets`, `total_simulations`, or execution-derived properties.
   - Verify that `ExperimentDefinition` does **not** check dataset length or snapshot counts.
5. **Value Equality and Hashing:**
   - Two instances with identical arguments compare equal (`==`).
   - Two instances with identical arguments produce the same `hash()`.
   - Instances can be used as keys in python `set` and `dict`.

---

## Approval Criteria

This updated specification is approved when `ExperimentDefinition` is defined as:

1. A pure, frozen domain value object representing declarative intent only.
2. Using explicit `CohortSpecification` domain objects instead of primitive strings.
3. Free of study targets (`targets`) and derived execution metrics (`total_simulations`).
4. Validating strictly local/intrinsic invariants (no dataset snapshot completeness checks).
5. Completely independent of simulation execution engines, database IO, and plotting libraries.
6. Providing deterministic equality and hash semantics.
