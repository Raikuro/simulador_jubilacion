# Architectural Review: `CohortGenerator`

## Executive Summary

This document presents the formal architectural review for `CohortGenerator`, the temporal windowing utility of the Research Layer (`v0.2-research-layer`).

The review evaluates responsibility boundaries, ownership, dependency direction, relationships with `Dataset`, `CohortSpecification`, `ExperimentDefinition`, and `ResearchExecutor`, stateless design guarantees, module placement, and future extensibility.

---

## 1. Responsibility Boundaries (Single Responsibility Principle)

`CohortGenerator` adheres strictly to the Single Responsibility Principle.

- **Primary Responsibility:** Translate a `Dataset` and a `horizon_months` constraint into chronologically ordered, horizon-feasible `CohortSpecification` tuples.
- **Explicit Boundary Limits:**
  - It generates and validates **which historical dates** are valid cohort entry points given the dataset's temporal depth.
  - It applies **no** financial logic, portfolio calculations, or market return analysis.
  - It contains **no** experiment design, sampling strategy, or study-specific selection criteria.
  - It performs **no** file I/O, database access, or configuration loading.
  - It does **not** create `SimulationContext`, `ExperimentDefinition`, or any execution-layer objects.

```
┌───────────────────────────────────────────────────────────┐
│                     CohortGenerator                       │
│       (Temporal Windowing & Feasibility Utility)          │
│                                                           │
│  generate_rolling_monthly(dataset, horizon_months)        │
│  generate_range(dataset, horizon_months, start, end)      │
│  from_start_dates(dataset, horizon_months, dates)         │
└──────────────────────────┬────────────────────────────────┘
                           │ Produces
                           ▼
             tuple[CohortSpecification, ...]
```

The three generation strategies share an identical output contract while differing only in their candidate selection and validation semantics:

| Strategy                   | Candidate Selection          | Infeasibility Handling  |
|----------------------------|------------------------------|-------------------------|
| `generate_rolling_monthly` | All dataset snapshot dates   | Silent tail exclusion   |
| `generate_range`           | Dates within `[start, end]`  | Silent tail exclusion   |
| `from_start_dates`         | Explicitly named dates       | Fail-fast `ValueError`  |

---

## 2. Ownership & Lifecycle

- **Owner:** The Research Domain (`research.domain.cohort`).
- **Creation Context:** `CohortGenerator` has **no instance state**. It is a stateless utility implemented entirely via `@staticmethod` methods. It is never instantiated; callers invoke its class-level methods directly.
- **Consumers:**
  - `ResearchExecutor` (v0.2): invokes `CohortGenerator` during study expansion to obtain the concrete `CohortSpecification` sequence for a given `ExperimentDefinition`.
  - Future infrastructure, CLI, or notebook layers that need to enumerate valid cohorts independently of study execution.
- **Lifecycle:** Because `CohortGenerator` is stateless, it has no construction, teardown, or lifecycle management concerns. It cannot be misconfigured, leaked, or left in an inconsistent state.

```
Research Layer ownership hierarchy:

  ExperimentDefinition  (declarative study specification — immutable value object)
          │
          │ referenced by
          ▼
  ResearchExecutor      (execution planning & coordination — consumes both below)
          │
          ├── CohortGenerator (temporal windowing — owns feasibility filtering)
          │         └─ returns tuple[CohortSpecification, ...]
          │
          └── SimulationExecutor (frozen v0.1 engine — via SimulationContext)
```

---

## 3. Dependency Direction

`CohortGenerator` respects strict unidirectional dependency flow:

```
Application / Infrastructure Layer
    ResearchExecutor ──────────────────────────────────────┐
    CLI / Notebooks ────────────────────────────────────┐  │
                                                        │  │
Research Domain [src/research/domain]                   │  │
    ExperimentDefinition ◄──────────────────────────────┘  │
    CohortGenerator ◄──────────────────────────────────────┘
        │ depends on
        ├──► CohortSpecification   (research domain)
        └──► Dataset               (engine domain, frozen v0.1)

Engine Domain [src/engine/domain — Frozen v0.1]
    Dataset  (read-only by CohortGenerator)
```

### Dependency Invariants

1. `CohortGenerator` depends only on `Dataset` (frozen engine domain) and `CohortSpecification` (research domain).
2. `CohortGenerator` has **zero dependencies** on `ExperimentDefinition`, `ResearchExecutor`, `SimulationExecutor`, `SimulationRunner`, `SimulationContext`, or any other research component.
3. The `v0.1` Execution Engine has **zero knowledge** of `CohortGenerator`'s existence. The frozen engine is not touched.
4. `CohortSpecification` has **zero knowledge** of `CohortGenerator`. The value object is passive.
5. `ExperimentDefinition` has **zero knowledge** of `CohortGenerator`. The study specification is passive.

This ensures the dependency graph remains a strict DAG with no cycles.

---

## 4. Component Relationships

### 4.1 Relationship with `Dataset`

- `Dataset` (frozen `v0.1` engine domain model) is `CohortGenerator`'s sole external input dependency.
- `CohortGenerator` reads `dataset.snapshots` to determine valid temporal entry points.
- **Boundary:** `CohortGenerator` never mutates `Dataset` or its snapshots. It reads snapshot dates only to determine feasibility and construct `CohortSpecification` objects. No financial snapshot values (`index_levels`, `inflation`, portfolio metrics, etc.) are accessed.

```
Dataset (frozen engine domain)
   │  read-only access to snapshot dates only
   ▼
CohortGenerator → tuple[CohortSpecification, ...]
```

### 4.2 Relationship with `CohortSpecification`

- `CohortSpecification` is `CohortGenerator`'s sole output type.
- `CohortGenerator` constructs `CohortSpecification` instances using `start_date` extracted from feasible dataset snapshots.
- The external `id` field of `CohortSpecification` defaults to `start_date.isoformat()` when not explicitly provided; `CohortGenerator` relies on this default and never injects a custom id.
- **Boundary:** `CohortGenerator` does not bypass the `CohortSpecification` constructor, alter canonical identity, or inject arbitrary string ids.

### 4.3 Relationship with `ExperimentDefinition`

This relationship must be understood at two distinct levels: **implementation dependency** and **conceptual dependency**.

#### Implementation Dependency (zero)

`CohortGenerator` has **no implementation dependency** on `ExperimentDefinition`:

- It never imports, receives, or stores an `ExperimentDefinition` instance.
- Its method signatures accept only primitive arguments (`Dataset`, `int`, `Sequence[date]`, `date`).
- It can be constructed, tested, and reused in isolation without any `ExperimentDefinition` in scope.

#### Conceptual Dependency (acknowledged)

`ExperimentDefinition` is the declarative description of a research study. `CohortGenerator` exists to **materialise the cohort portion** of that description — translating the study's temporal windowing intent into concrete `CohortSpecification` sequences.

Neither component owns the other. Both are coordinated by higher-level research orchestration:

```
ExperimentDefinition
        │  (declarative study description)
        ▼
ResearchExecutor  (or future planning layer)
        │  coordinates
        ├──► CohortGenerator        (materialises cohort portion)
        └──► ParameterSweepEngine   (materialises policy matrix portion)
```

This preserves dependency inversion while accurately describing the architecture: `CohortGenerator` is not a free-floating utility — it has a defined conceptual role within the Research Layer's execution planning pipeline, even though that role is expressed through primitive arguments rather than direct object coupling.

### 4.4 Relationship with `ResearchExecutor`

- `ResearchExecutor` is the primary consumer of `CohortGenerator` during study execution planning.
- `ResearchExecutor` calls the appropriate `CohortGenerator` strategy based on cohort configuration embedded in `ExperimentDefinition`, then uses the resulting tuple to expand simulation tasks.
- **Boundary:** `CohortGenerator` has zero knowledge of `ResearchExecutor`. The dependency flows strictly from `ResearchExecutor` → `CohortGenerator`, never in reverse.

### 4.5 Relationship with `SimulationContext` and `SimulationRunner`

- `CohortGenerator` has **no relationship** with `SimulationContext` or `SimulationRunner`.
- It produces only `CohortSpecification` objects. The downstream translation from `CohortSpecification` into a `SimulationContext` is the exclusive responsibility of `ResearchExecutor`.
- **Boundary:** The frozen `v0.1` execution engine is completely isolated from `CohortGenerator`.

---

## 5. Stateless Design & Concurrency Guarantees

`CohortGenerator` is implemented as a **pure stateless utility class**:

1. **No Instance State:** All methods are `@staticmethod`. The class holds no fields, caches, or mutable variables.
2. **Referential Transparency:** Given identical `dataset` and `horizon_months` inputs, each strategy returns an identical, deterministic output tuple. No random generators, system clocks, or global variables are consulted.
3. **No Side Effects:** `CohortGenerator` performs no I/O, no network calls, no file writes, and no mutations to its inputs.
4. **Thread & Process Safety:** Because it is stateless and side-effect free, `CohortGenerator` can safely be called concurrently from multiple threads or processes inside `ResearchExecutor` without locks, shared state, or race conditions.
5. **Immutable Output:** The returned `tuple[CohortSpecification, ...]` is immutable. Each `CohortSpecification` element is a frozen dataclass. Consumers cannot alter the generated cohort sequence.

---

## 6. Validation Architecture

The approved split between natural filtering and strict validation reflects the two fundamentally different usage contexts `CohortGenerator` serves:

```
                    Dataset Snapshot Dates
                          │
             ┌────────────┴────────────┐
             │                         │
   Rolling / Range strategy     from_start_dates strategy
   (candidate = all/range dates) (candidate = explicit dates)
             │                         │
   Silent feasibility filter    Strict fail-fast validation
   (tail exclusion, no error)   (missing or infeasible → ValueError)
             │                         │
             └────────────┬────────────┘
                          │
             tuple[CohortSpecification, ...]
               (chronologically ordered,
                horizon-feasible)
```

This split honours a key ergonomic principle:

- **Exploratory / survey use cases** (`generate_rolling_monthly`, `generate_range`) should never fail on partial data; they return what is available. The caller receives a complete picture of what the dataset can support.
- **Reproducibility / exact-cohort use cases** (`from_start_dates`) must guarantee the exact cohorts requested. Silently dropping requested cohorts would corrupt a study's reproducibility contract.

This distinction is intrinsic to `CohortGenerator`'s identity and must be preserved in all future strategy additions.

---

## 7. Module Placement

### Approved Location

```
src/research/domain/cohort/generator.py
```

This placement is correct for the following reasons:

1. **Domain Layer Membership:** `CohortGenerator` is a pure domain utility. It references only domain value objects (`Dataset`, `CohortSpecification`) and applies no infrastructure concerns.
2. **Cohort Package Co-location:** `CohortGenerator` belongs alongside `CohortSpecification` inside `research.domain.cohort`, since it exists to produce and validate `CohortSpecification` sequences. Keeping them co-located makes the package self-contained and cohesive.
3. **No Circular Dependencies:** `generator.py` imports from `specification.py` (same package) and from `engine.domain.model.dataset` (frozen engine domain). Neither imports from `generator.py`.

### Export Surface

```python
# src/research/domain/cohort/__init__.py
from research.domain.cohort.specification import CohortSpecification
from research.domain.cohort.generator import CohortGenerator

# src/research/domain/__init__.py
from research.domain.cohort import CohortSpecification, CohortGenerator

# src/research/__init__.py
from research.domain import CohortSpecification, CohortGenerator
```

Consumers import via the stable public interface:
```python
from research import CohortGenerator, CohortSpecification
```

Internal sub-module layout remains an implementation detail hidden from consumers.

---

## 8. Future Extensibility

`CohortGenerator` is designed for extension without modification:

- **Additional Strategies:** New generation strategies (e.g. `generate_decade_starts`, `generate_crisis_periods`, `generate_cape_conditioned`) are added as additional `@staticmethod` methods without altering existing strategies or their signatures.
- **No Protocol Required:** Because `CohortGenerator` is a pure utility class (not a polymorphic service), no `Protocol` or abstract base class is needed. Strategy selection is a caller responsibility (e.g. `ResearchExecutor` selects the appropriate method based on `ExperimentDefinition` configuration).
- **Dataset Evolution:** If `Dataset` gains additional metadata fields, `CohortGenerator` is unaffected as long as the snapshot date access pattern is preserved.
- **Parallel Execution:** The stateless, side-effect-free design means `CohortGenerator` strategies can be trivially wrapped in parallel map operations if very large datasets require concurrent cohort generation in future milestones.

---

## 9. Architectural Approval Summary

| Concern                    | Verdict                                                                 |
|----------------------------|-------------------------------------------------------------------------|
| Responsibility boundary    | Single: temporal windowing & feasibility filtering only                 |
| Ownership                  | `research.domain.cohort` — pure domain utility                         |
| Dependency direction       | Strictly downward: `CohortGenerator` → `Dataset`, `CohortSpecification`|
| Engine isolation           | Complete — frozen `v0.1` engine is untouched and unaware               |
| Stateless design           | All methods are `@staticmethod`; no instance state                     |
| Concurrency safety         | Guaranteed — referentially transparent, no shared mutable state         |
| Immutable output           | `tuple[CohortSpecification, ...]` — frozen elements, immutable sequence|
| Validation split           | Natural filtering (rolling/range) vs. strict validation (explicit)     |
| Module placement           | `src/research/domain/cohort/generator.py`                               |
| Export surface             | `from research import CohortGenerator`                                  |

---

## Next Immediate Step

Proceed to **Step 3: Public API Review** (`COHORT_GENERATOR_PUBLIC_API.md`).
