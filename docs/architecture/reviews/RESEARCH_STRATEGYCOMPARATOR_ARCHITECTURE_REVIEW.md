# Architecture Review: StrategyComparator (v0.3)

Status: Approved & Frozen
The `StrategyComparator` is designed as a pure analytical consumer component in the v0.3 optimization layer. Its primary goal is to provide deterministic, comparable statistical output from labelled strategy evaluation artifacts.

## 2. Architectural Design Principles
- **Separation of Concerns:** The comparator strictly performs grouping, reduction, and ranking. It remains decoupled from data persistence, visualization, and execution orchestration.
- **Determinism:** All aggregation and ranking operations are pure functions of the input artifacts.
- **Extensibility:** The component consumes abstract evaluation artifacts, adhering to the Open/Closed principle by allowing future evaluation strategies to be added without modifying the comparator core.

## 3. Dependency Analysis
- **Upstream:** `ResultAggregator`, `ExperimentRun`.
- **Downstream:** Visualization components (external to the research library).
- **Invariants:** The comparator operates on immutable `StrategyComparisonReport`.

## 4. Architectural Self-Review
- **API Quality:** The API is structured around explicit grouping and ranking rules, ensuring high usability for research scripts.
- **Naming:** Follows the established domain language.
- **Separation of Concerns:** Rigidly adheres to pure analytical logic.
- **Determinism:** Guaranteed by the immutable, artifact-driven design.
- **Extensibility:** Supports new metric types through abstract mapping.
- **Failure Semantics:** Explicit error handling via `InvalidInputError` and `EvaluationError`.
- **Testability:** High, as the pure functional design allows for deterministic testing via fixtures.

## 5. Decision
The architecture is APPROVED and FROZEN for implementation.
