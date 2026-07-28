"""Tests for RunCommand — YAML experiment definition execution."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from cli.commands import COMMANDS
from cli.commands.run_command import RunCommand
from cli.error_handling import ExitCode
from cli.main import main
from engine.domain import AssetClass, Dataset, MarketSnapshot
from infrastructure.persistence.codecs import DefaultDatasetResolver

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
  name: "Test Study"
  version: "1.0"
  description: "A test study for execution"

dataset:
  identifier: "TEST_DATASET"

cohorts:
  type: "monthly_rolling"
  window_years: 30

allocation_policies:
  - name: "Static 75/25"
    type: "ConstantAllocationPolicy"
    equity_ratio: 0.75
  - name: "Static 60/40"
    type: "ConstantAllocationPolicy"
    equity_ratio: 0.60

withdrawal_policy:
  type: "ConstantInflationAdjustedWithdrawalPolicy"
  withdrawal_rate: 0.04

parameters:
  equity_allocation: [0.50, 0.75]
  glidepath_duration: [5, 10]
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_resolve(self: DefaultDatasetResolver, identifier: str) -> Dataset:
        return _make_dataset(500)

    monkeypatch.setattr(DefaultDatasetResolver, "resolve", mock_resolve)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRunCommand:
    def test_dry_run_exits_zero(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--dry-run", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Study:" in out
        assert "Cohorts:" in out
        assert "Parameters:" in out
        assert "Policies:" in out
        assert "Total Units:" in out
        assert "DRY RUN" in out

    def test_missing_file_exits_two(
        self,
        capsys: pytest.CaptureFixture,
    ) -> None:
        rc = main(["run", "/tmp/nonexistent_study.yaml"])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out
        assert "not found" in out.lower()

    def test_invalid_yaml_syntax_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "bad_syntax.yaml", "{invalid: yaml: [broken}")
        rc = main(["run", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out
        assert "Invalid YAML" in out

    def test_invalid_yaml_not_a_mapping_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "scalar.yaml", "just a string")
        rc = main(["run", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_invalid_dataset_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_invalid_experiment_definition_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def mock_resolve(self: DefaultDatasetResolver, identifier: str) -> Dataset:
            return _make_dataset(5)

        monkeypatch.setattr(DefaultDatasetResolver, "resolve", mock_resolve)

        yaml_content = """\
metadata:
  name: "Test"
dataset:
  identifier: "TEST"
cohorts:
  window_years: 30
allocation_policies:
  - name: "p1"
    equity_ratio: 0.75
withdrawal_policy:
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.50]
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_content)
        rc = main(["run", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR

    def test_dry_run_prints_plan_details(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--dry-run", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out

        assert "Test Study" in out
        assert "v1.0" in out
        assert "monthly rolling" in out
        assert "simulations" in out
        assert "allocation" in out
        assert "withdrawal" in out
        assert "No simulations executed" in out

    def test_help_text(
        self,
        capsys: pytest.CaptureFixture,
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["run", "--help"])
        assert exc_info.value.code == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "run" in out.lower()
        assert "study_file" in out
        assert "--dry-run" in out
        assert "--workers" in out

    def test_command_registered(self) -> None:
        assert "run" in COMMANDS
        assert COMMANDS["run"] is RunCommand

    def test_dry_run_without_version(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        yaml_content = """\
metadata:
  name: "No Version Study"
dataset:
  identifier: "TEST"
cohorts:
  window_years: 30
allocation_policies:
  - name: "p1"
    equity_ratio: 0.75
withdrawal_policy:
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.50]
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_content)
        rc = main(["run", "--dry-run", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "No Version Study" in out
        assert "DRY RUN" in out


class TestRunCommandWorkers:
    def test_workers_1_dry_run(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--dry-run", "--workers", "1", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "DRY RUN" in out

    def test_workers_4_dry_run(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--dry-run", "--workers", "4", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "DRY RUN" in out


class TestRunCommandEdgeCases:
    def test_horizon_negative_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        yaml_content = """\
metadata:
  name: "Test"
dataset:
  identifier: "TEST"
cohorts:
  window_years: -5
allocation_policies:
  - name: "p1"
    equity_ratio: 0.75
withdrawal_policy:
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.50]
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_content)
        rc = main(["run", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_empty_policies_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        yaml_content = """\
metadata:
  name: "Test"
dataset:
  identifier: "TEST"
cohorts:
  window_years: 30
allocation_policies: []
withdrawal_policy:
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.50]
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_content)
        rc = main(["run", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
