# Behavioural Specification: SWROptimizer (v0.3)

Status: Behavioural specification (draft)

## Purpose

`SWROptimizer` is a consumer component whose sole behavioural responsibility
is to determine, in a reproducible and auditable way, a candidate optimisation
value that satisfies an externally supplied success predicate when evaluated
against a specified set of evaluation artefacts.

It is an analysis/consumer service that operates on outputs produced by the
frozen Research Infrastructure (`v0.2`) and the v0.1 execution engine. It
must not modify any upstream artefact or depend on internal behaviours of
frozen components.

## Scope and Ownership

- Ownership: `SWROptimizer` belongs to the `v0.3` consumer/analysis layer. Its
  implementation and operational concerns (persistence, UI, distributed
  orchestration) are out-of-scope for `v0.2`.
- The optimizer consumes evaluation information exclusively via an abstract
  `Evaluator` behavioural contract (defined below). It must never import or
  depend directly on `ResearchExecutor` or on any concrete evaluator
  implementation.
- It is strictly an analytical solver: responsibilities such as storage,
  plotting, user interaction, or scheduling belong to infrastructure or
  higher-level orchestration layers and are explicitly out-of-scope.

## Abstract Evaluator Behavioural Contract

The optimizer relies on an abstract `Evaluator` contract that describes only
the observable behaviour required to assess a candidate. Both the optimizer
and callers must treat the evaluator as a black box.

Evaluator contract (behavioural):
- `evaluate(candidate) -> EvaluationResult`
  - Accepts a candidate optimisation value (type-agnostic) and returns an
    immutable `EvaluationResult` containing at minimum a deterministically
    computed `success_indicator` and provenance references to source planned
    unit identities that contributed to the evaluation.
- The optimizer validates `EvaluationResult` invariants but does not inspect
  or assume any internal behaviour of the evaluator beyond this contract.

Notes:
- The term `candidate` is intentionally type-agnostic to allow optimisation
  over different variable types (numeric, ordinal, discrete choices, etc.).
- The evaluator contract is the sole external dependency of `SWROptimizer`.

## Observable Behavioural Contract

Inputs
- an `Evaluator` instance adhering to the behavioural contract above, or a
  non-empty ordered collection of evaluation artefact identities that the
  caller expects the evaluator to use;
- an externally supplied success predicate (behavioural contract) that maps
  an `EvaluationResult` to boolean success/failure; and
- a clearly described candidate domain appropriate to the optimisation
  variable (the domain description is type-appropriate and not constrained
  by the optimizer specification).

Outputs
- an immutable `SWROptimizerResult` containing:
  - `candidate_value`: the optimisation candidate selected as satisfying the
    externally supplied success predicate (or an explicit absence value when
    none found);
  - `provenance`: canonical references that map back to the `EvaluationResult`
    objects (and through those to original planned unit identities) used to
    confirm the candidate; and
  - `diagnostic`: a concise, human-readable explanation of the outcome.

Success semantics
- The optimizer provides an unambiguous decision: whether a candidate that
  satisfies the externally provided success predicate exists within the
  declared domain. The semantics of the predicate itself are an external
  contract and are not defined by `SWROptimizer`.

Provenance preservation
- For any reported `candidate_value`, the optimizer must include or reference
  a lossless mapping back to the `EvaluationResult` object(s) that were used
  to verify that candidate. This mapping must be sufficient to identify the
  originating planned unit identities in `v0.2` provenance terms.

Determinism
- Given the same inputs (including an evaluator that produces identical
  `EvaluationResult` values for identical candidates), the optimizer must
  produce identical outputs. Any non-determinism must be declared in the
  evaluator or predicate contract and surfaced to callers.

Failure behaviour
- The optimizer validates inputs prior to any evaluation. If inputs are
  invalid (e.g., missing evaluator, empty candidate domain, malformed
  predicate), it raises `InvalidInputError` and performs no evaluations.
- If the evaluator raises an error for a candidate, the optimizer wraps the
  error in `EvaluationError` and propagates it; the optimizer must not swallow
  exceptions or return misleading partial results.

Non-responsibilities (explicit)
- Must not: persist results, produce visualisations, schedule or orchestrate
  distributed runs, or mutate any upstream artefact.
- Must not: assume or depend on `ResearchExecutor` or any concrete evaluator
  implementation; all interactions must occur via the abstract `Evaluator`
  behavioural contract.

Dependencies & Architectural Layering
- Depends only on: the abstract `Evaluator` behavioural contract and the
  public provenance identity contracts exported by `v0.2`.
- Must not depend on: private internals of `v0.2` or `v0.1`, or any concrete
  evaluator implementations.

Acceptance Checklist (behavioural criteria)
- `Evaluator` behavioural contract is defined and documented.
- The optimizer returns a clear decision output indicating candidate presence
  or absence relative to the externally supplied success predicate.
- Reported candidates include lossless provenance mapping to evaluation and
  planned-unit identities.
- Decision outputs are deterministic given identical evaluator outputs and
  inputs, as stated in the Determinism section.
