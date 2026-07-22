# Architectural Review: `ParameterSweepEngine`

## Executive Summary

This document presents the formal architectural review for `ParameterSweepEngine` and its accompanying value objects (`ParameterConfiguration`, `ParameterAxis`), the parameter-space generation subsystem of the Research Layer (`v0.2-research-layer`, Sub-Milestone `v0.2.2`).

The review evaluates responsibility boundaries, ownership, dependency direction, relationships with peer and future research components, domain-agnostic content rules, stateless design guarantees, module placement, and future extensibility.

**Baseline:** Behavioural specification `PARAMETER_SWEEP_ENGINE_SPECIFICATION.md` is **frozen and approved**.

---

## 1. Responsibility Boundaries (Single Responsibility Principle)

`ParameterSweepEngine` adheres strictly to the Single Responsibility Principle.

- **Primary Responsibility:** Translate one or more named parameter axes into a deterministic, ordered Cartesian product of domain-agnostic `ParameterConfiguration` points.
- **Explicit Boundary Limits:**
  - It generates **which primitive parameter assignments** form the research grid.
  - It applies **no** financial logic, portfolio calculations, or market analysis.
  - It constructs **no** `AllocationPolicy` or `WithdrawalPolicy` instances.
  - It performs **no** study matrix expansion with cohorts or horizons.
  - It performs **no** file I/O, database access, or configuration loading.
  - It does **not** create `SimulationContext`, `ExperimentDefinition`, or any execution-layer objects.

```
┌──────────────────────────────────────────────────────────────┐
│                   ParameterSweepEngine                       │
│     (Parameter-Space Grid Generation Utility)                │
│                                                              │
│  axis_from_values(name, values) → ParameterAxis              │
│  axis_from_range(name, start, stop, step) → ParameterAxis    │
│  cartesian_product(axes) → tuple[ParameterConfiguration, ...]│
│  generate(axes) → tuple[ParameterConfiguration, ...]         │
└──────────────────────────────┬───────────────────────────────┘
                               │ Produces
                               ▼
              tuple[ParameterConfiguration, ...]
              (primitive name→value bindings only)
```

### Separation of three architectural concerns

| Concern | Owner | Explicit non-owner |
| :--- | :--- | :--- |
| **Parameter-space generation** | `ParameterSweepEngine` | `ResearchExecutor`, Execution Engine |
| **Policy materialisation** (`ParameterConfiguration` → policies) | `ResearchExecutor` / future policy factory | `ParameterSweepEngine`, `ParameterConfiguration` |
| **Simulation execution** | `SimulationRunner` (frozen v0.1) | Entire Research Layer generators |

This three-way split is a permanent architectural invariant of `v0.2.2` and beyond.

### Value-object responsibility split

| Type | Responsibility | Lifecycle |
| :--- | :--- | :--- |
| `ParameterConfiguration` | Long-lived Public Research Domain Contract: immutable, domain-agnostic named assignment of primitive scalars | Survives generation; used as identity/key by executor, aggregator, comparator, optimizer |
| `ParameterAxis` | Public construction helper: validated named dimension for product input | Short-lived; discarded after product expansion |

---

## 2. Ownership & Lifecycle

- **Owner:** The Research Domain (`research.domain.parameter`).
- **Creation Context:** `ParameterSweepEngine` has **no instance state**. It is a stateless utility implemented entirely via `@staticmethod` methods. It is never instantiated; callers invoke its class-level methods directly.
- **Consumers:**
  - `ResearchExecutor` (v0.2.2): primary consumer during study expansion; obtains parameter grids and owns policy materialisation.
  - `SWROptimizer` / `StrategyComparator` (v0.3): may generate or reuse grids for search and comparison.
  - Infrastructure, CLI, or notebook layers that enumerate parameter spaces independently of full study execution.
- **Lifecycle:** Because `ParameterSweepEngine` is stateless, it has no construction, teardown, or lifecycle management concerns. Emitted `ParameterConfiguration` instances are immutable value objects owned by the caller after return.

```
Research Layer ownership hierarchy:

  ExperimentDefinition  (declarative study specification — immutable)
          │
          │ referenced by
          ▼
  ResearchExecutor      (execution planning, policy materialisation, coordination)
          │
          ├── CohortGenerator        (temporal windowing)
          │         └─ returns tuple[CohortSpecification, ...]
          │
          ├── ParameterSweepEngine   (parameter-space generation)
          │         └─ returns tuple[ParameterConfiguration, ...]
          │                    │
          │                    └── ResearchExecutor / policy factory
          │                              materialises → AllocationPolicy / WithdrawalPolicy
          │
          └── SimulationRunner (frozen v0.1 engine — via SimulationContext)
```

---

## 3. Dependency Direction

`ParameterSweepEngine` respects strict unidirectional dependency flow:

```
Application / Infrastructure Layer
    ResearchExecutor ──────────────────────────────────────────┐
    CLI / Notebooks / SWROptimizer ─────────────────────────┐  │
                                                            │  │
Research Domain [src/research/domain]                       │  │
    ExperimentDefinition ◄──────────────────────────────────┘  │
    ParameterSweepEngine ◄─────────────────────────────────────┘
        │ depends on (same package only)
        ├──► ParameterConfiguration   (research domain contract)
        └──► ParameterAxis            (construction helper)

Engine Domain [src/engine/domain — Frozen v0.1]
    (no dependency from ParameterSweepEngine)
```

### Dependency Invariants

1. `ParameterSweepEngine` depends **only** on Python standard types and its co-located value objects (`ParameterAxis`, `ParameterConfiguration`).
2. `ParameterSweepEngine` has **zero dependencies** on:
   - `ExperimentDefinition`
   - `CohortGenerator` / `CohortSpecification`
   - `AllocationPolicy` / `WithdrawalPolicy`
   - `SimulationRunner` / `SimulationExecutor` / `SimulationContext`
   - `Dataset`, `Money`, portfolio services, or any other engine domain type
3. The `v0.1` Execution Engine has **zero knowledge** of `ParameterSweepEngine`.
4. `ParameterConfiguration` has **zero knowledge** of the engine, of policies, or of `ParameterSweepEngine`.
5. `ParameterAxis` has **zero knowledge** of configurations' downstream use.

This ensures the dependency graph remains a strict DAG with no cycles and **no engine-domain coupling** for the sweep subsystem (stronger isolation than `CohortGenerator`, which legitimately reads `Dataset` dates).

---

## 4. Component Relationships

### 4.1 Relationship with `ParameterConfiguration`

- `ParameterConfiguration` is the **sole long-lived output type** of product expansion.
- It is a Public Research Domain Contract: immutable, hashable, domain-agnostic, execution-agnostic.
- Content is restricted to primitive name→value bindings (`int`, `float`, `bool`, `str`).
- **Boundary:** `ParameterSweepEngine` constructs configurations via their public constructor only. It never injects policies, cohorts, experiment references, or execution handles into them.

### 4.2 Relationship with `ParameterAxis`

- `ParameterAxis` is the validated input dimension for multi-axis products.
- Produced by `axis_from_values` / `axis_from_range`; consumed by `cartesian_product` / `generate`.
- **Boundary:** Axes are not result keys. They must not appear in aggregation identity, optimizer result tables, or reproducibility fingerprints as substitutes for `ParameterConfiguration`.

### 4.3 Relationship with `ExperimentDefinition`

#### Implementation dependency (zero)

`ParameterSweepEngine` never imports, receives, or stores an `ExperimentDefinition`.

#### Conceptual dependency (acknowledged)

`ExperimentDefinition` is the declarative study blueprint. `ParameterSweepEngine` materialises the **parameter-matrix portion** of research intent in the same conceptual role that `CohortGenerator` materialises the cohort portion. Coordination is performed exclusively by higher-level orchestration:

```
ExperimentDefinition
        │
        ▼
ResearchExecutor
        │
        ├──► CohortGenerator         (cohort portion)
        └──► ParameterSweepEngine    (parameter portion)
```

`ExperimentDefinition` currently holds already-materialised policy tuples. That does not force `ParameterSweepEngine` to produce policies; materialisation remains outside the sweep engine.

### 4.4 Relationship with `CohortGenerator`

- **Peer components.** Zero implementation coupling.
- Both are pure generators coordinated only by `ResearchExecutor`.
- Orthogonal axes of the study matrix: time (`CohortSpecification`) vs parameters (`ParameterConfiguration`).

### 4.5 Relationship with `ResearchExecutor`

- Primary consumer.
- Invokes `ParameterSweepEngine` to obtain `tuple[ParameterConfiguration, ...]`.
- **Sole owner** (or delegate to a policy factory) of translating each configuration into concrete `AllocationPolicy` / `WithdrawalPolicy` instances.
- Joins configuration + policies + cohort into simulation tasks; propagates the **primitive** configuration into result provenance.
- **Boundary:** `ParameterSweepEngine` has zero knowledge of `ResearchExecutor`. Dependency is strictly `ResearchExecutor` → `ParameterSweepEngine`.

### 4.6 Relationship with `ResultAggregator`, `StrategyComparator`, `SWROptimizer`

| Component | Relationship |
| :--- | :--- |
| `ResultAggregator` | Uses `ParameterConfiguration` as a hashable grouping key; never calls the sweep engine for aggregation itself. |
| `StrategyComparator` | Compares metrics across configurations; may request grids but does not own generation semantics. |
| `SWROptimizer` | Treats configurations as candidate evaluation points; adaptive search loops are owned by the optimizer, not by `ParameterSweepEngine`. |

### 4.7 Relationship with Execution Engine

- **None.** The frozen `v0.1` engine never sees `ParameterConfiguration`, `ParameterAxis`, or `ParameterSweepEngine`.
- Policy objects that eventually reach `SimulationRunner` are produced only after materialisation by higher-level research components.

---

## 5. Domain-Agnostic Content Architecture

`ParameterConfiguration` is architecturally constrained to remain a pure data identity:

```
Allowed payload:  Mapping[str, int | float | bool | str]
Forbidden payload: any engine domain object, research orchestration object,
                   callable, factory, or nested non-primitive structure
```

### Ownership of config → policy materialisation

```
ParameterSweepEngine
        │ emits
        ▼
ParameterConfiguration     ← primitives only; no policy knowledge
        │
        │  (external composition only)
        ▼
ResearchExecutor / policy factory
        │ materialises
        ▼
AllocationPolicy + WithdrawalPolicy
        │
        ▼
SimulationRunner (black box)
```

**Normative rules:**

1. No `to_allocation_policy()` / `to_withdrawal_policy()` methods on `ParameterConfiguration`.
2. No fields of policy, experiment, cohort, or context type on `ParameterConfiguration`.
3. Study-specific interpretation of names such as `"glide_start"` lives outside this type.
4. Downstream joins of config with policies/cohorts are external composition, not structural embedding.

This preserves three clean layers: parameter-space generation → policy materialisation → simulation execution.

---

## 6. Stateless Design & Concurrency Guarantees

`ParameterSweepEngine` is a **pure stateless utility class**:

1. **No Instance State:** All methods are `@staticmethod`. No fields, caches, or mutable class variables that affect outputs.
2. **Referential Transparency:** Identical inputs produce identical outputs (same product order, same configuration values).
3. **No Side Effects:** No I/O, no network, no mutation of inputs.
4. **Thread & Process Safety:** Safe for concurrent use by `ResearchExecutor` without locks.
5. **Immutable Outputs:** Returned tuples and value objects are frozen; consumers cannot alter generated grids.

### Ordering vs identity (architectural distinction)

| Property | Scope | Contract |
| :--- | :--- | :--- |
| **Product sequence order** | The returned `tuple` | Deterministic lexicographic order; rightmost axis varies fastest |
| **Configuration identity** | Each `ParameterConfiguration` | Content-based set of name→value pairs; independent of product index and axis declaration order |

Consumers that key on configuration content remain correct even if they reshuffle the tuple. Consumers that rely on product order get a stable, documented expansion order.

---

## 7. Validation Architecture

Validation is fail-fast and local to construction/generation:

```
                    Caller inputs
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   axis_from_values  axis_from_range   cartesian_product / generate
   (name, sequence)  (name, range)     (axes sequence)
          │               │               │
   reject empty/dup/  reject zero step,  reject empty axes list,
   hetero/blank name  non-finite, bad    null elements, duplicate
                      direction          axis names
          │               │               │
          └───────┬───────┘               │
                  ▼                       │
            ParameterAxis                 │
                  └───────────────────────┘
                                  │
                                  ▼
                 tuple[ParameterConfiguration, ...]
                 (each config validates non-empty primitive bindings)
```

There is **no** market-feasibility filtering (unlike `CohortGenerator`'s horizon checks). Parameter grids are abstract; feasibility against datasets or policies is a higher-level concern.

---

## 8. Module Placement

### Approved Location

```
src/research/domain/parameter/
    __init__.py
    configuration.py    # ParameterConfiguration
    axis.py             # ParameterAxis
    engine.py           # ParameterSweepEngine
```

### Placement rationale

1. **Domain Layer Membership:** Pure domain utility and value objects; no infrastructure concerns.
2. **Cohesive package:** Generator and its value objects live together, parallel to `research.domain.cohort`.
3. **No circular dependencies:**
   - `configuration.py` — no internal research imports beyond stdlib/typing.
   - `axis.py` — no dependency on configuration or engine.
   - `engine.py` — imports `ParameterAxis` and `ParameterConfiguration` only.
4. **Engine isolation:** Package does not import from `engine.*`.

### Export Surface

```python
# src/research/domain/parameter/__init__.py
from research.domain.parameter.configuration import ParameterConfiguration
from research.domain.parameter.axis import ParameterAxis
from research.domain.parameter.engine import ParameterSweepEngine

# src/research/domain/__init__.py — re-export
# src/research/__init__.py — re-export in __all__
```

Consumers import via the stable public interface:

```python
from research import (
    ParameterSweepEngine,
    ParameterConfiguration,
    ParameterAxis,
)
```

Internal file layout remains an implementation detail hidden behind the `research` package surface.

---

## 9. Future Extensibility

Designed for extension without modification of frozen contracts:

| Extension | How it is added | What stays frozen |
| :--- | :--- | :--- |
| Additional axis constructors (e.g. log-spaced ranges) | New `@staticmethod` on `ParameterSweepEngine` | Existing method signatures and output contracts |
| Additional scalar types (e.g. pure enums) | Expand allowed scalar set in a deliberate contract revision | Identity/equality model (name→value set) |
| Policy factories | New research components outside this package | `ParameterConfiguration` remains policy-free |
| Adaptive search / SWR root finding | `SWROptimizer` (v0.3) | Sweep engine remains pure Cartesian/grid |
| YAML grid loaders | Infrastructure layer | Domain objects stay I/O-free |
| Parallel product materialisation | Optional internal optimization | Deterministic order and content unchanged |

**Non-extensions (rejected):**

- Embedding policies into configurations
- Coupling sweep generation to `Dataset` or cohort feasibility
- Making `ParameterAxis` a long-lived result identity
- Introducing `ParameterGrid` wrapper types without new identity semantics

---

## 10. Architectural Approval Summary

| Concern | Verdict |
| :--- | :--- |
| Responsibility boundary | Single: deterministic parameter-space grid generation only |
| Ownership | `research.domain.parameter` — pure domain utility + value objects |
| Long-lived public contract | `ParameterConfiguration` only (domain-agnostic primitives) |
| Construction helper | `ParameterAxis` (not a result identity) |
| Policy materialisation ownership | `ResearchExecutor` / policy factory — never the sweep engine |
| Dependency direction | Strictly local: engine → axis/configuration; zero engine-domain imports |
| Engine isolation | Complete — frozen `v0.1` engine untouched and unaware |
| Peer isolation | Zero coupling to `CohortGenerator` / `ExperimentDefinition` |
| Stateless design | All methods `@staticmethod`; no instance state |
| Concurrency safety | Referentially transparent; immutable outputs |
| Module placement | `src/research/domain/parameter/` |
| Export surface | `from research import ParameterSweepEngine, ParameterConfiguration, ParameterAxis` |

---

## 11. Approval Status

| Item | Status |
| :--- | :--- |
| Behavioural specification | **Frozen / Approved** |
| Architecture review | **Submitted for approval** |
| Public API review | Proceeds immediately as workflow Step 3 |
| Implementation | Blocked until Public API is approved |

---

## Next Immediate Step

Proceed to **Step 3: Public API Review** (`PARAMETER_SWEEP_ENGINE_PUBLIC_API.md`).
