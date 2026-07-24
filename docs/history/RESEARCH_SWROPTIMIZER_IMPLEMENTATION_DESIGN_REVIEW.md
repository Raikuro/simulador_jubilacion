# Implementation Design Review: SWROptimizer (v0.3)

Status: Implementation Design Review (working draft — uncommitted)

## Purpose

This document defines the internal implementation design for `SWROptimizer`
without producing executable production code. It describes the internal
optimization flow, the selected binary search execution strategy, interaction
with the external `Evaluator`, internal state and control flow, construction of
`OptimizationOutcome`, internal invariants, and the observable error-handling
strategy.

## Scope

- Internal structure of `SWROptimizer` only.
- Binary search as the primary candidate refinement strategy.
- `Evaluator` interaction and outcome handling.
- Internal state, control flow, and outcome construction.
- Design-level sequence diagrams and pseudocode.
- Not included: concrete module names, package wiring, or production-ready code.

## Assumptions

1. `SWROptimizer` is implemented as an internal controller operating over an
   externally supplied candidate domain and evaluation contract.
2. The public API remains generic. Internally, the implementation uses a
   binary-search-friendly representation of the candidate domain.
3. The evaluator is an external behavioural protocol that exposes:
   - `evaluate(candidate: object) -> EvaluationOutcome`
4. The `EvaluationOutcome` includes at least:
   - observable success/failure indicator,
   - immutable provenance references,
   - enough data for the caller-supplied `ordering` and `success_predicate` to
     operate.
5. The optimizer implementation is allowed to require an internal adapter for
   the public `candidate_domain` that converts it into a numeric, ordered search
   space for binary search.

## High-level implementation architecture

The internal implementation consists of the following conceptual
subsystems:

- `InputValidator`
  - Confirms public inputs satisfy the minimal contract.
  - Rejects malformed evaluator, predicate, ordering, or candidate domain.
- `CandidateDomainAdapter`
  - Converts the opaque public `candidate_domain` into an internal ordered
    search representation suitable for binary search.
  - Exposes methods for `lower_bound`, `upper_bound`, `midpoint`, and
    convergence checks.
- `SearchController`
  - Orchestrates the binary search loop.
  - Maintains internal search state and the best successful candidate seen so
    far.
- `EvaluatorAdapter`
  - Invokes the external evaluator protocol.
  - Validates returned `EvaluationOutcome` invariants.
- `OutcomeBuilder`
  - Creates the immutable `OptimizationOutcome` from the selected candidate,
    provenance, and diagnostics.
- `DiagnosticsBuilder`
  - Produces human-readable decision explanations.

## Internal roles and responsibilities

### Internal controller

The implementation centers on a controller that:

- validates inputs,
- adapts the public candidate domain,
- executes the binary search loop,
- updates internal state,
- builds the final `OptimizationOutcome`.

This controller is the single internal authority for search control flow.

### Candidate domain adapter

The adapter is an internal implementation concept that defines how the public
`candidate_domain` is consumed.

It provides:

- `initial_lower_bound()`
- `initial_upper_bound()`
- `midpoint(lower, upper)`
- `is_converged(lower, upper)`
- `candidate_to_public(candidate)` if the internal representation differs from
  the public candidate value.

This adapter is intentionally internal and not part of the public API. Its
responsibility is to preserve the public contract while enabling binary search.

### Evaluator adapter

The evaluator adapter shields the internal search loop from evaluator details.
It is responsible for:

- invoking `evaluate(candidate)` on the supplied evaluator,
- ensuring the returned `EvaluationOutcome` is immutable,
- confirming the outcome contains provenance and a success indicator,
- wrapping evaluator failures in observable error types if necessary.

### Outcome builder

The internal outcome builder constructs the final public `OptimizationOutcome`
from the selected candidate and the associated `EvaluationOutcome`.
It ensures that:

- `candidate_value` is exactly the selected public candidate or `None`,
- `provenance` is extracted from the selected `EvaluationOutcome`,
- `diagnostic` reflects the completed search result.

## Binary search execution strategy

The optimizer uses a binary search strategy internally to locate the best
candidate that satisfies the supplied `success_predicate`.

### Binary search contract

The internal binary search assumes:

- candidates can be ordered along a one-dimensional search axis,
- the candidate domain can produce a midpoint between bounds,
- the success predicate is monotonic in the search direction implied by the
  domain and ordering.

These assumptions are internal. The public API remains intentionally generic.

### Boundary state

The internal search state tracks:

- `lower_bound` — the current lowest candidate bound where success is still
  possible,
- `upper_bound` — the current highest candidate bound where failure has been
  observed,
- `best_successful_evaluation` — the best known successful candidate outcome,
  ranked by the supplied ordering,
- `iteration_count` — the current binary search iteration used for convergence
  and safety.

On each loop iteration:

1. The controller requests a midpoint candidate from the adapter.
2. The evaluator assesses the candidate.
3. The controller applies `success_predicate` to the outcome.
4. If the outcome is successful:
   - the candidate becomes a successful contender,
   - the internal ordering comparator determines whether it is better than the
     current `best_successful_evaluation`,
   - the `lower_bound` is advanced to move the search toward more aggressive
     candidates.
5. If the outcome is unsuccessful:
   - the `upper_bound` is moved to the failed candidate,
   - the search focuses on safer candidates.

### Ordering and candidate selection

The implementation does not define optimisation ordering. Instead, it:

- accepts the caller-supplied `ordering` as a comparator for successful
  outcomes,
- uses ordering only to maintain the best successful candidate observed, and
- uses the candidate domain adapter and monotonicity assumptions to select
  which side of the interval to explore next.

This preserves the public contract while making the internal search strategy
deterministic.

### Termination criteria

The binary search loop terminates when:

- the adapter reports the bounds have converged to within the domain's
  resolution or tolerance,
- a fixed maximum number of iterations is reached for safety,
- or the domain no longer permits refinement.

On termination, the implementation uses the best successful candidate if
available, otherwise it returns an outcome representing absence of selection.

## Interaction with the Evaluator

### Invocation

The controller interacts with the evaluator exclusively through the public
evaluation protocol.

- Each candidate is passed to `evaluate(candidate)`.
- The evaluator returns an `EvaluationOutcome`.

### Outcome validation

The implementation validates each returned `EvaluationOutcome`:

- it must be immutable,
- it must expose a success indicator,
- it must include provenance references.

If an outcome violates these invariants, the internal evaluator adapter
converts the condition into an observable `EvaluationError` or
`OptimizationError`.

### Provenance handling

Whenever a candidate is selected as the current best successful option, the
implementation retains the corresponding `EvaluationOutcome` provenance.
The final `OptimizationOutcome` uses that provenance object directly.

## Internal state and control flow

### High-level flow

1. Validate inputs.
2. Adapt the public `candidate_domain` to the internal binary search domain.
3. Initialize `lower_bound`, `upper_bound`, and no successful candidate.
4. Execute the binary search loop.
5. Build the final `OptimizationOutcome`.

### State snapshot

The internal state during search includes:

- `candidate_domain_adapter`
- `lower_bound`
- `upper_bound`
- `current_candidate`
- `best_successful_outcome`
- `best_failure_outcome` (optional, for diagnostics)
- `evaluation_count`
- `search_iteration`

### Control flow outline

The controller's internal sequence is:

- pre-flight validation
- if the domain adapter cannot support binary search, raise `InvalidInputError`
- while not converged:
  - obtain midpoint candidate
  - evaluate candidate
  - classify outcome success/failure
  - update search boundaries and best-success state
- build and return final `OptimizationOutcome`

## Construction of `OptimizationOutcome`

The final `OptimizationOutcome` is assembled from:

- `candidate_value`
  - the public candidate value from the selected best successful outcome,
    or `None` if no successful candidate exists;
- `provenance`
  - the provenance object carried by the selected `EvaluationOutcome`;
- `diagnostic`
  - a concise summary of the search result and the reason for termination.

The builder ensures immutability and public contract compliance.

## Diagnostic information

Diagnostic information is produced internally to explain:

- whether a successful candidate was found,
- how many evaluations were performed,
- the final candidate bounds at termination,
- why the search terminated.

This diagnostics object is public-facing as a string in the outcome, but the
internal builder may use richer data during construction.

## Error handling strategy

### Input validation errors

- Missing or malformed evaluator, predicate, ordering, or candidate domain
  raises `InvalidInputError`.
- Unsupported candidate domains for binary search also raise
  `InvalidInputError`.

### Evaluation failures

- Any exception from the evaluator is captured and surfaced as
  `EvaluationError`.
- If the evaluator returns an unexpected or invalid outcome, the controller
  treats it as an `EvaluationError` or `OptimizationError` depending on the
  nature of the defect.

### Ordering and predicate failures

- Exceptions thrown by `success_predicate` or `ordering` are treated as
  `OptimizationError`.
- These failures abort the search; no partial successful outcome is returned.

### Search safety

- The implementation protects against infinite loops with explicit convergence
  and iteration guards.
- If the search cannot converge despite repeated refinement, it terminates with
  a descriptive `OptimizationError`.

## Internal invariants

The implementation preserves these internal invariants:

- the candidate domain adapter always exposes a valid search interval;
- `lower_bound` and `upper_bound` bracket the search space,
- `best_successful_outcome`, when present, is the highest-ranked successful
  outcome observed according to the caller-supplied ordering,
- evaluated `EvaluationOutcome` objects remain immutable and preserve provenance,
- the search loop terminates when the adapter indicates convergence or when the
  iteration guard is reached,
- no `OptimizationOutcome` is built until search termination or an error is raised.

## Pseudocode example

The following pseudocode illustrates the intended internal search flow.

```text
controller = SWROptimizerController(
    evaluator, success_predicate, ordering, candidate_domain
)

controller.validate_inputs()
adapter = controller.adapt_domain(candidate_domain)

lower, upper = adapter.initial_bounds()
best_success = None
iteration = 0

while not adapter.is_converged(lower, upper):
    candidate = adapter.midpoint(lower, upper)
    outcome = controller.evaluate(candidate)

    if success_predicate(outcome):
        best_success = controller.select_best_success(best_success, outcome)
        lower = adapter.next_lower_bound(candidate)
    else:
        upper = adapter.next_upper_bound(candidate)

    iteration += 1
    if iteration > controller.max_iterations:
        raise OptimizationError("Binary search did not converge")

if best_success is None:
    return controller.build_outcome(None, None, "No candidate satisfied the predicate")

return controller.build_outcome(
    best_success.candidate,
    best_success.provenance,
    "Selected best successful candidate"
)
```

## Sequence diagram

```text
CandidateDomain -> SWROptimizerController: adapt_domain()
SWROptimizerController -> CandidateDomainAdapter: initial_bounds()
SWROptimizerController -> Evaluator: evaluate(candidate)
Evaluator -> SWROptimizerController: EvaluationOutcome
SWROptimizerController -> success_predicate: evaluate(outcome)
SWROptimizerController -> ordering: rank(outcome)
SWROptimizerController -> OutcomeBuilder: build(selected_outcome)
OutcomeBuilder -> SWROptimizerController: OptimizationOutcome
```

## Next steps

- Review this design for completeness and consistency with the frozen
  behavioural, architecture, and public API reviews.
- If approved, implementation can proceed with minimal ambiguity.
- If implementation uncovers an actual issue, revisit the design and update
  this review before committing code.
