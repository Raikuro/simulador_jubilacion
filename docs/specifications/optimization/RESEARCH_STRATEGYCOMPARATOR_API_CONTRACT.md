# Public API Contract: StrategyComparator (v0.3)

## 1. Overview
The `StrategyComparator` exposes a clean, functional interface for strategy comparative analysis.

The component accepts either live strategy evaluators or precomputed evaluation result collections derived from the canonical `ExperimentRun` contract defined by the SimulationExecutor public API.

## 2. Core Interface
```python
from typing import Literal, Mapping, Protocol, Sequence, Union
from dataclasses import dataclass

class InvalidInputError(ValueError):
    """Raised when StrategyComparator input validation fails."""

class EvaluationError(Exception):
    """Raised when evaluation execution fails."""

@dataclass(frozen=True)
class EvaluationResult:
    """Evaluation result for a strategy label."""

    label: str
    metrics: Mapping[str, float]
    provenance: Mapping[str, Sequence[str]]

class Evaluator(Protocol):
    """Abstract evaluator to provide evaluation artifacts."""

    def get_evaluations(self, label: str) -> Sequence[EvaluationResult]: ...

@dataclass(frozen=True)
class RankingRule:
    """Deterministic ranking rule for strategies."""

    primary_metric: str
    tie_breakers: Sequence[str]

GroupingDimension = Literal["parameter_config", "cohort", "global"]
"""
Grouping dimension selection.
Allowed values: 'parameter_config', 'cohort', 'global'.
"""

StrategySource = Union[Sequence[EvaluationResult], Evaluator]
"""
The value associated with each strategy label.
Must be either a non-empty ordered collection of EvaluationResult values
or an Evaluator capable of producing them on demand.
"""

@dataclass(frozen=True)
class StrategyComparisonReport:
    """Immutable report containing aggregated metrics, ranking, provenance, and diagnostics."""

    aggregated_metrics: Mapping[str, Mapping[str, Mapping[str, float]]]
    ranking: Mapping[str, Sequence[str]]
    provenance: Mapping[str, Mapping[str, Sequence[str]]]
    diagnostics: Mapping[str, Mapping[str, str]]

class StrategyComparator:
    """
    Consumer component for comparative analytics.
    """

    def __init__(self, metrics: Sequence[str], ranking_rule: RankingRule):
        self._metrics = metrics
        self._ranking_rule = ranking_rule

    def compare(
        self,
        strategy_map: Mapping[str, StrategySource],
        group_by: GroupingDimension = "global",
    ) -> StrategyComparisonReport:
        """
        Produces a deterministic report from the provided strategies.

        Args:
            strategy_map: Mapping from strategy label to either a non-empty ordered
                collection of EvaluationResult values or an abstract Evaluator.
            group_by: Grouping dimension that controls output aggregation.

        Returns:
            StrategyComparisonReport: Immutable report containing grouped aggregated
                metrics, ranking, provenance, and diagnostics.

        Raises:
            InvalidInputError: If input validation fails, including invalid grouping.
            EvaluationError: If evaluation execution fails.
        """
        ...
```

## 3. Guarantees
- **Inmutability:** The input artifacts are never mutated. The output `StrategyComparisonReport` is strictly immutable.
- **Determinism:** The `compare` method is pure; same `strategy_map`, grouping selection, and ranking rule yield identical results.
- **Fail-Fast:** Invalid `strategy_map`, metrics, or grouping selection trigger immediate `InvalidInputError`.
- **Evaluation Errors:** Any evaluator failure is wrapped and propagated as `EvaluationError`.
- **Grouped Outputs:** `aggregated_metrics`, `ranking`, `provenance`, and `diagnostics` are keyed by canonical grouping keys.
EOF
