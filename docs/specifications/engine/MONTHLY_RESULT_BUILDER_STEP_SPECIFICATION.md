# MonthlyResultBuilderStep Behavioural Specification

## Purpose
The purpose of this step is to construct an immutable `MonthlyResult` record representing the completed simulation state for the current month.

This step captures the current state of the simulation without performing any financial transformations, policy decisions, or state advancement.

---

## Inputs
The step requires:

- `SimulationState`
- `SimulationState.current_date`
- `SimulationState.period_index`
- `SimulationState.market_snapshot`
- `SimulationState.portfolio`
- `SimulationState.allocation`
- `SimulationState.allocation_target`
- `SimulationState.allocation_drift`
- `SimulationState.withdrawal_decision`
- `SimulationState.current_withdrawal`
- `SimulationState.current_wealth`
- `SimulationState.peak_wealth`
- `SimulationState.status`
- `SimulationState.failure_state`
- `SimulationState.decision_context`
- `SimulationState.monthly_results`

The step may also consume `SimulationState.context` only to preserve existing execution metadata if required by the step implementation, but it must never depend on or mutate the context for financial logic.

---

## Outputs
Returns the updated `SimulationState`.

Specifically, it updates:

- `SimulationState.monthly_results`

The step must append a new immutable `MonthlyResult` instance to the existing `monthly_results` list.

No other execution state is modified.

---

## Responsibilities
The step is responsible for:

- validating required state;
- constructing a `MonthlyResult` from the current `SimulationState` fields;
- appending the new `MonthlyResult` to `SimulationState.monthly_results`.

Nothing else.

---

## Forbidden Responsibilities
This step must not:

- execute any policy;
- perform withdrawals;
- perform rebalancing;
- perform market evolution;
- execute financial logic or valuation;
- modify `SimulationState.portfolio`, `SimulationState.allocation`, `SimulationState.allocation_target`, `SimulationState.current_wealth`, or any other financial state;
- advance the simulation date or increment `period_index`;
- construct or mutate `SimulationState.decision_context`;
- alter dataset or `MarketSnapshot` contents;
- update statistics outside of the timeline record;
- use external data sources or environment state for construction.

---

## Domain Delegation
This step is an Application-layer responsibility only.

All financial and valuation calculations must already have happened in prior pipeline steps.

The step may use Domain models such as `MonthlyResult`, `MarketSnapshot`, `Portfolio`, and `Allocation` as value objects, but it must not implement or replicate financial computation.

---

## MonthlyResult Semantics
The `MonthlyResult` record must represent the completed state at the end of one simulation month.

It must capture the following fields exactly as they exist in the `SimulationState` at the time of execution:

- `date`
- `period_index`
- `market_snapshot`
- `portfolio`
- `allocation`
- `allocation_target`
- `allocation_drift`
- `withdrawal_decision`
- `rebalance_result`
- `drawdown`
- `cumulative_return`
- `cumulative_inflation`
- `events`

The `MonthlyResultBuilderStep` may preserve `None` values for optional fields when they are not yet set.

---

## Immutability
The resulting `MonthlyResult` must be immutable.

The `MonthlyResultBuilderStep` must not reuse a previously created record for a new month.

Each month must produce a new `MonthlyResult` instance with the current simulation state snapshot.

---

## Timeline Behaviour
The step must append the new result in chronological order.

`SimulationState.monthly_results` must preserve the order of months simulated.

The step must not reorder, remove, or modify prior `MonthlyResult` entries.

---

## Failure Conditions
Programming/configuration errors raise exceptions only:

- required state is missing;
- `SimulationState.monthly_results` is not a list or appendable sequence;
- required fields for `MonthlyResult` construction are invalid.

Normal simulation inputs must not raise exceptions in this step.

---

## Determinism
Given the same `SimulationState`, the step must always produce the same `MonthlyResult` and append it in the same position.

No external randomness or environment-dependent behavior may influence `MonthlyResultBuilderStep`.

---

## Testing Requirements
Unit tests must verify:

- required `SimulationState` fields are validated;
- `monthly_results` is appended with a new `MonthlyResult` instance;
- the appended `MonthlyResult` matches the current state snapshot exactly;
- existing state outside `monthly_results` is unchanged;
- optional fields may remain `None` when not provided;
- the step is idempotent only in the sense that repeated execution on the same state appends new results each time.

Integration tests should verify:

- the step can be inserted after `MarketEvolutionStep` without changing the financial state;
- the timeline grows by one record per step execution;
- prior `MonthlyResult` entries remain unchanged.

---

## Approval Criteria
The specification is approved when the step is defined to:

- create a single immutable monthly snapshot;
- preserve all existing simulation state except `monthly_results`;
- avoid any financial or policy execution;
- append results chronologically;
- depend only on the current `SimulationState`.

Once this specification is approved, implementation may begin.
