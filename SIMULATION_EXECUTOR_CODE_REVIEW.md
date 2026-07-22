# SimulationExecutor Code Review

## Review Result

**Approved for the SimulationExecutor scope.**

The implementation matches the frozen public API and approved behavioural specification. It introduces only application-level experiment coordination and its required immutable public-contract realization.

---

## Reviewed Changes

- `src/engine/application/executor.py`
- `src/engine/application/simulation.py`
- `tests/test_simulation_executor.py`

No financial service, policy, pipeline step, runner implementation, or statistics-builder implementation was changed.

---

## Public Contract Review

- `ExperimentDefinition` is frozen and contains the ordered immutable tuple of `SimulationContext` values.
- Its validation protects the frozen contract: non-empty name, required description, tuple-only contexts, `SimulationContext` membership, and no repeated context identity.
- `ExperimentRun` is frozen and aggregates the unchanged `SimulationResult` tuple.
- `ExperimentRun` enforces a one-to-one context/result count and result-type integrity.
- The removed mutable singular `result` field is not retained.

These changes realize the approved API without adding a synonym or an alternate aggregate model.

---

## Executor Review

`SimulationExecutor` exposes exactly the approved API:

```python
SimulationExecutor(simulation_runner)
execute(definition) -> ExperimentRun
```

The constructor validates only the injected collaborator's required `run()` capability. `execute` delegates each context exactly once, in definition order, and builds one immutable aggregate after all invocations return.

The implementation contains no market, withdrawal, allocation, valuation, policy, statistics, pipeline, persistence, reporting, optimizer, timing, concurrency, or filesystem logic. Unexpected runner exceptions are not caught, so they propagate without a partial aggregate being returned.

---

## Test Review

`tests/test_simulation_executor.py` provides 12 passing tests covering:

- immutable and structurally valid experiment contracts;
- dependency-injected runner validation;
- one runner invocation per context;
- unchanged context forwarding and result ordering;
- modelled failed result aggregation;
- valid empty-experiment behaviour;
- unexpected runner-error propagation without partial result publication;
- real `SimulationRunner` integration across multiple contexts;
- repeatable equivalent ordered aggregate results.

---

## Validation

Passed:

- `python -m pytest tests/test_simulation_executor.py` — 12 passed.
- `python -m pytest tests --ignore=tests/test_simulation_runner.py --ignore=tests/test_simulation_runner_integration.py` — 125 passed.
- `python -m compileall -q src tests`.
- `ruff check` on changed source and test files.
- `black --check --workers 1` on changed source and test files.
- `mypy` on changed application source files.
- `git diff --check`.

The full `python -m pytest tests/` run collected 158 tests: 134 passed and 24 failed, all in the pre-existing `test_simulation_runner.py` and `test_simulation_runner_integration.py` fixture suite. The failures occur before executor use because those fixtures instantiate the current frozen `Money` and `MarketSnapshot` domain models with obsolete constructor assumptions; several also construct duplicate pipeline-step types rejected by the established pipeline contract. No production runner, pipeline, domain-model, or statistics-builder code was changed in this implementation. These failures are outside the approved SimulationExecutor scope and must be resolved in a separately approved runner-test maintenance task.

---

## Conclusion

The reviewed code is deterministic, dependency-injected, immutable at its public boundaries, and limited to the approved executor responsibility. No further changes are recommended within this implementation phase.
