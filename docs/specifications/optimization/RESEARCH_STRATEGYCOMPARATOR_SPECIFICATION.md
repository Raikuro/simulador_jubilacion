# Behavioural Specification: StrategyComparator (v0.3)

Status: Behavioural specification (draft)

## Purpose

`StrategyComparator` is a consumer component responsible for producing
deterministic, auditable comparative analytics between labelled strategies.
Each strategy is an externally defined label that maps to a set of evaluation
artefacts or to an abstract evaluator capable of materialising them.

This component focuses exclusively on pure analysis: grouping, reduction, and
deterministic ranking. It must not perform persistence, plotting, or orchestrate
execution beyond calling an abstract evaluator boundary.

## Scope and Ownership

- Ownership: `StrategyComparator` belongs to the `v0.3` consumer/analysis layer.
- It consumes evaluation artefacts via an abstract `Evaluator` contract or via
  precomputed `ExperimentRun`/`EvaluationResult` inputs. It must not assume any
  concrete evaluator implementation.
- Responsibilities such as storage, presentation, or distributed orchestration
  are out-of-scope and belong to infrastructure or higher-level orchestration.

## Observable Behavioural Contract

Inputs
- a mapping from `label` -> non-empty ordered collection of evaluation
  artefacts or to an `Evaluator` capable of producing them on demand;
- a grouping dimension selection (e.g., `parameter_config`, `cohort`, or `global`);
- an explicit list of metrics to compute (defaults may be provided but must be
  overridable by the caller);
- an explicit deterministic ranking rule (primary metric and tie-breakers).

Outputs
- an immutable `StrategyComparisonReport` containing:
  - per-label aggregated metrics for each group;
  - canonical grouping keys and provenance references to the original planned units;
  - a deterministic ranking of labels per group according to the specified rule;
  - summary diagnostics (sample sizes, warnings about insufficient data);
  - no side-effects (no persistence or external I/O in the core component).

Determinism and stability
- Aggregation and ranking must be stable: identical input values and ranking
  rules must produce identical ordered outputs. Tie-breaking must be explicit
  and deterministic (for example: secondary stable sort by label).

Provenance preservation
- Every aggregated value must include or be derivable from a lossless mapping
  back to the source planned unit identities that contributed to it.

Failure behaviour
- The component validates inputs upfront. If invalid, it raises
  `InvalidInputError` and performs no aggregations.
- If any evaluator call fails, the component must wrap the error in
  `EvaluationError` and propagate it. Partial aggregation results must not be
  returned when validation or execution errors occur unless explicitly agreed
  in a separate error-handling policy.

Non-responsibilities (explicit)
- Must not: perform persistence, produce plots, trigger long-running
  orchestrations, mutate upstream artefacts, or assume evaluator internals.

Dependencies & Architectural Layering
- Depends on: public provenance identity contracts from `v0.2` and an abstract
  `Evaluator` or precomputed `EvaluationResult` inputs.
- Must not depend on: private internals of `v0.2` or `v0.1`.

Acceptance Checklist
- Canonical grouping key semantics confirmed (how `ParameterConfiguration` is represented).
- Deterministic ranking semantics validated with representative fixtures.
- Provenance mapping verified for aggregated outputs.
