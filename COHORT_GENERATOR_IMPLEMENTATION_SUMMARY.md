# CohortGenerator Implementation Summary

## Status: COMPLETE & FROZEN

**Component:** `CohortGenerator`  
**Sub-Milestone:** `v0.2.1` — Experiment Definition & Cohort Generation  
**Date Completed:** 2026-07-22  

---

## Deliverables

### Documentation (Frozen)

| Document | Purpose |
|---|---|
| `COHORT_GENERATOR_SPECIFICATION.md` | Behavioural specification — approved |
| `COHORT_GENERATOR_ARCHITECTURE_REVIEW.md` | Architecture review — approved with clarification |
| `COHORT_GENERATOR_PUBLIC_API.md` | Frozen public API contract |

### Implementation

| File | Role |
|---|---|
| `src/research/domain/cohort/generator.py` | `CohortGenerator` stateless utility class |
| `src/research/domain/cohort/__init__.py` | Cohort package exports (updated) |
| `src/research/domain/__init__.py` | Research domain exports (updated) |
| `src/research/__init__.py` | Top-level research package exports (updated) |

### Tests

| File | Coverage |
|---|---|
| `tests/test_cohort_generator.py` | 48 unit tests across 5 test classes |

---

## Design Decisions (Frozen Rationale)

### 1. Stateless Pure Utility

`CohortGenerator` is implemented as a class with all `@staticmethod` methods. It is never instantiated. This was chosen because:

- It owns no state; its behaviour depends entirely on its arguments.
- It is concurrency-safe without locks or shared mutable data.
- It is trivially testable in isolation.
- A `Protocol` or ABC is unnecessary — strategy selection is a caller responsibility.

### 2. Filtering vs. Validation Split

Three strategies with two distinct infeasibility behaviours:

| Strategy | Infeasibility Handling | Rationale |
|---|---|---|
| `generate_rolling_monthly` | Silent tail exclusion | Capability query — returns what is available |
| `generate_range` | Silent tail exclusion + `ValueError` if result empty | Constrained research query — empty era indicates misconfigured study |
| `from_start_dates` | Fail-fast `ValueError` per date | Reproducibility contract — partial results corrupt study integrity |

The distinction between **capability queries** (rolling/range), **constrained research queries** (range), and **explicit reproducibility requests** (from_start_dates) is an intentional API decision, not an implementation detail.

### 3. `generate_range` Raises on Empty Result

If the requested interval is syntactically valid but contains no feasible cohorts, `generate_range` raises `ValueError` rather than returning an empty tuple. Returning empty would create a silent failure where `ResearchExecutor` runs zero simulations and produces a vacuous result with no diagnostic signal. The `ValueError` surfaces misconfigured study era selection at cohort generation time.

### 4. Deduplication Semantics in `from_start_dates`

`dict.fromkeys(start_dates)` deduplicates while preserving insertion order (first occurrence retained). However, insertion order is immediately discarded by the final chronological sort. **Chronological ordering by `start_date` always takes precedence.** Caller input order has no effect on the returned sequence.

### 5. Output Guarantees

All three strategies enforce:
- **Ordering:** `start_date` ascending, unconditional.
- **Uniqueness:** no duplicate `start_date` values, canonical identity only.
- **Feasibility:** every cohort satisfies `horizon_months` remaining history.
- **Immutability:** `tuple[CohortSpecification, ...]` with frozen elements.

---

## Validation Results

| Check | Result |
|---|---|
| `CohortGenerator` unit tests | 48 / 48 passed |
| Full regression suite | 231 / 231 passed |
| `mypy src/research` | 0 errors (12 source files) |

---

## Export Surface

```python
from research import CohortGenerator
from research import CohortSpecification
from research import ExperimentDefinition
```

---

## Next Component

`ParameterSweepEngine` — Sub-Milestone `v0.2.2`  
First step: Behavioural specification.
