# SimulationStateUpdateStep Behavioural Specification

## Purpose
The purpose of this step is to update execution state at the end of a completed simulation month so the next month can begin.

This step is responsible for advancing the simulation state only, not for performing any financial calculations, policy decisions, or reporting.

---

## Inputs
The step requires:

- `SimulationState`
- `SimulationState.current_date`
- `SimulationState.period_index`
- `SimulationState.market_snapshot`
- `SimulationState.context`
- `SimulationState.context.dataset`
- `SimulationState.context.horizon_months`
- `SimulationState.current_wealth`
- `SimulationState.monthly_results`
- `SimulationState.failure_state`

The step may also read existing derived state that must remain valid for the next period.

---

## Outputs
Returns the updated `SimulationState`.

Specifically, it updates:

- `SimulationState.current_date`
- `SimulationState.period_index`
- `SimulationState.market_snapshot`
- any cached or derived state required for the subsequent iteration
- `SimulationState.status` or equivalent end-of-simulation marker when natural completion is reached

The step must not modify historical timeline records or monthly results.

---

## Responsibilities
The step is responsible for:

- validating that the required current execution state is present;
- advancing the simulation date to the next monthly period;
- incrementing the period index;
- selecting the next `MarketSnapshot` from the current dataset for the upcoming month;
- refreshing cached derived state needed by the next pipeline iteration;
- detecting natural end-of-simulation conditions such as dataset exhaustion or horizon completion;
- preserving all historical `MonthlyResult` entries intact.

Nothing else.

---

## Forbidden Responsibilities
This step must not:

- execute policies;
- perform withdrawals;
- rebalance the portfolio;
- evolve market prices;
- value the portfolio;
- calculate statistics;
- construct or modify `MonthlyResult` objects;
- mutate previous timeline entries;
- execute optimizer logic;
- detect or declare failure except natural completion;
- perform any business logic beyond state advancement.

---

## Dataset and Snapshot Selection
The step must use the current `SimulationState.context.dataset` and the current `period_index` to determine the next `MarketSnapshot`.

The simulator dataset is immutable and represents the historical market path for the simulation.

The step may only consume the dataset and `state.market_snapshot` as its source of truth for snapshot selection.

---

## Natural Completion Semantics
The step should detect natural completion conditions when:

- the next `MarketSnapshot` is not available because the dataset has been exhausted;
- the current period index has reached the configured horizon.

When natural completion is reached, the step must not perform additional monthly state advancement.

It may set an execution marker on `SimulationState` such as `status` to indicate the simulation should stop naturally.

---

## Immutability and Timeline Safety
The step must preserve previously appended `MonthlyResult` records without modification.

The execution timeline is append-only, and this step does not append or remove entries.

If the step must derive new values for the next month, it may do so using immutable copies or read-only references only.

---

## Determinism
Given the same `SimulationState` and dataset, the step must always produce the same updated state.

No external randomness, system time, filesystem access, or environment variables may influence the update.

---

## Testing Requirements
Unit tests must verify:

- required current state validation;
- correct next date advancement;
- correct period index increment;
- correct next `MarketSnapshot` selection from the dataset;
- preservation of prior `MonthlyResult` entries;
- detection of natural completion when the dataset or horizon ends;
- no financial state or timeline mutation beyond the allowed next-period updates.

Integration tests should verify:

- the step can be placed after `MonthlyResultBuilderStep` in the monthly pipeline;
- the step enables the next monthly execution cycle without altering completed month history;
- the step stops advancement cleanly at the end of the dataset or horizon.

---

## Approval Criteria
The specification is approved when the step is defined to:

- advance the monthly execution state only;
- load the next market snapshot from the current dataset;
- preserve historical timeline data;
- detect natural end-of-simulation conditions;
- avoid all financial, policy, and reporting logic.

Once this specification is approved, implementation may begin.
