"""Tests for OptimizeCommand — optimal withdrawal rate via SWROptimizer."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from cli.commands import COMMANDS
from cli.commands.optimize_command import OptimizeCommand
from cli.error_handling import ExitCode
from cli.main import main
from engine.domain import AssetClass, Dataset, MarketSnapshot
from infrastructure.persistence.codecs import DefaultDatasetResolver
from research.optimization.swr_optimizer import (
    OptimizerOutcome,
    SWROptimizer,
)

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
# YAML template
# ---------------------------------------------------------------------------

_VALID_YAML = """\
metadata:
  name: "Optimize Test Study"
  version: "1.0"
  description: "A test study for optimization"

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

_VALID_YAML_AXIS_ALLOCATION = """\
metadata:
  name: "Optimize Test Study"
  version: "1.0"

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
  equity_allocation: [0.75]
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_resolve(self: DefaultDatasetResolver, identifier: str) -> Dataset:
        return _make_dataset(500)

    monkeypatch.setattr(DefaultDatasetResolver, "resolve", mock_resolve)


@pytest.fixture
def mock_optimizer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock SWROptimizer.optimize to return a fixed outcome without real execution."""

    def mock_optimize(
        self: SWROptimizer,
        evaluator: object,
        domain_min: Decimal,
        domain_max: Decimal,
        precision: Decimal = Decimal("0.0001"),
    ) -> OptimizerOutcome:
        return OptimizerOutcome(
            candidate_value=Decimal("0.0395"),
            provenance={
                "candidate": "0.0395",
                "success_rate": "0.951",
                "success_count": 137,
                "total_units": 144,
            },
            diagnostic="Successfully found SWR: 0.0395",
        )

    monkeypatch.setattr(SWROptimizer, "optimize", mock_optimize)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestOptimizeCommandValidation:
    def test_missing_file_exits_two(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = main(["optimize", "/tmp/nonexistent_study.yaml"])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().err
        assert "ERROR" in out
        assert "not found" in out.lower()

    def test_invalid_yaml_syntax_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "bad_syntax.yaml", "{invalid: yaml: [broken}")
        rc = main(["optimize", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().err
        assert "ERROR" in out
        assert "Invalid YAML" in out

    def test_withdrawal_rate_axis_exits_two(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        yaml_with_rate_axis = """\
metadata:
  name: "Test"
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
parameters:
  equity_allocation: [0.75]
  withdrawal_rate: [0.03, 0.04]
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_with_rate_axis)
        rc = main(["optimize", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "withdrawal_rate" in err

    def test_multi_value_axis_exits_two(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        yaml_multi_axis = """\
metadata:
  name: "Test"
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
  equity_allocation: [0.50, 0.75]
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_multi_axis)
        rc = main(["optimize", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "single configuration" in err

    def test_missing_concrete_allocation_exits_two(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        yaml_no_alloc = """\
metadata:
  name: "Test"
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
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_no_alloc)
        rc = main(["optimize", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "equity_allocation" in err

    def test_target_success_rate_above_one_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "optimize",
                str(study_file),
                "--target-success-rate",
                "1.5",
            ]
        )
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "1.5" in err

    def test_target_success_rate_below_zero_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "optimize",
                str(study_file),
                "--target-success-rate",
                "-0.1",
            ]
        )
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "-0.1" in err

    def test_initial_capital_non_numeric_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "optimize",
                str(study_file),
                "--initial-capital",
                "not_a_number",
            ]
        )
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "not_a_number" in err

    def test_tolerance_non_numeric_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "optimize",
                str(study_file),
                "--tolerance",
                "not_a_number",
            ]
        )
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "not_a_number" in err

    def test_invalid_dataset_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["optimize", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        err = capsys.readouterr().err
        assert "ERROR" in err

    def test_help_text(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["optimize", "--help"])
        assert exc_info.value.code == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "optimize" in out.lower()
        assert "study_file" in out
        assert "--target-success-rate" in out
        assert "--initial-capital" in out
        assert "--workers" in out
        assert "--tolerance" in out
        assert "--output-dir" in out
        assert "--allocation-policy" not in out


class TestOptimizeCommandExecution:
    def test_valid_yaml_exits_zero(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_optimizer: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["optimize", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Optimization Complete" in out
        assert "Optimal Withdrawal Rate" in out

    def test_optimal_rate_printed(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_optimizer: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["optimize", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Optimal Withdrawal Rate" in out
        assert "%" in out

    def test_allocation_from_single_value_axis(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_optimizer: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(
            tmp_path / "study.yaml", _VALID_YAML_AXIS_ALLOCATION
        )
        rc = main(["optimize", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "equity_allocation=0.75" in out

    def test_custom_target_success_rate(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_optimizer: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "optimize",
                str(study_file),
                "--target-success-rate",
                "0.99",
                "--tolerance",
                "0.01",
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Optimization Complete" in out

    def test_custom_initial_capital(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_optimizer: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "optimize",
                str(study_file),
                "--initial-capital",
                "500000",
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Optimization Complete" in out

    def test_workers_flag(
        self,
        tmp_path: Path,
        mock_dataset: None,
        mock_optimizer: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "optimize",
                str(study_file),
                "--workers",
                "4",
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Optimization Complete" in out

    def test_command_registered(self) -> None:
        assert "optimize" in COMMANDS
        assert COMMANDS["optimize"] is OptimizeCommand

    def test_no_candidate_satisfies_criteria(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def mock_optimize_no_candidate(
            self: SWROptimizer,
            evaluator: object,
            domain_min: Decimal,
            domain_max: Decimal,
            precision: Decimal = Decimal("0.0001"),
        ) -> OptimizerOutcome:
            return OptimizerOutcome(
                candidate_value=None,
                provenance={},
                diagnostic="No candidate satisfied success criteria.",
            )

        monkeypatch.setattr(SWROptimizer, "optimize", mock_optimize_no_candidate)

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["optimize", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "No withdrawal rate satisfies criteria" in out


class TestOptimizeCommandPersistence:
    def test_study_persists_to_database(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db_path = str(tmp_path / "test_optimize.db")

        def mock_optimize_with_persistence(
            self: SWROptimizer,
            evaluator: object,
            domain_min: Decimal,
            domain_max: Decimal,
            precision: Decimal = Decimal("0.0001"),
        ) -> OptimizerOutcome:
            return OptimizerOutcome(
                candidate_value=Decimal("0.0395"),
                provenance={
                    "candidate": "0.0395",
                    "success_rate": "0.951",
                    "success_count": 137,
                    "total_units": 144,
                },
                diagnostic="Successfully found SWR: 0.0395",
            )

        monkeypatch.setattr(SWROptimizer, "optimize", mock_optimize_with_persistence)
        monkeypatch.setattr("cli.commands.optimize_command._DEFAULT_DB_PATH", db_path)

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["optimize", str(study_file)])
        (out, err) = capsys.readouterr()
        assert rc == ExitCode.SUCCESS
        assert "Study ID:" in out or "experiment saved" in err
