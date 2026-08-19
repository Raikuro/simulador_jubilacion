"""CompareCommand — compare generated parameter configurations side-by-side.

The study's parameter configurations are the comparison strategies: one
``sim-retire run`` plan already carries every configuration, so ``compare``
executes the single plan once and partitions the results by configuration.
``--strategy name=value`` selects a subset of configurations (all of them when
the flag is absent).  The withdrawal policy comes from the normalized study
configuration; there is no policy-name selection.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml

from cli.builders import StudyConfiguration, build_study_plan, load_yaml
from cli.commands.base import BaseCommand, ExecutionContext
from cli.error_handling import ExitCode
from engine.domain.model.money import Currency, Money
from engine.domain.optimizer.strategy_comparator import StrategyComparator
from engine.domain.optimizer.types import (
    EvaluationResult,
    GroupingDimension,
    RankingRule,
    StrategyComparisonReport,
)
from infrastructure.persistence.context import create_persistence_context
from infrastructure.persistence.errors import DuplicateStudyError, RepositoryError
from infrastructure.persistence.sqlite_repository import (
    ExperimentIdentity,
    SQLiteRepository,
)
from research.domain.plan import ResearchPlan
from research.orchestration.result import ResearchExecutionResult

_DEFAULT_DB_PATH = "~/.sim-retire/studies.db"


def _canonical_param_key(config: Any) -> str:
    return ";".join(f"{name}={value}" for name, value in config.items())


def _withdrawal_policy_label(policy_type: str) -> str:
    """Human-readable withdrawal-policy label for the comparison header."""
    return {
        "ConstantWithdrawalPolicy": "Constant",
        "FixedRealWithdrawalPolicy": "Fixed Real",
    }.get(policy_type, policy_type)


def _parse_strategy_filter(value: str) -> tuple[str, Any]:
    """Parse a ``name=value`` strategy selector into a configuration constraint."""
    name, sep, raw = value.partition("=")
    if not sep or not name.strip() or not raw:
        raise ValueError(
            f"--strategy must be 'name=value', got {value!r}"
        )
    name = name.strip()
    parsed: Any
    try:
        parsed = float(raw)
    except ValueError:
        parsed = raw
    return name, parsed


def _config_matches(
    config: Any, constraints: Sequence[tuple[str, Any]]
) -> bool:
    """True when *config* satisfies every ``(name, value)`` constraint."""
    return all(config.get(name) == value for name, value in constraints)


def _extract_evaluation_results(
    label: str,
    plan: ResearchPlan,
    result: ResearchExecutionResult,
    configs_by_key: dict[str, Any],
) -> list[EvaluationResult]:
    evaluations: list[EvaluationResult] = []
    for unit, sim_result in zip(plan.units, result.results, strict=True):
        key = _canonical_param_key(unit.parameter_config)
        if key not in configs_by_key:
            continue
        success_val = Decimal("1") if sim_result.statistics.success else Decimal("0")
        evaluations.append(
            EvaluationResult(
                label=label,
                metrics={
                    "success_rate": success_val,
                    "final_wealth": sim_result.statistics.final_wealth.amount,
                    "max_drawdown": Decimal(str(sim_result.statistics.max_drawdown)),
                },
                provenance={
                    "cohort": [unit.cohort.id or unit.cohort.start_date.isoformat()],
                    "parameter_config": [key],
                },
            )
        )
    return evaluations


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {secs}s"


def _format_metric(key: str, value: Decimal) -> str:
    if key == "success_rate":
        return f"{float(value) * 100:.1f}%"
    elif key == "final_wealth":
        return f"\u20ac{float(value):,.0f}"
    elif key == "max_drawdown":
        display = -abs(float(value))
        return f"{display * 100:.1f}%"
    return f"{value}"


def _format_metric_header(key: str) -> str:
    headers = {
        "success_rate": "Success Rate",
        "final_wealth": "Mean Final Wealth",
        "max_drawdown": "Max Drawdown",
    }
    return headers.get(key, key)


def _print_report(report: StrategyComparisonReport) -> None:
    for gkey in report.ranking:
        print(f"Group: {gkey}")
        eval_count: str | None = None
        for diag_key, diag_val in report.diagnostics.get(gkey, {}).items():
            if diag_key.endswith(":count"):
                eval_count = diag_val
                break
        if eval_count is not None:
            print(f"Total Evaluations Per Strategy: {eval_count}")
        print()

        ranked_labels = report.ranking[gkey]
        metrics_in_order = ["success_rate", "final_wealth", "max_drawdown"]

        headers = ["Rank", "Strategy"] + [_format_metric_header(m) for m in metrics_in_order]
        print(" \u2502 ".join(headers))

        sep_parts = []
        for w in [6, 13, 14, 19, 13]:
            sep_parts.append("\u2500" * w)
        print("\u253c".join(sep_parts))

        for rank, label in enumerate(ranked_labels, start=1):
            metrics_data = report.aggregated_metrics[gkey].get(label, {})
            row = [
                f"{rank:>2} ",
                label.ljust(11),
            ]
            for m in metrics_in_order:
                val = metrics_data.get(m, Decimal("0"))
                row.append(_format_metric(m, val).rjust(13))
            print(" \u2502 ".join(row))
        print()

    print("Diagnostics:")
    for gkey in report.ranking:
        for diag_key, diag_val in report.diagnostics.get(gkey, {}).items():
            print(f"  {diag_key}: {diag_val}")


class CompareCommand(BaseCommand):
    name = "compare"
    help_text = "Compare multiple allocation strategies side-by-side"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("study_file", type=str, help="Path to YAML experiment definition")
        parser.add_argument(
            "--strategy",
            type=str,
            action="append",
            dest="strategies",
            help="Configuration filter as 'name=value' (repeatable, AND-ed; "
            "default: all generated configurations)",
        )
        parser.add_argument(
            "--group-by",
            choices=["global", "cohort", "parameter_config"],
            default="global",
            help="Grouping dimension for strategy comparison",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=1,
            help="Number of parallel workers",
        )
        parser.add_argument(
            "--initial-capital",
            type=str,
            default="1000000",
            help="Starting portfolio value in EUR",
        )

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        try:
            initial_capital = Decimal(str(args.initial_capital))
        except (InvalidOperation, ValueError):
            print(
                f"ERROR: --initial-capital must be a valid number, got '{args.initial_capital}'",
                file=sys.stderr,
            )
            return ExitCode.VALIDATION_ERROR

        capital = Money(initial_capital, Currency.EUR)
        workers = max(args.workers, 1)

        constraints: list[tuple[str, Any]] = []
        for raw in args.strategies or []:
            try:
                constraints.append(_parse_strategy_filter(raw))
            except ValueError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return ExitCode.VALIDATION_ERROR

        study_path = Path(args.study_file)
        try:
            data = load_yaml(study_path)
        except FileNotFoundError:
            print("ERROR: Study file not found", file=sys.stderr)
            print(f"File: {study_path}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR
        except yaml.YAMLError as exc:
            print("ERROR: Invalid YAML in study file", file=sys.stderr)
            print(f"File: {study_path}", file=sys.stderr)
            if hasattr(exc, "problem_mark") and exc.problem_mark is not None:
                print(f"Line: {exc.problem_mark.line + 1}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        try:
            study_config = StudyConfiguration.from_yaml(data)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Invalid study configuration: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        try:
            built = build_study_plan(study_config, context.data_dir, capital)
        except (ValueError, TypeError, RepositoryError) as exc:
            print(f"ERROR: Cannot build study plan: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        plan = built.plan
        experiment_def = built.experiment_definition

        configs_by_key: dict[str, Any] = {}
        for param_config in built.param_configs:
            key = _canonical_param_key(param_config)
            if _config_matches(param_config, constraints):
                configs_by_key[key] = param_config

        if len(configs_by_key) < 2:
            print(
                "ERROR: At least two configurations are required for comparison; "
                "declare a parameter axis (or widen --strategy filters)",
                file=sys.stderr,
            )
            return ExitCode.VALIDATION_ERROR

        withdrawal_rate_val = getattr(
            built.base_withdrawal_policy, "withdrawal_rate", Decimal("0")
        )
        withdrawal_label = _withdrawal_policy_label(study_config.withdrawal_policy_type)

        print("\u2501" * 47)
        print("Strategy Comparison Complete")
        print("\u2501" * 47)
        print(f"Study:               {study_path}")
        print(f"Strategies:          {len(configs_by_key)} (generated parameter configurations)")
        print(f"Withdrawal Policy:   {withdrawal_label} {float(withdrawal_rate_val) * 100:.0f}%")
        print(f"Group By:            {args.group_by}")
        print(f"Workers:             {workers}")
        print()

        start_time = time.perf_counter()
        try:
            if workers == 1:
                from infrastructure.execution.parallel_executor import sequential_execute

                result = sequential_execute(plan)
            else:
                from infrastructure.execution.parallel_executor import parallel_execute

                result = parallel_execute(plan, max_workers=workers)
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            print(
                f"ERROR: Execution failed after {_format_duration(elapsed)}: {exc}",
                file=sys.stderr,
            )
            return ExitCode.ERROR

        elapsed = time.perf_counter() - start_time

        strategy_results: dict[str, Sequence[EvaluationResult]] = {}
        for key in configs_by_key:
            strategy_results[key] = _extract_evaluation_results(
                key, plan, result, configs_by_key
            )

        try:
            db_path = str(Path(_DEFAULT_DB_PATH).expanduser())
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            repo = SQLiteRepository(db_path)
            persistence_context = create_persistence_context(context.data_dir)

            identity = ExperimentIdentity(
                name=experiment_def.name,
                revision=study_config.version or "1.0",
            )

            experiment_id = repo.save_experiment(identity, experiment_def, persistence_context)
            plan_id = repo.save_plan(plan, experiment_id, persistence_context)
            repo.save_execution_result(plan_id, result, persistence_context, elapsed)
        except DuplicateStudyError:
            print(
                "NOTE: Experiment already exists with this name/revision; "
                "results were not persisted (existing study retained).",
                file=sys.stderr,
            )
        except Exception as exc:
            print(
                f"WARNING: Persistence failed (execution completed): {exc}",
                file=sys.stderr,
            )

        metrics = ["success_rate", "final_wealth", "max_drawdown"]
        ranking_rule = RankingRule(
            primary_metric="success_rate",
            tie_breakers=["final_wealth"],
        )

        comparator = StrategyComparator(metrics=metrics, ranking_rule=ranking_rule)

        group_by: GroupingDimension = args.group_by
        report = comparator.compare(strategy_results, group_by=group_by)

        _print_report(report)

        return ExitCode.SUCCESS
