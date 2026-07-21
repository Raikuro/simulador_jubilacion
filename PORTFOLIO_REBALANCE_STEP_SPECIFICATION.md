# PortfolioRebalanceStep Behavioural Specification

## Purpose
The purpose of `PortfolioRebalanceStep` is to execute the previously generated `AllocationDecision` by rebalancing the portfolio.

This step performs the portfolio rebalance and does not make any policy decisions.

---

## Inputs
The step requires:

- `SimulationState`
- `SimulationState.portfolio`
- `SimulationState.allocation_decision`
- `SimulationState.market_snapshot`

---

## Outputs
Returns the updated `SimulationState`.

Specifically, it updates only:

- `portfolio`
- `allocation`
- `allocation_target` (if required by the decision)
- `current_wealth`

No other execution state is modified.

---

## Responsibilities
The step is responsible for:

- validating that an `AllocationDecision` exists;
- delegating the rebalance to `PortfolioRebalanceService`;
- storing the returned `Portfolio`;
- storing the returned `Allocation`;
- storing the returned `AllocationTarget` when appropriate;
- updating the cached `current_wealth` from the service result.

Nothing else.

---

## Forbidden Responsibilities
This step must not:

- execute any policy;
- modify `DecisionContext`;
- perform market evolution;
- perform withdrawals;
- update statistics;
- build `MonthlyResult`;
- advance the simulation date.

---

## Rebalance Semantics
The rebalance is executed entirely according to the previously produced `AllocationDecision`.

This step never recalculates the target allocation.

The service is responsible for determining the required trades to satisfy the requested allocation.

---

## Domain Delegation
The `PortfolioRebalanceStep` must delegate all financial logic to `PortfolioRebalanceService`.

The Application layer must never manipulate holdings directly.

---

## Single Source of Truth
`Portfolio` remains the canonical financial state.

`Allocation` is derived from the resulting `Portfolio`.

`current_wealth` is derived from the resulting `Portfolio` valuation.

Neither `Allocation` nor `current_wealth` are independent pieces of state.

---

## Portfolio Reconstruction
The service must construct an entirely new immutable `Portfolio`.

No existing `AssetHolding` instance may be reused if its units have changed.

The input `Portfolio` must remain completely untouched.

---

## Wealth Conservation
The following must always hold whenever the rebalance completes successfully:

```
PortfolioValueBeforeRebalance
==
PortfolioValueAfterRebalance
```

except for globally defined Decimal quantization rules.

Rebalancing must never create or destroy wealth.

---

## Allocation Accuracy
After successful execution, the resulting allocation must satisfy:

```
ResultingAllocation
==
AllocationDecision.allocation_target
```

within the globally defined numerical precision rules.

The service should not rely on approximate equality unless that approximation has been defined globally.

---

## Asset Universe Preservation
The rebalance operation must not change the asset universe.

The set of `AssetClass` instances present in the resulting `Portfolio` must exactly match the set expected by the active `AllocationTarget`.

The service must never:

- create unexpected asset classes;
- silently remove asset classes;
- introduce holdings not represented in the `AllocationTarget`.

If an asset required by the `AllocationTarget` cannot be valued because its market price is unavailable, the service must fail with a programming/configuration error.

---

## No Implicit Policy Behaviour
The rebalance service must not:

- decide whether to rebalance;
- modify `AllocationTarget`;
- inspect glidepath logic;
- inspect withdrawal logic.

It only executes the already approved `AllocationDecision`.

---

## Failure Conditions
Programming/configuration errors raise exceptions.

Programming/configuration errors include:

- missing market prices;
- inconsistent portfolio;
- invalid allocation;
- invalid decision object;
- missing `MarketSnapshot`.

Expected simulation outcomes should never generate exceptions.

---

## Interaction With Domain
Uses only:

- `Portfolio`
- `AllocationDecision`
- `PortfolioRebalanceService`

All financial calculations are performed exclusively inside `PortfolioRebalanceService`.

The `PortfolioRebalanceStep` should only:

- validate preconditions;
- invoke the service;
- store the returned objects.

No financial calculations should appear in the Application layer.

---

## Interaction With Following Steps
After completion, the next pipeline step may safely assume:

- `portfolio` reflects the requested allocation;
- `allocation` is synchronized with `portfolio`;
- `allocation_target` reflects the active investment policy;
- `current_wealth` matches the portfolio valuation;
- no market movement has yet been applied.

---

## Determinism
Given identical:

- `Portfolio`;
- `AllocationDecision`;
- `MarketSnapshot`;

the service must always produce identical:

- `Portfolio`;
- `Allocation`;
- `current_wealth`.

Given a portfolio already matching the `AllocationTarget`, the same `AllocationDecision`, and the same `MarketSnapshot`, executing the rebalance multiple times must produce exactly the same `Portfolio`.

No trades should occur.
No holdings should change.
No numerical drift should accumulate.

This guarantees that repeated execution of the same monthly step is stable.

The implementation must not depend on:

- system time;
- random generators;
- filesystem;
- environment variables;
- external services.

---

## Domain Service Design: PortfolioRebalanceService

### Public API

```python
class PortfolioRebalanceResult:
    portfolio: Portfolio
    allocation: Allocation
    allocation_target: AllocationTarget
    current_value: Money

class PortfolioRebalanceService:
    def execute_rebalance(
        self,
        portfolio: Portfolio,
        allocation_decision: AllocationDecision,
        market_snapshot: MarketSnapshot,
    ) -> PortfolioRebalanceResult:
        ...
```

### Inputs

- `portfolio: Portfolio`
- `allocation_decision: AllocationDecision`
- `market_snapshot: MarketSnapshot`

### Outputs

Returns `PortfolioRebalanceResult` containing:

- `portfolio: Portfolio`
- `allocation: Allocation`
- `allocation_target: AllocationTarget`
- `current_value: Money`

### Invariants

- `portfolio` must be immutable and must not be modified in place.
- returned `Portfolio` must be a new instance.
- returned `Allocation` must sum to 1.00 and be non-negative.
- returned `AllocationTarget` must match `allocation_decision.allocation_target`.
- `current_value` must equal the portfolio valuation at `market_snapshot` prices.
- portfolio value before and after rebalancing must be equal within deterministic rounding.

### Failure Behaviour

Raise on programming/configuration errors only:

- `portfolio` is `None`;
- `allocation_decision` is `None`;
- `market_snapshot` is `None`;
- any asset in `portfolio.holdings` is missing a price in `market_snapshot.index_levels`;
- `allocation_decision.allocation_target` is invalid;
- any resulting holding would require negative units.

The service must not raise for expected simulation behaviour.

### Rebalancing Algorithm

The service is responsible for the financial model. The conceptual sequence is:

1. Compute the current market value of every holding.
2. Compute the current portfolio value.
3. Compute the target market value for every asset using `AllocationTarget`.
4. Compute the required buy/sell value for every asset.
5. Convert those values into traded units using current `MarketSnapshot` prices.
6. Construct a new immutable `Portfolio`.
7. Produce the resulting `Allocation`.
8. Produce the updated cached portfolio valuation.

This defines the financial model independently of the implementation.

### Market Prices

- prices from `MarketSnapshot.index_levels` are the only market data used.
- missing prices raise errors.
- prices are used directly for valuation and for converting target values into units.

### Fractional Units and Precision

- `Decimal` is preserved for all calculations.
- the service must not introduce binary floating point error.
- final unit values may be rounded only in a deterministic way specified by the project.
- if the project defines a minimum tradable unit, that rule must be documented and applied consistently.

---

## Testing Requirements

Unit tests must verify:

- successful rebalance;
- already balanced portfolio;
- 100% allocation to a single asset;
- multi-asset rebalance;
- exact wealth conservation;
- deterministic execution;
- delegation to `PortfolioRebalanceService`;
- no unrelated state modification;
- portfolio idempotency when the portfolio already matches the target allocation.

---

## Integration Testing

Add an integration test covering:

```text
BuildDecisionContextStep
↓
WithdrawalDecisionStep
↓
WithdrawalExecutionStep
↓
AllocationDecisionStep
↓
PortfolioRebalanceStep
```

Verify that:

- portfolio value is conserved across withdrawal and rebalance (except for the executed withdrawal);
- the resulting allocation matches the requested allocation;
- state flows correctly between all pipeline steps;
- no intermediate state is lost or unintentionally modified.

Additionally, include one scenario covering:

- 100% Equity -> Withdrawal -> AllocationDecision (60/40) -> PortfolioRebalance
- verify wealth is conserved;
- verify allocation is exactly 60/40 within global precision rules;
- verify `current_wealth` equals portfolio valuation;
- verify no state outside the expected fields changed.

---

## Approval Criteria

Once both this behavioural specification and the `PortfolioRebalanceService` design have been reviewed and approved, implementation of `PortfolioRebalanceStep` may begin.

The implementation must stop after completion and provide:

- Summary.
- Files created.
- Files modified.
- Public API changes.
- Unit test summary.
- Integration test summary.

Do not continue with `MarketEvolutionStep` until this implementation has been reviewed and approved.
