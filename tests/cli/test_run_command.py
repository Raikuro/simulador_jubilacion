"""Tests for RunCommand — YAML experiment definition execution."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from cli.commands import COMMANDS
from cli.commands.run_command import RunCommand, _resolve_workers_arg
from cli.error_handling import ExitCode
from cli.main import main
from engine.domain import AssetClass, Dataset, MarketSnapshot
from engine.domain.model.money import Currency, Money
from infrastructure.persistence.codecs import DefaultDatasetResolver
from research.domain.plan import ResearchPlan
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

# Single-config, single-horizon study: exactly one unit per cohort, so every
# chaining family is a singleton and ``derived_results == 0``.  The default
# execution gate therefore keeps it on the independent Reference dispatch.
_VALID_SINGLE_UNIT_YAML = """\
metadata:
  name: "Test Single Unit Study"
  version: "1.0"
dataset:
  identifier: "TEST_DATASET"
cohorts:
  type: "monthly_rolling"
  window_years: 30
allocation_policies:
  - name: "Static 75/25"
    type: "ConstantAllocationPolicy"
    equity_ratio: 0.75
withdrawal_policy:
  type: "ConstantInflationAdjustedWithdrawalPolicy"
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.75]
"""

# Multi-horizon grid study: every cohort carries two horizons whose datasets
# are identity prefixes of the longest, so ``derived_results > 0`` and the
# default routes to the chained Reference executor.
_VALID_GRID_YAML = """\
metadata:
  name: "Test Grid Study"
  version: "1.0"
  description: "A multi-horizon grid study for execution"

dataset:
  identifier: "TEST_DATASET"

cohorts:
  type: "monthly_rolling"
  window_years: 4

allocation_policies:
  - name: "Static 75/25"
    type: "ConstantAllocationPolicy"
    equity_ratio: 0.75

withdrawal_policy:
  type: "FixedRealWithdrawalPolicy"
  withdrawal_rate: 0.04

parameters:
  horizon_years: [3, 4]
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
        capsys: pytest.CaptureFixture[str],
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
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = main(["run", "/tmp/nonexistent_study.yaml"])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out
        assert "not found" in out.lower()

    def test_invalid_yaml_syntax_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
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
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "scalar.yaml", "just a string")
        rc = main(["run", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_invalid_dataset_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_invalid_experiment_definition_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
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
        capsys: pytest.CaptureFixture[str],
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
        capsys: pytest.CaptureFixture[str],
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
        capsys: pytest.CaptureFixture[str],
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
        capsys: pytest.CaptureFixture[str],
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
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--dry-run", "--workers", "4", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "DRY RUN" in out


class TestResolveWorkersArg:
    """Direct unit tests for the CLI ``--workers`` value resolver."""

    def test_max_resolves_to_every_logical_cpu(self) -> None:
        assert _resolve_workers_arg("max") == (os.cpu_count() or 1)

    def test_max_is_case_insensitive(self) -> None:
        assert _resolve_workers_arg("MAX") == (os.cpu_count() or 1)
        assert _resolve_workers_arg("  Max ") == (os.cpu_count() or 1)

    def test_positive_integer_passes_through(self) -> None:
        assert _resolve_workers_arg("1") == 1
        assert _resolve_workers_arg("16") == 16
        assert _resolve_workers_arg(" 8 ") == 8

    def test_zero_and_negative_integers_rejected(self) -> None:
        with pytest.raises(ValueError):
            _resolve_workers_arg("0")
        with pytest.raises(ValueError):
            _resolve_workers_arg("-1")

    def test_non_numeric_values_rejected(self) -> None:
        with pytest.raises(ValueError):
            _resolve_workers_arg("abc")
        with pytest.raises(ValueError):
            _resolve_workers_arg("")
        with pytest.raises(ValueError):
            _resolve_workers_arg("3.5")


class TestRunCommandEdgeCases:
    def test_horizon_negative_exits_two(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
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
        capsys: pytest.CaptureFixture[str],
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
        out = capsys.readouterr().out
        assert "ERROR" in out


def _make_fake_executor_result(plan: ResearchPlan, **kwargs: object) -> ResearchExecutionResult:
    """Build a ResearchExecutionResult that satisfies the completion summary."""
    from datetime import date

    from engine.application.simulation import (
        ExperimentDefinition as EngineExperimentDefinition,
        ExperimentRun,
        SimulationResult,
        SimulationStatistics,
        SimulationTimeline,
    )
    from engine.application.simulation_context import SimulationContext

    units = plan.units
    results = tuple(
        SimulationResult(
            timeline=SimulationTimeline(monthly_results=()),
            statistics=SimulationStatistics(
                final_wealth=Money(Decimal("1000000"), Currency.EUR),
                max_drawdown=0.0,
                success=True,
                failure_month=None,
                months_simulated=360,
                execution_time_seconds=0.01,
            ),
        )
        for _ in units
    )
    contexts = tuple(
        SimulationContext(
            experiment_name="fake",
            cohort="c",
            start_date=date(2000, 1, 1),
            horizon_months=360,
            initial_wealth=Money(Decimal("1000000"), Currency.EUR),
            initial_portfolio=unit.initial_portfolio,
            dataset=unit.dataset,
            allocation_policy=unit.allocation_policy,
            withdrawal_policy=unit.withdrawal_policy,
        )
        for unit in units
    )
    engine_def = EngineExperimentDefinition(
        name=plan.experiment_definition.name,
        description="fake",
        simulation_contexts=contexts,
    )
    return ResearchExecutionResult(
        plan=plan,
        experiment_result=ExperimentRun(definition=engine_def, simulation_results=results),
    )


class TestExecutionModeSelection:
    """The CLI selects an exact execution mode explicitly and rejects
    incompatible combinations rather than silently picking one.

    Default (no flag) = Reference Chained for plans that actually benefit from
    horizon chaining (``derived_results > 0``); single-horizon / non-chainable
    plans degrade to the independent Reference dispatch.  ``--reference-chained``
    stays an explicit force; ``--reference-independent`` requests the canonical
    oracle; ``--fast-path`` stays a separate opt-in."""

    def _capture(
        self, monkeypatch: pytest.MonkeyPatch, capture: dict[str, object], parallel: bool
    ) -> None:
        import infrastructure.execution.parallel_executor as pe

        if parallel:

            def fake_parallel(
                plan: ResearchPlan,
                max_workers: int,
                simulation_executor: object = None,
                **kwargs: object,
            ) -> ResearchExecutionResult:
                capture["executor"] = simulation_executor
                capture["workers"] = max_workers
                return _make_fake_executor_result(plan, **kwargs)

            monkeypatch.setattr(pe, "parallel_execute", fake_parallel)
        else:

            def fake_sequential(
                plan: ResearchPlan,
                simulation_executor: object = None,
                **kwargs: object,
            ) -> ResearchExecutionResult:
                capture["executor"] = simulation_executor
                return _make_fake_executor_result(plan, **kwargs)

            monkeypatch.setattr(pe, "sequential_execute", fake_sequential)

    def _capture_chained(
        self, monkeypatch: pytest.MonkeyPatch, capture: dict[str, object]
    ) -> None:
        """Patch the slice-dispatch call site used by ``execute_reference_chained``.

        ``reference_chaining`` binds ``parallel_execute`` at import time, so
        patching the executor module's attribute does not intercept the slice
        dispatch.  Patch the module-local name instead.
        """
        import infrastructure.execution.reference_chaining as rc

        def fake_slice_parallel(
            plan: ResearchPlan,
            max_workers: int,
            simulation_executor: object = None,
            **kwargs: object,
        ) -> ResearchExecutionResult:
            capture["executor"] = simulation_executor
            capture["workers"] = max_workers
            return _make_fake_executor_result(plan, **kwargs)

        monkeypatch.setattr(rc, "parallel_execute", fake_slice_parallel)

    def test_default_single_horizon_plan_uses_independent_reference(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A single-config, single-horizon plan without any flag stays on the
        independent Reference dispatch: no horizon family would chain
        (``derived_results == 0``), so chained grouping/slicing overhead is
        never paid."""
        capture: dict[str, object] = {}
        self._capture(monkeypatch, capture, parallel=False)
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_SINGLE_UNIT_YAML)
        rc = main(["run", "--no-persist", str(study_file)])
        assert rc == ExitCode.SUCCESS
        assert capture["executor"] is None

    def test_default_chainable_grid_uses_chained_executor(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A multi-horizon grid without any flag routes through the chained
        Reference executor by default (it benefits from horizon chaining)."""
        from infrastructure.execution.reference_chaining import (
            ChainedReferenceSimulationExecutor,
        )

        capture: dict[str, object] = {}
        self._capture_chained(monkeypatch, capture)
        study_file = _write_yaml(tmp_path / "grid.yaml", _VALID_GRID_YAML)
        rc = main(["run", "--no-persist", str(study_file)])
        assert rc == ExitCode.SUCCESS
        assert isinstance(capture["executor"], ChainedReferenceSimulationExecutor)

    def test_reference_independent_uses_independent_executor(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """--reference-independent forces the independent Reference even for a
        chainable grid, making the canonical oracle explicitly selectable."""
        capture: dict[str, object] = {}
        self._capture(monkeypatch, capture, parallel=False)
        study_file = _write_yaml(tmp_path / "grid.yaml", _VALID_GRID_YAML)
        rc = main(["run", "--reference-independent", "--no-persist", str(study_file)])
        assert rc == ExitCode.SUCCESS
        assert capture["executor"] is None

    def test_reference_chained_conflicts_with_reference_independent(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Reference-chained + reference-independent is rejected explicitly."""
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "run",
                "--reference-chained",
                "--reference-independent",
                "--no-persist",
                str(study_file),
            ]
        )
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "--reference-chained" in out
        assert "--reference-independent" in out

    def test_reference_chained_uses_chained_executor(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """--reference-chained selects ChainedReferenceSimulationExecutor."""
        from infrastructure.execution.reference_chaining import (
            ChainedReferenceSimulationExecutor,
        )

        capture: dict[str, object] = {}
        self._capture_chained(monkeypatch, capture)
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--reference-chained", "--no-persist", str(study_file)])
        assert rc == ExitCode.SUCCESS
        assert isinstance(capture["executor"], ChainedReferenceSimulationExecutor)

    def test_fast_path_remains_separate_opt_in(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """--fast-path still selects the fast-path executor, independently."""
        from cli.fast_path import ChainedFastPathSimulationExecutor

        capture: dict[str, object] = {}
        self._capture(monkeypatch, capture, parallel=False)
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--fast-path", "--no-persist", str(study_file)])
        assert rc == ExitCode.SUCCESS
        assert isinstance(capture["executor"], ChainedFastPathSimulationExecutor)

    def test_reference_chained_conflicts_with_fast_path(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Fast-path + reference-chained is rejected explicitly at pre-flight."""
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            ["run", "--reference-chained", "--fast-path", "--no-persist", str(study_file)]
        )
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "--reference-chained" in out
        assert "--fast-path" in out

    def test_reference_chained_workers_parallel_preserved(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """With --workers N, slice dispatch passes the chained executor + N."""
        from infrastructure.execution.reference_chaining import (
            ChainedReferenceSimulationExecutor,
        )

        capture: dict[str, object] = {}
        self._capture_chained(monkeypatch, capture)
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "run",
                "--reference-chained",
                "--workers",
                "3",
                "--no-persist",
                str(study_file),
            ]
        )
        assert rc == ExitCode.SUCCESS
        assert isinstance(capture["executor"], ChainedReferenceSimulationExecutor)
        assert capture["workers"] == 3

    def test_reference_chained_reports_coverage(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The completion summary reports reference-chained chaining counts."""
        import infrastructure.execution.parallel_executor as pe

        monkeypatch.setattr(pe, "sequential_execute", _make_fake_executor_result)
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--reference-chained", "--no-persist", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Reference Chained:" in out
        assert "Chained Groups:" in out
        assert "Longest Path:" in out
        assert "Month-Work:" in out


class TestPersistenceControls:
    def test_summary_only_conflicts_with_persist(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--summary-only", "--persist-study", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        assert "--summary-only" in capsys.readouterr().out

    def test_fast_path_conflicts_with_persist(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """F1: --fast-path must not silently persist empty timelines."""
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--fast-path", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "--fast-path" in out

    def test_fast_path_with_no_persist_reports_coverage(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """F6: the completion summary reports fast-path vs reference coverage."""
        import unittest.mock

        import infrastructure.execution.parallel_executor as pe

        repo_cls = unittest.mock.Mock()
        monkeypatch.setattr("cli.commands.run_command.SQLiteRepository", repo_cls)
        monkeypatch.setattr(pe, "sequential_execute", _make_fake_executor_result)

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--fast-path", "--no-persist", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Fast Path:" in out
        assert "Reference Path:" in out
        repo_cls.assert_not_called()

    def test_validate_requires_fast_path(
        self,
        tmp_path: Path,
        mock_dataset: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """F7: --validate without --fast-path is a pre-flight error."""
        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--validate", str(study_file)])
        assert rc == ExitCode.VALIDATION_ERROR
        assert "--fast-path" in capsys.readouterr().out

    def test_fast_path_validate_runs_and_reports(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """F7: --fast-path --validate runs the pre-flight and reports coverage."""
        import unittest.mock

        import cli.fast_path as fp
        import infrastructure.execution.parallel_executor as pe

        repo_cls = unittest.mock.Mock()
        monkeypatch.setattr("cli.commands.run_command.SQLiteRepository", repo_cls)
        monkeypatch.setattr(pe, "sequential_execute", _make_fake_executor_result)
        monkeypatch.setattr(fp, "sequential_execute", _make_fake_executor_result)
        monkeypatch.setattr(
            fp,
            "select_validation_units",
            lambda plan, max_units=8: tuple(plan.units[:2]),
        )

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(
            [
                "run",
                "--fast-path",
                "--validate",
                "--no-persist",
                str(study_file),
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Validation:" in out
        assert "fast-path unit(s)" in out
        repo_cls.assert_not_called()

    def test_no_persist_skips_database(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        import unittest.mock

        import infrastructure.execution.parallel_executor as pe

        repo_cls = unittest.mock.Mock()
        monkeypatch.setattr("cli.commands.run_command.SQLiteRepository", repo_cls)
        monkeypatch.setattr(pe, "sequential_execute", _make_fake_executor_result)

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", "--no-persist", "--summary-only", str(study_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Units Run:" in out
        repo_cls.assert_not_called()

    def test_default_persists(
        self,
        tmp_path: Path,
        mock_dataset: None,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        import unittest.mock

        import infrastructure.execution.parallel_executor as pe

        repo_cls = unittest.mock.Mock()
        repo = unittest.mock.Mock()
        repo.save_experiment.return_value = "exp-1"
        repo.save_plan.return_value = "plan-1"
        repo.save_execution_result.return_value = "res-1"
        repo_cls.return_value = repo
        monkeypatch.setattr("cli.commands.run_command.SQLiteRepository", repo_cls)
        monkeypatch.setattr(pe, "sequential_execute", _make_fake_executor_result)

        study_file = _write_yaml(tmp_path / "study.yaml", _VALID_YAML)
        rc = main(["run", str(study_file)])
        assert rc == ExitCode.SUCCESS
        repo_cls.assert_called_once()
        repo.save_experiment.assert_called_once()
        repo.save_plan.assert_called_once()
        repo.save_execution_result.assert_called_once()

    def test_progress_display_silent_on_non_tty(self) -> None:
        import io

        from cli.progress import ProgressDisplay

        stream = io.StringIO()
        display = ProgressDisplay(total=10, stream=stream)
        assert display.enabled is False
        display.update(5, 10)
        display.finish()
        assert stream.getvalue() == ""
