"""OptimizeCommand — find optimal withdrawal rate using SWROptimizer.

Contains the private _SWREvaluator that bridges the SWROptimizer protocol
to the simulation execution engine, and the OptimizeCommand itself.
"""

from __future__ import annotations

import argparse
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

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
from infrastructure.persistence.context import create_persistence_context
from infrastructure.persistence.sqlite_repository import (
    ExperimentIdentity,
    SQLiteRepository,
)
from research.domain.experiment.definition import ExperimentDefinition
from research.optimization.swr_optimizer import (
    EvaluationOutcome,
    OptimizerOutcome,
    SWROptimizer,
)

_DEFAULT_DB_PATH = "~/.sim-retire/studies.db"
_DOMAIN_MIN = Decimal("0.0")
_DOMAIN_MAX = Decimal("0.10")


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


def _select_allocation_policy(
    policies_data: list[dict[str, Any]], policy_name: str
) -> AllocationPolicy:
    for entry in policies_data:
        if entry.get("name") == policy_name:
            ratio = Decimal(str(entry.get("equity_ratio", "0.75")))
            return ConstantAllocationPolicy(equity_allocation=ratio)
    raise ValueError(f"Allocation policy '{policy_name}' not found in YAML")


class _SWREvaluator:
    """Evaluator adapter: bridges SWROptimizer binary search to simulation execution.

    Implements the SWROptimizer.Evaluator protocol:
        evaluate(candidate: Decimal) -> EvaluationOutcome
    """

    def __init__(
        self,
        dataset: Any,
        horizon_months: int,
        cohorts: tuple[Any, ...],
        param_configs: tuple[Any, ...],
        allocation_policy: AllocationPolicy,
        capital: Money,
        target_success_rate: Decimal,
        workers: int,
    ) -> None:
        self._dataset = dataset
        self._horizon_months = horizon_months
        self._cohorts = cohorts
        self._param_configs = param_configs
        self._allocation_policy = allocation_policy
        self._capital = capital
        self._target = target_success_rate
        self._workers = workers
        self._iteration = 0

    def evaluate(self, candidate: Decimal) -> EvaluationOutcome:
        self._iteration += 1

        withdrawal_policy = ConstantWithdrawalPolicy(withdrawal_rate=candidate)

        experiment_def = ExperimentDefinition(
            name="SWROptimization",
            description=f"SWR optimization at candidate {candidate}",
            dataset=self._dataset,
            horizon_months=self._horizon_months,
            initial_wealth=self._capital,
            cohorts=self._cohorts,
            allocation_policies=(self._allocation_policy,),
            withdrawal_policies=(withdrawal_policy,),
        )

        plan = build_research_plan(
            experiment_def,
            self._cohorts,
            self._param_configs,
            self._allocation_policy,
            withdrawal_policy,
        )

        if self._workers == 1:
            from infrastructure.execution.parallel_executor import sequential_execute

            result = sequential_execute(plan)
        else:
            from infrastructure.execution.parallel_executor import parallel_execute

            result = parallel_execute(plan, max_workers=self._workers)

        sim_results = result.results
        success_count = sum(1 for r in sim_results if r.statistics.success)
        total = len(sim_results)
        success_rate = Decimal(success_count) / Decimal(total) if total > 0 else Decimal("0")

        # Print iteration progress
        direction = (
            "Low — increasing rate" if success_rate >= self._target else "High — decreasing rate"
        )
        print(f"Iteration {self._iteration}: Testing {float(candidate):.4f} withdrawal rate")
        print(
            f"  Cohorts: {total} | Success Rate: "
            f"{float(success_rate * 100):.1f}% ({success_count}/{total})"
        )
        print(f"  → {direction}")
        print()

        return EvaluationOutcome(
            success=success_rate >= self._target,
            provenance={
                "candidate": str(candidate),
                "success_rate": str(success_rate),
                "success_count": success_count,
                "total_units": total,
            },
        )


class OptimizeCommand(BaseCommand):
    name = "optimize"
    help_text = "Find optimal withdrawal rate using SWROptimizer"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("study_file", type=str, help="Path to YAML experiment definition")
        parser.add_argument(
            "--target-success-rate",
            type=float,
            default=0.95,
            help="Target success rate (0.0-1.0)",
        )
        parser.add_argument(
            "--initial-capital",
            type=str,
            default="1000000",
            help="Starting portfolio value in EUR",
        )
        parser.add_argument(
            "--allocation-policy",
            type=str,
            required=True,
            help="Name of the allocation policy to optimize (must match YAML policy name)",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=1,
            help="Number of parallel workers",
        )
        parser.add_argument(
            "--tolerance",
            type=str,
            default="0.001",
            help="Withdrawal rate precision for binary search",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="./results/",
            help="Output directory",
        )

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        # --- 0. Validate --target-success-rate range -------------------------
        target_success_rate = args.target_success_rate
        if target_success_rate < 0.0 or target_success_rate > 1.0:
            print(
                f"ERROR: --target-success-rate must be between 0.0 and 1.0, "
                f"got {target_success_rate}",
                file=sys.stderr,
            )
            return ExitCode.VALIDATION_ERROR

        # Parse Decimal arguments
        try:
            initial_capital = Decimal(str(args.initial_capital))
        except (InvalidOperation, ValueError):
            print(
                f"ERROR: --initial-capital must be a valid number, got '{args.initial_capital}'",
                file=sys.stderr,
            )
            return ExitCode.VALIDATION_ERROR

        try:
            tolerance = Decimal(str(args.tolerance))
        except (InvalidOperation, ValueError):
            print(
                f"ERROR: --tolerance must be a valid number, got '{args.tolerance}'",
                file=sys.stderr,
            )
            return ExitCode.VALIDATION_ERROR

        capital = Money(initial_capital, Currency.EUR)

        policy_name = args.allocation_policy
        workers = max(args.workers, 1)

        # --- 1. Parse and validate YAML --------------------------------------
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

        # --- 2. Extract metadata from YAML -----------------------------------
        dataset_info: dict[str, Any] = data.get("dataset", {})
        cohorts_info: dict[str, Any] = data.get("cohorts", {})
        params_data: dict[str, Any] = data.get("parameters", {})
        alloc_policies_data: list[Any] = data.get("allocation_policies", [])

        dataset_id: str = dataset_info.get("identifier", "")

        window_years = cohorts_info.get("window_years", 30)
        if not isinstance(window_years, int) or window_years <= 0:
            print("ERROR: window_years must be a positive integer", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR
        horizon_months = window_years * 12

        # --- 3. Resolve dataset ----------------------------------------------
        try:
            dataset = resolve_dataset(dataset_id, context.data_dir)
        except Exception as exc:
            print(f"ERROR: Cannot resolve dataset: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        # --- 4. Build cohorts ------------------------------------------------
        try:
            cohorts = build_cohort_specs(dataset, horizon_months)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Cohort generation failed: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        # --- 5. Build parameter configs --------------------------------------
        try:
            param_configs = build_parameter_configs(params_data)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Invalid parameters: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        # --- 6. Select allocation policy -------------------------------------
        try:
            allocation_policy = _select_allocation_policy(alloc_policies_data, policy_name)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        # --- 7. Build evaluator ----------------------------------------------
        evaluator = _SWREvaluator(
            dataset=dataset,
            horizon_months=horizon_months,
            cohorts=cohorts,
            param_configs=param_configs,
            allocation_policy=allocation_policy,
            capital=capital,
            target_success_rate=Decimal(str(target_success_rate)),
            workers=workers,
        )

        # Print optimization header
        print("=" * 50)
        print("Optimization Started")
        print("=" * 50)
        print(f"Study: {study_path}")
        print(f"Allocation Policy: {policy_name}")
        print(f"Target Success Rate: {target_success_rate:.1%}")
        print(f"Capital: {capital.amount:,.0f} {capital.currency.value}")
        print(f"Workers: {workers}")
        print(f"Tolerance: {tolerance}")
        print()

        # --- 8. Run optimizer ------------------------------------------------
        optimizer = SWROptimizer()
        start_time = time.perf_counter()

        try:
            outcome: OptimizerOutcome = optimizer.optimize(
                evaluator=evaluator,
                domain_min=_DOMAIN_MIN,
                domain_max=_DOMAIN_MAX,
                precision=tolerance,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            print(
                f"ERROR: Optimization failed after {_format_duration(elapsed)}: {exc}",
                file=sys.stderr,
            )
            return ExitCode.ERROR

        elapsed = time.perf_counter() - start_time

        # --- 9. Print summary ------------------------------------------------
        print("\u2501" * 47)
        print("Optimization Complete")
        print("\u2501" * 47)

        if outcome.candidate_value is not None:
            optimal_rate = outcome.candidate_value
            print(
                f"Optimal Withdrawal Rate:   {float(optimal_rate) * 100:.2f}% "
                f"\u00b1 {float(tolerance) * 100:.1f}%"
            )
            success_rate_val = outcome.provenance.get("success_rate", "N/A")
            print(f"Success Rate Achieved:     {float(Decimal(str(success_rate_val))) * 100:.1f}%")
        else:
            print("No withdrawal rate satisfies criteria")
            print(f"Diagnostic: {outcome.diagnostic}")

        equity_ratio = getattr(allocation_policy, "equity_allocation", "N/A")
        print(
            f"Policy:                    ConstantAllocationPolicy(equity_ratio={equity_ratio})"
        )
        print(f"Target Success Rate:       {target_success_rate:.1%}")
        print(f"Iterations Required:       {evaluator._iteration}")
        print(f"Execution Time:            {_format_duration(elapsed)}")
        print()

        # --- 10. Persist results ---------------------------------------------
        if outcome.candidate_value is not None:
            try:
                db_path = str(Path(_DEFAULT_DB_PATH).expanduser())
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                repo = SQLiteRepository(db_path)
                persistence_context = create_persistence_context(context.data_dir)

                name = data.get("metadata", {}).get("name", "SWROptimization")
                version_val = data.get("metadata", {}).get("version", "1.0")
                identity = ExperimentIdentity(name=name, revision=version_val)

                # Build the experiment definition for the optimal run
                optimal_withdrawal = ConstantWithdrawalPolicy(
                    withdrawal_rate=outcome.candidate_value
                )
                optimal_experiment_def = ExperimentDefinition(
                    name=name,
                    description=f"Optimal SWR: {outcome.candidate_value}",
                    dataset=dataset,
                    horizon_months=horizon_months,
                    initial_wealth=capital,
                    cohorts=cohorts,
                    allocation_policies=(allocation_policy,),
                    withdrawal_policies=(optimal_withdrawal,),
                )

                experiment_id = repo.save_experiment(
                    identity, optimal_experiment_def, persistence_context
                )
                print(f"Study ID:                  {experiment_id}")
                print()

                # Build and persist optimal plan
                optimal_plan = build_research_plan(
                    optimal_experiment_def,
                    cohorts,
                    param_configs,
                    allocation_policy,
                    optimal_withdrawal,
                )
                plan_id = repo.save_plan(optimal_plan, experiment_id, persistence_context)

                # Execute the optimal plan to get results
                try:
                    if workers == 1:
                        from infrastructure.execution.parallel_executor import sequential_execute
                        optimal_result = sequential_execute(optimal_plan)
                    else:
                        from infrastructure.execution.parallel_executor import parallel_execute
                        optimal_result = parallel_execute(optimal_plan, max_workers=workers)

                    repo.save_execution_result(
                        plan_id, optimal_result, persistence_context, elapsed
                    )
                except Exception as exec_exc:
                    print(
                        f"WARNING: Optimal execution failed (experiment saved): {exec_exc}",
                        file=sys.stderr,
                    )

            except Exception as exc:
                print(
                    f"WARNING: Persistence failed (optimization completed): {exc}",
                    file=sys.stderr,
                )
        else:
            print("No candidate found — nothing to persist.")
            print()

        return ExitCode.SUCCESS
