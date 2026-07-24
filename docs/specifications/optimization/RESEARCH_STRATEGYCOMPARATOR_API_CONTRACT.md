# Public API Contract: StrategyComparator (v0.3)

## 1. Overview
The `StrategyComparator` exposes a clean, functional interface for strategy comparative analysis.

## 2. Core Interface
```python
from typing import Mapping, Sequence, Protocol
from dataclasses import dataclass

class Evaluator(Protocol):
    """Abstract evaluator to provide evaluation artifacts."""
    def get_evaluation(self, label: str) -> EvaluationResult: ...

@dataclass(frozen=True)
class StrategyComparisonReport:
    """Immutable report containing aggregated metrics and ranking."""
    aggregated_metrics: Mapping[str, Mapping[str, float]]
    ranking: Sequence[str]
    provenance: Mapping[str, Sequence[str]]

class StrategyComparator:
    """
    Consumer component for comparative analytics.
    """
    def __init__(self, metrics: Sequence[str], ranking_rule: RankingRule):
        self._metrics = metrics
        self._ranking_rule = ranking_rule

    def compare(self, strategy_map: Mapping[str, Evaluator]) -> StrategyComparisonReport:
        """
        Produces a deterministic report from the provided strategies.
        """
        ...
```

## 3. Guarantees
- **Inmutability:** The input artifacts are never mutated. The output `StrategyComparisonReport` is strictly immutable.
- **Determinism:** The `compare` method is pure; same `strategy_map` and rules yield identical results.
- **Fail-Fast:** Invalid `strategy_map` or metrics trigger immediate `InvalidInputError`.
EOF
