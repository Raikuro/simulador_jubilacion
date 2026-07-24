# ParameterSweepEngine Behavioural Specification

## Purpose

`ParameterSweepEngine` is a Research Layer component responsible for generating deterministic multi-dimensional parameter spaces for quantitative research studies.

It translates declarative parameter axes (allocation ratios, glidepath endpoints and durations, withdrawal rates, and other research dimensions) into ordered, immutable sequences of parameter configurations.

It materialises the **policy-parameter matrix portion** of a research study in the same conceptual role that `CohortGenerator` materialises the temporal cohort portion. It does **not** execute simulations, instantiate execution contexts, or evaluate financial outcomes.

Primary consumers are `ResearchExecutor` (v0.2.2) and, later, v0.3 optimizers and strategy analyzers. Target Early Retirement Now (ERN) studies enabled by this component include:

- **SWR Part 19** — Equity Glidepaths (starting equity, ending equity, glide duration grids)
- **SWR Part 20 & 25** — Flexibility and dynamic withdrawal rate grids
- **SWR Part 28** — CAPE-conditioned allocation and withdrawal parameter surfaces

---

## Responsibilities & Scope Boundaries

### Core Responsibilities

`ParameterSweepEngine` owns exclusively:

- **Axis Construction:** Building ordered parameter axes from explicit value sequences or from closed numeric ranges with a fixed step.
- **Cartesian Expansion:** Computing the full Cartesian product of one or more parameter axes into an ordered sequence of parameter configurations.
- **Deterministic Ordering:** Emitting configurations in a strict, reproducible lexicographic order defined by axis declaration order and within-axis value order.
- **Local Validation:** Rejecting empty axes, invalid ranges, non-positive steps, duplicate axis names, and other intrinsic construction errors at generation time.
- **Identity Preservation:** Ensuring each emitted configuration is an immutable value object with stable equality and hashing based solely on its parameter values.

### Explicit Scope Boundaries

- **No Policy Instantiation:** `ParameterSweepEngine` does **not** construct concrete `AllocationPolicy` or `WithdrawalPolicy` instances. It emits pure, domain-agnostic parameter configurations. Mapping configurations onto engine policy objects is the exclusive responsibility of a higher-level component (`ResearchExecutor` or a future policy factory) — never of `ParameterSweepEngine` or of `ParameterConfiguration` itself.
- **No Study Expansion:** `ParameterSweepEngine` does **not** cross parameter configurations with cohorts, datasets, or horizons. Full study matrix expansion (cohort × allocation × withdrawal) belongs to `ResearchExecutor`.
- **No Adaptive / Stochastic Search:** `ParameterSweepEngine` does **not** implement random sampling, Latin-hypercube designs, Bayesian optimization, binary-search SWR solvers, or other adaptive search strategies. Those belong to v0.3 consumers (`SWROptimizer` and successors). This component is a pure grid / Cartesian generator only.
- **No Financial or Engine Semantics:** Parameter values are opaque primitives. Neither `ParameterSweepEngine` nor `ParameterConfiguration` interprets equity weights, CAPE thresholds, withdrawal rates, or any engine/research object beyond scalar range validation required for axis construction.

---

## Forbidden Responsibilities

`ParameterSweepEngine` must not:

- execute simulations or invoke `SimulationRunner` / `SimulationExecutor` / `ResearchExecutor`;
- create, mutate, or inspect `SimulationContext`, `SimulationResult`, or monthly pipeline state;
- instantiate, wrap, or call `AllocationPolicy` / `WithdrawalPolicy` / `Policy.decide`;
- import, receive, or store `ExperimentDefinition` or `CohortSpecification` instances;
- embed, reference, or return any engine or research execution type inside `ParameterConfiguration`;
- couple to `CohortGenerator` (peer component; both are coordinated only by higher-level orchestration);
- perform portfolio valuation, market evolution, rebalancing, or withdrawal math;
- access external resources (filesystems, databases, network endpoints, environment variables);
- depend on infrastructure drivers, serialization libraries, CLI parsers, or plotting tools;
- introduce non-determinism (random seeds, system clocks, unordered hash iteration, process-local caches that affect output order or content);
- filter, prune, or rank configurations by research merit, feasibility against market data, or expected success rates.

---

## Architectural Decision: Value Object Necessity

This section freezes the design decision on which new types are introduced, and why. The governing principle is:

> **Minimise the number of long-lived Public Research Domain Contracts.** Introduce a new public value object only when no existing immutable representation can carry identity, equality, validation, and cross-component semantics without ambiguity.

### Decision Summary

| Type | Status | Lifecycle | Rationale (one line) |
| :--- | :--- | :--- | :--- |
| **`ParameterConfiguration`** | **Public Research Domain Contract** | Long-lived: survives generation and flows through execution, aggregation, comparison, and optimisation | First-class identity of one research grid point; no existing type satisfies this role |
| **`ParameterAxis`** | **Public construction helper** (not a long-lived domain identity) | Short-lived: used only while building a grid; never stored in results or used as an aggregation key | Ergonomic, validated input to Cartesian expansion; not a research identity concept |

Only **one** new long-lived public contract is introduced: `ParameterConfiguration`.  
`ParameterAxis` is exported for API ergonomics and fail-fast axis validation, but it is **not** a peer of `CohortSpecification` / `ExperimentDefinition` in the identity graph of research results.

---

### 1. Why `ParameterConfiguration` must be an explicit immutable value object

#### Alternatives considered and rejected

| Representation | Why it is insufficient |
| :--- | :--- |
| **`dict[str, Scalar]`** | Mutable; not hashable; cannot be a dict/set key for aggregation; silent post-generation mutation would corrupt provenance. |
| **`types.MappingProxyType`** | Read-only view, but still not a domain type; weak equality story; awkward for fingerprints, serialization contracts, and typed public APIs; not self-validating. |
| **`tuple[tuple[str, Scalar], ...]`** | Hashable and immutable, but loses first-class named access, embeds ordering as identity noise unless a sort convention is reinvented at every call site, and provides no validation boundary (empty tuples, blank keys, mixed semantics). |
| **`tuple[Scalar, ...]` (positional only)** | Fragile: axis order becomes silent identity; renaming or reordering axes breaks equality across studies; unusable as a self-describing research key. |
| **Reuse `CohortSpecification` / policies** | Wrong abstraction: cohorts are temporal windows; policies are executable engine strategies. Neither is a pure parameter-space point. |
| **Reuse `ExperimentDefinition`** | Study blueprint, not a single grid point. Far too heavy and already frozen with different invariants. |

#### Positive justification

`ParameterConfiguration` is the **parameter-space analogue of `CohortSpecification`**:

| Concern | `CohortSpecification` | `ParameterConfiguration` |
| :--- | :--- | :--- |
| Domain question answered | *When* does the simulation start? | *Which* parameter point is being evaluated? |
| Generator | `CohortGenerator` | `ParameterSweepEngine` |
| Consumer identity use | Result indexing by cohort | Result indexing by parameter point |
| Must be immutable & hashable | Yes | Yes |
| Must be self-validating | Yes | Yes |

An explicit value object is therefore necessary because it must simultaneously provide:

1. **Semantic type** — public APIs and result schemas can declare `ParameterConfiguration` rather than an anonymous mapping.
2. **Immutability + hashability** — required for use as keys in aggregation maps, caches, and reproducibility structures.
3. **Canonical identity** — a single, documented equality/hash contract (see below), not reimplemented ad hoc by each consumer.
4. **Validation boundary** — reject empty assignments and blank keys at construction, once.
5. **Named access** — consumers read `config.get("withdrawal_rate")` without depending on product expansion order.

**Conclusion:** `ParameterConfiguration` is justified as a new public type. A raw immutable mapping or tuple does **not** already satisfy the responsibility of a long-lived research identity.

---

### 2. Canonical identity and equality semantics of `ParameterConfiguration`

#### Canonical identity

The **canonical identity** of a `ParameterConfiguration` is the **unordered set of name→value bindings**:

$$
\text{identity}(C) = \{ (n, v) \mid n \in \text{names}(C),\ v = C[n] \}
$$

Consequences:

- Identity is **content-based**, not position-based.
- Identity does **not** depend on axis declaration order used during Cartesian expansion.
- Identity does **not** depend on dict insertion order or any runtime memory address.
- Two configurations constructed from different axis orderings but with the same bindings are the **same** configuration.

#### Canonical form (for hashing, debugging, serialization)

For hashing, `repr`, fingerprints, and stable serialization, the configuration is reduced to a **canonical ordered form**:

1. Take all `(name, value)` pairs.
2. Sort by `name` ascending (lexicographic, Unicode code-point order of the Python `str`).
3. Form an immutable sequence: `((n₁, v₁), (n₂, v₂), …, (nₖ, vₖ))`.

This canonical form is a *derived representation* of identity. It is not a second identity key.

#### Equality

```text
C1 == C2  ⇔  set of (name, value) pairs of C1 equals set of (name, value) pairs of C2
```

- Value comparison uses ordinary Python equality (`==`) for the scalar types in scope (`int`, `float`, `bool`, `str`).
- Float equality is **exact** (`==`), not approximate. Grid points generated by `ParameterSweepEngine` for the same inputs are bit-stable by the range-generation contract; consumers must not rely on approximate float matching for identity.
- Missing keys and extra keys both break equality.
- Equal configurations must have equal hashes: `C1 == C2 ⇒ hash(C1) == hash(C2)`.

#### Non-identity (explicitly excluded)

The following are **not** part of identity:

| Non-identity aspect | Reason |
| :--- | :--- |
| Index in the product sequence | Ordering of the generated tuple is a generation property, not an identity property. |
| Source axes / range metadata | Configurations are pure value assignments; they forget how the grid was built. |
| Associated policies, cohorts, or experiment names | Those are joins performed by consumers, not fields of the configuration. |
| Display labels or human-readable titles | Reporting concern; may be derived later without affecting identity. |

#### Structural requirements

| Field | Constraint | Role |
| :--- | :--- | :--- |
| `values` | Non-empty immutable mapping `str → Scalar` | Sole identity payload |

**Scalar types:** `int`, `float`, `bool`, `str` only.

**Access contract:**

- `get(name) → Scalar` (raises `KeyError` if absent).
- `names() → tuple[str, ...]` in canonical sorted order.
- `items() → tuple[tuple[str, Scalar], ...]` in canonical sorted order.

**Immutability:** Frozen after construction. Mutation attempts raise the standard frozen-dataclass error.

---

### 3. Interaction with future components

`ParameterConfiguration` is the **join key** of the research parameter dimension. It is intentionally passive: consumers attach, group, compare, and search over it; they do not ask it to execute logic.

```
ParameterSweepEngine
        │  emits
        ▼
tuple[ParameterConfiguration, ...]
        │
        ▼
ResearchExecutor  ──── attaches config to each planned simulation task
        │                 (alongside CohortSpecification)
        ▼
SimulationRunner (black box)  ──── unaware of ParameterConfiguration
        │
        ▼
per-simulation results + provenance (cohort, config, …)
        │
        ├──────────────► ResultAggregator     (group / index by config)
        ├──────────────► StrategyComparator   (compare metrics across configs)
        └──────────────► SWROptimizer         (iterate candidate configs)
```

| Component | Milestone | Interaction with `ParameterConfiguration` |
| :--- | :--- | :--- |
| **`ResearchExecutor`** | v0.2.2 | Primary consumer of the generated tuple. Owns (or delegates to a policy factory) the **materialisation** of each domain-agnostic `ParameterConfiguration` into concrete `AllocationPolicy` / `WithdrawalPolicy` instances. Binds config + policies + `CohortSpecification` into simulation tasks and propagates the **primitive** configuration into result provenance. Does **not** mutate the configuration or push policy objects back into it. |
| **`ResultAggregator`** | v0.2.3 | Uses `ParameterConfiguration` as a **hashable grouping key** when synthesising statistics across cohorts for a fixed parameter point (e.g. success rate for equity=60%, WR=3.5%). May also pivot the opposite way (group by cohort, series over configs). Requires stable `==` / `hash`. |
| **`StrategyComparator`** | v0.3 | Compares aggregated metrics between configurations or families of configurations (e.g. static 60/40 vs. a glidepath point). Reads configuration fields for labeling and dimensional slicing; never regenerates grids itself unless it calls `ParameterSweepEngine`. |
| **`SWROptimizer`** | v0.3 | Treats configurations as candidate evaluation points. Typical pattern: fix all axes except the search dimension (e.g. withdrawal rate), generate or construct candidate `ParameterConfiguration` values, evaluate via `ResearchExecutor`, and select the optimum. May call `ParameterSweepEngine` for initial grids, but adaptive search loops are owned by the optimizer, not by the sweep engine. |
| **`ResearchReproducibilityManager`** | v0.2.3 | Fingerprints configurations via their canonical form (sorted name→value pairs) as part of study input hashes. |
| **`SimulationRunner` / Execution Engine** | v0.1 frozen | **No interaction.** The engine never sees `ParameterConfiguration`. |

**Interaction with `ParameterAxis`:** none of the components above store or key on `ParameterAxis`. Axes exist only as inputs to `ParameterSweepEngine` at grid-construction time.

---

### 4. Public contract classification

#### `ParameterConfiguration` — Public Research Domain Contract

**Classification:** Long-lived **Public Research Domain Contract**, same tier as `CohortSpecification`.

**Implications:**

- Exported from the public `research` package surface.
- Appears in typed signatures of generators and (future) result / aggregation APIs.
- Equality, hashing, and validation semantics are frozen once approved; breaking changes require an explicit research-layer revision.
- Downstream components must depend on this type rather than inventing parallel “param dict” conventions.

#### `ParameterAxis` — Public construction helper (not a long-lived identity contract)

**Classification:** Public **construction-time** value object supporting the `ParameterSweepEngine` API. It is **not** a long-lived research identity and must not be used as:

- a result grouping key,
- a field inside aggregated statistics identity,
- a substitute for `ParameterConfiguration` in executor provenance.

**Why expose it at all (rather than only primitives)?**

Multi-axis Cartesian products need a validated, named, ordered dimension object so that:

- `axis_from_range` / `axis_from_values` have a typed return value,
- duplicate names and empty axes fail once at axis construction,
- the same axis can be reused across multiple `generate` calls without re-validating sequences ad hoc.

**Why it is not elevated to a Public Research Domain Contract peer of `CohortSpecification`:**

- It does not identify a research evaluation unit.
- It does not flow through execution results.
- Eliminating it later in favour of a more ergonomic builder API would not break result provenance, aggregation keys, or optimizer identity — whereas removing `ParameterConfiguration` would.

This split minimises long-lived public surface area: **one identity contract** (`ParameterConfiguration`) plus **one construction helper** (`ParameterAxis`).

---

### 5. Explicit non-goals for new public concepts

The following are **not** introduced as public research contracts:

| Rejected concept | Reason |
| :--- | :--- |
| `ParameterGrid` / `SearchSpace` container type | A `tuple[ParameterConfiguration, ...]` already expresses an ordered grid; an extra wrapper adds no identity semantics. |
| `ParameterValue` wrapper around scalars | Scalars (`int`/`float`/`bool`/`str`) are sufficient; wrapping every number increases noise without validation benefit beyond axis/config checks. |
| Policy-parameter hybrid types | Mapping config → policy remains outside this component. |
| Mutable builders as public contracts | Builders, if any, stay implementation details; public outputs remain frozen value objects. |

---

## Domain Value Objects

### 1. `ParameterConfiguration` (Public Research Domain Contract)

Represents one point in a multi-dimensional parameter space — a single complete **named immutable assignment of primitive parameter values**.

| Field | Constraint / Local Invariant | Rationale |
| :--- | :--- | :--- |
| `values` | Non-empty immutable mapping from parameter name (`str`) to a **primitive scalar** value. Keys non-blank. | Sole identity payload; fully specifies one grid point. |

**Allowed scalar value types (exhaustive for v0.2.2):** `int`, `float`, `bool`, `str`.  
Future extensions may add pure enums if needed; they must remain primitive/value-level types with no engine or research object references.

**Identity, equality, hashing:** As defined in *Canonical identity and equality semantics* above. Content-based; canonical ordered form used for hash/debug/fingerprint only.

**Immutability:** Frozen after construction.

**Lifecycle:** Produced by `ParameterSweepEngine`; consumed and retained by `ResearchExecutor`, `ResultAggregator`, `StrategyComparator`, `SWROptimizer`, and reproducibility tooling.

**Domain-agnostic content rule:** See *Ownership Boundary: Domain-Agnostic `ParameterConfiguration`* immediately below. This type stores **only** primitive bindings. It never holds or references policies, experiments, cohorts, or execution components.

---

## Ownership Boundary: Domain-Agnostic `ParameterConfiguration`

This boundary is normative and implementation-binding.

### Responsibility of `ParameterConfiguration`

`ParameterConfiguration` has **exactly one** responsibility:

> Represent a named, immutable assignment of primitive parameter values (a pure point in an abstract parameter space).

It is intentionally **domain-agnostic** with respect to the financial engine and the broader research orchestration model. Parameter *names* may be study-meaningful strings (e.g. `"equity_weight"`, `"withdrawal_rate"`), but the value object itself attaches **no** financial, policy, or execution semantics to those names or values.

### Forbidden content and references

`ParameterConfiguration` must **not** contain, embed, wrap, import, or reference any of the following:

| Forbidden type / concern | Layer | Why forbidden |
| :--- | :--- | :--- |
| `AllocationPolicy` | Engine domain | Executable strategy; not a primitive parameter binding |
| `WithdrawalPolicy` | Engine domain | Executable strategy; not a primitive parameter binding |
| `ExperimentDefinition` | Research domain | Study blueprint; far heavier than a single grid point |
| `SimulationContext` | Engine application | Runtime execution state |
| `CohortSpecification` | Research domain | Temporal window identity; orthogonal join key |
| `SimulationRunner` / `SimulationExecutor` / pipeline steps | Engine application | Execution machinery |
| `Dataset`, `Portfolio`, `Money`, market snapshots, services | Engine domain | Financial/runtime objects |
| Any callable, factory, or lazy policy builder | Mixed | Turns a value object into hidden execution logic |

Only primitive parameter bindings are stored — for example:

```text
{"equity_weight": 0.60, "withdrawal_rate": 0.035, "glide_months": 120}
{"allocation_family": "passive_glide", "glide_start": 0.80, "glide_end": 0.40}
```

### Ownership of configuration → policy materialisation

| Concern | Owner | Must not own |
| :--- | :--- | :--- |
| Generate primitive parameter grids | `ParameterSweepEngine` | Policies, cohorts, execution |
| Hold primitive name→value bindings | `ParameterConfiguration` | Policies, experiments, contexts, cohorts |
| Transform `ParameterConfiguration` → concrete `AllocationPolicy` / `WithdrawalPolicy` | **Higher-level component only:** `ResearchExecutor` and/or a future dedicated policy factory | `ParameterSweepEngine`, `ParameterConfiguration`, `ParameterAxis` |
| Bind config + policies + cohort into a simulation task | `ResearchExecutor` | `ParameterSweepEngine` |
| Execute the simulation | `SimulationRunner` (frozen v0.1) | Research Layer generators |

**Normative rule:**

```text
ParameterSweepEngine  ──emits──►  ParameterConfiguration   (primitives only)
                                         │
                                         │  (no policy knowledge)
                                         ▼
              ResearchExecutor / policy factory
                                         │
                                         │  materialises
                                         ▼
                    AllocationPolicy + WithdrawalPolicy
                                         │
                                         ▼
                              SimulationRunner (black box)
```

Consequences:

1. `ParameterSweepEngine` never imports or constructs engine policy types.
2. `ParameterConfiguration` never gains factory methods such as `to_allocation_policy()` or fields of policy type.
3. Study-specific knowledge about how names like `"glide_start"` map onto a particular policy class lives **outside** this value object — in `ResearchExecutor`, a policy factory, or study construction code.
4. Downstream components may *join* a configuration with policies and cohorts for provenance, but that join is external composition, not part of `ParameterConfiguration`'s structure.

### Why this boundary exists

- Preserves a minimal long-lived public contract (pure data identity).
- Keeps the frozen Execution Engine unaware of research parameter grids.
- Allows multiple policy families and factories to interpret the same configuration without changing the sweep engine.
- Prevents leakage of execution concerns into grid generation and result keys.

### 2. `ParameterAxis` (Public construction helper)

Represents one named dimension of a research search space **during grid construction only**.

| Field | Constraint / Local Invariant | Rationale |
| :--- | :--- | :--- |
| `name` | Non-empty, non-whitespace string. Unique within a multi-axis product. | Dimension identifier (e.g. `"equity_weight"`, `"withdrawal_rate"`, `"glide_start"`, `"glide_end"`, `"glide_months"`). |
| `values` | Non-empty ordered sequence of unique homogeneous scalar values. | Ordered discrete points along this axis. Order drives lexicographic expansion only; it is not part of `ParameterConfiguration` identity. |

**Scalar value types on an axis:** same as configuration scalars. Heterogeneous types within a single axis are forbidden. Mixed types across different axes are allowed.

**Equality / hashing (construction helper only):** Two axes are equal if and only if they have the same `name` and the same ordered `values` sequence. This equality is for testing and reuse of axis objects; it is **not** used as a research result key.

**Lifecycle:** Created by `axis_from_values` / `axis_from_range`; consumed immediately by `cartesian_product` / `generate`; not retained in simulation results.

---

## Strategy Specifications & Generation Semantics

### 1. Explicit Axis Construction (`axis_from_values`)

- **Behavior:** Constructs a `ParameterAxis` from a name and an explicit ordered sequence of values.
- **Filtering:** None. Every provided value is retained in the given order.
- **Duplicates:** Duplicate values within an axis are **rejected** (`ValueError`). Axes must contain unique values so that Cartesian expansion does not silently produce duplicate configurations from a single dimension.
- **Empty sequence:** Rejected (`ValueError`).
- **Type homogeneity:** All values in the sequence must share the same Python type (with `bool` treated as distinct from `int`). Heterogeneous sequences raise `ValueError`.

### 2. Numeric Range Axis Construction (`axis_from_range`)

- **Behavior:** Constructs a `ParameterAxis` from a closed numeric interval `[start, stop]` and a positive `step`, producing the discrete sequence:

  $$
  v_k = \text{start} + k \cdot \text{step}, \quad k = 0, 1, 2, \ldots
  $$

  such that every $v_k \le \text{stop}$ (for positive step) or $v_k \ge \text{stop}$ (for negative step), and the endpoint `stop` is **included** when it is exactly representable as a grid point under the generation rules below.

- **Endpoint inclusion (critical for research reproducibility):**
  - The sequence always includes `start`.
  - The sequence includes every intermediate grid point generated by successive addition of `step`.
  - The sequence includes `stop` if and only if `stop` lies on the arithmetic progression defined by `start` and `step` within a documented floating-point tolerance, **or** if an integer-step exact path is used (see below).
  - When `start == stop`, the axis contains exactly one value: `start`.

- **Floating-point determinism:**
  - Generation must be deterministic across platforms for the same `(start, stop, step)` triple.
  - Implementations must prefer an integer-index formulation (e.g. compute count of steps, then emit `start + i * step` for `i in 0..n`) over open-ended `while` accumulation that can drift.
  - For research-critical decimal grids (e.g. withdrawal rates `0.030` to `0.050` step `0.001`), the specification requires that the produced sequence match exact arithmetic progression values; minor IEEE-754 representation noise in intermediate multiplications is acceptable only if equality checks against expected research grids still pass under a documented absolute tolerance of $1 \times 10^{-12}$ when comparing floats in tests.
  - Negative `step` is permitted when `start > stop`. Zero `step` is forbidden.

- **Type of emitted values:**
  - If `start`, `stop`, and `step` are all `int` and the progression is integral, values may be emitted as `int`.
  - Otherwise values are emitted as `float`.

- **Error cases:** See Fail-Fast section.

### 3. Cartesian Product Expansion (`cartesian_product`)

- **Behavior:** Accepts an ordered sequence of `ParameterAxis` objects $(A_1, A_2, \ldots, A_n)$ and emits the full Cartesian product as an immutable tuple of `ParameterConfiguration` objects.
- **Cardinality:**

  $$
  \lvert \text{product} \rvert = \prod_{i=1}^{n} \lvert A_i.\text{values} \rvert
  $$

- **Ordering (lexicographic, axis-declaration order):**
  - The rightmost axis ($A_n$) varies fastest.
  - The leftmost axis ($A_1$) varies slowest.
  - This matches nested-loop semantics:

    ```text
    for v1 in A1.values:
        for v2 in A2.values:
            ...
                for vn in An.values:
                    yield ParameterConfiguration({A1.name: v1, ..., An.name: vn})
    ```

- **Single axis:** A product of one axis yields one configuration per axis value, in axis order.
- **Empty axis list:** Forbidden (`ValueError`). At least one axis is required.
- **Duplicate axis names:** Forbidden (`ValueError`). Axis names must be unique within a product.
- **No silent deduplication of configurations:** If two different axes somehow produced identical full configurations (should not occur under unique names), both would still be distinct mappings; with unique names, each product index maps to a unique name→value assignment. Duplicate full configurations can only arise if an axis itself had duplicate values, which is already forbidden at axis construction.

### 4. Convenience Composition (`generate`)

- **Behavior:** Accepts one or more axes (already constructed) and returns `cartesian_product` of those axes.
- **Rationale:** Provides a single entry point for research scripts: build axes, then `generate`.
- **Semantics:** Identical to `cartesian_product`; no additional filtering or sorting beyond the product ordering contract.

---

## Input & Output Contracts

### Inputs

| Input | Type / Form | Notes |
| :--- | :--- | :--- |
| Axis name | `str` | Non-empty, non-whitespace. |
| Explicit values | ordered sequence of homogeneous scalars | Used by `axis_from_values`. |
| Range triple | `start`, `stop`, `step` | Used by `axis_from_range`. Numeric (`int` or `float`). |
| Axes | ordered sequence of `ParameterAxis` | Used by `cartesian_product` / `generate`. |

### Outputs

| Output | Type | Notes |
| :--- | :--- | :--- |
| Axis | `ParameterAxis` | Immutable. |
| Configuration sequence | `tuple[ParameterConfiguration, ...]` | Immutable, lexicographically ordered, length equal to the Cartesian product cardinality. |

### Non-outputs (explicit)

`ParameterSweepEngine` never returns:

- `AllocationPolicy` / `WithdrawalPolicy` instances
- `ExperimentDefinition` instances
- `CohortSpecification` instances
- simulation results, statistics, or success rates

---

## Fail-Fast & Validation Rules

`ParameterSweepEngine` (and its value objects) raise `ValueError` with a descriptive message when any of the following hold:

### Axis construction

1. **Blank axis name:** `name` is empty or whitespace-only.
2. **Empty values:** Explicit value sequence is empty.
3. **Duplicate values in axis:** Explicit sequence contains duplicate entries.
4. **Heterogeneous value types:** Explicit sequence mixes incompatible scalar types.
5. **Invalid range direction:** For `axis_from_range`, `step > 0` but `start > stop`, or `step < 0` but `start < stop` (empty progression that is not the single-point `start == stop` case).
6. **Zero step:** `step == 0`.
7. **Non-numeric range arguments:** `start`, `stop`, or `step` is not an `int` or `float` (bools rejected).
8. **Non-finite numerics:** `start`, `stop`, or `step` is NaN or ±Infinity.

### Product expansion

9. **Empty axis list:** No axes provided to `cartesian_product` / `generate`.
10. **Null / invalid axis elements:** Axes sequence contains `None` or non-`ParameterAxis` objects.
11. **Duplicate axis names:** Two or more axes share the same `name`.

### Value object construction

12. **Empty configuration:** `ParameterConfiguration` constructed with an empty mapping.
13. **Blank parameter keys:** Configuration keys that are empty or whitespace-only.

Expected generation with valid inputs never raises.

`TypeError` may be raised by Python for fundamentally incorrect argument types where appropriate; behavioural tests focus on `ValueError` domain failures above.

---

## Behavioral Interface

The following sketch defines the behavioural surface. Exact module placement and signature polishing are deferred to the Public API Review (workflow step 3). Semantics here are binding.

```python
class ParameterAxis:
    """Immutable named dimension of a research parameter space."""

    name: str
    values: tuple[Scalar, ...]  # Scalar ∈ {int, float, bool, str}


class ParameterConfiguration:
    """Immutable point in a multi-dimensional parameter space."""

    values: Mapping[str, Scalar]

    def get(self, name: str) -> Scalar: ...
    def names(self) -> tuple[str, ...]: ...


class ParameterSweepEngine:
    """Stateless utility for generating deterministic parameter grids.

    All methods are @staticmethod. This class is never instantiated.
    """

    @staticmethod
    def axis_from_values(
        name: str,
        values: Sequence[Scalar],
    ) -> ParameterAxis:
        ...

    @staticmethod
    def axis_from_range(
        name: str,
        start: int | float,
        stop: int | float,
        step: int | float,
    ) -> ParameterAxis:
        ...

    @staticmethod
    def cartesian_product(
        axes: Sequence[ParameterAxis],
    ) -> tuple[ParameterConfiguration, ...]:
        ...

    @staticmethod
    def generate(
        axes: Sequence[ParameterAxis],
    ) -> tuple[ParameterConfiguration, ...]:
        """Alias of cartesian_product for research-script ergonomics."""
        ...
```

### Illustrative Research Usage (non-normative examples)

**Static equity allocation grid (0%–100%, 5% steps):**

```text
equity_axis = axis_from_range("equity_weight", start=0.0, stop=1.0, step=0.05)
configs = generate([equity_axis])
# → 21 configurations: 0.00, 0.05, ..., 1.00
```

**Withdrawal rate grid (3.0%–5.0%, 0.1% steps):**

```text
wr_axis = axis_from_range("withdrawal_rate", start=0.030, stop=0.050, step=0.001)
configs = generate([wr_axis])
# → 21 configurations
```

**ERN-style glidepath surface (start × end × duration):**

```text
start_eq = axis_from_range("glide_start", 0.0, 1.0, 0.10)
end_eq   = axis_from_range("glide_end",   0.0, 1.0, 0.10)
months   = axis_from_values("glide_months", [60, 120, 180])
configs  = generate([start_eq, end_eq, months])
# → 11 × 11 × 3 = 363 configurations, ordered with glide_months varying fastest
```

**Multi-family categorical × numeric product:**

```text
family = axis_from_values("allocation_family", ["static", "passive_glide", "active_glide"])
wr     = axis_from_range("withdrawal_rate", 0.03, 0.05, 0.01)
configs = generate([family, wr])
```

---

## Determinism & Identity

`ParameterSweepEngine` is strictly deterministic and side-effect free:

1. **Referential transparency:** Identical axis inputs always produce identical output tuples (same length, same product order, same configuration values).
2. **No external state:** No random generators, system timestamps, environment variables, or global mutable caches influence generation.
3. **Content-based configuration identity:** `ParameterConfiguration` equality and hashing depend only on the unordered set of name→value pairs (see *Canonical identity and equality semantics*). Product index and axis declaration order are not part of configuration identity.
4. **Stable hashing:** Equal configurations produce equal hashes, enabling use as keys in aggregation maps, optimizer caches, and reproducibility fingerprints.
5. **Thread / process safety:** Stateless static methods with immutable outputs are safe for concurrent use by `ResearchExecutor` without locks.

**Note:** Product **sequence order** is deterministic (rightmost axis fastest) and is a property of the generated tuple, not of each configuration's identity. Two runs may yield equal configurations at the same indices; consumers that key on configuration content remain correct even if they reshuffle the tuple.

---

## Architectural Placement & Dependency Rules

```
ExperimentDefinition          (declarative study blueprint)
        │
        ▼
ResearchExecutor              (coordinates study materialisation)
        │
        ├──► CohortGenerator           (temporal cohort portion)
        └──► ParameterSweepEngine      (parameter matrix portion)
                    │
                    ▼
           tuple[ParameterConfiguration, ...]   ← primitives only; domain-agnostic
                    │
                    ▼
        ResearchExecutor / policy factory       ← sole owner of config → policy materialisation
                    │  AllocationPolicy + WithdrawalPolicy
                    ▼
        SimulationRunner (frozen v0.1 black box)
```

### Dependency invariants

1. **Implementation decoupling from `ExperimentDefinition`:** Like `CohortGenerator`, `ParameterSweepEngine` has **zero** implementation dependency on `ExperimentDefinition`. Method signatures accept only primitive/scalar arguments, the construction helper `ParameterAxis`, and the public contract `ParameterConfiguration`. `ResearchExecutor` extracts or constructs axes before calling the engine.
2. **Peer relationship with `CohortGenerator`:** No import, call, or shared mutable state between the two. Both are pure generators coordinated only by orchestration.
3. **Engine boundary:** Depends at most on Python standard types. Must not import `engine.application` (runner, executor, pipeline). May later share only pure scalar concepts; it must not depend on portfolio or market services.
4. **No reverse dependency:** The frozen v0.1 Execution Engine remains unaware of `ParameterSweepEngine`.

---

## Relationship to `ExperimentDefinition` Policy Fields

`ExperimentDefinition` currently stores already-materialised:

- `allocation_policies: tuple[AllocationPolicy, ...]`
- `withdrawal_policies: tuple[WithdrawalPolicy, ...]`

`ParameterSweepEngine` does **not** replace those fields and does **not** write into `ExperimentDefinition`.  
`ParameterConfiguration` does **not** substitute for those policy fields and must never hold policy instances.

The intended division of labour is:

| Layer | Role |
| :--- | :--- |
| `ParameterSweepEngine` | Generates pure, domain-agnostic parameter grids (`ParameterConfiguration` sequences of primitive bindings only). |
| `ResearchExecutor` / policy factory | **Sole owners** of transforming `ParameterConfiguration` → concrete `AllocationPolicy` / `WithdrawalPolicy`. |
| Study construction | May pre-materialise policies into `ExperimentDefinition`, or leave materialisation to `ResearchExecutor`. |
| `ExperimentDefinition` | Holds the declarative study including policy sequences (and cohorts) — never raw execution state. |
| `ResearchExecutor` | Expands cohorts × (materialised) policies into individual simulation tasks and executes them. |

This preserves the frozen public contract of `ExperimentDefinition` while still enabling systematic grid construction for ERN-style studies, and keeps `ParameterConfiguration` free of engine domain types.

---

## Error Handling

- Domain invariant violations → `ValueError` with a descriptive message identifying the failing constraint.
- Fundamentally wrong Python types → `TypeError` where appropriate.
- Valid generation paths never raise.

There is no partial success mode: either a complete immutable result is returned, or an exception is raised before any incomplete product is exposed.

---

## Testing Requirements

### Unit Tests

The unit test suite for `ParameterSweepEngine` and its value objects must verify:

1. **Explicit axis construction:**
   - Valid sequences produce axes with identical ordered values.
   - Empty sequences raise `ValueError`.
   - Duplicate values raise `ValueError`.
   - Heterogeneous types raise `ValueError`.
   - Blank names raise `ValueError`.

2. **Range axis construction:**
   - Inclusive endpoint behaviour for integer ranges (e.g. `0` to `10` step `2` → `(0, 2, 4, 6, 8, 10)`).
   - Inclusive endpoint behaviour for research-critical float grids:
     - equity `0.0`–`1.0` step `0.05` → 21 values, first `0.0`, last `1.0`;
     - withdrawal `0.030`–`0.050` step `0.001` → 21 values, first `0.030`, last `0.050`.
   - Single-point range when `start == stop`.
   - Negative step with `start > stop`.
   - Zero step raises `ValueError`.
   - Inverted range with positive step raises `ValueError`.
   - NaN / Infinity inputs raise `ValueError`.

3. **Cartesian product:**
   - Single-axis product preserves order and cardinality.
   - Two-axis product has cardinality `|A| × |B|` and rightmost-axis-fastest ordering.
   - Three-axis glidepath-style product (e.g. 11 × 11 × 3 = 363) has correct length and ordering.
   - Empty axis list raises `ValueError`.
   - Duplicate axis names raise `ValueError`.

4. **`ParameterConfiguration` identity contract:**
   - Immutability (`FrozenInstanceError` on attribute assignment).
   - Equality and hashing independent of construction / insertion order of mapping keys.
   - Two configurations with the same bindings built from different axis orderings compare equal.
   - Empty mapping raises `ValueError`.
   - Blank keys raise `ValueError`.
   - Usable as `dict` / `set` keys (aggregation / optimizer readiness).
   - `names()` / `items()` return canonical sorted order.

5. **Public-contract surface minimisation:**
   - `ParameterConfiguration` is the only long-lived identity type emitted into consumer-facing result flows.
   - `ParameterAxis` is not required for equality tests of configurations and is not used as a simulated aggregation key in tests.

6. **Determinism:**
   - Two identical generation calls produce equal tuples element-wise (same product order).
   - No dependence on dict iteration order or set ordering for configuration identity.

7. **Decoupling & domain-agnostic content verification:**
   - Module does not import `ExperimentDefinition`, `CohortGenerator`, `SimulationRunner`, `SimulationExecutor`, `AllocationPolicy`, `WithdrawalPolicy`, `SimulationContext`, or `CohortSpecification`.
   - `ParameterConfiguration` instances hold only primitive scalars (`int`, `float`, `bool`, `str`); no nested domain objects.
   - Generated configurations expose no `decide` method and no policy/factory conversion methods.

8. **Forbidden behaviour guards (by design tests / static checks):**
   - No filesystem, network, or environment access in the generation path.

---

## Approval Criteria

This specification is approved when `ParameterSweepEngine` is defined as:

1. A **stateless** Research Layer utility that generates deterministic multi-dimensional parameter grids without executing simulations.
2. Introducing **exactly one** new long-lived Public Research Domain Contract — `ParameterConfiguration` — with content-based identity (unordered name→value bindings), stable hashing, and frozen immutability.
3. Keeping `ParameterConfiguration` **completely domain-agnostic**: only primitive parameter bindings; no references to `AllocationPolicy`, `WithdrawalPolicy`, `ExperimentDefinition`, `SimulationContext`, `CohortSpecification`, or any execution component.
4. Assigning ownership of `ParameterConfiguration` → policy materialisation exclusively to higher-level components (`ResearchExecutor` / future policy factory), never to `ParameterSweepEngine` or `ParameterConfiguration`.
5. Treating `ParameterAxis` only as a **public construction helper**, not as a result identity or aggregation key.
6. Justifying why raw `dict` / `MappingProxyType` / positional or sorted tuples are insufficient for the long-lived configuration role.
7. Emitting pure parameter configurations — **not** engine policy instances, cohorts, or experiment definitions.
8. Owning exclusively axis construction, Cartesian expansion, deterministic product ordering, and local validation.
9. Differentiating clearly from `CohortGenerator` (temporal windows) and from `ResearchExecutor` (study expansion, policy materialisation, and execution).
10. Documenting interactions of `ParameterConfiguration` with `ResearchExecutor`, `ResultAggregator`, `StrategyComparator`, and `SWROptimizer`.
11. Fully decoupled at the implementation level from `ExperimentDefinition`, `CohortGenerator`, engine policies, and the frozen v0.1 Execution Engine.
12. Providing fail-fast validation for empty/invalid axes, invalid ranges, and duplicate axis names.
13. Guaranteeing referential transparency and immutable outputs suitable for reproducibility and result indexing.
14. Sufficient to express the parameter surfaces required by ERN SWR Parts 19, 20/25, and 28 at the grid-generation level, without implementing adaptive search or SWR root-finding (v0.3).

---

## Out of Scope (Deferred)

The following are explicitly **not** part of this behavioural specification and must not appear in the v0.2.2 `ParameterSweepEngine` implementation:

| Deferred Item | Owner / Milestone |
| :--- | :--- |
| Mapping `ParameterConfiguration` → concrete `AllocationPolicy` / `WithdrawalPolicy` | **`ResearchExecutor` and/or future policy factory only** (never `ParameterSweepEngine` / `ParameterConfiguration`) |
| Cohort × parameter study matrix expansion | `ResearchExecutor` (v0.2.2) |
| Binary search / SWR root finding over withdrawal rate | `SWROptimizer` (v0.3) |
| Random or quasi-random sampling of parameter spaces | Future research utilities (post v0.3 as needed) |
| YAML/JSON persistence of grids | Infrastructure layer |
| Plotting parameter surfaces | Analysis layer |
| CAPE-series lookups or market-conditioned axis filtering | Study-specific research code / future components |

---

## Workflow Status

| Step | Artifact | Status |
| :--- | :--- | :--- |
| 1. Behavioural Specification | `PARAMETER_SWEEP_ENGINE_SPECIFICATION.md` | **Frozen / Approved** |
| 2. Architecture Review | `PARAMETER_SWEEP_ENGINE_ARCHITECTURE_REVIEW.md` | Submitted for approval |
| 3. Public API Review | `PARAMETER_SWEEP_ENGINE_PUBLIC_API.md` | Submitted for approval |
| 4. Implementation | (pending) | Blocked until steps 2–3 approved |
| 5. Code Review | (pending) | Not started |
| 6. Architecture Review (post-impl) | (pending) | Not started |
| 7. Validation | (pending) | Not started |
| 8. Commit | (pending) | Not started |
| 9. Tag milestone | (pending) | Not started |

**No implementation code is included with these review documents.**
