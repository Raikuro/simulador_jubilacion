"""RunCommand — load, execute, and persist a research study."""

from __future__ import annotations

import argparse
import time
from decimal import Decimal
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
from cli.commands.config_command import load_configuration
from cli.error_handling import ExitCode
from cli.policies import (
    ConstantAllocationPolicy,
    ConstantWithdrawalPolicy,
    FixedRealWithdrawalPolicy,
)
from engine.domain.model.money import Currency, Money
from engine.domain.policies.allocation_policy import AllocationPolicy
from engine.domain.policies.withdrawal_policy import WithdrawalPolicy
from infrastructure.persistence.context import create_persistence_context
from infrastructure.persistence.sqlite_repository import (
    ExperimentIdentity,
    SQLiteRepository,
)
from research.domain.experiment.definition import ExperimentDefinition

_DEFAULT_INITIAL_WEALTH = Money(Decimal("1000000"), Currency.EUR)
_DEFAULT_DB_PATH = "~/.sim-retire/studies.db"

# Conservative per-unit estimate used ONLY by the dry-run preview. Measured
# reference throughput on the ERN 360-month slice is ~0.027-0.03 s/unit with a
# single worker; the constant is set higher (0.05) so the dry-run preview is an
# upper bound rather than an optimistic promise. It is deliberately separate
# from the LIVE ETA, which is computed from observed throughput as units
# actually complete (see cli.progress.ProgressDisplay).
_DRY_RUN_SECONDS_PER_UNIT = 0.05


def _build_allocation_policies(policies_data: list[Any]) -> tuple[AllocationPolicy, ...]:
    """Build constant allocation policies from the YAML allocation_policies section.

    Reuses the execution-grade ``ConstantAllocationPolicy`` so the study can be
    executed through the real simulation engine (not a decision stub).
    """
    if not policies_data:
        raise ValueError("At least one allocation policy is required")
    policies: list[AllocationPolicy] = []
    for policy in policies_data:
        if not isinstance(policy, dict):
            raise ValueError("Each allocation policy must be a mapping")
        ratio = Decimal(str(policy.get("equity_ratio", "0.75")))
        policies.append(ConstantAllocationPolicy(equity_allocation=ratio))
    return tuple(policies)


def _build_withdrawal_policy(policy_data: dict[str, Any]) -> tuple[WithdrawalPolicy, ...]:
    """Build a withdrawal policy from the YAML ``withdrawal_policy`` section.

    Dispatches on the ``type`` key: ``FixedRealWithdrawalPolicy`` builds the
    fixed-real policy; any other or absent ``type`` builds the legacy
    constant policy (backwards compatible).
    """
    if not isinstance(policy_data, dict):
        raise ValueError("withdrawal_policy must be a mapping")
    rate = Decimal(str(policy_data.get("withdrawal_rate", "0.04")))
    policy_type = policy_data.get("type", "ConstantWithdrawalPolicy")
    if policy_type == "FixedRealWithdrawalPolicy":
        return (FixedRealWithdrawalPolicy(withdrawal_rate=rate),)
    return (ConstantWithdrawalPolicy(withdrawal_rate=rate),)


def _format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {secs}s"


def _format_cohort_range(cohorts: Any) -> str:
    """Format the cohort date range for dry-run output."""
    start = min(c.start_date for c in cohorts)
    end = max(c.start_date for c in cohorts)
    return f"{start.year}-{end.year}"


def _estimate_execution_time(total_units: int, workers: int) -> str:
    """Estimate execution time based on unit count and worker count.

    Uses the conservative dry-run constant (an upper bound) — live execution
    reports an observed-throughput ETA instead. See ``_DRY_RUN_SECONDS_PER_UNIT``.
    """
    est_seconds = (total_units * _DRY_RUN_SECONDS_PER_UNIT) / max(workers, 1)
    return _format_duration(est_seconds)


class RunCommand(BaseCommand):
    name = "run"
    help_text = "Execute a research study"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("study_file", type=str, help="Path to YAML experiment definition")
        parser.add_argument(
            "--output-dir",
            type=str,
            default=None,
            help="Output directory (default: ./results/, or output.default_directory from config)",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=None,
            help="Number of parallel workers (default: config execution.default_workers or 1)",
        )
        parser.add_argument(
            "--format",
            choices=["csv", "json", "sqlite", "all"],
            default=None,
            help="Output format (default: csv, or output.default_format from config)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate plan without executing",
        )
        parser.add_argument(
            "--resume",
            type=str,
            default=None,
            help="Resume interrupted study ID",
        )
        persist_group = parser.add_mutually_exclusive_group()
        persist_group.add_argument(
            "--persist-study",
            dest="persist_study",
            action="store_true",
            default=True,
            help="Save study, plan and results to the database (default)",
        )
        persist_group.add_argument(
            "--no-persist",
            dest="persist_study",
            action="store_false",
            help="Execute without persisting any study, plan or result data",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            help="Keep only aggregate statistics in memory (strip per-month "
            "timelines); cannot be combined with --persist-study",
        )
        parser.add_argument(
            "--fast-path",
            action="store_true",
            help="Use the closed-form fast path for constant-allocation + "
            "fixed-real-withdrawal studies (results validated equivalent to the "
            "reference Decimal engine)",
        )

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        study_path = Path(args.study_file)

        # --- 0. Resolve config-driven execution defaults (CLI > config > defaults) --
        config = load_configuration(context)
        args.workers = (
            args.workers
            if args.workers is not None
            else int(config.execution.get("default_workers", 1))
        )
        args.format = args.format or str(config.output.get("default_format", "csv"))
        args.output_dir = args.output_dir or str(
            config.output.get("default_directory", "./results/")
        )

        # --- 1. Parse YAML ---------------------------------------------------
        try:
            data = load_yaml(study_path)
        except FileNotFoundError:
            print("ERROR: Study file not found")
            print(f"File: {study_path}")
            print()
            print("Suggestion: Check file path and ensure it exists.")
            return ExitCode.VALIDATION_ERROR
        except yaml.YAMLError as exc:
            print("ERROR: Invalid YAML in study file")
            print(f"File: {study_path}")
            if hasattr(exc, "problem_mark") and exc.problem_mark is not None:
                print(f"Line: {exc.problem_mark.line + 1}")
            print()
            return ExitCode.VALIDATION_ERROR

        # --- 2. Extract metadata ---------------------------------------------
        metadata: dict[str, Any] = data.get("metadata", {})
        dataset_info: dict[str, Any] = data.get("dataset", {})
        cohorts_info: dict[str, Any] = data.get("cohorts", {})
        params_data: dict[str, Any] = data.get("parameters", {})
        alloc_policies_data: list[Any] = data.get("allocation_policies", [])
        withdrawal_policy_data: dict[str, Any] = data.get("withdrawal_policy", {})

        name: str = metadata.get("name", "Unnamed Study")
        description_val: str = metadata.get("description", "")
        version: str = metadata.get("version", "")
        dataset_id: str = dataset_info.get("identifier", "")

        window_years = cohorts_info.get("window_years", 30)
        if not isinstance(window_years, int) or window_years <= 0:
            print("ERROR: window_years must be a positive integer")
            return ExitCode.VALIDATION_ERROR
        horizon_months = window_years * 12

        # --- 3. Resolve dataset ----------------------------------------------
        try:
            dataset = resolve_dataset(dataset_id, context.data_dir)
        except Exception as exc:
            print(f"ERROR: Cannot resolve dataset: {exc}")
            return ExitCode.VALIDATION_ERROR

        # --- 4. Build cohorts ------------------------------------------------
        try:
            cohorts = build_cohort_specs(dataset, horizon_months)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Cohort generation failed: {exc}")
            return ExitCode.VALIDATION_ERROR

        # --- 5. Build parameter configs --------------------------------------
        try:
            param_configs = build_parameter_configs(params_data)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Invalid parameters: {exc}")
            return ExitCode.VALIDATION_ERROR

        # --- 6. Build allocation policies ------------------------------------
        try:
            alloc_policies = _build_allocation_policies(alloc_policies_data)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Invalid allocation policies: {exc}")
            return ExitCode.VALIDATION_ERROR

        # --- 7. Build withdrawal policy --------------------------------------
        try:
            withdrawal_policies = _build_withdrawal_policy(withdrawal_policy_data)
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Invalid withdrawal policy: {exc}")
            return ExitCode.VALIDATION_ERROR

        # --- 8. Build ExperimentDefinition -----------------------------------
        try:
            experiment_def = ExperimentDefinition(
                name=name,
                description=description_val or name,
                dataset=dataset,
                horizon_months=horizon_months,
                initial_wealth=_DEFAULT_INITIAL_WEALTH,
                cohorts=cohorts,
                allocation_policies=alloc_policies,
                withdrawal_policies=withdrawal_policies,
            )
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Invalid experiment definition: {exc}")
            return ExitCode.VALIDATION_ERROR

        # --- 9. Build ResearchPlan -------------------------------------------
        try:
            plan = build_research_plan(
                experiment_def,
                cohorts,
                param_configs,
                alloc_policies[0],
                withdrawal_policies[0],
            )
        except (ValueError, TypeError) as exc:
            print(f"ERROR: Plan construction failed: {exc}")
            return ExitCode.VALIDATION_ERROR

        total_units = len(plan)
        num_cohorts = len(cohorts)
        num_param_configs = len(param_configs)
        num_alloc = len(alloc_policies)
        num_withd = len(withdrawal_policies)

        # --- 10. Dry-run: print plan summary and exit ------------------------
        if args.dry_run:
            cohort_range = _format_cohort_range(cohorts)
            est_time = _estimate_execution_time(total_units, args.workers)
            param_names = ", ".join(param_configs[0].names()) if param_configs else "none"

            print(f"Study:          {name} (v{version})" if version else f"Study:          {name}")
            print(f"Cohorts:        {num_cohorts} (monthly rolling, {cohort_range})")
            print(f"Parameters:     {num_param_configs} (sweep: {param_names})")
            print(f"Policies:       {num_alloc} allocation x {num_withd} withdrawal")
            print(f"Total Units:    {total_units:,} simulations")
            print(f"Estimated Time: ~{est_time} ({args.workers} workers)")
            print()
            print("DRY RUN — No simulations executed.")
            return ExitCode.SUCCESS

        # --- 11. Execute study -----------------------------------------------
        workers = max(args.workers, 1)

        if args.persist_study and args.summary_only:
            print("ERROR: --summary-only cannot be combined with --persist-study")
            print("       Persisted results require full per-month timelines.")
            return ExitCode.VALIDATION_ERROR

        if args.fast_path and args.persist_study:
            print("ERROR: --fast-path cannot be combined with --persist-study")
            print("       The fast path produces summary-grade results without")
            print("       per-month timelines, so persisted results would be")
            print("       silently empty. Re-run with --no-persist or --summary-only.")
            return ExitCode.VALIDATION_ERROR

        from cli.progress import ProgressDisplay

        progress = ProgressDisplay(total_units)
        start_time = time.perf_counter()

        simulation_executor = None
        if args.fast_path:
            from cli.fast_path import FastPathSimulationExecutor

            simulation_executor = FastPathSimulationExecutor(precision="float")

        try:
            if workers == 1:
                from infrastructure.execution.parallel_executor import (
                    sequential_execute,
                )

                research_result = sequential_execute(
                    plan,
                    simulation_executor=simulation_executor,
                    progress_callback=progress.update,
                    summary_only=args.summary_only,
                )
            else:
                from infrastructure.execution.parallel_executor import (
                    parallel_execute,
                )

                research_result = parallel_execute(
                    plan,
                    max_workers=workers,
                    simulation_executor=simulation_executor,
                    progress_callback=progress.update,
                    summary_only=args.summary_only,
                )
        except Exception as exc:
            progress.finish()
            elapsed = time.perf_counter() - start_time
            print(f"ERROR: Execution failed after {_format_duration(elapsed)}: {exc}")
            return ExitCode.ERROR

        progress.finish()
        elapsed = time.perf_counter() - start_time

        # --- 12. Persist results (skipped entirely when --no-persist) ---------
        if args.persist_study:
            try:
                db_path = Path(_DEFAULT_DB_PATH).expanduser()
                db_path.parent.mkdir(parents=True, exist_ok=True)
                repo = SQLiteRepository(str(db_path))
                persistence_context = create_persistence_context(context.data_dir)

                identity = ExperimentIdentity(name=name, revision=version or "1.0")

                experiment_id = repo.save_experiment(identity, experiment_def, persistence_context)
                plan_id = repo.save_plan(plan, experiment_id, persistence_context)
                repo.save_execution_result(plan_id, research_result, persistence_context, elapsed)
            except Exception as exc:
                print(f"WARNING: Persistence failed (execution completed): {exc}")

        # --- 13. Print completion summary ------------------------------------
        sim_results = research_result.results
        success_count = sum(1 for r in sim_results if r.statistics.success)
        failure_count = total_units - success_count

        print("\u2501" * 47)
        print("Execution Complete")
        print("\u2501" * 47)
        print(f"Status:         {'SUCCESS' if failure_count == 0 else 'COMPLETED WITH ERRORS'}")
        print(f"Units Run:      {total_units:,}")
        print(f"Units Failed:   {failure_count:,}")
        if args.fast_path:
            from cli.fast_path import fast_path_unit_counts

            fast_units, reference_units = fast_path_unit_counts(plan)
            print(f"Fast Path:      {fast_units:,} units (closed form)")
            print(f"Reference Path: {reference_units:,} units (fallback)")
        print(f"Execution Time: {_format_duration(elapsed)}")

        return ExitCode.SUCCESS
