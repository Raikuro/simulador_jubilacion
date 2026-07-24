# SimulationExecutor Public API

## Purpose

This document freezes the public contracts used by `SimulationExecutor` before implementation. The contracts deliberately reuse the established names `ExperimentDefinition`, `ExperimentRun`, `SimulationContext`, and `SimulationResult`; no `SimulationExperiment`, `ExperimentResult`, batch-request, or batch-result synonym is introduced.

The executor receives an experiment definition and returns the corresponding completed experiment run.

---

## 1. Experiment Request Type

### Exact Class Name

`ExperimentDefinition`

### Responsibility

`ExperimentDefinition` is the immutable Research-owned request for one scientific experiment. It describes the exact, ordered set of independent simulations that must be executed. It does not execute simulations, contain their results, or expose lifecycle state.

### Final Immutable Fields

```python
@dataclass(frozen=True)
class ExperimentDefinition:
    name: str
    description: str
    simulation_contexts: tuple[SimulationContext, ...]
```

`simulation_contexts` is the complete ordered execution plan. Each `SimulationContext` already owns the configuration for one simulation, including its dataset, horizon, initial portfolio and wealth, and allocation and withdrawal policies. Keeping that configuration in `SimulationContext` avoids duplicating it in a separate experiment-request model.

### Invariants

- `name` is non-empty and identifies the scientific experiment.
- `description` is non-null; it documents the experiment but has no execution semantics.
- `simulation_contexts` is an immutable tuple, never a mutable list.
- Every item is a valid, non-null `SimulationContext`.
- The tuple order is the declared experiment order and is therefore part of the reproducible definition.
- The same context object may not occur more than once unless the experiment explicitly supports a stable, distinct simulation identity for each occurrence. The initial contract forbids such duplicates.
- The definition contains no `SimulationResult`, `ExperimentRun`, mutable portfolio state, timeline, statistics, execution status, persistence metadata, or financial calculation.

### Reuse and Replacement Decision

The existing `ExperimentDefinition` name is reused. Its currently incomplete field layout (`dataset`, `horizon_months`, and single policy fields) is replaced by the frozen contract above before the executor is implemented.

This is not a new concept: the project plan defines `ExperimentDefinition` as the object that describes which simulations must run. The canonical per-simulation configuration already exists as `SimulationContext`; storing an ordered collection of those contexts is the minimal non-duplicating representation of that responsibility.

---

## 2. Aggregate Result Type

### Exact Class Name

`ExperimentRun`

### Responsibility

`ExperimentRun` is the immutable aggregate result of executing one `ExperimentDefinition`. It associates the definition with the completed individual results. It does not recalculate, alter, summarize, or persist those results.

### Final Immutable Fields

```python
@dataclass(frozen=True)
class ExperimentRun:
    definition: ExperimentDefinition
    simulation_results: tuple[SimulationResult, ...]
```

### Ordering Guarantees

- `simulation_results[i]` is the unmodified result produced by executing `definition.simulation_contexts[i]`.
- The result tuple has the same order and length as `definition.simulation_contexts`.
- The executor never sort, groups, filters, or otherwise reorders completed results.
- An explicitly valid empty definition produces an `ExperimentRun` with an empty result tuple.

### Failure Semantics

- A `SimulationResult` whose statistics indicate an unsuccessful or failed modelled simulation remains a completed result. It is included in the same position and does not fail the `ExperimentRun`.
- A malformed definition, invalid context, or unexpected `SimulationRunner` exception is an orchestration/configuration failure. `execute` raises; it returns no partial `ExperimentRun`.
- Because an `ExperimentRun` is returned only after all delegated executions have completed, it needs no mutable `Pending`, `Running`, `Completed`, `Cancelled`, or `Failed` status field. A returned run is completed by definition.

### Reuse and Replacement Decision

The existing `ExperimentRun` name is reused as the aggregate result type required by the project plan. Its current mutable, single-result shape (`definition`, `result`) is replaced by the frozen contract above. The singular `result` field must not be retained, because it cannot represent an experiment composed of multiple simulations and would duplicate the aggregate role of `simulation_results`.

Run identifiers, timestamps, progress state, persistence state, and similar operational metadata are not part of this core deterministic public contract. If Infrastructure later requires them, it must introduce an injected persistence record or adapter outside `ExperimentRun`; it must not make this aggregate result mutable.

---

## 3. Relationship with Existing Types

| Type | Final role | Created by | Reused or replaced |
|---|---|---|---|
| `ExperimentDefinition` | Immutable, ordered request for an experiment | Research / experiment builder | Reused; field layout frozen as specified above |
| `ExperimentRun` | Immutable aggregate of completed results | `SimulationExecutor` | Reused; mutable single-result form replaced |
| `SimulationContext` | Immutable configuration for exactly one simulation | Research / experiment builder, before executor invocation | Reused unchanged |
| `SimulationResult` | Immutable result of exactly one simulation | `SimulationRunner` | Reused unchanged |

The relationships are:

```text
Research
  └─ creates ExperimentDefinition
       └─ contains ordered SimulationContext values

SimulationExecutor
  └─ delegates each SimulationContext to SimulationRunner
       └─ creates one SimulationResult per context
  └─ creates ExperimentRun from the unchanged results
```

`ExperimentDefinition` is the request, not a run. `ExperimentRun` is the aggregate result, not a request. `SimulationContext` is neither a result nor an experiment-level object. `SimulationResult` is never replaced by an experiment aggregate.

---

## 4. Public API of SimulationExecutor

```python
class SimulationExecutor:
    def __init__(self, simulation_runner: SimulationRunner) -> None: ...

    def execute(self, definition: ExperimentDefinition) -> ExperimentRun: ...
```

### Constructor

`simulation_runner` is a required injected collaborator. The executor must not instantiate a concrete runner, pipeline, statistics builder, policy, service, dataset provider, persistence component, or reporting component.

### `execute`

`execute` validates the structural request contract, delegates each declared `SimulationContext` exactly once to `simulation_runner.run(context)`, preserves the order, and returns one frozen `ExperimentRun`.

It has no optional callbacks, persistence parameters, optimizer parameters, policy parameters, pipeline parameters, or parallel-execution parameters. Such concerns are intentionally outside this initial public API.

---

## 5. Ownership Boundaries

- **Research / experiment builder** creates `ExperimentDefinition` and all of its `SimulationContext` values. It owns scientific choices and request composition.
- **SimulationExecutor** creates the aggregate `ExperimentRun`. It owns only experiment lifecycle coordination, ordered delegation, and aggregation.
- **SimulationRunner** creates one `SimulationResult` for each supplied `SimulationContext`. It owns the single-simulation lifecycle.
- **SimulationPipeline** owns ordered monthly orchestration.
- **PipelineStep** owns one monthly responsibility.
- **SimulationStatisticsBuilder** creates the statistics contained in a `SimulationResult` through the runner's existing single-simulation flow.
- **Domain policies and services** remain the only owners of financial decisions and calculations.

The executor receives results but never constructs, changes, or interprets their financial content.

---

## 6. Naming Consistency

The public vocabulary is intentionally limited to the established terms:

- `ExperimentDefinition`: what to execute.
- `ExperimentRun`: the completed execution aggregate.
- `SimulationContext`: configuration for one execution.
- `SimulationResult`: outcome of one execution.

The following names are rejected because they duplicate an established responsibility or introduce an unnecessary synonym: `SimulationExperiment`, `ExperimentRequest`, `ExperimentResult`, `BatchRequest`, `BatchResult`, `ExecutionBatch`, and `SimulationBatch`.

This naming keeps the application-layer lifecycle explicit without changing the established ownership chain:

```text
ExperimentDefinition → SimulationContext → SimulationResult → ExperimentRun
                 (executor delegates)              (executor aggregates)
```

---

## Approval Requirement

This contract must be reviewed and approved before implementation. No `SimulationExecutor` code, model migration, or test update is authorized by this document alone.
