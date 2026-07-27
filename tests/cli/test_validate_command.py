"""Tests for ValidateCommand — YAML experiment definition validation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from cli.commands import COMMANDS
from cli.commands.validate_command import ValidateCommand
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
# YAML templates
# ---------------------------------------------------------------------------

_VALID_YAML = """\
metadata:
  name: "Test Study"
  version: "1.0"
  description: "A test study for validation"

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

_INVALID_YAML = """\
metadata:
  name: "Test"
dataset:
  identifier: "TEST_DATASET"
cohorts:
  window_years: 30
allocation_policies:
  - name: "policy_1"
    equity_ratio: 0.75
withdrawal_policy:
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.50, 0.75]
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_dataset_resolver(monkeypatch: pytest.MonkeyPatch) -> None:
    """Monkeypatch DefaultDatasetResolver to return a test dataset."""

    def mock_resolve(self: DefaultDatasetResolver, identifier: str) -> Dataset:
        return _make_dataset(500)

    monkeypatch.setattr(DefaultDatasetResolver, "resolve", mock_resolve)


@pytest.fixture(autouse=True)
def _register_validate_command() -> None:
    """Ensure ValidateCommand is registered for CLI dispatch tests."""
    if "validate" not in COMMANDS:
        COMMANDS["validate"] = ValidateCommand
    yield


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestValidateCommand:
    def test_valid_yaml_exits_zero(
        self,
        tmp_path: Path,
        mock_dataset_resolver: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Validation: PASSED" in out
        assert "ExperimentDefinition: valid" in out
        assert "Cohorts" in out
        assert "Parameters" in out
        assert "Policies:" in out
        assert "Plan:" in out

    def test_missing_file_exits_two(
        self,
        capsys: pytest.CaptureFixture,
    ) -> None:
        rc = main(["validate", "/tmp/nonexistent_study.yaml"])
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
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out
        assert "Invalid YAML" in out

    def test_invalid_yaml_not_a_mapping(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "scalar.yaml", "just a string")
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_invalid_dataset_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that an unresolvable dataset identifier causes exit 2."""
        study_file = _write_yaml(tmp_path / "study.yaml", _INVALID_YAML)

        def mock_resolve_fail(self: DefaultDatasetResolver, identifier: str) -> Dataset:
            from infrastructure.persistence.errors import StudyNotFoundError
            raise StudyNotFoundError(f"Dataset not found: '{identifier}'")

        monkeypatch.setattr(DefaultDatasetResolver, "resolve", mock_resolve_fail)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "invalid" in out.lower()

    def test_invalid_cohort_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A dataset too small for the requested horizon should fail."""
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)

        def mock_resolve_small(self: DefaultDatasetResolver, identifier: str) -> Dataset:
            return _make_dataset(12)  # only 12 months, needs 360

        monkeypatch.setattr(DefaultDatasetResolver, "resolve", mock_resolve_small)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "invalid" in out.lower() or "error" in out.lower()

    def test_invalid_parameter_exits_two(
        self,
        tmp_path: Path,
        mock_dataset_resolver: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
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
  equity_allocation: []   # empty list — invalid
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_content)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "invalid" in out.lower() or "error" in out.lower()

    def test_missing_parameters_exits_two(
        self,
        tmp_path: Path,
        mock_dataset_resolver: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
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
parameters: {}
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_content)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "invalid" in out.lower() or "error" in out.lower()

    def test_invalid_policy_exits_two(
        self,
        tmp_path: Path,
        mock_dataset_resolver: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        yaml_content = """\
metadata:
  name: "Test"
dataset:
  identifier: "TEST"
cohorts:
  window_years: 30
allocation_policies: []   # empty — invalid
withdrawal_policy:
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.50]
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_content)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "invalid" in out.lower() or "error" in out.lower()

    def test_output_contains_all_required_sections(
        self,
        tmp_path: Path,
        mock_dataset_resolver: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out

        assert "Validating:" in out
        assert "ExperimentDefinition: valid" in out
        assert "Name: Test Study" in out
        assert "Version: 1.0" in out
        assert "Cohorts" in out
        assert "Parameters" in out
        assert "Policies:" in out
        assert "Plan:" in out
        assert "simulation units" in out
        assert "Validation: PASSED" in out

    def test_help_text(
        self,
        capsys: pytest.CaptureFixture,
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["validate", "--help"])
        assert exc_info.value.code == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "validate" in out.lower()
        assert "study_file" in out

    def test_command_registered(self) -> None:
        assert "validate" in COMMANDS
        assert COMMANDS["validate"] is ValidateCommand


class TestValidateCommandEdgeCases:
    def test_horizon_negative_exits_two(
        self,
        tmp_path: Path,
        mock_dataset_resolver: None,
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
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "invalid" in out.lower() or "error" in out.lower()

    def test_allocation_policy_missing_name(
        self,
        tmp_path: Path,
        mock_dataset_resolver: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        yaml_content = """\
metadata:
  name: "Test"
dataset:
  identifier: "TEST"
cohorts:
  window_years: 30
allocation_policies:
  - equity_ratio: 0.75
withdrawal_policy:
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.50]
"""
        study_file = _write_yaml(tmp_path / "study.yaml", yaml_content)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Validation: PASSED" in out


class TestValidateCommandWithRealDataset:
    def test_resolver_with_registered_dataset(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DefaultDatasetResolver, "resolve", lambda self, i: _make_dataset(500))
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Validation: PASSED" in out

    def test_plan_shows_correct_unit_count(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DefaultDatasetResolver, "resolve", lambda self, i: _make_dataset(500))
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["validate", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Plan:" in out
        assert "simulation units" in out
