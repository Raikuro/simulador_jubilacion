# `ParameterSweepEngine` Public API Review

## Purpose

This document defines and freezes the public API contract for:

- `ParameterConfiguration` — long-lived Public Research Domain Contract
- `ParameterAxis` — public construction helper
- `ParameterSweepEngine` — stateless parameter-space grid generator

of the Research Layer (`v0.2-research-layer`, Sub-Milestone `v0.2.2`).

After approval, implementation proceeds strictly against this frozen public interface.

**Baselines:**

- Behavioural specification: `PARAMETER_SWEEP_ENGINE_SPECIFICATION.md` (**frozen**)
- Architecture review: `PARAMETER_SWEEP_ENGINE_ARCHITECTURE_REVIEW.md`

---

## 1. Module Placement & Export Interface

### Canonical File Locations

```text
src/research/domain/parameter/configuration.py
src/research/domain/parameter/axis.py
src/research/domain/parameter/engine.py
```

### Public Export Contract

```python
# src/research/domain/parameter/__init__.py
from research.domain.parameter.configuration import ParameterConfiguration
from research.domain.parameter.axis import ParameterAxis
from research.domain.parameter.engine import ParameterSweepEngine

__all__ = [
    "ParameterConfiguration",
    "ParameterAxis",
    "ParameterSweepEngine",
]

# src/research/domain/__init__.py — re-exports the above

# src/research/__init__.py
from research.domain.cohort.specification import CohortSpecification
from research.domain.cohort.generator import CohortGenerator
from research.domain.experiment.definition import ExperimentDefinition
from research.domain.parameter.configuration import ParameterConfiguration
from research.domain.parameter.axis import ParameterAxis
from research.domain.parameter.engine import ParameterSweepEngine

__all__ = [
    "CohortSpecification",
    "CohortGenerator",
    "ExperimentDefinition",
    "ParameterConfiguration",
    "ParameterAxis",
    "ParameterSweepEngine",
]
```

External consumers import via the stable public interface:

```python
from research import (
    ParameterSweepEngine,
    ParameterConfiguration,
    ParameterAxis,
)
```

---

## 2. Shared Scalar Type Alias

```python
# Documented public type alias (may live in configuration.py or a tiny types module
# re-exported from research.domain.parameter). Not a runtime class.

ParameterScalar = int | float | bool | str
```

**Rules:**

- `bool` is distinct from `int` for axis type-homogeneity checks (`isinstance(True, int)` is True in Python; implementations must treat `bool` as its own scalar kind, e.g. via `type(x) is bool` vs `type(x) is int`).
- No other types are permitted in v0.2.2 (including `Decimal`, `None`, enums, domain objects).
- Future pure enums require an explicit contract revision.

---

## 3. Public Classes & Signatures

### 3.1 `ParameterConfiguration` (Public Research Domain Contract)

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ParameterConfiguration:
    """Immutable, domain-agnostic named assignment of primitive parameter values.

    Public Research Domain Contract. Represents one point in a multi-dimensional
    parameter space. Stores only primitive bindings — never policies, experiments,
    cohorts, or execution components.
    """

    values: Mapping[str, ParameterScalar]

    def __post_init__(self) -> None:
        """Validate and freeze bindings into an immutable internal mapping."""
        ...

    def get(self, name: str) -> ParameterScalar:
        """Return the value for ``name``.

        Raises:
            KeyError: If ``name`` is not present.
        """
        ...

    def names(self) -> tuple[str, ...]:
        """Return parameter names in canonical sorted order."""
        ...

    def items(self) -> tuple[tuple[str, ParameterScalar], ...]:
        """Return ``(name, value)`` pairs in canonical sorted order."""
        ...

    def __eq__(self, other: object) -> bool:
        """Content equality: same unordered set of name→value bindings."""
        ...

    def __hash__(self) -> int:
        """Stable hash derived from the canonical ordered form of bindings."""
        ...
```

#### Construction & coercion

1. Constructor accepts any `Mapping[str, ParameterScalar]` (e.g. `dict`).
2. `__post_init__` defensively copies into an immutable structure (implementation may use `MappingProxyType` over a plain `dict`, or a sorted tuple stored privately — the public field `values` must behave as an immutable mapping).
3. Empty mapping → `ValueError`.
4. Any key that is not a `str`, or is empty/whitespace-only → `ValueError`.
5. Any value whose type is not exactly one of `int`, `float`, `bool`, `str` (with `bool` recognized as its own kind) → `ValueError`.
6. Mutation of the instance or of its exposed mapping is impossible after construction.

#### Canonical identity

$$
\text{identity}(C) = \{ (n, v) \mid n \mapsto v \in C \}
$$

- Equality ignores insertion order.
- Hash is computed from the canonical form: pairs sorted by name ascending.
- Product index and source axes are not part of identity.

#### Domain-agnostic content (normative)

`ParameterConfiguration` **must not** accept, store, or expose:

- `AllocationPolicy`, `WithdrawalPolicy`
- `ExperimentDefinition`, `CohortSpecification`
- `SimulationContext` or any execution component
- callables, factories, or non-primitive nested objects

No conversion methods such as `to_allocation_policy()` are part of this API.

#### Illustrative error messages

| Condition | Message (illustrative) |
| :--- | :--- |
| Empty mapping | `"ParameterConfiguration values cannot be empty."` |
| Blank key | `"ParameterConfiguration parameter names cannot be empty or whitespace."` |
| Invalid value type | `"ParameterConfiguration values must be int, float, bool, or str."` |

---

### 3.2 `ParameterAxis` (Public construction helper)

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ParameterAxis:
    """Immutable named dimension of a research parameter space (construction-time only).

    Not a long-lived research identity. Not used as an aggregation or result key.
    """

    name: str
    values: tuple[ParameterScalar, ...]

    def __post_init__(self) -> None:
        """Validate name and value sequence invariants."""
        ...
```

#### Construction & coercion

1. `name` must be a non-empty, non-whitespace `str` → else `ValueError`.
2. `values` is coerced to `tuple`.
3. Empty `values` → `ValueError`.
4. Duplicate values (by Python `==`) → `ValueError`.
5. Heterogeneous scalar kinds within `values` → `ValueError` (`bool` ≠ `int`).
6. Equality: same `name` and same ordered `values` tuple.

**Lifecycle note:** `ParameterAxis` is retained only while building a product. Downstream research result schemas key on `ParameterConfiguration`, not `ParameterAxis`.

#### Illustrative error messages

| Condition | Message (illustrative) |
| :--- | :--- |
| Blank name | `"ParameterAxis name cannot be empty or whitespace."` |
| Empty values | `"ParameterAxis values cannot be empty."` |
| Duplicates | `"ParameterAxis values must be unique."` |
| Heterogeneous types | `"ParameterAxis values must be homogeneous in scalar type."` |

---

### 3.3 `ParameterSweepEngine` (Stateless utility)

```python
from __future__ import annotations

from typing import Sequence

from research.domain.parameter.axis import ParameterAxis
from research.domain.parameter.configuration import ParameterConfiguration


class ParameterSweepEngine:
    """Stateless utility for generating deterministic multi-dimensional parameter grids.

    Emits domain-agnostic ParameterConfiguration sequences only.
    Never materialises AllocationPolicy or WithdrawalPolicy instances.
    Never executes simulations.

    All methods are @staticmethod. This class is never instantiated.
    """

    @staticmethod
    def axis_from_values(
        name: str,
        values: Sequence[ParameterScalar],
    ) -> ParameterAxis:
        """Construct a ParameterAxis from an explicit ordered value sequence.

        Args:
            name: Non-empty axis name.
            values: Non-empty sequence of unique homogeneous scalar values.

        Returns:
            Validated ParameterAxis preserving the given value order.

        Raises:
            ValueError: If name is blank, values empty, contains duplicates,
                        or mixes scalar kinds.
        """
        ...

    @staticmethod
    def axis_from_range(
        name: str,
        start: int | float,
        stop: int | float,
        step: int | float,
    ) -> ParameterAxis:
        """Construct a ParameterAxis from a closed numeric range [start, stop].

        Emits the discrete arithmetic progression:

            v_i = start + i * step,  i = 0, 1, ..., n

        such that every v_i lies on the closed interval between start and stop
        (inclusive of both endpoints when they lie on the progression).

        Generation uses an integer-index formulation (not open-ended float
        accumulation) for cross-platform determinism.

        Args:
            name:  Non-empty axis name.
            start: Range start (included).
            stop:  Range end (included when on-progression).
            step:  Non-zero step. Positive when start <= stop; negative when
                   start >= stop. When start == stop, the axis is the singleton
                   (start,) and step must still be non-zero.

        Returns:
            ParameterAxis whose values are int when start, stop, and step are
            all int and the progression is integral; otherwise float.

        Raises:
            ValueError: If name is blank.
            ValueError: If step == 0.
            ValueError: If start/stop/step are bool, non-numeric, NaN, or ±Inf.
            ValueError: If step direction cannot progress from start toward stop
                        (except the start == stop singleton case).
        """
        ...

    @staticmethod
    def cartesian_product(
        axes: Sequence[ParameterAxis],
    ) -> tuple[ParameterConfiguration, ...]:
        """Compute the full Cartesian product of the given axes.

        Ordering (lexicographic, axis-declaration order):
            - Rightmost axis varies fastest.
            - Leftmost axis varies slowest.

        Equivalent nested-loop semantics:

            for v1 in axes[0].values:
                for v2 in axes[1].values:
                    ...
                        yield ParameterConfiguration({...})

        Args:
            axes: Non-empty sequence of ParameterAxis with unique names.

        Returns:
            Immutable tuple of ParameterConfiguration with length equal to
            the product of axis lengths. Each configuration contains exactly
            the bindings for all axis names.

        Raises:
            ValueError: If axes is empty.
            ValueError: If any element is None or not a ParameterAxis.
            ValueError: If two or more axes share the same name.
        """
        ...

    @staticmethod
    def generate(
        axes: Sequence[ParameterAxis],
    ) -> tuple[ParameterConfiguration, ...]:
        """Ergonomic alias of ``cartesian_product``.

        Semantics, ordering, validation, and return type are identical to
        ``cartesian_product``. Provided as the preferred entry point for
        research scripts.
        """
        ...
```

---

## 4. Method Contracts Summary

| Method | Input | Output | Notes |
| :--- | :--- | :--- | :--- |
| `axis_from_values` | name + explicit sequence | `ParameterAxis` | Preserves caller order; rejects duplicates |
| `axis_from_range` | name + closed numeric range | `ParameterAxis` | Inclusive endpoints; deterministic float grid |
| `cartesian_product` | ordered axes | `tuple[ParameterConfiguration, ...]` | Rightmost axis fastest |
| `generate` | ordered axes | `tuple[ParameterConfiguration, ...]` | Alias of `cartesian_product` |

---

## 5. Output Contracts

### 5.1 Product sequence guarantees

All product methods (`cartesian_product`, `generate`) share:

```python
tuple[ParameterConfiguration, ...]
```

| # | Guarantee | Detail |
| :--- | :--- | :--- |
| 1 | **Cardinality** | \(\prod_i \|A_i.\mathrm{values}\|\) |
| 2 | **Ordering** | Lexicographic; rightmost axis varies fastest |
| 3 | **Completeness** | Every combination appears exactly once |
| 4 | **Immutability** | Returned tuple and each element are immutable |
| 5 | **Primitive-only content** | Every configuration holds only `ParameterScalar` bindings |
| 6 | **Name coverage** | Each configuration contains exactly the axis names of the product |

Consumers must **not** re-sort unless they intentionally abandon product order. Configuration **identity** remains content-based regardless of position.

### 5.2 Range-axis numeric contract

For research-critical grids, implementations must satisfy these examples exactly (value count and endpoints):

| Call | Expected length | First | Last |
| :--- | ---: | ---: | ---: |
| `axis_from_range("e", 0.0, 1.0, 0.05)` | 21 | `0.0` | `1.0` |
| `axis_from_range("w", 0.030, 0.050, 0.001)` | 21 | `0.030` | `0.050` |
| `axis_from_range("i", 0, 10, 2)` | 6 | `0` | `10` |
| `axis_from_range("s", 5, 5, 1)` | 1 | `5` | `5` |

**Float comparison in tests:** absolute tolerance \(1 \times 10^{-12}\) when asserting range endpoints and progression members is permitted; configuration identity itself still uses exact `==`.

**Algorithmic requirement:** Prefer

```text
n = number of steps such that start + n*step is the last on-progression point within [start, stop]
values[i] = start + i * step  for i in 0..n
```

over open-ended `while` accumulation that can drift.

**Bool rejection:** `start`, `stop`, and `step` must not be `bool` (`True`/`False`), even though `bool` is a subclass of `int` in Python.

---

## 6. Validation & Fail-Fast Rules

| # | Condition | API surface | Error |
| :--- | :--- | :--- | :--- |
| 1 | Blank axis / parameter name | Axis, Config, engine factories | `ValueError` |
| 2 | Empty axis values | `ParameterAxis`, `axis_from_values` | `ValueError` |
| 3 | Duplicate axis values | `ParameterAxis`, `axis_from_values` | `ValueError` |
| 4 | Heterogeneous axis value kinds | `ParameterAxis`, `axis_from_values` | `ValueError` |
| 5 | `step == 0` | `axis_from_range` | `ValueError` |
| 6 | Non-finite or non-numeric range args (incl. `bool`) | `axis_from_range` | `ValueError` |
| 7 | Step direction incompatible with start/stop (non-singleton) | `axis_from_range` | `ValueError` |
| 8 | Empty axes sequence | `cartesian_product`, `generate` | `ValueError` |
| 9 | Non-`ParameterAxis` element in axes | `cartesian_product`, `generate` | `ValueError` |
| 10 | Duplicate axis names in product | `cartesian_product`, `generate` | `ValueError` |
| 11 | Empty configuration mapping | `ParameterConfiguration` | `ValueError` |
| 12 | Non-primitive configuration value | `ParameterConfiguration` | `ValueError` |

Expected generation with valid inputs never raises.

`TypeError` may still arise from fundamentally wrong Python types at the interpreter boundary; behavioural tests focus on the `ValueError` domain failures above.

---

## 7. Determinism Contract

`ParameterSweepEngine` is strictly deterministic:

- Identical axis inputs produce identical product tuples (same length, order, and values) on every call.
- No random generators, system clocks, environment variables, or global mutable state affect outputs.
- `ParameterConfiguration` equality/hash depends only on content (canonical sorted form for hashing).
- Determinism is required for study reproducibility and for cryptographic fingerprints in `ResearchReproducibilityManager`.

---

## 8. Explicit API Exclusions

The following are **explicitly excluded** from this public API:

1. **No policy materialisation:** No methods construct, wrap, or return `AllocationPolicy` / `WithdrawalPolicy`.
2. **No `ExperimentDefinition` / `CohortSpecification` parameters or fields.**
3. **No execution types:** No `SimulationContext`, runner, executor, or pipeline references.
4. **No adaptive search:** No binary search, random sampling, or optimizer loops.
5. **No dataset / market coupling:** No `Dataset` arguments; no feasibility filtering against history.
6. **No instance construction of the engine:** `ParameterSweepEngine` is never instantiated.
7. **No I/O:** No file, database, or network access.
8. **No `ParameterGrid` container type:** The ordered grid is `tuple[ParameterConfiguration, ...]`.
9. **No conversion helpers on `ParameterConfiguration`** such as `to_policies()` or `materialize()`.

---

## 9. Public API Usage Examples

### Static equity allocation grid (0%–100%, 5% steps)

```python
from research import ParameterSweepEngine

equity = ParameterSweepEngine.axis_from_range(
    "equity_weight", start=0.0, stop=1.0, step=0.05
)
configs = ParameterSweepEngine.generate([equity])

assert len(configs) == 21
assert configs[0].get("equity_weight") == 0.0
assert configs[-1].get("equity_weight") == 1.0
```

### Withdrawal rate grid (3.0%–5.0%, 0.1% steps)

```python
from research import ParameterSweepEngine

wr = ParameterSweepEngine.axis_from_range(
    "withdrawal_rate", start=0.030, stop=0.050, step=0.001
)
configs = ParameterSweepEngine.generate([wr])

assert len(configs) == 21
```

### ERN-style glidepath surface (start × end × duration)

```python
from research import ParameterSweepEngine

start_eq = ParameterSweepEngine.axis_from_range("glide_start", 0.0, 1.0, 0.10)
end_eq = ParameterSweepEngine.axis_from_range("glide_end", 0.0, 1.0, 0.10)
months = ParameterSweepEngine.axis_from_values("glide_months", [60, 120, 180])

configs = ParameterSweepEngine.generate([start_eq, end_eq, months])

assert len(configs) == 11 * 11 * 3  # 363
# Rightmost axis (glide_months) varies fastest:
assert configs[0].get("glide_months") == 60
assert configs[1].get("glide_months") == 120
assert configs[2].get("glide_months") == 180
```

### Configuration identity independent of construction order

```python
from research import ParameterConfiguration

a = ParameterConfiguration({"withdrawal_rate": 0.04, "equity_weight": 0.6})
b = ParameterConfiguration({"equity_weight": 0.6, "withdrawal_rate": 0.04})

assert a == b
assert hash(a) == hash(b)
assert a.names() == ("equity_weight", "withdrawal_rate")
```

### Ownership boundary (non-API; illustrative consumer side)

```python
# ParameterSweepEngine — generation only
configs = ParameterSweepEngine.generate([equity, wr])

# ResearchExecutor / policy factory — materialisation only (future component)
# for config in configs:
#     allocation = policy_factory.build_allocation(config)
#     withdrawal = policy_factory.build_withdrawal(config)
#     ...
```

---

## 10. Import & Dependency Constraints (implementation-binding)

The `research.domain.parameter` package **must not** import:

| Forbidden import root | Reason |
| :--- | :--- |
| `engine.application` | Execution machinery |
| `engine.domain.policies` | Policy materialisation is out of scope |
| `engine.domain.services` | Financial services |
| `research.domain.experiment` | Decoupling from `ExperimentDefinition` |
| `research.domain.cohort` | Peer isolation from cohorts |
| infrastructure / CLI packages | I/O and presentation layers |

Allowed: Python standard library, typing, and co-located parameter package modules.

---

## 11. Approval Requirement

This document freezes the public API contract for:

- `ParameterConfiguration`
- `ParameterAxis`
- `ParameterSweepEngine`

Implementation proceeds strictly against this frozen interface. No method signature, output contract, validation rule, identity semantic, or export path may be altered during implementation without returning to this review step.

| Workflow step | Artifact | Status |
| :--- | :--- | :--- |
| 1. Behavioural Specification | `PARAMETER_SWEEP_ENGINE_SPECIFICATION.md` | **Frozen / Approved** |
| 2. Architecture Review | `PARAMETER_SWEEP_ENGINE_ARCHITECTURE_REVIEW.md` | Submitted with this package |
| 3. Public API Review | `PARAMETER_SWEEP_ENGINE_PUBLIC_API.md` | **Submitted for approval** |
| 4. Implementation | (pending) | Blocked until this API is approved |

**No implementation code is included with this document.**
