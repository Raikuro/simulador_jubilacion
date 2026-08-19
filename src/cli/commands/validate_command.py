"""ValidateCommand — validate YAML experiment definition without execution."""

from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from cli.builders import StudyConfiguration, build_study_plan, load_yaml
from cli.commands.base import BaseCommand, ExecutionContext
from cli.error_handling import ExitCode
from engine.domain.model.money import Currency, Money
from infrastructure.persistence.errors import RepositoryError

_DEFAULT_INITIAL_WEALTH = Money(Decimal("1000000"), Currency.EUR)
_UNIT_WARNING_THRESHOLD = 10000


def _format_param_summary(param_configs: tuple[Any, ...]) -> list[str]:
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


def _format_cohort_summary(cohorts: tuple[Any, ...]) -> list[str]:
    """Build human-readable cohort summary lines."""
    if not cohorts:
        return []
    start = min(c.start_date for c in cohorts)
    end = max(c.start_date for c in cohorts)
    return [
        f"   Range: {start.isoformat()} to {end.isoformat()}",
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
            print("Suggestion: Check YAML syntax and indentation.")
            return ExitCode.VALIDATION_ERROR

        errors: list[str] = []
        warnings: list[str] = []

        # --- 2. Interpret the study configuration -----------------------------
        try:
            study_config = StudyConfiguration.from_yaml(data)
        except (ValueError, TypeError) as exc:
            _print_section("ExperimentDefinition: invalid", False, str(exc))
            _print_verdict(errors, warnings)
            return ExitCode.VALIDATION_ERROR

        # --- 3. Build the unified plan ----------------------------------------
        try:
            built = build_study_plan(
                study_config, context.data_dir, _DEFAULT_INITIAL_WEALTH
            )
        except (ValueError, TypeError, RepositoryError) as exc:
            _print_section("ExperimentDefinition: invalid", False, str(exc))
            _print_verdict(errors, warnings)
            return ExitCode.VALIDATION_ERROR

        experiment_def = built.experiment_definition
        plan = built.plan
        cohorts = built.cohorts
        param_configs = built.param_configs

        # --- 4. Print ExperimentDefinition section ---------------------------
        exp_details = [f"   Name: {experiment_def.name}"]
        if study_config.version:
            exp_details.append(f"   Version: {study_config.version}")
        exp_details.append(f"   Dataset: {study_config.dataset_identifier}")
        _print_section("ExperimentDefinition: valid", True, details=exp_details)

        # --- 5. Print Cohorts section ----------------------------------------
        cohort_details = _format_cohort_summary(cohorts)
        _print_section(f"Cohorts: {len(cohorts)} valid", True, details=cohort_details)

        # --- 6. Print Parameters section -------------------------------------
        param_details = _format_param_summary(param_configs)
        _print_section(f"Parameters: {len(param_configs)} valid", True, details=param_details)

        # --- 7. Print Policies section ---------------------------------------
        _print_section(
            "Policies: 1 allocation policy x 1 withdrawal policy", True
        )

        # --- 8. Print Plan section -------------------------------------------
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

        # --- 9. Final verdict ------------------------------------------------
        _print_verdict(errors, warnings)
        return ExitCode.SUCCESS if not errors else ExitCode.VALIDATION_ERROR
