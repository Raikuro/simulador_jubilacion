# IMPLEMENTATION_PHASE_GUIDANCE.md

## Status
`MARKET_EVOLUTION_IMPLEMENTATION_GUIDANCE.md` is acknowledged.

The project has now entered the implementation phase.

The overall architecture is considered stable.

Future work should focus on implementing the approved specifications rather than redesigning the system.

---

# Implementation Workflow
From this point onward, every component should follow the same lifecycle:

1. Implement the approved specification.
2. Provide an implementation summary.
3. Perform an architectural review.
4. Perform a financial correctness review (when applicable).
5. Obtain approval.
6. Freeze the implementation.
7. Proceed to the behavioural specification of the next component.
This workflow should remain consistent throughout the remainder of the project.

---

# Review Priorities
Future reviews should primarily focus on:

- correctness of the financial model;
- compliance with the approved behavioural specification;
- deterministic behaviour;
- complete test coverage;
- absence of regressions.
Architectural redesign should only occur if a genuine design issue is discovered during implementation.

---

# Regression Policy
The current architecture is now considered the baseline.

Future implementations must preserve:

- public APIs;
- ownership rules;
- Domain/Application separation;
- financial invariants;
- deterministic execution;
- existing behavioural guarantees.
Whenever functionality is extended:

- add new tests;
- never remove existing tests to accommodate new behaviour;
- preserve backwards compatibility unless an explicit architectural review approves otherwise.

---

# Remaining Roadmap
After the successful implementation and approval of `MarketEvolutionStep`, the remaining implementation order should be:

1. MonthlyResultBuilderStep
2. SimulationStateUpdateStep
3. Complete SimulationRunner
4. SimulationExecutor
5. BinarySearchOptimizer
6. CSV Dataset Provider
7. SQLite Persistence
8. Research Experiments
9. CLI
10. Reporting / Analysis
These components should build upon the existing financial engine without modifying its behaviour.

---

# Engineering Goal
The objective from this point forward is no longer to evolve the architecture, but to complete it faithfully.

Every new component should integrate with the existing design rather than redefine it.

The financial execution pipeline should remain unchanged unless an explicit architectural review determines that a change is necessary.

---

# Approval
Proceed with the implementation of `PortfolioMarketEvolutionService` and `MarketEvolutionStep`.

Once completed, submit the implementation for architectural and financial review before continuing with `MonthlyResultBuilderStep`.
