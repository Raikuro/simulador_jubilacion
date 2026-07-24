# Architecture Review: SWROptimizer (v0.3) — Working Draft

Status: Architecture Review (working draft — uncommitted)

Purpose

This Architecture Review documents the stable architectural decisions that
implement the approved behavioural specification (`RESEARCH_SWROPTIMIZER_SPECIFICATION.md`)
while preserving the provenance and dependency boundaries established by the
frozen `v0.2` deliverables.

Scope and approach

- Focus only on architecture-level responsibilities, dependency boundaries,
  and information flow. Implementation details (evaluation algorithm tactics,
  in-memory vs streaming choices, batching strategies) are intentionally
  excluded from this review; they remain implementation concerns unless they
  alter an architectural boundary.
- The `Evaluator` behavioural contract (from the frozen spec) is the single
  external dependency that defines the optimizer's interface to research
  outputs. Architectural decisions must preserve and revolve around this
  abstraction.

Architectural decisions

1) `Evaluator` as the primary dependency (central architectural decision)

- Rationale: the Behavioural Specification mandates that `SWROptimizer`
  depend only on an abstract `Evaluator`. Making this the central architectural
  decision enforces strong separation of concerns: the optimizer reasons only
  about observable evaluation outcomes and provenance, and remains agnostic to
  how evaluations are produced (local execution, cached artefacts, remote
  services, or mocks).
- Consequences:
  - `SWROptimizer` must never import or depend on `ResearchExecutor` or other
    concrete components; integrations must be mediated by implementations of
    the `Evaluator` abstraction.
  - Different evaluator implementations (cached, distributed, analytical,
    instrumented test doubles) are pluggable without architectural changes.

2) Dependency inversion and layering

- The optimizer is placed in the consumer/analysis layer and depends only on
  behavioural contracts (Evaluator, success predicate, ordering). It must not
  depend on lower-layer internals of `v0.2` or `v0.1`.
- The layer exposes only a behaviourally defined interface for invocation;
  callers remain responsible for providing evaluator and ordering contracts.

Explicit dependency direction

- The dependency direction is strictly one-way: `SWROptimizer -> Evaluator`.
  No concrete evaluator implementation may depend on `SWROptimizer`, and
  `SWROptimizer` must never acquire knowledge of evaluator implementations.

3) Provenance preservation as a data-flow invariant

- Rationale: provenance must survive each optimisation step without loss.
  This is an architectural requirement, not an implementation artifact.
- Specification:
  - Every observable evaluation outcome used in a selection decision must
    carry canonical provenance references sufficient to map back to `v0.2`
    planned-unit identities.
  - The architecture guarantees provenance forwarding and non-destructive
    propagation through the optimizer's data-flow; the mechanism (wrappers,
    forwarded references, or aggregation) is an implementation detail.

4) Responsibility boundaries (what `SWROptimizer` owns)

`SWROptimizer` owns:
- orchestration of candidate evaluation through the supplied `Evaluator`;
- orchestration of the optimisation process according to the supplied
  behavioural contracts;
- selection of the candidate according to the externally supplied
  ordering/selection criterion; and
- production of optimisation diagnostics and returned provenance for
  auditability.

`SWROptimizer` does NOT own:
- simulation execution, portfolio modelling, research planning, or parameter
  generation (these belong to `v0.1`/`v0.2` layers),
- persistence or long-term storage of results,
- user-facing visualisation or reporting,
- responsibility for what constitutes success or ordering semantics (those
  are provided externally).

5) Information flow and interfaces

- Inputs: behaviourally defined contracts only — an `Evaluator`, a success
  predicate, a candidate domain description, and an optimisation ordering
  (selection criterion). All inputs are opaque behavioural contracts.
- Internal flow: the optimizer treats evaluation outcomes as opaque objects
  with observable success indicators and provenance; decisions and diagnostics
  flow outward to the caller along with provenance references.
- Outputs: an immutable optimisation outcome containing the selected
  candidate (per supplied ordering), provenance, and diagnostic information.

Non-functional architectural considerations

- Determinism: the architecture must permit reproducible execution when the
  external contracts (evaluator, predicate, ordering) are deterministic. This
  influences execution choices (e.g., avoiding non-deterministic parallel
  scheduling) but does not mandate a specific implementation.
- Observability: the architecture must surface sufficient diagnostics and
  provenance to support auditing and validation of decisions.
- Concurrency: the architecture allows implementations to introduce parallelism
  internally, but only if they preserve the observable behaviour and
  provenance invariants.

Acceptance Criteria (Architecture Review)

- The architecture centers the `Evaluator` abstraction as the sole external
  dependency and documents why dependency inversion is required.
- The architecture specifies clear responsibility boundaries (owns / does not
  own) as listed above.
- Provenance preservation is stated as an invariant and mapped to the data
  flow (how provenance must be forwarded), without prescribing a concrete
  implementation mechanism.
- Non-functional concerns (determinism, observability, concurrency) are
  described at the architectural level with recommendations for implementers.

Next steps

- Review this draft for any remaining architectural issues; do not commit this
  document until you explicitly approve and freeze it.
