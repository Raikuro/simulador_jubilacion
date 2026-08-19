"""OptimizeCommand — find optimal withdrawal rate using SWROptimizer.

Contains the private _SWREvaluator that bridges the SWROptimizer protocol
to the simulation execution engine, and the OptimizeCommand itself.

The allocation policy comes from the normalized study configuration (a concrete
``equity_allocation`` is required via the declared ``allocation_policy.equity_allocation``
array).  The optimizer owns the candidate withdrawal-rate values; the YAML
``withdrawal_policy.type`` supplies the policy mechanism.  The optimizer replaces
the study's single-value ``withdrawal_policy.withdrawal_rate`` placeholder with each
candidate; multi-value arrays are rejected.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from pathlib import Path

import yaml

from cli.builders import StudyConfiguration, build_study_plan, load_yaml
from cli.commands.base import BaseCommand, ExecutionContext
from cli.error_handling import ExitCode
from engine.domain.model.money import Currency, Money
from infrastructure.persistence.context import create_persistence_context
from infrastructure.persistence.errors import DuplicateStudyError, RepositoryError
from infrastructure.persistence.sqlite_repository import (
    ExperimentIdentity,
    SQLiteRepository,
)
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


class _SWREvaluator:
    """Evaluator adapter: bridges SWROptimizer binary search to simulation execution.

    Implements the SWROptimizer.Evaluator protocol:
        evaluate(candidate: Decimal) -> EvaluationOutcome

    Each candidate builds the study plan with the candidate as the withdrawal
    rate; the allocation policy (and every other value) is unchanged.
    """

    def __init__(
        self,
        config: StudyConfiguration,
        data_dir: str | None,
        capital: Money,
        target_success_rate: Decimal,
        workers: int,
    ) -> None:
        self._config = config
        self._data_dir = data_dir
        self._capital = capital
        self._target = target_success_rate
        self._workers = workers
        self._iteration = 0

    def evaluate(self, candidate: Decimal) -> EvaluationOutcome:
        self._iteration += 1

        candidate_config = replace(self._config, withdrawal_policy_values=(candidate,))
        built = build_study_plan(candidate_config, self._data_dir, self._capital)
        plan = built.plan

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

        # --- 2. Interpret the study configuration ----------------------------
        try:
            study_config = StudyConfiguration.from_yaml(data)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Invalid study configuration: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        # --- 3. Validate the single-configuration requirement ---------------
        if len(study_config.withdrawal_policy_values) != 1:
            print(
                "ERROR: optimize requires a single-value withdrawal_policy.withdrawal_rate; "
                "the optimizer owns the candidate withdrawal-rate values",
                file=sys.stderr,
            )
            return ExitCode.VALIDATION_ERROR
        if len(study_config.allocation_policy_values) != 1:
            print(
                "ERROR: optimize requires a single configuration; "
                "allocation_policy.equity_allocation must have exactly one value",
                file=sys.stderr,
            )
            return ExitCode.VALIDATION_ERROR
        if len(study_config.horizon_years) != 1:
            print(
                "ERROR: optimize requires a single configuration; "
                "cohorts.horizon_years must have exactly one value",
                file=sys.stderr,
            )
            return ExitCode.VALIDATION_ERROR

        allocation_scalar = study_config.allocation_policy_values[0]

        # --- 4. Validate plan buildability (dataset + cohort feasibility) -----
        try:
            build_study_plan(study_config, context.data_dir, capital)
        except (ValueError, TypeError, RepositoryError) as exc:
            print(f"ERROR: Cannot build study plan: {exc}", file=sys.stderr)
            return ExitCode.VALIDATION_ERROR

        # --- 5. Build evaluator ----------------------------------------------
        evaluator = _SWREvaluator(
            config=study_config,
            data_dir=context.data_dir,
            capital=capital,
            target_success_rate=Decimal(str(target_success_rate)),
            workers=workers,
        )

        # Print optimization header
        print("=" * 50)
        print("Optimization Started")
        print("=" * 50)
        print(f"Study: {study_path}")
        print(
            f"Allocation Policy: {study_config.allocation_policy_type} "
            f"(equity_allocation={allocation_scalar})"
        )
        print(f"Target Success Rate: {target_success_rate:.1%}")
        print(f"Capital: {capital.amount:,.0f} {capital.currency.value}")
        print(f"Workers: {workers}")
        print(f"Tolerance: {tolerance}")
        print()

        # --- 5. Run optimizer ------------------------------------------------
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

        # --- 6. Print summary ------------------------------------------------
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

        print(
            f"Policy:                    {study_config.allocation_policy_type}"
            f"(equity_allocation={allocation_scalar})"
        )
        print(f"Target Success Rate:       {target_success_rate:.1%}")
        print(f"Iterations Required:       {evaluator._iteration}")
        print(f"Execution Time:            {_format_duration(elapsed)}")
        print()

        # --- 7. Persist results ----------------------------------------------
        if outcome.candidate_value is not None:
            try:
                db_path = str(Path(_DEFAULT_DB_PATH).expanduser())
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                repo = SQLiteRepository(db_path)
                persistence_context = create_persistence_context(context.data_dir)

                identity = ExperimentIdentity(
                    name=study_config.name,
                    revision=study_config.version or "1.0",
                )

                optimal_config = replace(
                    study_config, withdrawal_policy_values=(outcome.candidate_value,)
                )
                optimal_built = build_study_plan(
                    optimal_config, context.data_dir, capital
                )
                optimal_experiment_def = optimal_built.experiment_definition
                optimal_plan = optimal_built.plan

                experiment_id = repo.save_experiment(
                    identity, optimal_experiment_def, persistence_context
                )
                print(f"Study ID:                  {experiment_id}")
                print()

                plan_id = repo.save_plan(optimal_plan, experiment_id, persistence_context)

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

            except DuplicateStudyError:
                print(
                    "NOTE: Experiment already exists with this name/revision; "
                    "optimal results were not persisted (existing study retained).",
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
