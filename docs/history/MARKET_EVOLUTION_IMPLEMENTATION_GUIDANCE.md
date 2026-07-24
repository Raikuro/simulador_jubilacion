# MARKET_EVOLUTION_IMPLEMENTATION_GUIDANCE.md

## Status
`MARKET_EVOLUTION_SPECIFICATION_FINAL_APPROVAL.md` is acknowledged.

The financial model for market evolution is now considered frozen.

Implementation of:

- `PortfolioMarketEvolutionService`
- `MarketEvolutionStep`

may proceed.

---

# Implementation Scope
The implementation should follow the approved specification exactly.

Do not introduce:

- new financial behaviour;
- optimizations that change semantics;
- additional abstractions unless they simplify the existing design without changing behaviour.
The implementation should prioritize correctness, determinism, and readability over premature optimization.

---

# Review Expectations
After implementation, provide a complete implementation review package including:

- Summary.
- Files created.
- Files modified.
- Public API changes.
- Unit test summary.
- Integration test summary.
- Validation results.
Confirm explicitly that every invariant defined in `MARKET_EVOLUTION_SPECIFICATION.md` has been verified.

---

# Financial Verification
The implementation review should explicitly demonstrate that:

- Portfolio holdings (units) remain unchanged.
- Market prices evolve according to the approved GrowthFactor model.
- Portfolio valuation is computed exclusively from:
  - Portfolio units;
  - MarketSnapshot prices.
- Allocation drifts naturally according to relative asset performance.
- current_wealth matches the evolved portfolio valuation exactly.
- No hidden transactions occur.
- No policy logic is executed.

---

# Regression Requirements
All existing tests must continue to pass.

Any new behaviour must be accompanied by additional tests.

Existing behavioural guarantees must never be weakened.

---

# Next Phase
Do **not** begin implementation of:

```
MonthlyResultBuilderStep
```

until:

- `PortfolioMarketEvolutionService` has been reviewed;
- `MarketEvolutionStep` has been reviewed;
- all financial invariants have been verified.
Only after approval should the project continue with the next execution stage.

---

# Approval
Implementation of the Market Evolution subsystem is approved.

Await implementation and review before proceeding with the remainder of the execution pipeline.
