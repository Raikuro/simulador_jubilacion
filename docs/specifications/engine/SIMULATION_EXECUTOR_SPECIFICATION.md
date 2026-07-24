# SimulationExecutor Behavioural Specification

## Purpose

`SimulationExecutor` orchestrates an experiment composed of one or more independent simulation requests.

It delegates each individual simulation to `SimulationRunner`, collects the resulting immutable `SimulationResult` values, and returns an immutable experiment-level result for consumption by the Research layer.

It is an application-layer coordinator. It contains no financial model, no monthly execution behaviour, and no statistics calculations.

---

## Public API

The public API must expose a dependency-injected executor and one operation that executes an experiment:

```python
class SimulationExecutor:
    def __init__(self, simulation_runner: SimulationRunner) -> None: ...

    def execute(self, experiment: SimulationExperiment) -> ExperimentResult: ...
```

The exact names of the experiment request and aggregate-result types must follow the existing public domain/research naming conventions when those types are introduced. Their contract must provide:

- an ordered collection of simulation requests or `SimulationContext` values;
- stable identification of each requested simulation sufficient to associate results with requests;
- an immutable aggregate result containing the completed individual `SimulationResult` values.

The executor must expose no API for executing monthly pipeline steps, calculating financial values, or constructing `SimulationStatistics` directly.

---

## Responsibilities

The executor is responsible only for:

- validating the structural completeness of an experiment request before execution;
- managing the lifecycle of a multi-simulation experiment;
- invoking `SimulationRunner` once for every requested simulation;
- preserving the experiment's declared simulation order in the aggregate result;
- associating every completed result with its requested simulation identity;
- aggregating completed `SimulationResult` values into the experiment-level result;
- returning an immutable result suitable for the Research layer.

The executor may coordinate progress or lifecycle status only when such status is application-level metadata and does not alter simulation semantics.

---

## Forbidden Responsibilities

The executor must not:

- implement market evolution, withdrawals, allocations, rebalancing, valuation, inflation adjustment, depletion, or any other financial calculation;
- execute, reorder, skip, or otherwise manage individual monthly pipeline steps;
- construct or mutate `SimulationState`;
- construct `SimulationStatistics` or calculate derived simulation metrics;
- duplicate `SimulationRunner` validation, state initialization, termination, or final-result construction behaviour;
- alter a `SimulationContext`, `SimulationResult`, timeline, statistics object, policy, dataset, or portfolio;
- select historical market data or access CSV, SQLite, filesystem, configuration, logging, CLI, or presentation infrastructure;
- perform optimization, binary search, strategy selection, or research-study definition;
- conceal an unexpected runner failure by converting it into a successful or partial experiment result.

---

## Lifecycle

For a valid experiment, execution proceeds in this order:

1. Receive the experiment request and its ordered simulation requests.
2. Validate the experiment structure, including non-null requests and unambiguous identities.
3. For each request in declared order, obtain its `SimulationContext` and delegate exactly one execution to `SimulationRunner`.
4. Receive the completed immutable `SimulationResult` from the runner without changing it.
5. Associate the result with the originating request identity and retain it in the same declared order.
6. Once every requested simulation completes, construct and return the immutable aggregate experiment result.

An empty experiment is valid only if the experiment contract explicitly permits it. If permitted, it must return a valid immutable aggregate with zero results and must not invoke the runner.

The executor must not start the next phase of an experiment by reusing mutable state from a prior simulation. Each runner invocation receives the request's own context.

---

## Dependency Rules

- `SimulationExecutor` belongs to the application layer.
- It receives `SimulationRunner` through constructor injection; it must not instantiate a concrete runner internally.
- It depends only on public contracts of the experiment request, `SimulationContext`, `SimulationRunner`, `SimulationResult`, and aggregate result types.
- `SimulationRunner` remains the sole owner of a single simulation's lifecycle and final result construction.
- `SimulationPipeline` remains the sole owner of ordered monthly orchestration.
- `SimulationStatisticsBuilder` remains the sole owner of statistics generation from completed simulation state.
- Research defines experiments; the executor executes them but must not define their scientific assumptions.
- Infrastructure dependencies, if added later for progress reporting or persistence, must be injected through interfaces and must not be required for the core execution path.

---

## Failure Behaviour

Expected simulation outcomes are represented by each returned `SimulationResult`, including simulations that terminate with a modelled failure state. Such outcomes do not cause the executor to raise and do not prevent aggregation of later requested simulations.

The executor must raise a clear exception for programming or configuration errors, including:

- a missing experiment or malformed simulation request;
- a missing, duplicate, or ambiguous simulation identity;
- a missing required context;
- an invalid injected runner collaborator;
- a runner contract violation, such as no result returned for an invocation.

Unexpected exceptions raised by `SimulationRunner` must propagate unchanged, or be wrapped only in a documented application-level execution exception that preserves the original exception as its cause and identifies the affected simulation. The executor must stop aggregation at that point and must not publish a result that implies the experiment completed.

---

## Determinism

Given the same immutable experiment request, simulation contexts, injected runner behaviour, and execution order, the executor must return an equivalent aggregate result with the same ordering and request-to-result association.

The executor must not depend on randomness, system time, filesystem state, environment state, network state, or unordered collection iteration. It must not introduce concurrency whose scheduling could change observable result order or failure behaviour.

Any optional elapsed-time or progress instrumentation must be observational only and must not change returned simulation or aggregate financial results.

---

## Required Tests

Unit tests must verify:

- the executor accepts a runner through dependency injection and does not instantiate one itself;
- one experiment request invokes the runner exactly once per requested simulation;
- each invocation receives the corresponding original context without mutation;
- results preserve the declared request order and identity association;
- the returned aggregate result is immutable;
- modelled failed `SimulationResult` values are aggregated normally;
- a valid empty experiment follows the approved empty-experiment contract;
- malformed requests and invalid identities raise clear errors before runner execution;
- unexpected runner errors preserve failure semantics and do not yield a completed aggregate result;
- execution contains no financial calculations and does not access pipeline steps or statistics builders.

Runner-integration tests must verify:

- multiple valid contexts can be executed through a real or contract-faithful `SimulationRunner`;
- the aggregate preserves the exact individual results produced by the runner;
- executor use does not change runner, pipeline, state, timeline, or statistics behaviour;
- repeated execution with equal inputs produces equivalent ordered aggregate results.

Regression tests must verify that existing `SimulationRunner`, `SimulationPipeline`, and `SimulationStatisticsBuilder` public behaviour remains unchanged.

---

## Integration Requirements

- The executor must be introduced without changing the established financial pipeline.
- The executor must sit above `SimulationRunner`; Research invokes the executor rather than duplicating multi-simulation coordination.
- Each simulation remains isolated at the application boundary: no state or result of one simulation may be used as mutable input to another.
- Aggregate result types must be immutable and expose enough information for Research to compare or persist simulation outcomes without recalculating them.
- Any persistence, reporting, CLI, optimizer, or experiment-builder integration must consume executor inputs and outputs through public contracts; those concerns must not be embedded in the executor.
- Existing single-simulation use of `SimulationRunner` remains supported and unchanged.

---

## Approval Criteria

This specification is approved when it unambiguously defines an executor that:

- orchestrates experiments only;
- delegates each single simulation exclusively to `SimulationRunner`;
- preserves the responsibilities of `SimulationPipeline` and `SimulationStatisticsBuilder`;
- aggregates immutable individual results deterministically;
- distinguishes modelled simulation failures from orchestration/configuration failures;
- introduces no financial logic, infrastructure coupling, or architectural redesign;
- can be implemented with focused unit, integration, and regression tests without changing existing engine behaviour.

Implementation of `SimulationExecutor` may begin only after this specification has been reviewed and explicitly approved.
