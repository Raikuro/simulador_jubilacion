# MarketEvolutionStep Behavioural Specification

## Purpose
The purpose of this step is to apply the market evolution for the current simulation month.

This step is responsible for transforming the portfolio from its value at the beginning of the month to its value at the end of the month by applying the market data contained in the current `MarketSnapshot`.

No policy decisions are made.

No withdrawals or rebalancing occur.

---

## Inputs
The step requires:

- `SimulationState`
- `SimulationState.portfolio`
- `SimulationState.market_snapshot`
- `SimulationState.current_wealth`

---

## Outputs
Returns the updated `SimulationState`.

Specifically, it updates:

- `portfolio`
- `allocation`
- `current_wealth`
No other execution state is modified.

---

## Responsibilities
The step is responsible for:

- validating required state;
- delegating market evolution to the Domain service;
- storing the returned `Portfolio`;
- updating `Allocation` derived from the new `Portfolio`;
- updating the cached `current_wealth`.
Nothing else.

---

## Forbidden Responsibilities
This step must not:

- execute any policy;
- perform withdrawals;
- perform rebalancing;
- modify `AllocationTarget`;
- modify `DecisionContext`;
- update statistics;
- build `MonthlyResult`;
- advance the simulation date;
- access the Dataset beyond the current `MarketSnapshot`.

---

## Domain Delegation
All financial calculations must be delegated to:

```
PortfolioMarketEvolutionService
```
The PipelineStep performs no financial calculations.

---

## Market Evolution Semantics
Each holding evolves according to the market data contained in the current `MarketSnapshot`.

`MarketSnapshot` represents the complete market state for one historical month and is the single source of truth for market evolution.
The Domain service must not derive or infer market values from any external source.

For every `AssetHolding`:

1. Obtain its current index level.
2. Obtain the next index level represented by the current month's market evolution.
3. Apply the proportional change.
4. Compute the new number of units or value according to the chosen valuation model.
5. Construct a new immutable `Portfolio`.
No trading occurs.

Only market prices change.

---

## Valuation Model
The simulator follows a **mark-to-market** model.

Market evolution changes asset prices only.

Portfolio composition remains unchanged.

Index levels are treated as Total Return indices.
The simulator evolves asset prices exclusively from the ratio between index levels.
For every asset:

```
GrowthFactor = IndexLevelEnd / IndexLevelStart
```

Portfolio evolution is based exclusively on this growth factor.
No additional return calculation should exist elsewhere in the simulator.

Therefore:

- `AssetHolding.units` remain constant.
- Asset prices evolve.
- Portfolio value changes.
- Allocation changes automatically as a consequence of differing asset returns.
No implicit rebalance occurs.

---

## Dataset Interaction
The step consumes exactly one:

- `MarketSnapshot`
corresponding to the current simulation month.

The Dataset itself is immutable.

The step must never modify `Dataset` or `MarketSnapshot`.

---

## Numerical Invariants
After successful execution:

```
UnitsBeforeMarketEvolution
==
UnitsAfterMarketEvolution
```
for every `AssetHolding`, exactly.

No Decimal tolerance is permitted for units.
Market evolution must never modify units.
Only:

- withdrawals
- rebalancing
may change holdings.

Only prices change.

Likewise:

```
PortfolioValueAfter
=
Σ(UnitsBefore × MarketPriceAfter)
```
using exact `Decimal` arithmetic.

No independent wealth calculation should exist.

---

## Allocation Behaviour
Allocation is **not** preserved.

Allocation is recalculated from the evolved `Portfolio`.

This natural drift is the mechanism that later motivates rebalancing according to the investment policy.

No correction must occur during `MarketEvolutionStep`.
The next month's policy evaluation will decide whether rebalancing is required.

---

## Failure Conditions
Programming/configuration errors raise exceptions.

Examples:

- missing `MarketSnapshot`;
- missing market price;
- invalid index level;
- negative index value;
- inconsistent asset universe.
Expected market behaviour never raises exceptions.

Negative monthly returns are normal simulation inputs.

---

## No Hidden Transactions
The service must never introduce:

- implicit sales;
- implicit purchases;
- transaction costs;
- taxes;
- slippage;
- spread simulation.

The simulator assumes frictionless markets unless explicitly extended in a future version.

---

## Determinism
Given identical:

- `Portfolio`;
- `MarketSnapshot`;

the resulting `Portfolio` must always be identical.

No external state may influence the result.

---

## Price Ownership
`Portfolio` owns quantities.

`MarketSnapshot` owns prices.

`PortfolioMarketEvolutionService` combines both to compute valuation.

Neither object should duplicate the other's responsibility.

---

## Domain Service Design: PortfolioMarketEvolutionService

### Public API

```python
class PortfolioMarketEvolutionResult:
    portfolio: Portfolio
    allocation: Allocation
    current_value: Money

class PortfolioMarketEvolutionService:
    def apply_market_evolution(
        self,
        portfolio: Portfolio,
        market_snapshot: MarketSnapshot,
    ) -> PortfolioMarketEvolutionResult:
        ...
```

### Inputs

- `portfolio: Portfolio`
- `market_snapshot: MarketSnapshot`

### Outputs

Returns `PortfolioMarketEvolutionResult` containing:

- `portfolio: Portfolio`
- `allocation: Allocation`
- `current_value: Money`

### Invariants

- `portfolio` must be immutable and must not be modified in place.
- returned `Portfolio` must be a new instance.
- returned `Allocation` must be derived from the returned `Portfolio`.
- `current_value` must equal the evolved `Portfolio` valuation at `market_snapshot` prices.
- `AssetHolding.units` must remain unchanged.
- the asset universe of the returned `Portfolio` must match the original portfolio's asset universe exactly.
- the service must use `MarketSnapshot` as the single source of market values and must not infer prices from elsewhere.

### Failure Behaviour

Raise on programming/configuration errors only:

- `portfolio` is `None`;
- `market_snapshot` is `None`;
- missing asset price in `market_snapshot.index_levels`;
- invalid or negative index level;
- inconsistent asset universe between `portfolio` and `market_snapshot`.

Expected market behaviour should never raise exceptions.

### Valuation Algorithm

1. Interpret index levels from `MarketSnapshot.index_levels` as end-of-month prices.
2. For each holding, determine the asset's updated price.
3. Preserve the holding's `units`.
4. Construct a new `AssetHolding` for every asset with the same `units`.
5. Build a new `Portfolio` from the new holdings.
6. Recalculate allocation from the evolved portfolio and the updated prices.
7. Compute `current_value` as the sum of `units × updated price`.
8. Preserve exact `Decimal` precision throughout.

---

## Market Evolution Algorithm

The specification defines:

1. how index levels are interpreted;
2. how monthly returns are applied;
3. how prices are updated;
4. how `Portfolio` is reconstructed;
5. how `Allocation` is recalculated;
6. how `current_wealth` is obtained;
7. how `Decimal` precision is preserved.

---

## Testing Requirements

Unit tests must verify:

- one asset + positive return;
- one asset + negative return;
- one asset + zero return;
- multiple assets with different returns;
- identical returns for all assets (allocation must remain unchanged);
- one asset doubles while another is unchanged (allocation drift);
- unchanged units after evolution;
- repeated execution produces identical results;
- deterministic execution;
- no unrelated state modification.

---

## Integration Tests

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
        ↓
MarketEvolutionStep
```

Verify:

- holdings remain unchanged during market evolution;
- portfolio value changes according to market data;
- allocation drifts naturally after market evolution;
- `current_wealth` equals portfolio valuation;
- all previous financial invariants remain valid.

Additionally, add an integration scenario covering:

```
Withdrawal
↓
Rebalance
↓
Market Evolution
```

Verify:

- holdings remain unchanged during market evolution;
- prices update according to the market snapshot;
- allocation drift occurs as expected;
- wealth evolves correctly;
- `current_wealth` equals portfolio valuation.

---

## Important Financial Principle
The simulator models market evolution by changing **asset prices**, never by changing the quantity of assets held.

Therefore:

- withdrawals change units;
- rebalancing changes units;
- market evolution changes prices only.
This distinction is fundamental to the correctness of the simulator.

---

## Approval Criteria
Once the behavioural specification and the `PortfolioMarketEvolutionService` design have been reviewed and approved, implementation of:

- `PortfolioMarketEvolutionService`
- `MarketEvolutionStep`

may begin.

Implementation must stop after completion and provide:

- Summary.
- Files created.
- Files modified.
- Public API changes.
- Unit test summary.
- Integration test summary.
Do **not** continue with `MonthlyResultBuilderStep` until this implementation has been reviewed and approved.
