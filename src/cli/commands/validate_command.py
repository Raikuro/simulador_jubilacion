"""ValidateCommand — validate YAML experiment definition without execution."""

from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from cli.commands.base import BaseCommand, ExecutionContext
from cli.error_handling import ExitCode
from engine.domain.model.asset import AssetClass
from engine.domain.model.dataset import Dataset
from engine.domain.model.decision_context import DecisionContext
from engine.domain.model.money import Currency, Money
from engine.domain.model.portfolio import AssetHolding, Portfolio
from engine.domain.policies.allocation_policy import AllocationPolicy
from engine.domain.policies.decisions import AllocationDecision, WithdrawalDecision
from engine.domain.policies.withdrawal_policy import WithdrawalPolicy
from infrastructure.persistence.codecs import DefaultDatasetResolver
from research.domain.cohort.generator import CohortGenerator
from research.domain.cohort.specification import CohortSpecification
from research.domain.experiment.definition import ExperimentDefinition
from research.domain.parameter.axis import ParameterAxis
from research.domain.parameter.configuration import ParameterConfiguration
from research.domain.parameter.engine import ParameterSweepEngine
from research.domain.plan import ResearchPlan, materialize_research_plan

_DEFAULT_INITIAL_WEALTH = Money(Decimal("1000000"), Currency.EUR)
_UNIT_WARNING_THRESHOLD = 10000


class _ValidateAllocationPolicy(AllocationPolicy):
    """Concrete AllocationPolicy for validation purposes only.

    Stores YAML-supplied attributes for construction validation.
    Not intended for execution.
    """

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def decide(self, context: DecisionContext) -> AllocationDecision:
        raise NotImplementedError("_ValidateAllocationPolicy is a validation stub")


class _ValidateWithdrawalPolicy(WithdrawalPolicy):
    """Concrete WithdrawalPolicy for validation purposes only.

    Stores YAML-supplied attributes for construction validation.
    Not intended for execution.
    """

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def decide(self, context: DecisionContext) -> WithdrawalDecision:
        raise NotImplementedError("_ValidateWithdrawalPolicy is a validation stub")


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file. Raises FileNotFoundError or yaml.YAMLError."""
    if not path.exists():
        raise FileNotFoundError(str(path))
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        msg = "YAML root must be a mapping"
        raise yaml.YAMLError(msg)
    return data


def _resolve_dataset(identifier: str, data_dir: str | None) -> Dataset:
    """Resolve a dataset identifier using DefaultDatasetResolver."""
    if data_dir:
        resolver = DefaultDatasetResolver.from_data_dir(data_dir)
    else:
        resolver = DefaultDatasetResolver()
    return resolver.resolve(identifier)


def _build_cohort_specs(dataset: Dataset, horizon_months: int) -> tuple[CohortSpecification, ...]:
    """Generate cohorts from a dataset."""
    return CohortGenerator.generate_rolling_monthly(dataset, horizon_months)


def _build_parameter_configs(params_data: dict[str, Any]) -> tuple[ParameterConfiguration, ...]:
    """Build parameter configurations from YAML parameters section."""
    axes: list[ParameterAxis] = []
    for name, values in params_data.items():
        if not isinstance(values, list) or len(values) == 0:
            raise ValueError(f"Parameter '{name}' must have a non-empty list of values")
        axes.append(ParameterAxis(name=name, values=tuple(values)))
    if not axes:
        raise ValueError("At least one parameter axis is required")
    return ParameterSweepEngine.cartesian_product(axes)


def _build_allocation_policies(policies_data: list[Any]) -> tuple[AllocationPolicy, ...]:
    """Build allocation policy instances from YAML allocation_policies section."""
    if not policies_data:
        raise ValueError("At least one allocation policy is required")
    policies: list[AllocationPolicy] = []
    for policy in policies_data:
        if not isinstance(policy, dict):
            raise ValueError("Each allocation policy must be a mapping")
        kwargs = {k: v for k, v in policy.items() if k != "name"}
        policies.append(_ValidateAllocationPolicy(**kwargs))
    return tuple(policies)


def _build_withdrawal_policy(policy_data: dict[str, Any]) -> tuple[WithdrawalPolicy, ...]:
    """Build withdrawal policy instances from YAML withdrawal_policy section."""
    if not isinstance(policy_data, dict):
        raise ValueError("withdrawal_policy must be a mapping")
    return (_ValidateWithdrawalPolicy(**dict(policy_data)),)


def _build_initial_portfolio(initial_wealth: Money) -> Portfolio:
    """Build a minimal Portfolio from initial wealth for validation."""
    asset = AssetClass(id="initial", name="Initial Portfolio", description="")
    return Portfolio(holdings=(AssetHolding(asset_class=asset, units=initial_wealth.amount),))


def _build_research_plan(
    experiment_def: ExperimentDefinition,
    cohorts: tuple[CohortSpecification, ...],
    param_configs: tuple[ParameterConfiguration, ...],
    alloc_policy: AllocationPolicy,
    withdrawal_policy: WithdrawalPolicy,
) -> ResearchPlan:
    """Build a ResearchPlan from components for validation purposes.

    ResearchPlan uniqueness identity is (cohort.start_date, parameter_config),
    so only one allocation+withdrawal policy pair is used per plan.
    """
    portfolio = _build_initial_portfolio(experiment_def.initial_wealth)
    return materialize_research_plan(
        experiment_def=experiment_def,
        cohorts=cohorts,
        param_configs=param_configs,
        alloc_policy=alloc_policy,
        withdrawal_policy=withdrawal_policy,
        initial_portfolio=portfolio,
    )


def _format_param_summary(param_configs: tuple[ParameterConfiguration, ...]) -> list[str]:
    """Build human-readable parameter summary lines."""
    if not param_configs:
        return []
    names = param_configs[0].names()
    lines: list[str] = []
    for name in names:
        values = sorted(
            {str(p.get(name)) for p in param_configs},
            key=lambda v: (isinstance(v, str), v),
        )
        if len(values) == 1:
            lines.append(f"   {name}: {values[0]}")
        else:
            lines.append(f"   {name}: {values[0]} to {values[-1]} ({len(values)} values)")
    return lines


def _format_cohort_summary(cohorts: tuple[CohortSpecification, ...]) -> list[str]:
    """Build human-readable cohort summary lines."""
    if not cohorts:
        return []
    start = min(c.start_date for c in cohorts)
    end = max(c.start_date for c in cohorts)
    return [
        f"   Range: {start.isoformat()} to {end.isoformat()}",
        "   Type: monthly_rolling",
    ]


def _print_section(
    title: str,
    valid: bool,
    error: str | None = None,
    details: list[str] | None = None,
) -> None:
    """Print a validation section to stdout.

    The *title* should already contain the status suffix
    (e.g. ``"Cohorts: 144 valid"``) for exact output control.
    """
    icon = "✅" if valid else "❌"
    print(f"{icon} {title}")
    if details:
        for line in details:
            print(line)
    if error:
        print(f"   Error: {error}")
    print()


def _print_verdict(errors: list[str], warnings: list[str]) -> None:
    """Print the final validation verdict."""
    if errors:
        print("Validation: FAILED")
    else:
        print("Validation: PASSED")


class ValidateCommand(BaseCommand):
    name = "validate"
    help_text = "Validate an experiment definition"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("study_file", type=str, help="Path to YAML experiment definition")

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        study_path = Path(args.study_file)

        print(f"Validating: {study_path}")
        print()

        # --- 1. Parse YAML ---------------------------------------------------
        try:
            data = _load_yaml(study_path)
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
            print("Suggestion: Check YAML syntax and indentation.")
            return ExitCode.VALIDATION_ERROR

        errors: list[str] = []
        warnings: list[str] = []

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
            _print_section(
                "ExperimentDefinition: invalid",
                False,
                "window_years must be a positive integer",
            )
            _print_verdict(errors, warnings)
            return ExitCode.VALIDATION_ERROR
        horizon_months = window_years * 12

        # --- 3. Resolve dataset ----------------------------------------------
        try:
            dataset = _resolve_dataset(dataset_id, context.data_dir)
        except Exception as exc:
            _print_section("ExperimentDefinition: invalid", False, f"Cannot resolve dataset: {exc}")
            _print_verdict(errors, warnings)
            return ExitCode.VALIDATION_ERROR

        # --- 4. Build cohorts ------------------------------------------------
        try:
            cohorts = _build_cohort_specs(dataset, horizon_months)
        except (ValueError, TypeError) as exc:
            _print_section("Cohorts: invalid", False, str(exc))
            _print_verdict(errors, warnings)
            return ExitCode.VALIDATION_ERROR

        # --- 5. Build parameter configs --------------------------------------
        try:
            param_configs = _build_parameter_configs(params_data)
        except (ValueError, TypeError) as exc:
            _print_section("Parameters: invalid", False, str(exc))
            _print_verdict(errors, warnings)
            return ExitCode.VALIDATION_ERROR

        # --- 6. Build allocation policies ------------------------------------
        try:
            alloc_policies = _build_allocation_policies(alloc_policies_data)
        except (ValueError, TypeError) as exc:
            _print_section("Policies: invalid", False, str(exc))
            _print_verdict(errors, warnings)
            return ExitCode.VALIDATION_ERROR

        # --- 7. Build withdrawal policy --------------------------------------
        try:
            withdrawal_policies = _build_withdrawal_policy(withdrawal_policy_data)
        except (ValueError, TypeError) as exc:
            _print_section("Policies: invalid", False, str(exc))
            _print_verdict(errors, warnings)
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
            _print_section("ExperimentDefinition: invalid", False, str(exc))
            _print_verdict(errors, warnings)
            return ExitCode.VALIDATION_ERROR

        # --- 9. Print ExperimentDefinition section ---------------------------
        exp_details = [f"   Name: {experiment_def.name}"]
        if version:
            exp_details.append(f"   Version: {version}")
        exp_details.append(f"   Dataset: {dataset_id}")
        _print_section("ExperimentDefinition: valid", True, details=exp_details)

        # --- 10. Print Cohorts section ---------------------------------------
        cohort_details = _format_cohort_summary(cohorts)
        _print_section(f"Cohorts: {len(cohorts)} valid", True, details=cohort_details)

        # --- 11. Print Parameters section ------------------------------------
        param_details = _format_param_summary(param_configs)
        _print_section(f"Parameters: {len(param_configs)} valid", True, details=param_details)

        # --- 12. Print Policies section --------------------------------------
        _print_section(f"Policies: {len(alloc_policies)} distinct allocation policies", True)
        _print_section(f"Policies: {len(withdrawal_policies)} withdrawal policy", True)

        # --- 13. Build ResearchPlan ------------------------------------------
        try:
            plan = _build_research_plan(
                experiment_def,
                cohorts,
                param_configs,
                alloc_policies[0],
                withdrawal_policies[0],
            )
        except (ValueError, TypeError) as exc:
            _print_section("Plan: invalid", False, str(exc))
            errors.append(str(exc))
            _print_verdict(errors, warnings)
            return ExitCode.VALIDATION_ERROR

        # --- 14. Print Plan section ------------------------------------------
        total_units = len(plan)
        if total_units > _UNIT_WARNING_THRESHOLD:
            warnings.append(
                f"Total unit count ({total_units:,}) exceeds {_UNIT_WARNING_THRESHOLD:,}"
            )
            _print_section(
                f"Plan: {total_units:,} unique simulation units",
                True,
                details=[f"   Warning: exceeds {_UNIT_WARNING_THRESHOLD:,} units"],
            )
        else:
            _print_section(f"Plan: {total_units:,} unique simulation units", True)

        # --- 15. Final verdict -----------------------------------------------
        _print_verdict(errors, warnings)
        return ExitCode.SUCCESS if not errors else ExitCode.VALIDATION_ERROR
