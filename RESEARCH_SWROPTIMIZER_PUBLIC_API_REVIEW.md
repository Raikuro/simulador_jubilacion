# Public API Review: SWROptimizer (v0.3)

Status: Public API Review (working draft — uncommitted)

## Review result

**Pending. This document defines the public SWROptimizer contract.**

---

## Public types

The stable public type names in this API are:

- `SWROptimizer`
- `EvaluationOutcome`
- `Provenance`
- `OptimizationOutcome`
- `InvalidInputError`
- `EvaluationError`
- `OptimizationError`

---

## Public methods and functions

The public API exposes a single stable consumer entrypoint:

### `SWROptimizer`

Public constructor and method signatures:

```python
class SWROptimizer:
    def __init__(
        self,
        evaluator: object,
        success_predicate: Callable[[EvaluationOutcome], bool],
        ordering: Callable[[EvaluationOutcome], Any],
    ) -> None:
        ...

    def optimize(self, candidate_domain: object) -> OptimizationOutcome:
        ...
```

The supplied evaluator must implement an `evaluate(candidate: object) -> EvaluationOutcome` method.

---

## Parameters

### `evaluator: object`

- A public protocol value that implements `evaluate(candidate: object) -> EvaluationOutcome`.
- This is a public behavioural contract: consumers may implement any object
  exposing this method to satisfy the API.

### `success_predicate: Callable[[EvaluationOutcome], bool]`

- Receives an `EvaluationOutcome` and returns `True` or `False`.

### `ordering: Callable[[EvaluationOutcome], Any]`

- Receives an `EvaluationOutcome` and returns a value used to compare or rank
  successful candidates.
- Ordering is entirely supplied by the caller; the optimizer does not define
  or infer ordering semantics.

### `candidate_domain: object`

- An opaque public value describing the candidate search space.
- The API does not require a specific concrete representation.

---

## Returns

### `OptimizationOutcome`

The public contract returns an immutable `OptimizationOutcome` with exactly:

- `candidate_value: object | None`
  - The selected candidate when one or more candidates satisfy the predicate.
  - `None` when no candidate satisfies the predicate.
- `provenance: Provenance`
  - A dedicated immutable provenance reference object.
  - Guarantees that consumers can correlate the selected candidate with the
    underlying `EvaluationOutcome` provenance used for the optimisation decision.
- `diagnostic: str`
  - A concise, consumer-visible explanation of the decision.

---

## Observable errors

The public API exposes these observable error types:

- `InvalidInputError`
  - Raised when a required parameter is missing, malformed, or invalid.
  - Examples: missing evaluator, undefined predicate, invalid `candidate_domain`.
- `EvaluationError`
  - Raised when the supplied evaluator fails while assessing a candidate.
- `OptimizationError`
  - Raised for observable optimisation contract failures that are not direct
    evaluation errors.

The API must not return ambiguous or partial `OptimizationOutcome` values when
these errors occur.

---

## Public invariants

The public contract guarantees:

- `optimize()` returns an immutable `OptimizationOutcome` on success.
- If one or more candidates satisfy the supplied predicate, the returned
  outcome references exactly one selected `candidate_value` according to the
  supplied ordering.
- If no candidate satisfies the supplied predicate, the returned outcome
  explicitly represents absence of selection through `candidate_value is None`.
- No partially populated successful outcome is permitted.
- `OptimizationOutcome` is immutable from the consumer's view.
- Invalid inputs are rejected before producing optimisation results.
- Evaluator failures are surfaced as errors instead of ambiguous outcomes.

---

## Approval guidance

Approve this document only if it defines the public API contract for
`SWROptimizer` without implementation details, internal helpers, or
architecture rationale.

Once approved, the public API may be frozen and implementation may proceed.
