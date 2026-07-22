# SimulationRunner Behavioural Specification

## Purpose
The `SimulationRunner` is responsible for orchestrating a complete simulation from start to finish.

It constructs the initial execution state, runs the monthly pipeline until the simulation terminates, and produces the final `SimulationResult`.

This component must not implement financial behaviour.
All market, withdrawal, allocation, rebalance, and valuation logic must remain in the existing pipeline steps and Domain services.

---

## Responsibilities
The runner is responsible for:

- creating the initial `SimulationState` from a `SimulationContext`;
- executing the ordered monthly pipeline until termination;
- honoring the simulation lifecycle represented by `SimulationState.status` and `failure_state`;
- producing `SimulationStatistics` from the completed execution state;
- building a final `SimulationResult` containing the timeline and statistics;
- returning the completed simulation result.

Nothing else.

---

## Forbidden Responsibilities
The runner must not:

- execute financial calculations;
- perform policy decisions;
- mutate `MonthlyResult` records;
- change the ordering of pipeline steps;
- select market snapshots directly (except to initialize the first snapshot if required by state construction);
- compute portfolio valuation other than by consuming state already produced by pipeline steps;
- implement optimizer or experiment orchestration logic.

---

## Inputs
The runner requires:

- `SimulationContext` containing:
  - `start_date`
  - `horizon_months`
  - `initial_wealth`
  - `initial_portfolio`
  - `dataset`
  - allocation and withdrawal policies

- `SimulationPipeline` containing the monthly execution steps.

---

## Initial State Construction
The runner must construct the initial `SimulationState` with:

- the provided `SimulationContext`;
- `current_date` set to `context.start_date`;
- `period_index` set to `0`;
- `portfolio` initialized from `context.initial_portfolio`;
- `current_wealth` initialized from `context.initial_wealth`;
- `peak_wealth` initialized from `context.initial_wealth`;
- `market_snapshot` set if the dataset provides an initial snapshot for month 0.

The initial state must not perform any step execution or financial transformation as part of construction.

---

## Execution Loop
The runner must execute the monthly pipeline in order for each simulated month until termination.

Termination occurs when:

- `SimulationState.status` becomes `ExecutionStatus.COMPLETED`;
- `SimulationState.failure_state` becomes non-`None` and `ExecutionStatus` becomes `FAILED`;
- the configured simulation horizon is reached;
- there is no next snapshot available and the pipeline indicates natural completion.

The runner must not continue executing pipeline steps after termination.

---

## Final Result Construction
Once execution ends, the runner must construct a `SimulationResult` containing:

- `SimulationTimeline` with the completed `monthly_results` in chronological order;
- `SimulationStatistics` with:
  - `final_wealth` from `SimulationState.current_wealth` or `context.initial_wealth` if absent;
  - `max_drawdown` computed by a dedicated statistics component or placeholder until statistics are implemented;
  - `success` derived from `SimulationState.status` and `failure_state` semantics;
  - `failure_month` when `failure_state` is present;
  - `months_simulated` equal to the number of `monthly_results`;
  - `execution_time_seconds` measured or set to a default placeholder.

The runner itself should not compute financial statistics beyond assembling the available state.

---

## Determinism
The runner must behave deterministically given the same `SimulationContext`, `SimulationPipeline`, and initial dataset.

No external time, filesystem, randomness, or infrastructure may affect the flow except for measuring execution time if required.

---

## Error Handling
The runner should raise on programming/configuration errors only, such as:

- missing or invalid `SimulationContext` fields;
- missing pipeline steps;
- invalid initial dataset or market snapshot;
- inconsistent execution state.

Expected simulation completion must never raise an exception.

---

## Testing Requirements
Unit tests must verify:

- initial state is constructed correctly from `SimulationContext`;
- the runner executes the full monthly pipeline until completion;
- termination occurs cleanly on `COMPLETED` and `FAILED` states;
- final `SimulationResult` contains the timeline and statistics;
- no financial logic is performed by the runner itself.

Integration tests should verify:

- a simple pipeline with stubbed steps produces a valid result;
- the runner respects `SimulationState.status` and does not run extra iterations;
- the final timeline order matches the executed months.

---

## Approval Criteria
The specification is approved when the runner is defined to:

- orchestrate monthly execution only;
- construct initial state from `SimulationContext`;
- stop execution on natural completion or failure;
- assemble the final immutable result;
- avoid introducing financial semantics.

Once this specification is approved, implementation may begin.
