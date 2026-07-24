# SimulationExecutor Architecture Review

## Review Result

**Approved with one implementation-time API clarification.**

The behavioural specification defines `SimulationExecutor` as an application-level experiment coordinator only. It preserves the existing execution-engine ownership boundaries and introduces neither financial logic nor a reverse dependency.

Before implementation begins, the concrete public contract names for the experiment request, its simulation-request identity, and the immutable aggregate result must be selected from the established public naming conventions. This is a naming and contract-finalization clarification only; it does not change the component's responsibilities or add a feature.

---

## Architectural Assessment

`SimulationExecutor` has one responsibility: coordinate an experiment containing multiple independent single-simulation requests and aggregate their completed results.

Its lifecycle is deliberately above the single-simulation lifecycle. It delegates exactly one execution per request to `SimulationRunner`, receives completed `SimulationResult` values unchanged, and assembles an experiment-level immutable result. This is application orchestration, not execution-engine or domain behaviour.

No hidden monthly orchestration is introduced. The specification explicitly prohibits executing, ordering, skipping, or managing pipeline steps, as well as state construction and mutation. It also prohibits financial computations and statistical generation.

---

## Public API Review

The proposed public shape is consistent with the application layer:

```python
SimulationExecutor(simulation_runner).execute(experiment) -> experiment_result
```

It exposes one coarse-grained operation at the correct abstraction level and obtains its sole required collaborator through constructor injection. It does not expose pipeline, state, policy, or statistics operations.

The specification correctly defers the exact names of `SimulationExperiment` and `ExperimentResult` until they are aligned with the existing public contracts. To remove implementation ambiguity, those names and their minimum immutable fields must be finalized before code is written. The required semantics are already specified: ordered requests, stable request identities, and an immutable aggregate of the unmodified individual results.

---

## Dependency Review

The dependency direction is preserved exactly:

```text
SimulationExecutor
    ↓
SimulationRunner
    ↓
SimulationPipeline
    ↓
PipelineStep
    ↓
DecisionContext
    ↓
Domain Policies
    ↓
Domain Services
```

`SimulationExecutor` depends on `SimulationRunner` and public value contracts only. It has no dependency on `SimulationPipeline`, individual `PipelineStep` implementations, `DecisionContext`, policies, services, or infrastructure.

The specification explicitly retains these ownership boundaries:

- `SimulationRunner` owns one simulation's initial state, execution loop, termination, statistics delegation, and final `SimulationResult`.
- `SimulationPipeline` owns ordered monthly orchestration.
- Each `PipelineStep` owns one bounded monthly responsibility.
- `SimulationStatisticsBuilder` owns construction of simulation statistics.
- Domain policies and services remain the only owners of financial logic.

No reverse dependency is specified.

---

## Responsibility Review

The executor appropriately owns:

- batch execution;
- experiment lifecycle coordination;
- request-to-result association;
- deterministic aggregate ordering;
- aggregate result construction;
- injected-runner collaboration.

It appropriately does not own:

- financial calculations or policy decisions;
- `SimulationState` lifecycle;
- monthly step sequencing;
- market data selection;
- statistics generation;
- optimization, persistence, reporting, CLI, or research-study definition.

The distinction between a modelled failed simulation result and an orchestration/configuration failure is architecturally sound. A completed `SimulationResult` remains an aggregateable result regardless of its modelled outcome; malformed requests and unexpected runner exceptions remain failures of orchestration rather than financial outcomes.

---

## Extensibility Review

The specification is open to future optimizers, persistence, reporting, and parallel execution without modifying `SimulationRunner`:

- An optimizer can construct experiment requests and consume aggregate results through the executor's public contract.
- Persistence and reporting can consume immutable aggregate results outside the executor through injected interfaces or higher layers.
- A future scheduling strategy can coordinate independent runner invocations while preserving the declared result order and current failure semantics.

These extensions do not require the runner to take ownership of experiments or alter its single-simulation contract. The current sequential lifecycle is the correct deterministic baseline.

---

## Determinism Review

The specification requires declared-order execution and declared-order aggregation. It forbids randomness, external state, unordered iteration, and concurrency that changes observable ordering or failure behaviour.

This is sufficient to preserve deterministic application orchestration when the input experiment and injected runner behaviour are equal. Optional timing and progress instrumentation are correctly constrained to be observational only.

---

## Approval

The specification is architecturally approved, subject only to finalizing the concrete names and immutable fields of the experiment request and aggregate result before implementation.

It satisfies the required architecture: `SimulationExecutor` coordinates experiments only; `SimulationRunner` remains responsible for a single simulation; the pipeline and steps retain monthly orchestration; statistics remain with `SimulationStatisticsBuilder`; and all financial logic remains in the Domain.

---

## Next Phase

Finalize the public contract names for the experiment request and aggregate result in accordance with the existing application/research naming conventions, then obtain approval to implement `SimulationExecutor` and its focused test suite.

No code implementation is authorized by this review.
