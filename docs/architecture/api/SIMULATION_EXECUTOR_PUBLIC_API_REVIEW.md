# SimulationExecutor Public API Review

## Review Result

**Approved. The public API is frozen and implementation may begin.**

The contract uses the existing application vocabulary and defines the smallest complete boundary required for experiment-level orchestration.

---

## Concept and Responsibility Review

No duplicated public concept remains:

- `ExperimentDefinition` is the immutable request describing what to execute.
- `SimulationContext` is the immutable configuration for one requested simulation.
- `SimulationResult` is the immutable outcome of one completed simulation.
- `ExperimentRun` is the immutable aggregate outcome of the experiment.

Each type has exactly one responsibility. The request contains no results, the aggregate contains no execution plan of its own, a context is not an experiment-level result, and a result is not an aggregate.

---

## Ownership Review

Ownership is explicit and non-overlapping:

- Research creates `ExperimentDefinition` and its ordered `SimulationContext` values.
- `SimulationExecutor` coordinates those contexts and creates `ExperimentRun`.
- `SimulationRunner` creates one `SimulationResult` per context.
- The pipeline, steps, statistics builder, and Domain retain their established responsibilities.

The executor receives completed results unchanged. It has no authority to calculate, interpret, or modify their financial content.

---

## Public API Review

The executor exposes the minimum necessary API:

```python
SimulationExecutor(simulation_runner)
execute(definition) -> ExperimentRun
```

The sole collaborator is injected. The sole operation expresses the complete application-level use case. There are no public controls for pipeline execution, policies, financial behaviour, statistics, persistence, callbacks, progress, or scheduling.

No implementation detail leaks through this API. Its inputs and output are immutable public contracts, while sequencing and runner delegation remain implementation behaviour governed by the behavioural specification.

---

## Future Compatibility Review

The frozen API supports future extensions without changing `SimulationRunner`:

- **Optimizers** can build alternative immutable definitions and consume completed runs.
- **Parallel execution** can change internal scheduling while preserving context/result positional association and returned ordering.
- **Persistence** can store definitions and runs through Infrastructure adapters without adding mutable persistence state to core results.
- **Reporting** can consume immutable `ExperimentRun` and `SimulationResult` values without re-executing or changing the executor.
- **Reproducibility** is preserved by the ordered immutable context tuple and immutable results; the same definition and runner behaviour produce an equivalent ordered run.

---

## Naming Review

The names are consistent with the existing Application layer and project terminology:

- `ExperimentDefinition` describes;
- `ExperimentRun` aggregates the completed execution;
- `SimulationContext` configures one simulation;
- `SimulationResult` records one simulation outcome.

No synonymous request, aggregate, or batch type has been introduced.

---

## Approval

`SIMULATION_EXECUTOR_PUBLIC_API.md` is approved as the final public contract. The API is frozen.

Implementation of `SimulationExecutor` and its tests may now begin, provided the approved behavioural specification and architecture review remain unchanged.
