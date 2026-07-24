# Architectural Review: `ResearchExecutor`

## Executive Summary

This document presents the formal architectural review for `ResearchExecutor`, the execution orchestration component of the Research Layer (`v0.2-research-layer`).

The review evaluates responsibility boundaries, ownership and lifecycle, dependency direction, contract relationships with `ResearchPlan` and `SimulationExecutor`, policy coupling justifications, execution translation mechanics, defensive validation boundaries, error transparency, concurrency boundaries, module placement, and future extensibility.

**Baseline:** Behavioural specification `RESEARCH_EXECUTOR_SPECIFICATION.md` is **approved and frozen**.

---

## 1. Responsibility Boundaries (Single Responsibility Principle)

`ResearchExecutor` adheres strictly to the Single Responsibility Principle as a pure execution orchestrator.

- **Primary Responsibility:** Translate one pre-validated, immutable `ResearchPlan` into engine execution requests, delegate execution exactly once to `SimulationExecutor`, and return the engine results with lossless, ordered plan-unit provenance.
- **Explicit Boundary Limits:**
  - It **consumes** an already constructed `ResearchPlan`; it does **not** construct, build, modify, add to, remove from, or reorder a plan.
  - It performs **no** planning, cohort generation, or parameter grid generation (`CohortGenerator` and `ParameterSweepEngine` are planning dependencies only).
  - It performs **no** policy materialisation or binding resolution (concrete policy pairs are already attached to planned units).
  - It performs **no** financial calculations, portfolio mutations, market evolutions, or monthly step processing (owned by frozen `v0.1` engine).
  - It performs **no** statistical aggregation, quantile calculation, ranking, or reporting (owned by `ResultAggregator` in `v0.2.3`).
  - It performs **no** file I/O, database persistence, network communication, or CLI formatting.

```text
┌──────────────────────────────────────────────────────────────┐
│                       ResearchExecutor                       │
│             (Pure Execution Orchestration Service)           │
│                                                              │
│  execute(plan: ResearchPlan) → ResearchExecutionResult        │
└──────────────┬────────────────────────────────┬──────────────┘
               │ Consumes                       │ Delegates (1x)
               ▼                                ▼
         ResearchPlan                  SimulationExecutor
   (Immutable Value Object)           (Frozen v0.1 Engine)
```

### Architectural Separation of Four Research Concerns

| Concern | Owner Component | Explicit Non-Owner |
| :--- | :--- | :--- |
| **Plan Construction** | Dedicated planning component | `ResearchExecutor`, `SimulationExecutor` |
| **Execution Orchestration** | `ResearchExecutor` | Dedicated planning component, `SimulationExecutor` |
| **Single Simulation Execution** | `SimulationExecutor` (frozen `v0.1`) | `ResearchExecutor`, Research Domain |
| **Statistical Aggregation** | `ResultAggregator` | `ResearchExecutor`, `SimulationExecutor` |

This four-way separation guarantees that `ResearchExecutor` remains a lean orchestrator with a single reason to change: changes in the execution delegation contract between research plans and the frozen `v0.1` engine.

---

## 2. Ownership & Lifecycle

- **Owner:** Research Application/Orchestration Layer (`research.orchestration` / `research.executor`).
- **Dependency Injection:** `ResearchExecutor` receives its mandatory `SimulationExecutor` collaborator via constructor injection. It never instantiates engine executors, runners, generators, or policy factories internally.
- **State & Lifespan:** `ResearchExecutor` is a stateless service. It maintains zero mutable state across execution calls.
- **Consumers:**
  - Higher-level study runners, CLI tools, or notebooks.
  - `SWROptimizer` / `StrategyComparator` (`v0.3` consumers) executing iterative study sweeps.
- **Lifecycle:** As a stateless service, `ResearchExecutor` has no internal lifecycle management, setup, or teardown phase.

```text
Research Layer Layering & Boundary Graph:

  Dedicated Planning Component  (produces immutable study plan)
               │
               ▼
          ResearchPlan         (Immutable Value Object — Boundary contract)
               │
               ▼
        ResearchExecutor       (Stateless Orchestrator — Injectable service)
               │
               ├──► SimulationExecutor (Frozen v0.1 engine contract)
               │         │
               │         └──► SimulationRunner -> Monthly Pipeline
               │
               ▼
    ResearchExecutionResult    (Lossless plan-unit to SimulationResult output)
```

---

## 3. Dependency Direction & System Isolation

`ResearchExecutor` strictly obeys unidirectional dependency rules:

```text
Application / Orchestration Layer
    ResearchExecutor ───┐
                        │ depends on
                        ▼
Research Domain Contract Layer
    ResearchPlan ◄──────┘
        │ contains
        └──► PlannedSimulationUnit
                 ├──► CohortSpecification
                 ├──► ParameterConfiguration
                 └──► AllocationPolicy / WithdrawalPolicy (Engine interfaces)

Execution Engine Layer (Frozen v0.1 Baseline)
    SimulationExecutor ◄─── injected into ResearchExecutor
    SimulationContext
    SimulationResult
```

### Architectural Dependency Invariants

1. **Zero Generator Dependencies:** `ResearchExecutor` has **zero imports or runtime calls** to `CohortGenerator` or `ParameterSweepEngine`.
2. **Zero Financial Domain Dependencies:** `ResearchExecutor` has **zero financial calculations** or portfolio manipulation logic.
3. **Engine Baseline Protection:** The frozen `v0.1` engine (`SimulationExecutor`, `SimulationRunner`, monthly pipeline) has **zero knowledge** of `ResearchExecutor` or `ResearchPlan`.
4. **Passive Domain Contracts:** `ResearchPlan` and `CohortSpecification` have **zero knowledge** of `ResearchExecutor`.

---

### 3.1 Architectural Justification for Policy Interfaces in `PlannedSimulationUnit`

The decision for `PlannedSimulationUnit` to hold concrete `AllocationPolicy` and `WithdrawalPolicy` instances (the engine's frozen policy contracts) alongside abstract `ParameterConfiguration` bindings is intentional and fundamental to the Research Layer layering:

1. **Self-Contained Executable Blueprint:** `ResearchPlan` serves as the formal boundary contract between planning and execution. By carrying already-materialised concrete policy instances, a `ResearchPlan` is a fully self-contained, executable blueprint requiring zero dynamic lookup during execution.
2. **Zero Policy-Construction Logic in `ResearchExecutor`:** If `ResearchPlan` contained only abstract `ParameterConfiguration` bindings, `ResearchExecutor` would be forced to resolve policy classes, invoke policy factories, or perform dynamic string reflection to instantiate policies. This would leak policy-materialisation responsibilities into the execution orchestrator.
3. **Dual Role of `PlannedSimulationUnit`:**
   - `parameter_config: ParameterConfiguration` retains the domain-agnostic scalar parameter bindings for scientific provenance, audit logging, grouping, and downstream analysis.
   - `allocation_policy: AllocationPolicy`, `withdrawal_policy: WithdrawalPolicy`, and `initial_portfolio: Portfolio` provide the exact executable objects passed directly into `SimulationContext` during plan-to-engine translation.
4. **Ownership Boundary Preserved:** The dedicated planning component owns the policy materialisation phase (translating `ParameterConfiguration` → policy instances) and initial-portfolio materialisation *prior* to constructing `ResearchPlan`. `ResearchExecutor` simply passes these already-built objects to `SimulationContext` without inspecting or interpreting their internal financial rules, and never invents an initial portfolio.

---

## 4. Translation & Execution Provenance

`ResearchExecutor` translates a `ResearchPlan` into engine execution through a strict 4-step pipeline:

```text
1. Defensively validate ResearchPlan intrinsic structural invariants
                         │
                         ▼
2. Map each PlannedSimulationUnit → frozen SimulationContext (in exact plan order)
                         │
                         ▼
3. Call SimulationExecutor.execute(...) exactly ONCE with ordered contexts
                         │
                         ▼
4. Package returned SimulationResult tuple with original plan-unit provenance
```

### Scope of Defensive Validation

`ResearchExecutor` performs defensive structural validation at its boundary, but its scope is strictly bounded:

- **What `ResearchExecutor` validates (Intrinsic Structural Invariants):**
  - The plan object is non-null and conforms to the `ResearchPlan` structural contract.
  - The plan contains a positive, non-empty tuple of `PlannedSimulationUnit` objects.
  - Planned unit identities are non-duplicate, non-null, and unambiguous.
  - Each planned unit contains complete policy references suitable for constructing an engine `SimulationContext`.
- **What `ResearchExecutor` NEVER validates (Planning Invariants):**
  - It does **not** recompute or verify cohort feasibility against historical market datasets (owned by `CohortGenerator`).
  - It does **not** re-evaluate parameter axis range boundaries or cartesian product completeness (owned by `ParameterSweepEngine`).
  - It does **not** inspect or evaluate policy financial logic or parameter soundness (owned by policy materialiser / planning component).
  - It does **not** verify dataset snapshot depth or market coverage.

By restricting defensive validation exclusively to intrinsic structural completeness, `ResearchExecutor` avoids duplicating planning logic or leaking planning concerns into the execution layer.

### Determinism & Provenance Invariants

- **Exact Order Preservation:** Planned units are translated and passed to `SimulationExecutor` in their exact index order $0, 1, \dots, N-1$.
- **Lossless Association:** The output associates `ResearchPlan.units[i]` directly with `SimulationResult[i]`.
- **Pure Output:** Engine outputs are returned unmodified without calculating summary statistics, failure rates, or quantiles.

---

## 5. Failure Transparency & Exception Boundaries

- **Fail-Fast Validation:** Pre-execution structural checks occur before `SimulationExecutor` is called. Malformed plans or missing collaborators fail immediately.
- **Collaborator Failure Propagation:** Any exception raised by `SimulationExecutor` during execution is allowed to propagate cleanly (or wrapped in a dedicated execution error preserving the original cause). No partial or empty outputs are fabricated.
- **Modelled Depletion:** A simulation ending in zero wealth or early depletion yields a valid `SimulationResult` object from `v0.1`. `ResearchExecutor` treats this as a valid execution output and preserves it in the result association.

---

## 6. Concurrency Boundary & Parallelisation Architecture

- **Strict Single-Threaded Core:** `ResearchExecutor` is explicitly designed as a deterministic, single-threaded execution orchestrator. Multi-threading, async tasks, process spawning, or internal worker pool orchestration are **strictly prohibited** inside `ResearchExecutor`.
- **Architectural Concurrency Boundary:** Parallel execution is intentionally placed **outside** the responsibility of `ResearchExecutor`.
- **Partitioning Above the Execution Layer:** Future parallelisation, multi-core scaling, or distributed cluster execution (e.g. via Celery, Ray, or Python `multiprocessing`) must be achieved by **partitioning `ResearchPlan` instances above this layer**.
  - A higher-level distributed runner or optimization loop (e.g. `SWROptimizer`) splits a large study matrix into multiple smaller, independent `ResearchPlan` sub-plans.
  - Each sub-plan is passed to a separate, independent `ResearchExecutor` instance running in its own process or worker node.
- **Benefits:** This architecture keeps `ResearchExecutor` completely thread-agnostic, strictly deterministic, easy to test, and free of race conditions or concurrency management overhead.

---

## 7. Recommended Module Placement

```text
src/
└── research/
    ├── domain/
    │   ├── plan.py                  # ResearchPlan & PlannedSimulationUnit value objects
    │   ├── cohort.py                # CohortSpecification & CohortGenerator
    │   ├── experiment.py            # ExperimentDefinition
    │   └── parameter.py             # ParameterConfiguration, ParameterAxis, ParameterSweepEngine
    └── orchestration/               # (or research/executor.py)
        └── executor.py              # ResearchExecutor service implementation
```

---

## 8. Architectural Verdict & Status

**Status:** **APPROVED AND FROZEN**

1. **SRP Compliance:** Single responsibility of executing an immutable `ResearchPlan`.
2. **Frozen Boundary Integrity:** Permanently isolated from `v0.1` engine internals and planning-time generators.
3. **Explicit Policy Coupling:** Concrete policy interfaces in `PlannedSimulationUnit` keep `ResearchExecutor` free of policy factories.
4. **Bounded Defensive Validation:** Validates intrinsic structural invariants only; planning invariants remain strictly with the planning component.
5. **Frozen Concurrency Boundary:** Single-threaded core; parallelisation is achieved exclusively via `ResearchPlan` partitioning above `ResearchExecutor`.
6. **Immutability & Determinism:** Preserves plan immutability and exact output ordering.

Next Step: **Public API Review (`RESEARCH_EXECUTOR_PUBLIC_API.md`)**.
