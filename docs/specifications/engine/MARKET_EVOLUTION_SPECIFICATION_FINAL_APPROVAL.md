# MARKET_EVOLUTION_SPECIFICATION_FINAL_APPROVAL.md

## Status
The behavioural specification for `MarketEvolutionStep` is approved.

The architecture, financial model, responsibilities, and invariants are now considered frozen.

Implementation of:

- `PortfolioMarketEvolutionService`
- `MarketEvolutionStep`

may begin.

---

# Frozen Financial Model
The simulator now has an explicit and immutable financial model.

## Withdrawals
Withdrawals modify:

- Portfolio holdings (units).
They never modify market prices.

---

## Rebalancing
Rebalancing modifies:

- Portfolio holdings (units).
It never modifies market prices.

---

## Market Evolution
Market evolution modifies:

- market prices only.
It never modifies:

- units;
- allocation targets;
- policy decisions.

---

# Market Ownership Model
Ownership of financial information is now explicitly defined.

## Portfolio
Portfolio owns:

- AssetHolding
- Units
Portfolio never owns prices.

---

## MarketSnapshot
MarketSnapshot owns:

- historical market prices;
- Total Return index levels;
- inflation information.
MarketSnapshot never owns portfolio state.

---

## PortfolioMarketEvolutionService
The Domain service combines:

- Portfolio quantities;
- MarketSnapshot prices;
to produce:

- evolved Portfolio;
- updated Allocation;
- updated portfolio valuation.
No other component performs market valuation.

---

# Growth Model
Market evolution must use only the Total Return indices contained in the MarketSnapshot.

For every asset:

```
GrowthFactor =
IndexLevelEnd
/
IndexLevelStart
```
No additional return calculation is permitted anywhere else in the simulator.

---

# Numerical Invariants
The following invariants are now frozen.

## Units

```
UnitsAfter
==
UnitsBefore
```
exactly.

No tolerance.

---

## Portfolio Valuation

```
PortfolioValueAfter
=
Σ(
Units
×
MarketPriceAfter
)
```
using exact Decimal arithmetic.

---

## Allocation Drift
Allocation must be recalculated from the evolved Portfolio.

No correction is performed.

No implicit rebalance is allowed.

---

# Forbidden Behaviour
Market evolution must never perform:

- purchases;
- sales;
- rebalancing;
- transaction costs;
- taxes;
- slippage;
- spread simulation;
- policy evaluation.
The simulator models a frictionless market unless explicitly extended in a future version.

---

# Determinism
Given identical:

- Portfolio;
- MarketSnapshot;
the service must always produce identical:

- Portfolio;
- Allocation;
- current_wealth.
No external state may influence the result.

---

# Testing Requirements
Implementation must include explicit tests covering:

- positive returns;
- negative returns;
- zero returns;
- identical returns across all assets;
- differing returns causing allocation drift;
- unchanged units;
- correct valuation;
- deterministic execution;
- repeated execution;
- no unrelated state mutation.
Integration tests must verify:

- withdrawal;
- rebalance;
- market evolution;
operate together while preserving every previously established financial invariant.

---

# Regression Policy
The financial model established by this specification is now considered part of the simulator's public architecture.

Future modifications must preserve:

- deterministic behaviour;
- valuation rules;
- ownership model;
- numerical invariants;
- existing test suite.
Any extension should add behaviour without weakening these guarantees.

---

# Next Phase
After implementation of:

- `PortfolioMarketEvolutionService`
- `MarketEvolutionStep`
and successful review,

the project may proceed to the behavioural specification for:

```
MonthlyResultBuilderStep
```
No further execution pipeline components should be implemented before the Market Evolution implementation has been reviewed and approved.

---

# Approval
The behavioural specification for `MarketEvolutionStep` is fully approved.

Proceed with implementation.
