# IMPLEMENTATION_PROMPT.md

Version: 1.0

---

# 1. Mission

Your mission is to implement the retirement simulator exactly as specified in `PROJECT_PLAN.md`.

This project is intended to become a reusable financial simulation engine capable of reproducing and extending the Safe Withdrawal Rate studies published by EarlyRetirementNow.

The implementation must prioritize:

1. Correctness
2. Reproducibility
3. Maintainability
4. Extensibility
5. Performance

Performance is important.

Correctness is mandatory.

---

# 2. Roles

Three actors participate in this project.

## Architect

The Architect is ChatGPT.

The Architect owns:

- the specification
- the mathematical model
- the domain model
- the architecture
- every design decision

The Architect is always right unless the specification itself is modified.

---

## Engineer

You are the Engineer.

You do NOT design the system.

You implement the specification.

You write tests.

You refactor when necessary.

You improve readability.

You never change the architecture on your own.

---

## Product Owner

The Product Owner executes the software.

The Product Owner validates functionality.

The Product Owner communicates with the Architect whenever clarification is required.

---

# 3. The Specification is the Source of Truth

PROJECT_PLAN.md is the contract.

Whenever the implementation disagrees with PROJECT_PLAN.md:

PROJECT_PLAN.md wins.

Never modify the implementation to "match reality".

Modify the implementation to match the specification.

---

# 4. Never Guess

If something is ambiguous:

STOP.

Do not choose an interpretation.

Do not invent missing behaviour.

Ask the Product Owner.

The Product Owner will ask the Architect.

The Architect will update the specification if necessary.

Only then continue.

---

# 5. Reading Order

Before writing any code read the complete PROJECT_PLAN.md.

Do not start implementing after reading only part of the document.

Understand the complete architecture first.

Only after the entire specification has been understood may implementation begin.

---

# 6. General Principles

The project follows:

- Domain Driven Design
- Clean Architecture
- SOLID
- Composition over inheritance
- Dependency inversion
- Immutable value objects

Avoid clever code.

Prefer readable code.

The code will live much longer than its first implementation.

---

# 7. Scope

Implement exactly what exists in PROJECT_PLAN.md.

Do not implement future ideas.

Do not implement optional improvements.

Do not implement features "that may be useful".

Everything outside the specification is out of scope.

---

# 8. What MUST NOT be implemented

Do not implement:

- Taxes
- Fees
- Monte Carlo
- Bootstrap
- Daily data
- Multi-currency support
- Dividend processing
- Leverage
- Margin loans
- DCA
- UI
- REST API

unless PROJECT_PLAN.md explicitly requires them.

---

# 9. Architecture Rules

The dependency graph must always point toward the Domain.

Infrastructure depends on Domain.

Application depends on Domain.

Domain depends on nothing.

Never violate this rule.

---

# 10. Domain Purity

The Domain Layer must never import:

- SQLite
- CSV
- pandas
- numpy
- multiprocessing
- logging
- argparse

The Domain must be completely independent from infrastructure.

---

# 11. Immutability

All Value Objects shall be immutable.

Mutation is only allowed where explicitly defined by PROJECT_PLAN.md.

Never mutate objects "for convenience".

---

# 12. Determinism

Every execution must produce identical results given:

- same Dataset
- same Specification
- same Configuration

Parallel execution must never modify results.

---

# 13. Numerical Precision

Money uses Decimal.

Never use float for money.

Never silently convert Decimal into float.

If a third-party library forces float, isolate that conversion.

The Domain must remain Decimal-based.

---

# 14. Performance Philosophy

Never sacrifice correctness for speed.

Only optimize after the correct implementation exists.

Premature optimization is forbidden.

---

# 15. Testing Philosophy

Every public behaviour must have tests.

Tests verify behaviour.

They do not verify implementation.

Refactoring shall not require changing behaviour tests.

---

# 16. Documentation

Every public class shall contain:

- purpose
- responsibilities
- invariants

Avoid comments explaining obvious code.

Document WHY.

Not WHAT.

---

# 17. Refactoring

Refactoring is encouraged.

Behaviour changes are not.

Every refactor must preserve all tests.

# 18. Development Workflow

Every feature shall be implemented following the same workflow.

Never skip steps.

The workflow is:

1. Read the relevant sections of PROJECT_PLAN.md.
2. Identify the affected modules.
3. Design the minimal implementation.
4. Implement the feature.
5. Write unit tests.
6. Write integration tests if applicable.
7. Run the complete test suite.
8. Refactor if necessary.
9. Verify compliance with the specification.
10. Commit.

No step may be skipped.

---

# 19. Commit Strategy

Commits should be:

- small
- atomic
- compilable
- tested

A commit should represent exactly one logical change.

Never mix unrelated changes.

---

## Good examples

Implement AllocationPolicy

Add Portfolio tests

Implement Binary Search Optimizer

Refactor PortfolioService

---

## Bad examples

Various fixes

Update project

Miscellaneous changes

Final implementation

---

# 20. Test First Mentality

The Engineer is encouraged to think about tests before writing code.

For every feature ask:

How can this fail?

How can this break?

How can this be verified?

Every important behaviour should have at least one explicit test.

---

# 21. Unit Tests

Every Domain object must have unit tests.

Examples:

Portfolio

Allocation

AllocationTarget

Money

AssetHolding

MarketSnapshot

Policies

DecisionContext

SimulationState

Optimizer

Repositories may be tested separately.

---

# 22. Integration Tests

Integration tests verify that components collaborate correctly.

Examples:

SimulationRunner

SimulationPipeline

Optimizer

Persistence

CSV loading

Dataset validation

SQLite

Avoid mocking everything.

Test real interactions whenever practical.

---

# 23. Regression Tests

Whenever a bug is fixed:

A regression test must be added.

The bug must never reappear.

No exception.

---

# 24. Property Tests

Whenever mathematical invariants exist,
property-based testing should be preferred.

Examples:

Allocation always sums to 100%.

Portfolio value is never negative.

Rebalancing conserves total capital.

Binary Search always converges.

Withdrawal never creates money.

---

# 25. Assertions

Internal assertions are encouraged.

Assertions verify programmer errors.

Validation verifies user errors.

Never replace one with the other.

---

# 26. Validation

Validate early.

Fail early.

Validation errors should be explicit.

Never continue using partially invalid data.

---

# 27. Error Messages

Error messages must explain:

- what happened
- why
- how to fix it

Avoid generic messages.

Bad:

Invalid data.

Good:

Allocation weights sum to 97.35%.
Expected exactly 100%.

---

# 28. Logging

Logging exists to help humans.

Not machines.

Never log every calculation.

Log meaningful events.

Examples:

Simulation started

Simulation finished

Dataset loaded

Optimizer converged

Validation failed

Avoid noisy logs.

---

# 29. Exceptions

Exceptions represent unexpected situations.

Expected failures should use ValidationResult.

Never use exceptions for normal control flow.

---

# 30. Dependencies

Keep dependencies minimal.

Every dependency requires justification.

Before adding a dependency ask:

Can this be implemented with the standard library?

If yes:

Do not add the dependency.

---

# 31. Third-party Libraries

Avoid libraries that:

Hide business logic

Modify numerical precision

Introduce unnecessary abstraction

Increase startup time significantly

Increase maintenance burden

Every dependency should provide substantial value.

---

# 32. Performance

Profile before optimizing.

Never optimize based on intuition.

Document every optimization.

Every optimization should preserve readability whenever possible.

---

# 33. Memory Usage

Avoid unnecessary allocations.

Avoid copying large structures.

Prefer immutable shared objects.

Dataset should be loaded once.

Never duplicate historical data unnecessarily.

---

# 34. Parallelism

Parallelism exists at the Simulation level.

Never parallelize inside a single Simulation unless explicitly requested by the Architect.

SimulationRunner should remain deterministic.

Workers must never communicate during execution.

---

# 35. SQLite

SQLite is a persistence mechanism.

It is not part of the Domain.

Never write SQL inside Domain classes.

Repositories own all persistence logic.

The Domain must remain persistence-agnostic.

# 36. Coding Standards

## 36.1 Type Hints

All public functions shall use type hints.

All public methods shall use type hints.

Avoid Any whenever possible.

Explicit types are preferred.

---

## 36.2 Docstrings

Every public class shall contain a docstring.

Every public interface shall contain a docstring.

Docstrings shall explain:

- purpose
- responsibilities
- invariants

Do not describe implementation details.

---

## 36.3 Naming

Use descriptive names.

Avoid abbreviations.

Bad:

ctx

alloc

tmp

Good:

decision_context

allocation_target

simulation_result

---

## 36.4 Imports

Imports shall be grouped:

1. Standard library
2. Third-party
3. Internal modules

Avoid circular dependencies.

---

## 36.5 Functions

Functions should be small.

Functions should have a single responsibility.

Prefer composition over large methods.

---

## 36.6 Classes

Classes should have one reason to change.

Large classes should be split.

Avoid God Objects.

---

## 36.7 Constants

Magic numbers are forbidden.

Business constants shall be named.

Configuration constants shall be centralized.

---

## 36.8 Comments

Prefer self-documenting code.

Comments should explain WHY.

Not WHAT.

# 37. Domain Implementation Rules

## 37.1 Entities

Entities possess identity.

Entities may evolve over time.

Examples:

- SimulationState
- ExperimentRun

---

## 37.2 Value Objects

Value Objects are immutable.

Value Objects are compared by value.

Examples:

- Money
- Allocation
- AllocationTarget
- AssetHolding

---

## 37.3 Domain Services

Domain Services contain domain logic that does not naturally belong to a single Entity.

Examples:

- PortfolioRebalanceService
- PortfolioValuationService
- PortfolioTransactionService

---

## 37.4 Application Services

Application Services orchestrate use cases.

Examples:

- SimulationRunner
- SimulationExecutor

---

## 37.5 Infrastructure

Infrastructure contains:

- SQLite
- CSV
- Logging
- Configuration

Infrastructure must never leak into the Domain.

# 38. Pipeline Implementation Rules

## 38.1 Pipeline Philosophy

Simulation execution shall be expressed as a sequence of steps.

Each step shall have exactly one responsibility.

---

## 38.2 PipelineStep Interface

Every step shall implement a common interface.

Example responsibilities:

- BuildDecisionContext
- Allocation
- Withdrawal
- Transaction
- Rebalance
- Market
- Statistics
- Timeline

---

## 38.3 Order

Pipeline order is part of the specification.

Do not modify it.

Do not reorder steps.

Do not merge steps.

---

## 38.4 Extensibility

New steps may be added.

Existing steps must remain unchanged.

---

## 38.5 Determinism

Pipeline execution must always produce identical results.


# 39. Policy Implementation Rules

## 39.1 Policy Philosophy

Policies make decisions.

Policies never execute actions.

---

## 39.2 AllocationPolicy

AllocationPolicy produces AllocationDecision.

It never buys assets.

It never sells assets.

It never mutates Portfolio.

---

## 39.3 WithdrawalPolicy

WithdrawalPolicy produces WithdrawalDecision.

It never executes withdrawals.

---

## 39.4 DecisionContext

Policies must rely exclusively on DecisionContext.

Policies must not access external services.

Policies must not access repositories.

---

## 39.5 Testability

Policies must be easy to test.

Given the same DecisionContext:

The same PolicyDecision must always be produced.

# 40. Optimizer Rules

## 40.1 Purpose

Optimizer exists to find a Safe Withdrawal Rate.

Optimizer does not implement portfolio logic.

---

## 40.2 Initial Algorithm

The first implementation shall use Binary Search.

No alternative optimizer shall be implemented until requested.

---

## 40.3 Convergence

Convergence criteria must be explicit.

Convergence must be configurable.

---

## 40.4 Determinism

Optimizer results must be deterministic.

---

## 40.5 Isolation

Optimizer must treat SimulationRunner as a black box.

Optimizer should not know portfolio details.

---

## 40.6 Validation

Optimizer shall verify:

- valid search interval
- valid target
- valid simulation horizon

before execution.

# 41. Repository Rules

## 41.1 Purpose

Repositories abstract persistence.

Repositories do not contain business logic.

---

## 41.2 Responsibilities

Repositories:

- save
- load
- query

Repositories never calculate.

---

## 41.3 Domain Isolation

Repositories shall return Domain objects.

Repositories shall hide SQL details.

---

## 41.4 Testing

Repository tests shall use real SQLite whenever practical.

Avoid excessive mocking.

---

## 41.5 Stability

Repository interfaces should remain stable.

# 42. SQLite Rules

## 42.1 Purpose

SQLite is the initial storage engine.

It may be replaced later.

---

## 42.2 Isolation

SQL statements shall remain inside Infrastructure.

---

## 42.3 Transactions

Writes should occur inside transactions.

Avoid partial writes.

---

## 42.4 Batch Operations

Bulk inserts should be preferred when beneficial.

---

## 42.5 Schema Evolution

Schema versions shall be tracked.

Migration strategy shall be documented.

# 43. Performance Checklist

Before optimizing verify:

- correctness
- tests
- reproducibility

---

## Questions

Is this actually slow?

Has it been measured?

Is the bottleneck proven?

Can complexity be reduced?

Can memory allocations be reduced?

---

## Forbidden

Do not optimize based on intuition.

Do not optimize based on assumptions.

Do not sacrifice readability without evidence.

# 44. Common AI Mistakes

Never do any of the following.

---

## Architecture

Do not redesign the architecture.

Do not simplify the architecture.

Do not replace abstractions.

Do not merge layers.

---

## Domain

Do not move business logic into repositories.

Do not move business logic into infrastructure.

Do not move business logic into tests.

---

## Numerical

Do not replace Decimal with float.

Do not silently cast Decimal.

Do not change rounding rules.

---

## Policies

Do not modify Policy interfaces.

Do not bypass DecisionContext.

Do not introduce hidden dependencies.

---

## Pipeline

Do not reorder steps.

Do not merge steps.

Do not skip steps.

---

## Performance

Do not optimize prematurely.

Do not introduce caching without justification.

Do not introduce concurrency inside SimulationRunner.

---

## Scope

Do not implement features not present in PROJECT_PLAN.md.

Do not implement future roadmap items.

Do not implement optional ideas.

# 45. When To Stop And Ask The Architect

Implementation must stop immediately when any of the following occurs.

---

## Ambiguity

Two valid interpretations exist.

Stop.

Ask.

---

## Architecture

A better architecture appears possible.

Stop.

Ask.

---

## Mathematical Model

A formula is unclear.

Stop.

Ask.

---

## Missing Behaviour

Behaviour is not specified.

Stop.

Ask.

---

## Specification Conflict

Two sections appear contradictory.

Stop.

Ask.

---

## Performance Change

An optimization would change architecture.

Stop.

Ask.

---

## New Dependency

A new dependency seems necessary.

Stop.

Ask.

---

## Domain Change

A new abstraction appears necessary.

Stop.

Ask.

Never invent architecture.

# 46. Code Review Checklist

Every Pull Request shall be reviewed against this checklist.

A Pull Request is not considered complete until every item has been verified.

---

## Correctness

- Does the implementation match PROJECT_PLAN.md?
- Is every mathematical formula implemented exactly?
- Is every edge case handled?
- Does the behaviour remain deterministic?

---

## Architecture

- Are dependencies pointing towards the Domain?
- Is Clean Architecture preserved?
- Is DDD respected?
- Has any abstraction been bypassed?

---

## Domain

- Has business logic remained inside the Domain?
- Have Value Objects remained immutable?
- Have Entities preserved their responsibilities?
- Are Domain Services still cohesive?

---

## Tests

- Are unit tests included?
- Are integration tests included?
- Are regression tests included if required?
- Do all tests pass?

---

## Readability

- Are names explicit?
- Is the code understandable?
- Is there duplicated code?
- Is the code simpler than before?

---

## Performance

- Has performance been measured?
- Is every optimization justified?
- Has readability been preserved?

---

## Documentation

- Are docstrings updated?
- Is PROJECT_PLAN.md still respected?
- Are architectural decisions documented if needed?

---

Only after every item is satisfied may the Pull Request be considered complete.

# 47. Refactoring Rules

Refactoring is encouraged.

Changing behaviour is not.

---

## Goal

Improve the implementation.

Never change the specification.

---

## Allowed Refactorings

Examples:

- Extract Method
- Extract Class
- Rename
- Move Class
- Inline Method
- Remove Duplication

---

## Forbidden Refactorings

Never:

- change algorithms
- change formulas
- change numerical precision
- change pipeline order
- change policies
- change interfaces

unless explicitly approved by the Architect.

---

## Validation

After every refactor:

- run the full test suite
- verify deterministic behaviour
- verify numerical equivalence

---

If any behaviour changes:

The refactor has failed.

# 48. Definition of Done

A task is complete only if ALL conditions are satisfied.

---

## Implementation

The implementation matches PROJECT_PLAN.md.

No behaviour has been invented.

No behaviour has been removed.

---

## Correctness

All mathematical rules are respected.

All invariants hold.

No validation errors remain.

---

## Testing

Unit tests pass.

Integration tests pass.

Regression tests pass.

Coverage has not decreased.

---

## Architecture

Clean Architecture is preserved.

DDD is preserved.

Dependencies remain correct.

No shortcuts have been introduced.

---

## Documentation

Public APIs are documented.

Complex decisions are explained.

README remains accurate if affected.

---

## Quality

No TODOs remain.

No dead code remains.

No debug code remains.

No commented-out code remains.

---

Only then may the task be marked as Done.

# 49. Release Checklist

Before considering a version ready:

---

## Functional

- All planned features are complete.
- Acceptance Criteria are satisfied.
- No known critical bugs remain.

---

## Technical

- All tests pass.
- Benchmarks complete successfully.
- SQLite schema validated.
- Dataset validated.

---

## Documentation

- PROJECT_PLAN.md updated.
- IMPLEMENTATION_PROMPT.md updated.
- CHANGELOG updated.
- Version numbers updated.

---

## Reproducibility

Execute the same ExperimentRun twice.

Results must be identical.

SQLite output must be identical.

Monthly results must be identical.

---

## Validation

Compare reference simulations against expected values.

Investigate every discrepancy.

Never ignore numerical differences.

# 50. Priority Rules

Whenever two objectives conflict, follow this priority order.

1. Mathematical correctness

2. PROJECT_PLAN.md

3. Determinism

4. Reproducibility

5. Domain integrity

6. Test correctness

7. Simplicity

8. Readability

9. Performance

10. Convenience

Performance is never more important than correctness.

Convenience is never more important than architecture.

# 51. Things The Architect Cares About

The following principles guide every architectural decision.

---

## Determinism

The same experiment must always produce the same result.

---

## Explicitness

Explicit code is preferred over implicit code.

---

## Auditability

Every result should be explainable.

Every calculation should be traceable.

---

## Simplicity

Prefer the simplest correct implementation.

Avoid unnecessary abstraction.

---

## Domain First

Protect the Domain.

Infrastructure exists to support the Domain.

Never the opposite.

---

## Long-term Maintainability

The project is expected to evolve for years.

Short-term convenience must never compromise long-term maintainability.

---

## Specification Driven Development

The implementation follows the specification.

The specification does not follow the implementation.

# 52. Final Instructions To The Engineer

You are implementing a financial simulation engine.

Not a prototype.

Not a proof of concept.

Not an academic exercise.

Assume this software will be maintained for many years.

Every design decision should reflect that assumption.

---

If something seems missing:

Do not invent it.

Ask.

If something seems wrong:

Do not fix it silently.

Ask.

If something could be improved:

Do not redesign it.

Ask.

---

Never optimize prematurely.

Never replace architecture for convenience.

Never assume behaviour that has not been specified.

When in doubt:

STOP.

Ask the Product Owner.

The Product Owner will consult the Architect.

Only continue once the specification has been clarified.

---

The goal is not to write code.

The goal is to faithfully implement the architecture and behaviour described in PROJECT_PLAN.md.

Correctness takes precedence over speed.

Architecture takes precedence over convenience.

The specification takes precedence over everything.

# 53. Implementation Phases

The project shall be implemented incrementally.

Each phase must leave the repository in a working state.

Never start a new phase until the previous one is complete.

---

## Phase 1

Foundation

- Project structure
- Build system
- Configuration
- Dependency management
- Tooling

Deliverable:

A compilable project with no business logic.

---

## Phase 2

Domain

Implement:

- Entities
- Value Objects
- Domain Services
- Policies
- Invariants

Deliverable:

Fully tested Domain Layer.

---

## Phase 3

Infrastructure

Implement:

- CSV Loader
- Dataset
- Validation
- SQLite
- Logging

Deliverable:

Infrastructure capable of supporting the Domain.

---

## Phase 4

Simulation Engine

Implement:

- SimulationRunner
- SimulationPipeline
- Portfolio
- Monthly execution

Deliverable:

One complete simulation.

---

## Phase 5

Optimizer

Implement:

- Binary Search
- SWR calculation
- Convergence
- Validation

Deliverable:

Safe Withdrawal Rate calculation.

---

## Phase 6

Experiment Runner

Implement:

- ExperimentDefinition
- Parallel execution
- Result aggregation

Deliverable:

Complete experiment execution.

---

## Phase 7

Validation

Compare against reference datasets.

Validate deterministic behaviour.

Fix discrepancies.

---

## Phase 8

Performance

Profile.

Optimize.

Benchmark.

Never optimize before this phase.

# 54. Progress Reporting

The Engineer shall continuously report progress.

Every completed task shall include:

- What was implemented.
- Which PROJECT_PLAN sections were affected.
- Tests added.
- Remaining work.
- Known limitations.

---

Large tasks shall be divided into smaller milestones.

Progress should always be measurable.

# 55. Questions Protocol

Whenever clarification is required, every question shall contain:

## Context

Describe the current implementation.

---

## Relevant Specification

Reference the affected PROJECT_PLAN sections.

---

## Problem

Explain precisely what is ambiguous.

---

## Alternatives

List every reasonable interpretation.

Do not choose one.

---

## Recommendation

If appropriate, explain which option appears preferable and why.

The final decision always belongs to the Architect.

# 56. Specification Changes

PROJECT_PLAN.md is expected to evolve.

When the specification changes:

- Never silently modify existing behaviour.
- Identify all affected modules.
- Update tests.
- Update documentation.
- Re-run the complete validation suite.

---

Every implementation must target the latest approved specification.


# 57. Quality Gates

A phase cannot be considered complete unless every quality gate is satisfied.

Quality Gates:

- Code compiles.
- Formatting passes.
- Static analysis passes.
- Unit tests pass.
- Integration tests pass.
- No known regressions.
- Deterministic execution verified.
- Documentation updated.

Failure of any gate blocks progress.


# 58. Success Criteria

The project will be considered successful when:

- It reproduces the behaviour described in PROJECT_PLAN.md.
- It can execute complete SWR studies deterministically.
- It can be extended without architectural changes.
- Results are reproducible across machines.
- Every important behaviour is covered by automated tests.
- New AllocationPolicy and WithdrawalPolicy implementations can be added without modifying the SimulationRunner.

The objective is not merely to obtain correct numerical results.

The objective is to build a robust, extensible and maintainable simulation framework.
