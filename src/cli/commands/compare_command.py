"""CompareCommand — compare multiple allocation strategies side-by-side."""

from __future__ import annotations

import argparse
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Sequence

import yaml

from cli.builders import (
    build_cohort_specs,
    build_parameter_configs,
    build_research_plan,
    load_yaml,
    resolve_dataset,
)
from cli.commands.base import BaseCommand, ExecutionContext
from cli.error_handling import ExitCode
from cli.policies import ConstantAllocationPolicy, ConstantWithdrawalPolicy
from engine.domain.model.money import Currency, Money
from engine.domain.policies.allocation_policy import AllocationPolicy
from engine.domain.optimizer.strategy_comparator import StrategyComparator
from engine.domain.optimizer.types import (
    EvaluationResult,
    GroupingDimension,
    RankingRule,
    StrategyComparisonReport,
)
from infrastructure.persistence.context import create_persistence_context
from infrastructure.persistence.sqlite_repository import (
    ExperimentIdentity,
    SQLiteRepository,
)
from research.domain.experiment.definition import ExperimentDefinition
from research.domain.parameter.configuration import ParameterConfiguration
from research.domain.plan import ResearchPlan
from research.orchestration.result import ResearchExecutionResult

_DEFAULT_DB_PATH = "~/.sim-retire/studies.db"


def _canonical_param_key(config: ParameterConfiguration) -> str:
    return ";".join(f"{name}={value}" for name, value in config.items())


def _extract_evaluation_results(
    label: str,
    plan: ResearchPlan,
    result: ResearchExecutionResult,
) -> Sequence[EvaluationResult]:
    evaluations: list[EvaluationResult] = []
    for i, (unit, sim_result) in enumerate(zip(plan.units, result.results)):
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
                    "parameter_config": [_canonical_param_key(unit.parameter_config)],
                },
            )
        )
    return evaluations


def _select_allocation_policy(
    policies_data: list[dict[str, Any]], policy_name: str
) -> AllocationPolicy:
    for entry in policies_data:
        if entry.get("name") == policy_name:
            ratio = Decimal(str(entry.get("equity_ratio", "0.75")))
            return ConstantAllocationPolicy(equity_allocation=ratio)
    raise ValueError(f"Allocation policy '{policy_name}' not found in YAML")


def _select_withdrawal_policy(
    policies_data: list[dict[str, Any]], policy_name: str | None
) -> ConstantWithdrawalPolicy:
    target = policy_name
    for entry in policies_data:
        if target is None or entry.get("name") == target:
            rate = Decimal(str(entry.get("withdrawal_rate", "0.04")))
            return ConstantWithdrawalPolicy(withdrawal_rate=rate)
    raise ValueError(
        f"Withdrawal policy '{policy_name}' not found in YAML"
        if policy_name
        else "No withdrawal policies defined in YAML"
    )


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
    if key == "success_rate":
        return "Success Rate"
    elif key == "final_wealth":
        return "Mean Final Wealth"
    elif key == "max_drawdown":
        return "Max Drawdown"
    return key


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
            required=True,
            dest="strategies",
            help="Name of allocation policy from YAML (repeatable, min 2)",
        )
        parser.add_argument(
            "--withdrawal-policy",
            type=str,
            default=None,
            help="Name of withdrawal policy from YAML (default: first withdrawal policy)",
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
        if len(args.strategies) < 2:
            print("ERROR: At least two strategies required for comparison", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

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

        study_name = data.get("metadata", {}).get("name", "Comparison")
        dataset_info: dict[str, Any] = data.get("dataset", {})
        cohorts_info: dict[str, Any] = data.get("cohorts", {})
        params_data: dict[str, Any] = data.get("parameters", {})
        alloc_policies_data: list[Any] = data.get("allocation_policies", [])
        withdrawal_policies_data: list[Any] = data.get("withdrawal_policies", [])

        dataset_id: str = dataset_info.get("identifier", "")
        window_years = cohorts_info.get("window_years", 30)
        if not isinstance(window_years, int) or window_years <= 0:
            print("ERROR: window_years must be a positive integer", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR
        horizon_months = window_years * 12

        try:
            dataset = resolve_dataset(dataset_id, context.data_dir)
        except Exception as exc:
            print(f"ERROR: Cannot resolve dataset: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        try:
            cohorts = build_cohort_specs(dataset, horizon_months)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Cohort generation failed: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        try:
            param_configs = build_parameter_configs(params_data)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Invalid parameters: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        try:
            withdrawal_policy = _select_withdrawal_policy(
                withdrawal_policies_data, args.withdrawal_policy
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        selected_policies: dict[str, AllocationPolicy] = {}
        for strategy_name in args.strategies:
            try:
                selected_policies[strategy_name] = _select_allocation_policy(
                    alloc_policies_data, strategy_name
                )
            except ValueError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return ExitCode.VALIDATION_ERROR

        print("\u2501" * 47)
        print("Strategy Comparison Complete")
        print("\u2501" * 47)
        print(f"Study:               {study_path}")
        print(f"Strategies:          {len(args.strategies)} ({', '.join(args.strategies)})")
        withdrawal_rate_val = getattr(withdrawal_policy, "withdrawal_rate", Decimal("0"))
        print(f"Withdrawal Policy:   Fixed {float(withdrawal_rate_val) * 100:.0f}%")
        print(f"Group By:            {args.group_by}")
        print(f"Workers:             {workers}")
        print()

        strategy_results: dict[str, Sequence[EvaluationResult]] = {}
        strategy_execution_info: dict[str, float] = {}
        execution_failures: list[str] = []

        for strategy_name in args.strategies:
            policy = selected_policies[strategy_name]

            experiment_def = ExperimentDefinition(
                name=f"{study_name} - {strategy_name}",
                description=f"Comparison strategy: {strategy_name}",
                dataset=dataset,
                horizon_months=horizon_months,
                initial_wealth=capital,
                cohorts=cohorts,
                allocation_policies=(policy,),
                withdrawal_policies=(withdrawal_policy,),
            )

            plan = build_research_plan(
                experiment_def,
                cohorts,
                param_configs,
                policy,
                withdrawal_policy,
            )

            start_time = time.perf_counter()

            try:
                if workers == 1:
                    from infrastructure.execution.parallel_executor import (
                        sequential_execute,
                    )

                    result = sequential_execute(plan)
                else:
                    from infrastructure.execution.parallel_executor import (
                        parallel_execute,
                    )

                    result = parallel_execute(plan, max_workers=workers)
            except Exception as exc:
                elapsed = time.perf_counter() - start_time
                print(
                    f"ERROR: Strategy '{strategy_name}' failed after {_format_duration(elapsed)}: {exc}",
                    file=sys.stderr,
                )
                execution_failures.append(strategy_name)
                continue

            elapsed = time.perf_counter() - start_time
            strategy_execution_info[strategy_name] = elapsed

            evaluations = _extract_evaluation_results(strategy_name, plan, result)
            strategy_results[strategy_name] = evaluations

            try:
                db_path = str(Path(_DEFAULT_DB_PATH).expanduser())
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                repo = SQLiteRepository(db_path)
                persistence_context = create_persistence_context(context.data_dir)

                identity = ExperimentIdentity(
                    name=f"{study_name} - {strategy_name}",
                    revision="1.0",
                )

                experiment_id = repo.save_experiment(identity, experiment_def, persistence_context)
                plan_id = repo.save_plan(plan, experiment_id, persistence_context)
                repo.save_execution_result(plan_id, result, persistence_context, elapsed)
            except Exception as exc:
                print(
                    f"WARNING: Persistence failed for strategy '{strategy_name}': {exc}",
                    file=sys.stderr,
                )

        if len(strategy_results) < 2:
            print("ERROR: Fewer than 2 strategies completed", file=sys.stderr)
            return ExitCode.ERROR

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
