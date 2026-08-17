"""RunCommand — load, execute, and persist a research study."""

from __future__ import annotations

import argparse
import os
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from cli.builders import (
    ResolvedDatasetFamily,
    build_cohort_specs,
    build_dataset_family,
    build_grid_research_plan,
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
from engine.application.executor import SimulationExecutor
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

# Historical field order for the per-cell grid output: the three ERN axes keep
# their original relative order so existing ERN cell lines stay byte-identical.
# Any additional parameter axis is appended afterwards in sorted order.
_GRID_CELL_PARAMETER_ORDER = ("equity_allocation", "withdrawal_rate", "horizon_years")

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


def _resolve_workers_arg(value: str) -> int:
    """Resolve the ``--workers`` argument to an integer worker count.

    Accepts ``'max'`` (case-insensitive) for every available logical CPU, or a
    positive integer.  Raises ``ValueError`` for anything else so the CLI exits
    with a validation error instead of passing an invalid count downstream.
    """
    text = value.strip()
    if text.lower() == "max":
        return os.cpu_count() or 1
    try:
        workers = int(text)
    except ValueError:
        raise ValueError(f"--workers must be a positive integer or 'max', got {value!r}") from None
    if workers <= 0:
        raise ValueError(f"--workers must be a positive integer or 'max', got {value!r}")
    return workers


def _print_grid_per_cell_results(
    plan: Any,
    sim_results: Any,
) -> None:
    """Print one result block per parameter configuration for a grid study.

    Groups the executed per-unit statistics by the unit's ``parameter_config``
    and prints one machine-parseable block per configuration.  The per-cell
    values come from the actual execution statistics (``SimulationStatistics``),
    not from the plan or the expected oracle.

    The block layout is a stable key=value line, one per parameter
    configuration, so a future black-box E2E harness can parse it:
    ``cell: equity_allocation=1.0 withdrawal_rate=0.03 horizon_years=30
    units_run=1739 units_failed=123 success_rate=0.9293``.

    The cell key/label is derived from ALL parameter axes of the configuration
    rather than a hard-coded ERN triple, so grids with additional axes (e.g.
    ``glidepath_duration``) are aggregated per full configuration instead of
    silently merging units that differ only on the extra axis.  The three ERN
    axes keep their historical field order (``equity_allocation``,
    ``withdrawal_rate``, ``horizon_years``) so existing ERN cell lines are
    byte-identical; any additional axes are appended afterwards in sorted order.
    """
    from collections import defaultdict

    from research.domain.parameter.configuration import ParameterConfiguration
    from research.domain.parameter.types import ParameterScalar

    CellKey = tuple[ParameterScalar | None, ...]
    cell_units: dict[CellKey, list[Any]] = defaultdict(list)
    cell_labels: dict[CellKey, str] = {}

    def _ordered_names(config: ParameterConfiguration) -> tuple[str, ...]:
        names = config.names()
        ordered = tuple(n for n in _GRID_CELL_PARAMETER_ORDER if n in names)
        ordered += tuple(n for n in names if n not in ordered)
        return ordered

    for unit, result in zip(plan.units, sim_results, strict=True):
        config: ParameterConfiguration = unit.parameter_config
        names = _ordered_names(config)
        key: CellKey = tuple(config.get(name) for name in names)
        cell_units[key].append(result)
        if key not in cell_labels:
            parts = [f"{name}={config.get(name)}" for name in names]
            cell_labels[key] = " ".join(parts)

    print()
    print("Per-Cell Results (grid):")
    for key in cell_units:
        results = cell_units[key]
        units_run = len(results)
        units_failed = sum(1 for r in results if not r.statistics.success)
        success_rate = (units_run - units_failed) / units_run if units_run else 0.0
        print(
            f"cell: {cell_labels[key]} "
            f"units_run={units_run} units_failed={units_failed} "
            f"success_rate={success_rate:.4f}"
        )


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
            type=str,
            default=None,
            help=(
                "Number of parallel workers; 'max' uses every available logical "
                "CPU (default: config execution.default_workers or 1)"
            ),
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
        parser.add_argument(
            "--reference-chained",
            action="store_true",
            help="Explicitly use the chained Reference executor: reproduce the "
            "canonical Reference Decimal run for each family's longest horizon "
            "and derive shorter-horizon results from it bit-exactly. This is "
            "the default exact execution mode for plans that benefit from "
            "horizon chaining; the flag documents intent and preserves existing "
            "scripts (cannot be combined with --reference-independent or "
            "--fast-path)",
        )
        parser.add_argument(
            "--reference-independent",
            action="store_true",
            help="Use the independent Reference executor: evaluate every unit "
            "through the canonical Decimal engine with no horizon chaining. "
            "This is the reference oracle against which optimized execution is "
            "verified (cannot be combined with --reference-chained or "
            "--fast-path)",
        )
        parser.add_argument(
            "--validate",
            action="store_true",
            help="Run a deterministic sample of the fast-path execution through "
            "both the fast path and the canonical Decimal reference engine and "
            "fail loudly on any divergence; requires --fast-path",
        )

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        study_path = Path(args.study_file)

        # --- 0. Resolve config-driven execution defaults (CLI > config > defaults) --
        config = load_configuration(context)
        if args.workers is not None:
            try:
                args.workers = _resolve_workers_arg(args.workers)
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return ExitCode.VALIDATION_ERROR
        else:
            args.workers = int(config.execution.get("default_workers", 1))
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
        datasets_data: list[Any] = data.get("datasets", [])
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
        has_grid_datasets = bool(datasets_data)
        has_horizon_axis = "horizon_years" in params_data
        is_grid_study = has_grid_datasets or has_horizon_axis

        # --- 3. Resolve datasets (grid family or single dataset) -------------
        try:
            if has_grid_datasets:
                dataset_family = build_dataset_family(datasets_data, context.data_dir)
                canonical_dataset = dataset_family.canonical
            else:
                canonical_dataset = resolve_dataset(dataset_id, context.data_dir)
                dataset_family = None
        except Exception as exc:
            print(f"ERROR: Cannot resolve dataset: {exc}")
            return ExitCode.VALIDATION_ERROR

        # --- 4. Build cohorts ------------------------------------------------
        try:
            if is_grid_study:
                axis_horizons = [
                    h
                    for h in params_data.get("horizon_years", [])
                    if isinstance(h, int) and not isinstance(h, bool) and h > 0
                ]
                declared_max = max(dataset_family.horizons) if dataset_family is not None else 0
                axis_max = max(axis_horizons) if axis_horizons else 0
                longest_horizon_years = max(declared_max, axis_max) or window_years
                longest_horizon_months = longest_horizon_years * 12
                cohorts = build_cohort_specs(canonical_dataset, longest_horizon_months)
            else:
                longest_horizon_months = window_years * 12
                cohorts = build_cohort_specs(canonical_dataset, longest_horizon_months)
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
                dataset=canonical_dataset,
                horizon_months=longest_horizon_months,
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
            if is_grid_study:
                if dataset_family is None:
                    dataset_family = ResolvedDatasetFamily(canonical=canonical_dataset, horizons={})
                default_horizon_years = (
                    window_years if "window_years" in cohorts_info else longest_horizon_years
                )
                plan = build_grid_research_plan(
                    experiment_def,
                    dataset_family,
                    cohorts,
                    param_configs,
                    alloc_policies[0],
                    withdrawal_policies[0],
                    default_horizon_years=default_horizon_years,
                )
            else:
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

        if args.validate and not args.fast_path:
            print("ERROR: --validate requires --fast-path")
            print("       --validate compares the fast path against the canonical")
            print("       Decimal reference engine, so it is meaningless without it.")
            return ExitCode.VALIDATION_ERROR

        execution_mode_flags = []
        if args.fast_path:
            execution_mode_flags.append("--fast-path")
        if args.reference_chained:
            execution_mode_flags.append("--reference-chained")
        if args.reference_independent:
            execution_mode_flags.append("--reference-independent")
        if len(execution_mode_flags) > 1:
            flags_text = " and ".join(execution_mode_flags)
            print("ERROR: execution-mode flags are mutually exclusive: " + flags_text)
            print("       Request exactly one; the default is Reference Chained,")
            print("       falling back to the independent Reference for plans that")
            print("       do not benefit from horizon chaining.")
            return ExitCode.VALIDATION_ERROR

        if args.validate:
            from cli.fast_path import FastPathValidationError, run_fast_path_validation

            try:
                sampled_units, _eligible_units = run_fast_path_validation(plan)
            except FastPathValidationError as exc:
                print("ERROR: " + str(exc))
                return ExitCode.VALIDATION_ERROR
            if sampled_units == 0:
                print("Validation:     skipped (no fast-path-eligible units)")
            else:
                print(
                    f"Validation:     OK ({sampled_units} fast-path unit(s) vs Decimal reference)"
                )

        from cli.progress import ProgressDisplay

        progress = ProgressDisplay(total_units)
        start_time = time.perf_counter()

        # --- 11a. Resolve the exact execution mode ---------------------------
        # ``--reference-chained`` and ``--reference-independent`` are explicit;
        # the default is Reference Chained only when the plan actually benefits
        # from horizon chaining (``derived_results > 0``).  Single-horizon and
        # other non-chainable plans stay on the independent Reference dispatch
        # so grouping/slicing overhead is never paid when chaining would derive
        # nothing.  Chaining never sacrifices correctness: non-eligible units
        # and families fall back to the independent Reference inside the
        # executor, and the default/independent paths are bit-exact (proven
        # over the full ERN grid).
        if args.reference_chained:
            use_chained = True
        elif args.reference_independent or args.fast_path:
            use_chained = False
        else:
            from infrastructure.execution.reference_chaining import (
                expected_reference_chaining_report,
            )

            use_chained = expected_reference_chaining_report(plan).derived_results > 0

        simulation_executor: SimulationExecutor | None = None
        if use_chained:
            # The chained Reference executor materializes ~0.37 MiB of timeline
            # payload per unit, so whole-plan dispatch (~110 GiB for the ERN
            # grid) must never be handed to a single executor call.  Route it
            # through the memory-safe cohort-slice dispatch instead.
            from infrastructure.execution.reference_chaining import (
                execute_reference_chained,
            )

            try:
                research_result = execute_reference_chained(
                    plan,
                    max_workers=workers,
                    progress_callback=progress.update,
                    summary_only=args.summary_only,
                )
            except Exception as exc:
                progress.finish()
                elapsed = time.perf_counter() - start_time
                print(f"ERROR: Execution failed after {_format_duration(elapsed)}: {exc}")
                return ExitCode.ERROR
        else:
            if args.fast_path:
                from cli.fast_path import ChainedFastPathSimulationExecutor

                simulation_executor = ChainedFastPathSimulationExecutor(precision="float")

            try:
                if args.fast_path and workers == 1:
                    from infrastructure.execution.parallel_executor import (
                        sequential_execute,
                    )

                    research_result = sequential_execute(
                        plan,
                        simulation_executor=simulation_executor,
                        progress_callback=progress.update,
                        summary_only=args.summary_only,
                    )
                elif args.fast_path:
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
                elif workers == 1:
                    from infrastructure.execution.parallel_executor import (
                        sequential_execute,
                    )

                    research_result = sequential_execute(
                        plan,
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
            from cli.fast_path import (
                expected_chaining_report,
                fast_path_unit_counts,
                reference_month_work,
            )

            fast_units, reference_units = fast_path_unit_counts(plan)
            print(f"Fast Path:      {fast_units:,} units (closed form)")
            print(f"Reference Path: {reference_units:,} units (fallback)")
            report = expected_chaining_report(plan)
            if report.chained_groups:
                print(f"Chained Groups: {report.chained_groups:,} families")
                print(
                    f"Longest Path:   {report.longest_path_evaluations:,} "
                    f"evaluation(s) reused for {report.derived_results:,} derived unit(s)"
                )
            print(
                f"Month-Work:     {report.month_work:,} months (chained) "
                f"/ {reference_month_work(plan):,} months (reference)"
            )
        if use_chained:
            from cli.fast_path import reference_month_work
            from infrastructure.execution.reference_chaining import (
                expected_reference_chaining_report,
            )

            chained_report = expected_reference_chaining_report(plan)
            print(f"Reference Chained: {chained_report.logical_units:,} units (chained reference)")
            if chained_report.independent_evaluations:
                print(
                    f"Independent Path: {chained_report.independent_evaluations:,} units "
                    f"(non-prefix fallback)"
                )
            if chained_report.chained_groups:
                print(f"Chained Groups: {chained_report.chained_groups:,} families")
                print(
                    f"Longest Path:   {chained_report.longest_path_evaluations:,} "
                    f"evaluation(s) reused for {chained_report.derived_results:,} derived unit(s)"
                )
            print(
                f"Month-Work:     {chained_report.month_work:,} months (chained) "
                f"/ {reference_month_work(plan):,} months (reference)"
            )
        print(f"Execution Time: {_format_duration(elapsed)}")

        # --- 14. Per-cell results for grid studies ---------------------------
        if is_grid_study and args.summary_only and not args.persist_study:
            _print_grid_per_cell_results(plan, sim_results)

        return ExitCode.SUCCESS
