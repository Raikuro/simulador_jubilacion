"""Tests for CompareCommand — compare generated parameter configurations."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from cli.commands import COMMANDS
from cli.commands.compare_command import (
    CompareCommand,
    _canonical_param_key,
    _config_matches,
    _extract_evaluation_results,
    _parse_strategy_filter,
)
from cli.error_handling import ExitCode
from cli.main import main
from cli.policies import ConstantAllocationPolicy, ConstantWithdrawalPolicy
from engine.application.simulation import (
    ExperimentDefinition as EngineExperimentDefinition,
    ExperimentRun as EngineExperimentRun,
    SimulationResult,
    SimulationStatistics,
    SimulationTimeline,
)
from engine.application.simulation_context import SimulationContext
from engine.domain.model.asset import AssetClass
from engine.domain.model.dataset import Dataset
from engine.domain.model.market_snapshot import MarketSnapshot
from engine.domain.model.money import Currency, Money
from engine.domain.model.portfolio import Portfolio
from engine.domain.optimizer.types import EvaluationResult
from infrastructure.persistence.codecs import DefaultDatasetResolver
from research.domain.cohort.specification import CohortSpecification
from research.domain.experiment.definition import (
    ExperimentDefinition as ResearchExperimentDefinition,
)
from research.domain.parameter.configuration import ParameterConfiguration
from research.domain.plan import PlannedSimulationUnit, ResearchPlan
from research.orchestration.result import ResearchExecutionResult

# ---------------------------------------------------------------------------
# Test dataset factory
# ---------------------------------------------------------------------------


def _make_snapshot(d: date) -> MarketSnapshot:
    asset = AssetClass(id="acwi", name="ACWI", description="Global equities")
    return MarketSnapshot(
        date=d,
        index_levels={asset: Decimal("100.00")},
        inflation=Decimal("0.00"),
        inflation_cumulative=Decimal("0.00"),
        is_ath=True,
        is_underwater=False,
        running_ath=Decimal("100.00"),
    )


def _make_dataset(num_months: int, start_year: int = 1871) -> Dataset:
    snapshots = []
    year = start_year
    month = 1
    for _ in range(num_months):
        snapshots.append(_make_snapshot(date(year, month, 1)))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return Dataset(snapshots=snapshots, frequency="monthly", version="1.0")


# ---------------------------------------------------------------------------
# Simulation result factory
# ---------------------------------------------------------------------------

_NULL_PORTFOLIO = Portfolio(holdings=())
_ASSET = AssetClass(id="test", name="Test", description="")


def _make_simulation_result(
    success: bool,
    final_wealth: Decimal,
    max_drawdown: float = 0.0,
) -> SimulationResult:
    return SimulationResult(
        timeline=SimulationTimeline(monthly_results=()),
        statistics=SimulationStatistics(
            final_wealth=Money(final_wealth, Currency.EUR),
            max_drawdown=max_drawdown,
            success=success,
            failure_month=None,
            months_simulated=360,
            execution_time_seconds=0.1,
        ),
    )


# ---------------------------------------------------------------------------
# ResearchPlan + ResearchExecutionResult factory
# ---------------------------------------------------------------------------


def _make_plan_unit(
    param_value: str,
    dataset: Dataset | None = None,
) -> PlannedSimulationUnit:
    if dataset is None:
        dataset = _make_dataset(400)
    return PlannedSimulationUnit(
        cohort=CohortSpecification(start_date=date(1871, 1, 1), id="1871-01-01"),
        parameter_config=ParameterConfiguration(
            values={"equity_allocation": param_value}
        ),
        allocation_policy=ConstantAllocationPolicy(Decimal(param_value)),
        withdrawal_policy=ConstantWithdrawalPolicy(Decimal("0.04")),
        initial_portfolio=_NULL_PORTFOLIO,
        dataset=dataset,
    )


def _make_research_plan(
    equity_values: list[Decimal],
    name: str = "test",
) -> ResearchPlan:
    full_dataset = _make_dataset(400)
    # Single cohort at origin; slice once for horizon=360
    sliced_dataset = full_dataset.slice(date(1871, 1, 1), 360)
    experiment_def = ResearchExperimentDefinition(
        name=name,
        description=f"Test: {name}",
        dataset=full_dataset,
        horizon_months=360,
        initial_wealth=Money(Decimal("1000000"), Currency.EUR),
        cohorts=(
            CohortSpecification(start_date=date(1871, 1, 1), id="1871-01-01"),
        ),
        allocation_policies=(ConstantAllocationPolicy(Decimal("0.75")),),
        withdrawal_policies=(ConstantWithdrawalPolicy(Decimal("0.04")),),
    )
    units = tuple(
        _make_plan_unit(param_value=str(v), dataset=sliced_dataset)
        for v in equity_values
    )
    return ResearchPlan(experiment_definition=experiment_def, units=units)


def _make_execution_result(
    plan: ResearchPlan,
    outcomes: list[tuple[bool, Decimal, float]],
) -> ResearchExecutionResult:
    contexts = []
    for unit in plan.units:
        cohort_id = unit.cohort.id
        assert cohort_id is not None
        contexts.append(
            SimulationContext(
                experiment_name="test",
                cohort=cohort_id,
                start_date=unit.cohort.start_date,
                horizon_months=360,
                initial_wealth=Money(Decimal("1000000"), Currency.EUR),
                initial_portfolio=unit.initial_portfolio,
                dataset=_make_dataset(400),
                allocation_policy=unit.allocation_policy,
                withdrawal_policy=unit.withdrawal_policy,
            )
        )
    engine_def = EngineExperimentDefinition(
        name="test",
        description="test",
        simulation_contexts=tuple(contexts),
    )
    sim_results = tuple(
        _make_simulation_result(success, fw, dd)
        for success, fw, dd in outcomes
    )
    engine_run = EngineExperimentRun(
        definition=engine_def,
        simulation_results=sim_results,
    )
    return ResearchExecutionResult(plan=plan, experiment_result=engine_run)


# ---------------------------------------------------------------------------
# YAML templates
# ---------------------------------------------------------------------------

_VALID_YAML_TWO_STRATEGIES = """\
metadata:
  name: "Compare Test Study"
  version: "1.0"
  description: "A test study for comparison"

dataset:
  identifier: "TEST_DATASET"

cohorts:
  type: "monthly_rolling"
  window_years: 30

allocation_policy:
  type: "ConstantAllocationPolicy"

withdrawal_policy:
  type: "FixedRealWithdrawalPolicy"
  withdrawal_rate: 0.04

parameters:
  equity_allocation: [0.60, 0.75]
"""

_VALID_YAML_THREE_STRATEGIES = """\
metadata:
  name: "Compare Test Study"
  version: "1.0"
  description: "A test study for comparison"

dataset:
  identifier: "TEST_DATASET"

cohorts:
  type: "monthly_rolling"
  window_years: 30

allocation_policy:
  type: "ConstantAllocationPolicy"

withdrawal_policy:
  type: "FixedRealWithdrawalPolicy"
  withdrawal_rate: 0.04

parameters:
  equity_allocation: [0.50, 0.60, 0.75]
"""

_VALID_YAML_SINGLE_STRATEGY = """\
metadata:
  name: "Compare Test Study"
  version: "1.0"

dataset:
  identifier: "TEST_DATASET"

cohorts:
  type: "monthly_rolling"
  window_years: 30

allocation_policy:
  type: "ConstantAllocationPolicy"
  equity_allocation: 0.75

withdrawal_policy:
  type: "FixedRealWithdrawalPolicy"
  withdrawal_rate: 0.04
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_resolve(self: DefaultDatasetResolver, identifier: str) -> Dataset:
        return _make_dataset(500)

    monkeypatch.setattr(DefaultDatasetResolver, "resolve", mock_resolve)


def _generate_outcomes(plan: ResearchPlan) -> list[tuple[bool, Decimal, float]]:
    outcomes = []
    for i in range(len(plan.units)):
        if i % 2 == 0:
            outcomes.append((True, Decimal("1200000"), 0.283))
        else:
            outcomes.append((True, Decimal("1100000"), 0.321))
    return outcomes


@pytest.fixture
def mock_sequential_execute(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock sequential_execute at the source module."""

    def _mock_sequential_execute(plan: ResearchPlan, **kwargs: Any) -> ResearchExecutionResult:
        outcomes = _generate_outcomes(plan)
        return _make_execution_result(plan, outcomes)

    import infrastructure.execution.parallel_executor as pe
    monkeypatch.setattr(pe, "sequential_execute", _mock_sequential_execute)


@pytest.fixture
def mock_parallel_execute(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock parallel_execute at the source module."""

    def _mock_parallel_execute(
        plan: ResearchPlan, max_workers: int = 1, **kwargs: Any
    ) -> ResearchExecutionResult:
        outcomes = _generate_outcomes(plan)
        return _make_execution_result(plan, outcomes)

    import infrastructure.execution.parallel_executor as pe
    monkeypatch.setattr(pe, "parallel_execute", _mock_parallel_execute)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _configs_by_key() -> dict[str, Any]:
    return {
        "equity_allocation=0.60": ParameterConfiguration(
            values={"equity_allocation": "0.60"}
        ),
        "equity_allocation=0.75": ParameterConfiguration(
            values={"equity_allocation": "0.75"}
        ),
    }


# ===================================================================
# Tests: Helper functions
# ===================================================================


class TestCanonicalParamKey:
    def test_single_axis(self) -> None:
        config = ParameterConfiguration(values={"equity_allocation": 0.75})
        assert _canonical_param_key(config) == "equity_allocation=0.75"

    def test_multi_axis_sorted(self) -> None:
        config = ParameterConfiguration(
            values={"equity_allocation": 0.75, "glidepath_duration": 10}
        )
        result = _canonical_param_key(config)
        parts = result.split(";")
        assert len(parts) == 2
        assert parts[0] == "equity_allocation=0.75"
        assert parts[1] == "glidepath_duration=10"

    def test_string_value(self) -> None:
        config = ParameterConfiguration(values={"type": "aggressive"})
        assert _canonical_param_key(config) == "type=aggressive"


class TestParseStrategyFilter:
    def test_numeric_value_parsed_as_float(self) -> None:
        assert _parse_strategy_filter("equity_allocation=0.75") == (
            "equity_allocation",
            0.75,
        )

    def test_string_value_kept(self) -> None:
        assert _parse_strategy_filter("type=aggressive") == ("type", "aggressive")

    def test_missing_equals_sign_raises(self) -> None:
        with pytest.raises(ValueError):
            _parse_strategy_filter("equity_allocation")

    def test_empty_value_raises(self) -> None:
        with pytest.raises(ValueError):
            _parse_strategy_filter("equity_allocation=")


class TestConfigMatches:
    def test_match_single_constraint(self) -> None:
        config = ParameterConfiguration(values={"equity_allocation": 0.75})
        assert _config_matches(config, [("equity_allocation", 0.75)])

    def test_mismatch_single_constraint(self) -> None:
        config = ParameterConfiguration(values={"equity_allocation": 0.60})
        assert not _config_matches(config, [("equity_allocation", 0.75)])

    def test_all_constraints_required(self) -> None:
        config = ParameterConfiguration(
            values={"equity_allocation": 0.75, "withdrawal_rate": 0.04}
        )
        constraints = [("equity_allocation", 0.75), ("withdrawal_rate", 0.05)]
        assert not _config_matches(config, constraints)


class TestExtractEvaluationResults:
    def test_count_matches_plan_units(self) -> None:
        plan = _make_research_plan([Decimal("0.60"), Decimal("0.75"), Decimal("0.61")])
        outcomes = [
            (True, Decimal("1000000"), 0.1),
            (False, Decimal("500000"), 0.5),
            (True, Decimal("1500000"), 0.2),
        ]
        result = _make_execution_result(plan, outcomes)
        evaluations = _extract_evaluation_results(
            "equity_allocation=0.75", plan, result, _configs_by_key()
        )
        # Only units whose canonical key is in configs_by_key are included
        # (0.61 is excluded); 0.60 and 0.75 are both present.
        assert len(evaluations) == 2

    def test_success_metric_true(self) -> None:
        plan = _make_research_plan([Decimal("0.75")])
        outcomes = [(True, Decimal("1000000"), 0.1)]
        result = _make_execution_result(plan, outcomes)
        evaluations = _extract_evaluation_results(
            "equity_allocation=0.75", plan, result, _configs_by_key()
        )
        assert evaluations[0].metrics["success_rate"] == Decimal("1")

    def test_success_metric_false(self) -> None:
        plan = _make_research_plan([Decimal("0.75")])
        outcomes = [(False, Decimal("500000"), 0.5)]
        result = _make_execution_result(plan, outcomes)
        evaluations = _extract_evaluation_results(
            "equity_allocation=0.75", plan, result, _configs_by_key()
        )
        assert evaluations[0].metrics["success_rate"] == Decimal("0")

    def test_final_wealth_metric(self) -> None:
        plan = _make_research_plan([Decimal("0.75")])
        outcomes = [(True, Decimal("1234567"), 0.1)]
        result = _make_execution_result(plan, outcomes)
        evaluations = _extract_evaluation_results(
            "equity_allocation=0.75", plan, result, _configs_by_key()
        )
        assert evaluations[0].metrics["final_wealth"] == Decimal("1234567")

    def test_max_drawdown_metric(self) -> None:
        plan = _make_research_plan([Decimal("0.75")])
        outcomes = [(True, Decimal("1000000"), 0.283)]
        result = _make_execution_result(plan, outcomes)
        evaluations = _extract_evaluation_results(
            "equity_allocation=0.75", plan, result, _configs_by_key()
        )
        assert evaluations[0].metrics["max_drawdown"] == Decimal("0.283")

    def test_provenance_contains_cohort(self) -> None:
        plan = _make_research_plan([Decimal("0.75")])
        outcomes = [(True, Decimal("1000000"), 0.1)]
        result = _make_execution_result(plan, outcomes)
        evaluations = _extract_evaluation_results(
            "equity_allocation=0.75", plan, result, _configs_by_key()
        )
        assert "cohort" in evaluations[0].provenance
        assert len(evaluations[0].provenance["cohort"]) == 1

    def test_provenance_contains_parameter_config(self) -> None:
        plan = _make_research_plan([Decimal("0.75")])
        outcomes = [(True, Decimal("1000000"), 0.1)]
        result = _make_execution_result(plan, outcomes)
        evaluations = _extract_evaluation_results(
            "equity_allocation=0.75", plan, result, _configs_by_key()
        )
        assert "parameter_config" in evaluations[0].provenance
        assert len(evaluations[0].provenance["parameter_config"]) == 1


# ===================================================================
# Tests: CompareCommand validation
# ===================================================================


class TestCompareCommandValidation:
    def test_missing_file_exits_two(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = main(["compare", "/tmp/nonexistent_study.yaml"])
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "not found" in err.lower()

    def test_invalid_yaml_syntax_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "bad_syntax.yaml", "{invalid: yaml: [broken}")
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "Invalid YAML" in err

    def test_single_config_study_exits_two(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A study without a parameter axis has a single configuration — not comparable."""
        study_file = _write_yaml(
            tmp_path / "study.yaml", _VALID_YAML_SINGLE_STRATEGY
        )
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "At least two configurations" in err

    def test_filter_narrows_to_one_config_exits_two(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(
            [
                "compare",
                str(study_file),
                "--strategy",
                "equity_allocation=0.75",
            ]
        )
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "At least two configurations" in err

    def test_malformed_strategy_filter_exits_two(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(
            [
                "compare",
                str(study_file),
                "--strategy",
                "equity_allocation",
            ]
        )
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "name=value" in err

    def test_non_numeric_capital_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(
            [
                "compare",
                str(study_file),
                "--initial-capital",
                "not_a_number",
            ]
        )
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "not_a_number" in err

    def test_help_text(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["compare", "--help"])
        assert exc_info.value.code == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "compare" in out.lower()
        assert "study_file" in out
        assert "--strategy" in out
        assert "--group-by" in out
        assert "--workers" in out
        assert "--initial-capital" in out
        assert "--withdrawal-policy" not in out

    def test_command_registered(self) -> None:
        assert "compare" in COMMANDS
        assert COMMANDS["compare"] is CompareCommand


# ===================================================================
# Tests: CompareCommand execution
# ===================================================================


class TestCompareCommandExecution:
    def test_two_strategies(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Strategy Comparison Complete" in out
        assert "equity_allocation=0.75" in out
        assert "equity_allocation=0.6" in out
        assert "Rank" in out

    def test_three_strategies(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(
            tmp_path / "study.yaml", _VALID_YAML_THREE_STRATEGIES
        )
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Strategy Comparison Complete" in out
        assert "Strategies:          3 (generated parameter configurations)" in out

    def test_header_reflects_configured_withdrawal_policy_type(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The comparison header names the configured policy, not a hardcoded label."""
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Withdrawal Policy:   Fixed Real 4%" in out

    def test_header_reflects_constant_withdrawal_policy_type(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """ConstantWithdrawalPolicy is labelled ``Constant``, not ``Fixed``."""
        yaml_content = """\
metadata:
  name: "Compare Test Study"
  version: "1.0"
  description: "A test study for comparison"

dataset:
  identifier: "TEST_DATASET"

cohorts:
  type: "monthly_rolling"
  window_years: 30

allocation_policy:
  type: "ConstantAllocationPolicy"

withdrawal_policy:
  type: "ConstantWithdrawalPolicy"
  withdrawal_rate: 0.04

parameters:
  equity_allocation: [0.60, 0.75]
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_content)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Withdrawal Policy:   Constant 4%" in out

    def test_ranked_by_success_rate(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Higher success rate strategy ranked first."""

        def _mock_exec(plan: ResearchPlan, **kwargs: Any) -> ResearchExecutionResult:
            outcomes = [(True, Decimal("1200000"), 0.283)] * len(plan.units)
            return _make_execution_result(plan, outcomes)

        import cli.commands.compare_command as cc_mod
        import infrastructure.execution.parallel_executor as pe

        strategy_data: dict[str, list[tuple[bool, Decimal, float]]] = {
            "equity_allocation=0.75": [
                (True, Decimal("1200000"), 0.283),
                (True, Decimal("1300000"), 0.250),
            ],
            "equity_allocation=0.6": [
                (True, Decimal("1100000"), 0.321),
                (False, Decimal("800000"), 0.400),
            ],
        }

        def _mock_extract(
            label: str,
            plan: ResearchPlan,
            result: ResearchExecutionResult,
            configs_by_key: dict[str, Any],
        ) -> list[EvaluationResult]:
            data = strategy_data.get(label, [])
            evals = []
            for success, fw, dd in data:
                evals.append(
                    EvaluationResult(
                        label=label,
                        metrics={
                            "success_rate": Decimal("1") if success else Decimal("0"),
                            "final_wealth": fw,
                            "max_drawdown": Decimal(str(dd)),
                        },
                        provenance={
                            "cohort": ["1871-01-01"],
                            "parameter_config": [label],
                        },
                    )
                )
            return evals

        monkeypatch.setattr(cc_mod, "_extract_evaluation_results", _mock_extract)
        monkeypatch.setattr(pe, "sequential_execute", _mock_exec)

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        # 75/25 has 100% success (2/2), 60/40 has 50% (1/2)
        # equity_allocation=0.75 should be ranked 1st
        rank_lines = [line for line in out.split("\n") if line.strip().startswith("1")]
        assert any("equity_allocation=0.75" in line for line in rank_lines)

    def test_global_group_by_default(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Group: global" in out
        assert "Total Evaluations Per Strategy:" in out

    def test_cohort_group_by(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(
            [
                "compare",
                str(study_file),
                "--group-by",
                "cohort",
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Group: 1871-01-01" in out

    def test_parameter_config_group_by(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(
            tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES
        )
        rc = main(
            [
                "compare",
                str(study_file),
                "--group-by",
                "parameter_config",
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "equity_allocation" in out

    def test_workers_flag(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_parallel_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(
            [
                "compare",
                str(study_file),
                "--workers",
                "4",
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Workers:             4" in out

    def test_custom_initial_capital(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(
            [
                "compare",
                str(study_file),
                "--initial-capital",
                "500000",
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Strategy Comparison Complete" in out

    def test_execution_failure_exits_one(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _mock_exec_fail(
            plan: ResearchPlan, **kwargs: Any
        ) -> ResearchExecutionResult:
            raise RuntimeError("Execution failed")

        import infrastructure.execution.parallel_executor as pe

        monkeypatch.setattr(pe, "sequential_execute", _mock_exec_fail)

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.ERROR
        err = capsys.readouterr().err
        assert "Execution failed" in err


# ===================================================================
# Tests: StrategyComparator integration
# ===================================================================


class TestStrategyComparatorIntegration:
    def test_strategy_comparator_called_with_correct_types(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Rank" in out
        assert "Success Rate" in out
        assert "Mean Final Wealth" in out
        assert "Max Drawdown" in out

    def test_report_output_contains_rank(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Rank" in out
        assert "Diagnostics" in out


# ===================================================================
# Tests: Persistence
# ===================================================================


class TestCompareCommandPersistence:
    def test_strategies_persist_to_database(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db_path = str(tmp_path / "test_compare.db")
        monkeypatch.setattr(
            "cli.commands.compare_command._DEFAULT_DB_PATH", db_path
        )

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        # Verify database was created
        assert Path(db_path).exists()

    def test_database_unreachable_does_not_crash(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_sequential_execute: None,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db_path = str(tmp_path / "nonexistent_dir" / "studies.db")
        monkeypatch.setattr(
            "cli.commands.compare_command._DEFAULT_DB_PATH", db_path
        )

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML_TWO_STRATEGIES)
        rc = main(["compare", str(study_file)])
        assert rc == ExitCode.SUCCESS
        err = capsys.readouterr().err
        assert "WARNING" in err or err == ""
