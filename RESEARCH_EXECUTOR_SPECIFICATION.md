# ResearchExecutor Behavioural Specification

## Purpose

`ResearchExecutor` is the Research Layer component that executes one already-materialised, immutable `ResearchPlan`.

It validates the execution request, translates the plan's ordered units to the frozen engine's public experiment/context contract, delegates exactly once to `SimulationExecutor`, and preserves the lossless association between every planned unit and its corresponding engine result.

It is purely an execution orchestrator and does **not** build, construct, or plan a study. In particular, it does not obtain cohorts, generate parameter configurations, materialise policies, construct the cohort × parameter matrix, or build or modify a `ResearchPlan`. The construction of a `ResearchPlan` belongs exclusively to a dedicated planning component to be introduced in a future specification.

This separates reusable study planning from one-shot execution orchestration, ensuring that `ResearchExecutor` can never absorb plan-building or planning responsibilities.

---

## Architectural Decision: `ResearchPlan` Is Required

### Decision

Introduce `ResearchPlan` as an immutable Public Research Domain Contract representing one fully materialised study ready for execution.

It is the boundary between planning and execution:

```text
ExperimentDefinition + cohorts + parameter configurations
                         │
                         ▼
             planning / policy-materialisation boundary
                         │
                         ▼
                    ResearchPlan
                         │
                         ▼
                 ResearchExecutor
                         │
                         ▼
                SimulationExecutor
```

`ResearchPlan` contains an ordered collection of immutable planned simulation units. Each unit retains its `CohortSpecification`, `ParameterConfiguration`, and concrete allocation and withdrawal policies. It contains no mutable engine state and no result values.

### Why a plan is necessary

Without `ResearchPlan`, `ResearchExecutor` would own two independent reasons to change:

1. how a study is generated and materialised; and
2. how an already-defined study is executed.

Those concerns evolve independently. An explicit immutable plan therefore provides:

- a reviewable, cacheable, reproducible representation of the exact work to run;
- a stable hand-off to execution without rerunning cohort generation, parameter sweeps, or policy materialisation;
- a boundary suitable for future sampling, optimisation, scheduling, parallel execution, persistence, and resumption; and
- a minimal executor that has no scientific or policy-construction knowledge.

### Ownership Boundary of ResearchPlan Construction

To ensure long-term architectural integrity and prevent responsibility drift across future milestones, the ownership of `ResearchPlan` construction is explicitly frozen now:

- **Immutable Value Object:** `ResearchPlan` is a pure, immutable domain value object representing a fully materialised study.
- **Pre-validated Input:** `ResearchExecutor` only accepts an already constructed and fully validated `ResearchPlan`.
- **No In-Flight Plan Manipulation:** `ResearchExecutor` never constructs, builds, modifies, adds, removes, reorders, or materialises anything inside the plan.
- **Dedicated Planning Component:** Construction of a `ResearchPlan` belongs exclusively to a dedicated planning component that will be introduced in a future milestone.
- **Frozen Ownership Boundary:** Even though the planning component is not yet specified, this ownership boundary is permanently frozen now so that `ResearchExecutor` cannot gradually absorb planning or plan-building responsibilities in future milestones.

### Contract classification

| Type | Classification | Responsibility |
| :--- | :--- | :--- |
| `ResearchPlan` | Public Research Domain Contract (Immutable Value Object) | Immutable, ordered description of all materialised simulations in one study. Constructed exclusively by a dedicated planning component. |
| Planned simulation unit | Public constituent value object or immutable structural contract | One cohort + configuration + concrete policy pair within a plan. |
| `ResearchExecutor` | Research application/orchestration service | Pure execution orchestrator. Accepts an already validated plan and delegates execution through `SimulationExecutor`. |

The exact names, module placement, and field signatures of `ResearchPlan` and its unit type are deferred to Public API Review. Their behavioural semantics in this specification are binding.

---

## `ResearchPlan` Behavioural Contract

### Required contents

Each `ResearchPlan` must contain:

- the immutable source `ExperimentDefinition` identifying shared study inputs;
- a non-empty, immutable, ordered tuple of planned simulation units; and
- no mutable execution state, result values, aggregate metrics, progress status, timestamps, caches, or infrastructure handles.

Each planned simulation unit must contain:

- one immutable `CohortSpecification`;
- one immutable `ParameterConfiguration`;
- one complete concrete `AllocationPolicy` / `WithdrawalPolicy` pair; and
- no `SimulationState`, `SimulationResult`, mutable portfolio, generated result metric, or hidden factory/callback.

The concrete policy pair is execution materialisation, not part of the identity of `ParameterConfiguration`. Neither the plan nor its unit may mutate or attach policies to a configuration or cohort value object.

### Identity, completeness, and validation

One planned unit is identified by:

```text
(study identity, cohort identity, parameter-configuration identity)
```

For a valid plan:

- every unit has a valid source study, cohort, configuration, and complete concrete policy pair;
- no two units have the same `(cohort identity, parameter-configuration identity)` within one plan;
- unit order is explicit and immutable;
- all units refer to the plan's one source `ExperimentDefinition`; and
- every unit can be translated to one valid frozen-engine `SimulationContext` without changing any input.

`ResearchPlan` (or its dedicated construction boundary) must reject invalid or ambiguous plans before an executor sees them. `ResearchExecutor` performs defensive structural validation at its public boundary, but it must not recreate cohort feasibility, sweep validation, or policy semantics.

### Ordering and cardinality

For a planner combining ordered cohorts $C$ and ordered configurations $P$, the normal complete matrix has:

$$
|C| \times |P|
$$

units in this deterministic order:

```text
for cohort in cohorts:                    # outer / slowest-changing dimension
    for configuration in configurations:  # inner / fastest-changing dimension
        yield materialised planned unit
```

The planner must preserve the chronological order emitted or declared for cohorts and the Cartesian-product order emitted or declared for configurations. A plan may represent a deliberately selected subset only when its construction contract states that selection explicitly; `ResearchExecutor` never filters, augments, reorders, or regenerates it.

### Plan construction boundary & ownership freeze

The construction of a `ResearchPlan` involves five preparation phases that occur strictly before execution:

1. Validate the planning request.
2. Obtain cohorts from `ExperimentDefinition` or an explicit `CohortGenerator` strategy.
3. Obtain parameter configurations from an explicit supplied sequence or `ParameterSweepEngine`.
4. Delegate configuration-to-policy conversion to an explicit policy-materialisation boundary.
5. Build and validate the immutable `ResearchPlan` value object.

**Ownership Boundary Invariants:**
- `ResearchExecutor` is strictly an execution orchestrator and **never** owns or executes any of these five preparation phases.
- Construction of a `ResearchPlan` belongs exclusively to a dedicated planning component to be introduced and specified in a future milestone.
- `ResearchExecutor` accepts an already built and validated `ResearchPlan` as an input invariant. It never adds, removes, reorders, materialises, or alters any content inside the plan.
- This ownership separation is permanently frozen at the behavioural specification phase to prevent `ResearchExecutor` from absorbing planning or plan-building responsibilities in future sub-milestones.

The planning boundary, not `ResearchExecutor`, is responsible for coordinating:

- `ExperimentDefinition` as immutable study intent;
- `CohortGenerator` as the sole owner of temporal feasibility and generation;
- `ParameterSweepEngine` as the sole owner of parameter-grid construction; and
- an explicit policy materialiser/factory as the sole owner of configuration-to-policy interpretation.

---

## Responsibilities & Scope Boundaries

### Core Responsibilities

`ResearchExecutor` owns exclusively:

- **Execution-request validation:** Ensure the supplied object is a structurally complete, pre-validated, immutable `ResearchPlan` executable through the frozen engine contracts.
- **Plan-to-engine translation:** Create one ordered engine `SimulationContext` for every planned unit using the plan's study inputs, cohort, and already-materialised policy pair without modifying the plan.
- **Single execution delegation:** Build one ordered engine experiment request and call `SimulationExecutor.execute(...)` exactly once per valid `ResearchPlan` execution request.
- **Provenance preservation:** Preserve the one-to-one ordered association between each planned unit and the correspondingly ordered individual engine result.
- **Failure transparency:** Propagate planning-independent execution and collaborator failures without fabricating a successful or partial study output.

### Explicit Scope Boundaries

- `ResearchExecutor` consumes an already constructed plan; it never builds, constructs, or modifies one.
- Construction of `ResearchPlan` belongs strictly to a dedicated planning component introduced in a future specification.
- `ResearchExecutor` is not a consumer of `CohortGenerator` or `ParameterSweepEngine` in its execution path. They are planning dependencies only.
- `ResearchExecutor` receives concrete policies from a plan; it never interprets `ParameterConfiguration` bindings or materialises a policy.
- `SimulationExecutor` owns engine-experiment execution; `SimulationRunner` owns individual simulation lifecycle; the frozen v0.1 pipeline owns monthly processing.
- Result aggregation, statistics comparison, optimisation, selection, reporting, persistence, and progress management are separate concerns.

---

## Forbidden Responsibilities

`ResearchExecutor` must not:

- construct, build, modify, add to, remove from, reorder, or materialise any unit, policy, or configuration inside a `ResearchPlan`;
- absorb any plan-building responsibilities, which belong exclusively to a dedicated planning component introduced in a future milestone;
- call `CohortGenerator` or `ParameterSweepEngine`, construct axes, select cohorts, or generate parameter configurations;
- create, materialise, inspect for meaning, mutate, or select allocation or withdrawal policies;
- cross cohorts and configurations, calculate plan cardinality as planning work, construct `ResearchPlan`, or alter a plan's unit order or membership;
- implement financial calculations, market evolution, inflation adjustment, valuation, withdrawal, allocation, rebalancing, depletion, or portfolio mutation;
- call monthly pipeline steps, construct or mutate `SimulationState`, or reproduce `SimulationRunner` / `SimulationExecutor` behaviour;
- execute an individual simulation directly in place of `SimulationExecutor` or `SimulationRunner`;
- mutate `ExperimentDefinition`, `ResearchPlan`, planned units, `CohortSpecification`, `ParameterConfiguration`, policies, datasets, portfolios, contexts, or results;
- aggregate, group, pivot, rank, compare, filter by outcome, calculate success rates, calculate summary statistics, or produce reports/charts;
- optimise, search, sample, prune, cache, schedule, parallelise, resume, or make a future execution decision based on outcomes;
- conceal an unexpected failure as an empty, successful, or partial study result; or
- access filesystems, databases, networks, environment configuration, CLI, plotting, persistence, or presentation infrastructure in its core path.

---

## Execution Lifecycle

The complete study flow is intentionally split into two ownership phases:

| Phase | Owner | Behaviour |
| :--- | :--- | :--- |
| 1. Validate planning request | Planning boundary | Validate source and composition choices before materialisation. |
| 2. Obtain cohorts | Planning boundary | Use declared cohorts or explicitly invoke `CohortGenerator`. |
| 3. Obtain parameter configurations | Planning boundary | Accept supplied configurations or explicitly invoke `ParameterSweepEngine`. |
| 4. Build immutable `ResearchPlan` | Dedicated planning component | Materialise policies through its dedicated collaborator; validate and freeze ordered planned units. |
| 5. Execute plan | `ResearchExecutor` | Validate plan, translate units to engine contexts, and delegate once to `SimulationExecutor`. |
| 6. Return execution + provenance | `ResearchExecutor` | Return unchanged engine execution values with lossless ordered plan-unit association. |

For phase 5, `ResearchExecutor` proceeds in this exact order:

1. Receive one `ResearchPlan` and the injected `SimulationExecutor` collaborator.
2. Defensively validate the plan's structural completeness, unique planned identities, immutability/ordering contract, and ability to form engine contexts without mutation.
3. Translate every plan unit to one `SimulationContext` in the plan's exact order.
4. Build one ordered engine experiment request using the source study name and description and the complete context tuple.
5. Invoke `SimulationExecutor.execute(...)` exactly once.
6. Return the completed immutable engine output with an equally ordered, lossless association to the original plan units.

No cohort generation, parameter generation, policy materialisation, plan reconstruction, aggregation, or second execution phase may occur during this lifecycle.

---

## Failure Behaviour

`ResearchExecutor` must reject the execution request before calling `SimulationExecutor` when:

1. the plan is missing or does not satisfy the approved `ResearchPlan` contract;
2. the injected `SimulationExecutor` is missing or does not satisfy its public contract;
3. the plan contains no units, malformed/non-immutable units, incomplete policy pairs, or invalid cohort/configuration types;
4. planned unit identities are missing, duplicate, or ambiguous;
5. plan order/membership cannot be preserved in the frozen engine request; or
6. a required `SimulationContext` cannot be constructed without mutation.

`ResearchExecutor` must validate the complete execution request before calling `SimulationExecutor`; it must not execute a valid prefix and then discover a malformed later unit.

Unexpected `SimulationExecutor` failures must propagate unchanged, or be wrapped only in a documented research-execution error that preserves the original exception as its cause and identifies the plan/unit context. No completed research execution output may be returned after such a failure.

A modelled failed `SimulationResult` is a normal immutable v0.1 output. `ResearchExecutor` must preserve it and its association to the planned unit without interpreting it, calculating a metric, or stopping a successfully delegated engine experiment.

Failures during cohort generation, parameter generation, policy materialisation, or plan construction occur before `ResearchExecutor` is called and remain the responsibility of the planning boundary.

---

## Result and Provenance Boundary

`ResearchExecutor` returns execution, not analysis.

Its result must preserve a one-to-one ordered relationship equivalent to:

```text
ResearchPlan.units[0] → engine result[0]
ResearchPlan.units[1] → engine result[1]
...
```

This return path must:

- preserve the exact immutable `SimulationResult` values returned by `SimulationExecutor`;
- preserve the original immutable plan units, including their cohort/configuration provenance;
- contain exactly one association for every plan unit and individual engine result; and
- preserve the plan's order exactly.

It must not derive or return a success rate, final-wealth summary, worst-case cohort, drawdown surface, ranking, recommendation, chart, or aggregate table. A future `ResultAggregator` or analysis component consumes this lossless output through its own reviewed contract.

The exact wrapper type versus adjacent provenance representation is deferred to Public API Review.

---

## Dependency Rules and Architectural Placement

```text
Planning boundary
    ├── ExperimentDefinition
    ├── CohortGenerator
    ├── ParameterSweepEngine
    └── policy materialiser
                 │
                 ▼
            ResearchPlan
                 │
                 ▼
          ResearchExecutor
                 │
                 ▼
         SimulationExecutor
                 │
                 ▼
      v0.1 execution engine (black box)
```

Dependency invariants:

1. `ResearchExecutor` depends only on the public contracts of `ResearchPlan`, its planned unit, `SimulationExecutor`, and the minimum frozen engine request/context/result contracts needed for delegation.
2. `ResearchExecutor` receives `SimulationExecutor` through dependency injection or an equally explicit composition boundary. It must not instantiate an executor, runner, generator, policy, materialiser, or planner internally.
3. `ResearchPlan` construction may depend on public research contracts and engine policy interfaces, but the frozen engine must remain unaware of research plans, cohorts, configurations, and provenance.
4. `CohortGenerator` and `ParameterSweepEngine` remain pure peers, unaware of planning/execution services and the v0.1 engine application layer.
5. Optional future caching, persistence, scheduling, parallelisation, progress, or resumption must operate above or around the immutable plan. They must not be embedded in `ResearchExecutor`.

---

## Determinism

Given an equal immutable `ResearchPlan`, equivalent injected `SimulationExecutor` behaviour, and the same frozen engine inputs, `ResearchExecutor` must:

- create an equivalent ordered engine experiment with one context per plan unit;
- invoke `SimulationExecutor` once with that same order; and
- return equivalent ordered, lossless plan-unit-to-result associations.

It must not depend on randomness, system time, memory addresses, filesystem/network/environment state, or unordered collection iteration. It must not introduce concurrency whose scheduling changes observable context order, result order, or failure semantics.

---

## Required Tests

After specification and Public API approval, implementation tests must verify:

1. `ResearchExecutor` receives a `SimulationExecutor` by injection and never instantiates a runner, generator, materialiser, planner, or concrete policy.
2. It accepts one valid immutable plan, creates one engine context per plan unit in exact plan order, and delegates exactly once to `SimulationExecutor`.
3. It never calls `CohortGenerator` or `ParameterSweepEngine`, even when plan provenance includes cohorts/configurations originally produced by those components.
4. It neither materialises policies nor interprets parameter binding names; engine contexts use the policy objects already held by plan units.
5. It preserves all plan units and returned individual results in a one-to-one, ordered, lossless provenance association.
6. It leaves the plan, experiment, cohort, configuration, policy, dataset, portfolio, context, and result values unmodified.
7. Invalid plans, invalid collaborators, malformed units, incomplete policy pairs, duplicate identities, and untranslatable units fail before any call to `SimulationExecutor`.
8. Executor failures preserve their causal exception and never yield a completed or partial research execution output.
9. Modelled failed `SimulationResult` values are retained without research-layer aggregation or interpretation.
10. Repeated execution with equal plan inputs and contract-faithful collaborators yields equivalent ordered contexts, single executor invocation, and output associations.
11. Static/design guards confirm no financial calculations, aggregation, optimisation, cohort/parameter generation, policy materialisation, planning, I/O, caching, scheduling, or pipeline-step calls in the execution service.
12. Plan-construction tests (owned by the later planning component) separately verify cohort/configuration acquisition, policy materialisation, matrix ordering, cardinality, and plan immutability.
13. Regression tests confirm existing frozen v0.1 execution-engine and approved research-generator/sweep contracts remain unchanged.

---

## Public API Review Decisions Deferred

Public API Review must decide, without weakening this specification:

- the exact names, module placement, constructors, exports, equality, and hash semantics of `ResearchPlan` and its planned-unit type;
- the exact policy-materialiser protocol and the component/API that builds a plan;
- whether `ResearchPlan` carries study metadata directly or references the immutable `ExperimentDefinition` as its source anchor;
- the exact engine-context translation mapping, including the existing engine `cohort` field representation;
- the exact immutable result/provenance wrapper returned by `ResearchExecutor`; and
- the error classes and public exception messages for invalid plans and execution failures.

The review must preserve these non-negotiable boundaries: planning is separate from execution; `ResearchExecutor` consumes but never constructs a plan; policy meaning stays outside the executor; and the executor performs no aggregation or optimisation.

---

## Approval Criteria

This specification is approved when it defines:

1. `ResearchPlan` as an immutable domain value object representing a fully materialised study;
2. construction of `ResearchPlan` as the exclusive responsibility of a dedicated planning component introduced later, establishing a frozen ownership boundary that prevents `ResearchExecutor` from building, modifying, or absorbing planning duties;
3. `ResearchExecutor` as a pure execution orchestrator accepting an already validated `ResearchPlan` without adding, removing, reordering, or materialising plan contents;
4. exactly one `SimulationExecutor` delegation per valid plan execution;
5. deterministic preservation of plan order and plan-unit provenance through engine results;
6. a strict prohibition on planning, plan construction, cohort/parameter generation, policy materialisation, financial logic, result aggregation, optimisation, and infrastructure concerns within `ResearchExecutor`; and
7. implementation feasibility without changing frozen v0.1 engine behaviour or approved research contracts.

Implementation may begin only after this behavioural specification and the subsequent Architecture Review and Public API Review have been explicitly approved.

---

## Workflow Status

| Step | Artifact | Status |
| :--- | :--- | :--- |
| 1. Behavioural Specification | `RESEARCH_EXECUTOR_SPECIFICATION.md` | **Approved and frozen** |
| 2. Architecture Review | `RESEARCH_EXECUTOR_ARCHITECTURE_REVIEW.md` | **Approved and frozen** |
| 3. Public API Review | `RESEARCH_EXECUTOR_PUBLIC_API.md` | **Approved and frozen** |
| 4. Implementation | Source and tests | Ready to begin |
