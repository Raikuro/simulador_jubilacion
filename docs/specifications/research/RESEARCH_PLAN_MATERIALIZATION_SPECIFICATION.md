# Research Plan Materialization Specification

**Document Type:** Behavioral Specification (Frozen)  
**Status:** APPROVED & FROZEN  
**Milestone:** v0.4 Infrastructure & Deployment (Multi-cohort execution support)  
**Responsibility:** Define the contract for materializing an immutable ResearchPlan from study components  

---

## 1. Purpose

This specification defines the **exact behavior and semantics** of research plan materialization — the process of constructing a fully-materialized, immutable `ResearchPlan` from research study components.

It establishes:
- The ownership boundary between planning (plan construction) and execution (ResearchExecutor)
- The complete input and output contracts for plan materialization
- How dataset slicing is performed at the cohort level
- Caching and deduplication semantics for sliced datasets
- Preservation of dataset identity and version semantics
- The Cartesian product ordering of planned units
- Determinism guarantees

---

## 2. Architectural Context

### 2.1 Planning vs. Execution Boundary

The research workflow is intentionally split into two ownership phases:

```text
ExperimentDefinition + cohorts + parameter configurations
        + allocation/withdrawal policies + initial portfolio
                         │
                         ▼
          PLANNING / MATERIALIZATION BOUNDARY
                         │
                         ▼
          materialize_research_plan()
                         │
                         ▼
                    ResearchPlan
                (fully materialized units)
                         │
                         ▼
          EXECUTION BOUNDARY
                         │
                         ▼
                 ResearchExecutor
                (never modifies plan)
                         │
                         ▼
             SimulationExecutor
                (v0.1 engine)
```

**Ownership Invariant:** `materialize_research_plan()` is responsible for all plan construction, including dataset slicing and policy materialization. `ResearchExecutor` accepts a pre-constructed plan and **never** builds, modifies, or regenerates it.

---

## 3. Function Signature and Inputs

### 3.1 Complete Signature

```python
def materialize_research_plan(
    experiment_def: ExperimentDefinition,
    cohorts: tuple[CohortSpecification, ...],
    param_configs: tuple[ParameterConfiguration, ...],
    alloc_policy: AllocationPolicy,
    withdrawal_policy: WithdrawalPolicy,
    initial_portfolio: Portfolio,
) -> ResearchPlan:
    """Build a ResearchPlan with cohort-sliced Dataset objects.

    Uses a local cache keyed by cohort start date to ensure each cohort's dataset
    is sliced exactly once, and all parameter sweep units for the same cohort share
    the exact same sliced Dataset instance.
    """
```

### 3.2 Input Contracts

#### `experiment_def: ExperimentDefinition`
- **Requirement:** Valid, non-null ExperimentDefinition
- **Purpose:** Source of shared study metadata
- **Used For:**
  - `experiment_def.name` — study identity
  - `experiment_def.description` — study documentation
  - `experiment_def.dataset` — full historical dataset (to be sliced per cohort)
  - `experiment_def.horizon_months` — simulation window length in months
  - `experiment_def.initial_wealth` — base portfolio value (independent of plan cohort)
- **Invariant:** Must not be mutated during materialization

#### `cohorts: tuple[CohortSpecification, ...]`
- **Requirement:** Non-empty ordered tuple of unique cohort specifications
- **Ordering:** Cohorts are processed in provided order (typically chronological)
- **Identity:** Cohort identity is `cohort.start_date`; no duplicate dates
- **Purpose:** Defines the temporal windows (historical cohorts) to execute
- **Processing:** Each cohort generates an independent sliced dataset from `experiment_def.dataset`
- **Invariant:** Cohorts must not be modified during materialization

#### `param_configs: tuple[ParameterConfiguration, ...]`
- **Requirement:** Non-empty ordered tuple of parameter configurations
- **Ordering:** Configurations are processed in provided order (typically from ParameterSweepEngine)
- **Identity:** Configuration identity is its contents (parameters)
- **Purpose:** Defines the parameter sweep (e.g., allocation percentages, withdrawal rates)
- **Cartesian Product:** For each cohort, every configuration is paired with it
- **Invariant:** Configurations must not be modified during materialization

#### `alloc_policy: AllocationPolicy`
- **Requirement:** Concrete, fully-materialized allocation policy instance
- **Scope:** Shared across ALL planned units (single policy for all cohorts + configurations)
- **Invariant:** Must not be modified; passed through to each unit unchanged

#### `withdrawal_policy: WithdrawalPolicy`
- **Requirement:** Concrete, fully-materialized withdrawal policy instance
- **Scope:** Shared across ALL planned units (single policy for all cohorts + configurations)
- **Invariant:** Must not be modified; passed through to each unit unchanged

#### `initial_portfolio: Portfolio`
- **Requirement:** Concrete, fully-materialized initial portfolio (immutable engine Portfolio)
- **Scope:** Shared across ALL planned units (single portfolio for all cohorts + configurations)
- **Purpose:** Base starting portfolio for all simulations (independent of cohort)
- **Invariant:** Must not be modified; passed through to each unit unchanged
- **Ownership:** Portfolio materialization belongs to the planning boundary; plan simply carries it forward

---

## 4. Materialization Process

### 4.1 Step 1: Cohort-Level Dataset Slicing

For each cohort in `cohorts`:

1. **Compute slice bounds:**
   - `start_date = cohort.start_date`
   - `end_date = start_date + experiment_def.horizon_months` months

2. **Slice the experiment dataset:**
   ```python
   sliced_dataset = experiment_def.dataset.slice(
       start_date,
       experiment_def.horizon_months
   )
   ```

3. **Semantics:**
   - The sliced dataset contains exactly `horizon_months` monthly snapshots starting from `start_date`
   - The sliced dataset **preserves `identifier` and `version`** from the original dataset (dataset identity is not changed by slicing)
   - Raises `ValueError` if `start_date` is not in the dataset or if there are insufficient snapshots

### 4.2 Step 2: Dataset Caching and Deduplication

To avoid redundant slicing:

1. **Local cache keyed by cohort start date:**
   ```python
   dataset_cache: dict[date, Dataset] = {}
   ```

2. **Before creating a unit for a cohort:**
   - If `cohort.start_date` is NOT in cache:
     - Perform the slice operation (Step 1)
     - Store result in cache: `dataset_cache[cohort.start_date] = sliced_dataset`
   - Retrieve cached dataset: `sliced_dataset = dataset_cache[cohort.start_date]`

3. **Guarantee:**
   - Each unique cohort start date has its dataset sliced exactly once
   - All parameter sweep units for the same cohort **share the identical Dataset instance**
   - This ensures efficient memory usage and deterministic unit construction

### 4.3 Step 3: Unit Materialization (Cartesian Product)

For each cohort in `cohorts`:
  - For each parameter configuration in `param_configs`:

1. **Retrieve cohort's sliced dataset from cache**
2. **Construct a new PlannedSimulationUnit:**
   ```python
   unit = PlannedSimulationUnit(
       cohort=cohort,
       parameter_config=param_config,
       allocation_policy=alloc_policy,
       withdrawal_policy=withdrawal_policy,
       initial_portfolio=initial_portfolio,
       dataset=sliced_dataset,  # Cohort-aligned, preserved identity
   )
   ```
3. **Append to units list**

### 4.4 Step 4: Plan Construction

After all units are materialized:

1. **Convert units list to immutable tuple**
2. **Construct ResearchPlan:**
   ```python
   return ResearchPlan(
       experiment_definition=experiment_def,
       units=tuple(units),
   )
   ```

3. **ResearchPlan validates:**
   - Non-empty units tuple
   - Each unit is a valid PlannedSimulationUnit
   - No duplicate unit identities (checked by ResearchPlan.__post_init__)

---

## 5. Output Contract

### 5.1 ResearchPlan Structure

The returned `ResearchPlan` contains:

- **experiment_definition:** The original, unmodified ExperimentDefinition
- **units:** An ordered, immutable tuple of PlannedSimulationUnit objects

Each PlannedSimulationUnit contains:

- **cohort:** The cohort specification (unmodified)
- **parameter_config:** The parameter configuration (unmodified)
- **allocation_policy:** The shared allocation policy (unmodified)
- **withdrawal_policy:** The shared withdrawal policy (unmodified)
- **initial_portfolio:** The shared initial portfolio (unmodified)
- **dataset:** A cohort-aligned, sliced Dataset with preserved `identifier` and `version`

### 5.2 Execution Readiness Guarantee

Every unit in the returned plan satisfies the "execution-ready" contract:

- ✓ All required fields are present and valid
- ✓ No mutable state
- ✓ No missing or None values
- ✓ Dataset is sliced to the correct horizon_months for this cohort
- ✓ Dataset identity (identifier + version) is preserved from the original
- ✓ Policies and portfolio are fully materialized and ready for engine execution
- ✓ Unit can be translated directly to a SimulationContext without further processing

---

## 6. Unit Ordering and Cardinality

### 6.1 Deterministic Ordering

For inputs:
- Cohorts C₀, C₁, ..., C_{m-1} (m cohorts, in provided order)
- Configurations P₀, P₁, ..., P_{n-1} (n configurations, in provided order)

The units tuple contains exactly m × n units in this order:

```text
(C₀, P₀), (C₀, P₁), ..., (C₀, P_{n-1}),
(C₁, P₀), (C₁, P₁), ..., (C₁, P_{n-1}),
...
(C_{m-1}, P₀), (C_{m-1}, P₁), ..., (C_{m-1}, P_{n-1})
```

**Invariant:** Cohorts vary slowest (outer loop); configurations vary fastest (inner loop).

### 6.2 Cardinality

```
|ResearchPlan.units| = |cohorts| × |param_configs|
```

No subset filtering or selection occurs during materialization; the complete Cartesian product is materialized.

---

## 7. Dataset Identity and Version Preservation

### 7.1 Preservation Through Slicing

The `Dataset.slice()` method preserves `identifier` and `version`:

```python
sliced = full_dataset.slice(start_date, horizon_months)
assert sliced.identifier == full_dataset.identifier
assert sliced.version == full_dataset.version
assert sliced.frequency == full_dataset.frequency
```

### 7.2 Semantics in Materialization

1. **External Resource Identity:** The `identifier` field represents where the data came from (e.g., filename stem or dataset registry key)
2. **Preservation:** Slicing does not change the external resource; only the time window changes
3. **Persistence:** When the plan is executed and results are persisted, `identifier` is stored for dataset reconstruction

### 7.3 Version Fallback

The `version` field is preserved for datasets without an explicit `identifier`:

- If `identifier` is not None: `identifier` is the canonical persistence key
- If `identifier` is None: `version` is the fallback persistence key
- Slicing preserves both, maintaining backward compatibility

---

## 8. Error Handling and Rejection Criteria

### 8.1 Input Validation Failures

The following errors are raised **before** any ResearchPlan is constructed:

#### Invalid Experiment Definition
- `experiment_def` is None or not an ExperimentDefinition instance
- `experiment_def.dataset` is None or invalid

#### Invalid Cohorts
- `cohorts` is empty
- A cohort's `start_date` is not present in `experiment_def.dataset`
- A cohort's `start_date` requires more than `horizon_months` snapshots but insufficient history exists

#### Invalid Configurations
- `param_configs` is empty
- A configuration is None or not a valid ParameterConfiguration

#### Invalid Policies
- `alloc_policy` is None or not a valid AllocationPolicy
- `withdrawal_policy` is None or not a valid WithdrawalPolicy

#### Invalid Portfolio
- `initial_portfolio` is None or not a valid engine Portfolio

### 8.2 Unit Construction Failures

If any unit cannot be constructed:

- PlannedSimulationUnit validation fails (missing or invalid field)
- Raises the exception from PlannedSimulationUnit.__post_init__ without recovering

### 8.3 Slicing Failures

If `Dataset.slice()` raises an error:

- `start_date` not found: `ValueError("Start date ... not found in dataset")`
- Insufficient snapshots: `ValueError("Insufficient dataset history starting from ...")`
- These errors propagate; the function does not retry or substitute datasets

---

## 9. Determinism and Reproducibility

### 9.1 Determinism Guarantee

Given:
- Identical `experiment_def` (same dataset, horizon, etc.)
- Identical `cohorts` (same order, dates, and specifications)
- Identical `param_configs` (same order and values)
- Identical `alloc_policy` and `withdrawal_policy` instances
- Identical `initial_portfolio` instance

The function produces a ResearchPlan with:

- ✓ Identical units in identical order
- ✓ Each unit has identical field values
- ✓ Sliced datasets have identical snapshots
- ✓ Dataset identity (`identifier`, `version`) is identical

### 9.2 No Randomness or Side Effects

The function:

- Does not use randomness or system time
- Does not depend on filesystem, network, or environment state
- Does not cache results across calls
- Does not modify input parameters
- Does not produce side effects observable to callers

---

## 10. Caching and Performance Implications

### 10.1 Local Cache Scope

The `dataset_cache` is:

- Local to a single call to `materialize_research_plan()`
- Not shared across multiple function calls
- Discarded after the function returns
- Purely an implementation detail for avoiding redundant slicing

### 10.2 Dataset Sharing Within a Plan

All units sharing a cohort's `start_date`:

- Point to the exact same Dataset instance (identity-preserved through cache)
- Share memory for snapshots
- Benefit from efficient representation of identical data

### 10.3 Multi-Plan Isolation

Two separate calls to `materialize_research_plan()`:

- Produce independent Dataset instances (not shared, even if sliced identically)
- Have independent caches
- Do not interfere with each other

---

## 11. Relationship to Other Components

### 11.1 ExperimentDefinition

- Used as-is; not modified or validated beyond basic None checks
- `dataset` field is the authoritative source of full historical market data
- All other fields (`horizon_months`, `name`, `description`) pass through to the plan

### 11.2 CohortGenerator

- Typically the source of `cohorts` input
- Materializer accepts cohorts in any order (processes them as provided)
- No dependency on how cohorts were generated; only their start dates matter

### 11.3 ParameterSweepEngine

- Typically the source of `param_configs` input
- Materializer accepts configurations in any order
- Cartesian product order is determined by the Cartesian order of inputs

### 11.4 ResearchExecutor

- Receives the output ResearchPlan
- Never calls `materialize_research_plan()`
- Assumes the plan is fully materialized and execution-ready
- Translates units to SimulationContext; never creates new units

### 11.5 Dataset Model

- `Dataset.slice()` is the mechanism for cohort-level slicing
- Slice operations preserve `identifier` and `version`
- Slicing is deterministic and side-effect-free

---

## 12. Testing Requirements

### 12.1 Construction and Basic Materialization

- [x] Valid inputs produce a valid ResearchPlan
- [x] ResearchPlan units count equals `|cohorts| × |param_configs|`
- [x] Units are in Cartesian product order (cohorts outer, configs inner)

### 12.2 Dataset Slicing

- [x] Each cohort's dataset is sliced at its start_date
- [x] Sliced dataset has exactly horizon_months snapshots
- [x] Dataset identifier is preserved through slicing
- [x] Dataset version is preserved through slicing
- [x] Dataset frequency is preserved through slicing

### 12.3 Dataset Caching and Deduplication

- [x] Multiple units for the same cohort share the same Dataset instance
- [x] Each cohort's dataset is sliced exactly once (verified by monitoring slice call count)
- [x] No unnecessary slicing occurs

### 12.4 Error Handling

- [x] Empty cohorts raises error
- [x] Empty param_configs raises error
- [x] Invalid start_date (not in dataset) raises ValueError
- [x] Insufficient snapshots (< horizon_months) raises ValueError
- [x] None experiment_def raises error
- [x] None policies raise error
- [x] None initial_portfolio raises error

### 12.5 Determinism and Reproducibility

- [x] Identical inputs produce identical ResearchPlan (field-by-field equality)
- [x] Multiple calls with same inputs produce results with same units in same order
- [x] No randomness in unit construction

### 12.6 Immutability and Non-Mutation

- [x] Input parameters are not modified
- [x] Returned plan is immutable (frozen dataclass)
- [x] Units in plan are immutable
- [x] Datasets in units are immutable

---

## 13. Approval Criteria

This specification is approved when `materialize_research_plan()` is verified to:

1. Accept all required input contracts and validate them correctly
2. Perform cohort-level dataset slicing using `Dataset.slice()`
3. Cache sliced datasets by cohort start date to avoid duplication
4. Preserve dataset identity (`identifier`, `version`) through slicing
5. Construct PlannedSimulationUnit objects with all required fields
6. Generate units in Cartesian product order (cohorts outer, configs inner)
7. Return an immutable, execution-ready ResearchPlan
8. Be deterministic, with no randomness or side effects
9. Reject invalid inputs with appropriate error messages
10. Pass all verification tests without modification to the specification

---

**Specification Status:** APPROVED & FROZEN  
**Implementation Ready:** YES  
**Next Gate:** ResearchExecutor execution of materialized plans
