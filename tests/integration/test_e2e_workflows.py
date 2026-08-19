"""P4.2 – End-to-End Workflow Validation Tests.

Validates complete CLI workflows through the public CLI interface,
verifying behaviour rather than internal implementation details.

Each test class covers a distinct workflow area.  Tests reuse the
P4.1 integration framework (conftest fixtures, helpers) and add
only the E2E-specific scaffolding needed for fast, reliable execution.

The actual simulation engine is already validated by 660+ unit tests;
this package tests the integration of CLI commands, persistence,
configuration, and error handling as a cohesive whole.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from cli.error_handling import ExitCode
from cli.main import main
from engine.domain.model.asset import AssetClass
from engine.domain.model.dataset import Dataset
from engine.domain.model.market_snapshot import MarketSnapshot
from infrastructure.persistence import create_persistence_context
from infrastructure.persistence.codecs import DefaultDatasetResolver
from infrastructure.persistence.sqlite_repository import (
    ExperimentIdentity,
    PersistenceReconstructionContext,
    SQLiteRepository,
)

from .helpers import (
    create_study_yaml,
    make_execution_result,
    make_experiment,
    make_plan,
)

# ---------------------------------------------------------------------------
# Constants – keep execution light (15-month dataset, 1-year horizon)
# ---------------------------------------------------------------------------

_E2E_ASSET = AssetClass(id="acwi", name="ACWI", description="Global equities")
_E2E_DATASET_ID = "E2E_TEST_v1"
_E2E_HORIZON_YEARS = 1
_E2E_DATASET_MONTHS = 15
_E2E_STUDY_NAME = "E2E Workflow Test"

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_e2e_dataset() -> Dataset:
    snapshots: list[MarketSnapshot] = []
    for i in range(_E2E_DATASET_MONTHS):
        m = i + 1
        year = 2000 + (m - 1) // 12
        month = ((m - 1) % 12) + 1
        snapshots.append(
            MarketSnapshot(
                date=date(year, month, 1),
                index_levels={_E2E_ASSET: Decimal("100.00")},
                inflation=Decimal("0.00"),
                inflation_cumulative=Decimal("0.00"),
                is_ath=True,
                is_underwater=False,
                running_ath=Decimal("100.00"),
            )
        )
    return Dataset(snapshots=snapshots, frequency="monthly", version=_E2E_DATASET_ID)


def _e2e_study_yaml(path: Path, **overrides: Any) -> Path:
    return create_study_yaml(
        path,
        name=_E2E_STUDY_NAME,
        dataset_id=_E2E_DATASET_ID,
        horizon_years=_E2E_HORIZON_YEARS,
        **overrides,
    )


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def e2e_dataset() -> Dataset:
    return _make_e2e_dataset()


@pytest.fixture
def mock_resolver(e2e_dataset: Dataset, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(DefaultDatasetResolver, "resolve", lambda self, i: e2e_dataset)


@pytest.fixture
def e2e_db(tmp_path: Path) -> Path:
    return tmp_path / "e2e_studies.db"


@pytest.fixture
def e2e_repo(e2e_db: Path) -> SQLiteRepository:
    return SQLiteRepository(str(e2e_db))


@pytest.fixture
def e2e_context(
    e2e_dataset: Dataset, monkeypatch: pytest.MonkeyPatch
) -> PersistenceReconstructionContext:
    monkeypatch.setattr(DefaultDatasetResolver, "resolve", lambda self, i: e2e_dataset)
    return create_persistence_context()


@pytest.fixture
def persist_paths(e2e_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for mod in [
        "run_command",
        "list_command",
        "export_command",
        "optimize_command",
        "compare_command",
    ]:
        monkeypatch.setattr(f"cli.commands.{mod}._DEFAULT_DB_PATH", str(e2e_db))


@dataclass
class _SeededDb:
    db_path: Path
    experiment_id: str
    study_name: str


@pytest.fixture
def seeded_db(
    e2e_db: Path, e2e_context: PersistenceReconstructionContext, e2e_dataset: Dataset
) -> _SeededDb:
    repo = SQLiteRepository(str(e2e_db))
    identity = ExperimentIdentity(name="E2E Seeded Study", revision="1.0")
    experiment = make_experiment(
        name="E2E Seeded Study",
        dataset=e2e_dataset,
        horizon_months=12,
    )
    exp_id = repo.save_experiment(identity, experiment, e2e_context)
    plan = make_plan(experiment, num_units=2)
    plan_id = repo.save_plan(plan, exp_id, e2e_context)
    result = make_execution_result(plan)
    repo.save_execution_result(plan_id, result, e2e_context, duration_seconds=0.5)
    return _SeededDb(db_path=e2e_db, experiment_id=exp_id, study_name="E2E Seeded Study")


@pytest.fixture
def cli_setup(mock_resolver: None, persist_paths: None) -> None: ...


# ===================================================================
# 1. Complete Study Lifecycle
# ===================================================================


class TestCompleteStudyLifecycle:
    """Validate – dry-run – execute – list – export as a single workflow."""

    def test_validate_study_yaml(
        self, tmp_path: Path, mock_resolver: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        study = _e2e_study_yaml(tmp_path / "lifecycle.yaml")
        rc = main(["validate", str(study)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Validation: PASSED" in out

    def test_run_dry_run(
        self, tmp_path: Path, mock_resolver: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        study = _e2e_study_yaml(tmp_path / "dryrun.yaml")
        rc = main(["run", "--dry-run", str(study)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "DRY RUN" in out
        assert "Total Units:" in out

    def test_run_execute_success(
        self, tmp_path: Path, cli_setup: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import infrastructure.execution.parallel_executor as _pe

        study = _e2e_study_yaml(tmp_path / "execute.yaml")

        captured_plans: list[Any] = []

        def _mock_execute(plan: Any, **kwargs: Any) -> Any:
            captured_plans.append(plan)
            return make_execution_result(plan)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(_pe, "sequential_execute", _mock_execute)
        try:
            rc = main(["run", str(study)])
        finally:
            monkeypatch.undo()

        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Execution Complete" in out
        assert len(captured_plans) == 1

    def test_list_shows_seeded_study(
        self, seeded_db: _SeededDb, cli_setup: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main(["list"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert seeded_db.study_name in out

    def test_export_seeded_study(
        self,
        seeded_db: _SeededDb,
        cli_setup: None,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = main(["export", seeded_db.experiment_id, "--output", str(tmp_path)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Rows Written" in out or seeded_db.experiment_id[:8] in out


# ===================================================================
# 2. CLI Command Interoperability
# ===================================================================


class TestCliCommandInteroperability:
    """Commands compose correctly through the CLI dispatcher."""

    def test_help_exits_success(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == ExitCode.SUCCESS

    def test_version_exits_success(self) -> None:
        rc = main(["--version"])
        assert rc == ExitCode.SUCCESS

    def test_all_commands_have_help(self) -> None:
        for cmd in ["validate", "run", "list", "export", "optimize", "compare", "config"]:
            with pytest.raises(SystemExit) as exc:
                main([cmd, "--help"])
            assert exc.value.code == ExitCode.SUCCESS, f"{cmd} --help failed"

    def test_validate_then_list_empty(
        self,
        tmp_path: Path,
        mock_resolver: None,
        cli_setup: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        study = _e2e_study_yaml(tmp_path / "compose.yaml")
        rc1 = main(["validate", str(study)])
        assert rc1 == ExitCode.SUCCESS
        capsys.readouterr()

        # cli_setup redirects _DEFAULT_DB_PATH to the isolated e2e database, so
        # this never touches (or depends on) the real ~/.sim-retire/ database.
        rc2 = main(["list"])
        assert rc2 == ExitCode.SUCCESS
        out2 = capsys.readouterr().out
        assert "Total:" in out2 or "studies" in out2

    def test_global_options_accepted(self, tmp_path: Path, mock_resolver: None) -> None:
        study = _e2e_study_yaml(tmp_path / "global.yaml")
        rc = main(["--verbose", "validate", str(study)])
        assert rc == ExitCode.SUCCESS


# ===================================================================
# 3. Persistence Round-Trip
# ===================================================================


class TestPersistenceRoundTrip:
    """Full save/load cycle through the repository."""

    def test_save_and_find_experiment(
        self,
        e2e_repo: SQLiteRepository,
        e2e_context: PersistenceReconstructionContext,
    ) -> None:
        identity = ExperimentIdentity(name="E2E Round-Trip", revision="v1")
        exp_id = e2e_repo.save_experiment(
            identity,
            make_experiment(name="E2E Round-Trip"),
            e2e_context,
        )
        found = e2e_repo.find_experiment_by_name("E2E Round-Trip")
        assert found == exp_id

    def test_save_and_load_plan(
        self,
        e2e_repo: SQLiteRepository,
        e2e_context: PersistenceReconstructionContext,
    ) -> None:
        exp = make_experiment(name="E2E Plan Round-Trip", horizon_months=12)
        identity = ExperimentIdentity(name="E2E Plan Round-Trip", revision="v1")
        exp_id = e2e_repo.save_experiment(identity, exp, e2e_context)
        plan = make_plan(exp, num_units=3)
        plan_id = e2e_repo.save_plan(plan, exp_id, e2e_context)
        loaded = e2e_repo.load_plan(plan_id, e2e_context)
        assert len(loaded.units) == 3

    def test_save_and_load_execution_result(
        self,
        e2e_repo: SQLiteRepository,
        e2e_context: PersistenceReconstructionContext,
    ) -> None:
        exp = make_experiment(name="E2E Result Round-Trip", horizon_months=12)
        identity = ExperimentIdentity(name="E2E Result Round-Trip", revision="v1")
        exp_id = e2e_repo.save_experiment(identity, exp, e2e_context)
        plan = make_plan(exp, num_units=2)
        plan_id = e2e_repo.save_plan(plan, exp_id, e2e_context)
        result = make_execution_result(plan)
        result_id = e2e_repo.save_execution_result(
            plan_id, result, e2e_context, duration_seconds=1.5
        )
        loaded = e2e_repo.load_execution_result(result_id, e2e_context)
        assert len(loaded.results) == 2

    def test_duplicate_study_rejected(
        self,
        e2e_repo: SQLiteRepository,
        e2e_context: PersistenceReconstructionContext,
    ) -> None:
        from infrastructure.persistence.errors import DuplicateStudyError

        identity = ExperimentIdentity(name="Unique E2E", revision="v1")
        e2e_repo.save_experiment(identity, make_experiment(name="Unique E2E"), e2e_context)
        with pytest.raises(DuplicateStudyError):
            e2e_repo.save_experiment(identity, make_experiment(name="Unique E2E"), e2e_context)

    def test_list_experiments_returns_saved_data(
        self,
        e2e_repo: SQLiteRepository,
        e2e_context: PersistenceReconstructionContext,
    ) -> None:
        e2e_repo.save_experiment(
            ExperimentIdentity(name="E2E List A", revision="v1"),
            make_experiment(name="E2E List A"),
            e2e_context,
        )
        e2e_repo.save_experiment(
            ExperimentIdentity(name="E2E List B", revision="v1"),
            make_experiment(name="E2E List B"),
            e2e_context,
        )
        experiments = e2e_repo.list_experiments()
        names = {e["name"] for e in experiments}
        assert "E2E List A" in names
        assert "E2E List B" in names


# ===================================================================
# 4. Export Workflow Integration
# ===================================================================


class TestExportWorkflowIntegration:
    """Export commands produce correct output after a study has been executed."""

    def test_export_csv_has_header(
        self, seeded_db: _SeededDb, cli_setup: None, tmp_path: Path
    ) -> None:
        rc = main(["export", seeded_db.experiment_id, "--format", "csv", "--output", str(tmp_path)])
        assert rc == ExitCode.SUCCESS
        csv_files = [f for f in tmp_path.iterdir() if f.suffix == ".csv"]
        assert len(csv_files) >= 1
        header = csv_files[0].read_text(encoding="utf-8").splitlines()[0]
        assert "cohort_start_date" in header

    def test_export_json_has_structure(
        self, seeded_db: _SeededDb, cli_setup: None, tmp_path: Path
    ) -> None:
        rc = main(
            ["export", seeded_db.experiment_id, "--format", "json", "--output", str(tmp_path)],
        )
        assert rc == ExitCode.SUCCESS
        json_files = [f for f in tmp_path.iterdir() if f.suffix == ".json"]
        assert len(json_files) >= 1
        data = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert "study_id" in data
        assert "rows" in data

    def test_export_json_summary(
        self, seeded_db: _SeededDb, cli_setup: None, tmp_path: Path
    ) -> None:
        rc = main(
            [
                "export",
                seeded_db.experiment_id,
                "--format",
                "json",
                "--metrics",
                "summary",
                "--output",
                str(tmp_path),
            ]
        )
        assert rc == ExitCode.SUCCESS
        json_files = [f for f in tmp_path.iterdir() if f.suffix == ".json"]
        assert len(json_files) >= 1
        data = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert "study_id" in data
        assert "total_units" in data

    def test_export_defaults_to_csv(
        self, seeded_db: _SeededDb, cli_setup: None, tmp_path: Path
    ) -> None:
        rc = main(["export", seeded_db.experiment_id, "--output", str(tmp_path)])
        assert rc == ExitCode.SUCCESS
        csv_files = [f for f in tmp_path.iterdir() if f.suffix == ".csv"]
        assert len(csv_files) >= 1

    def test_export_nonexistent_study_reports_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        dummy_path = "/tmp/__e2e_export_test__/studies.db"
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", dummy_path)
        rc = main(["export", "NonexistentStudy"])
        assert rc != ExitCode.SUCCESS


# ===================================================================
# 5. Configuration Loading
# ===================================================================


class TestConfigLoading:
    """Config subcommand workflows through the CLI."""

    @pytest.fixture
    def config_path(self, tmp_path: Path) -> Path:
        return tmp_path / "config.yaml"

    @pytest.fixture
    def valid_config(self, config_path: Path) -> Path:
        config_path.write_text(
            "database:\n  path: test.db\n"
            "output:\n  default_format: csv\n  default_directory: ./results\n"
            "execution:\n  default_workers: 4\n"
            "logging:\n  level: INFO\n",
            encoding="utf-8",
        )
        return config_path

    def test_config_validate_valid(
        self, valid_config: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main(["config", "validate", "--file", str(valid_config)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "valid" in out.lower()

    def test_config_validate_missing_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main(["config", "validate", "--file", str(tmp_path / "nonexistent.yaml")])
        assert rc == ExitCode.CONFIGURATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out or "Failed" in out

    def test_config_validate_empty_returns_errors(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        empty = tmp_path / "empty.yaml"
        empty.write_text("key: value\n", encoding="utf-8")
        rc = main(["config", "validate", "--file", str(empty)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        out = capsys.readouterr().out
        assert "validation failed" in out.lower()

    def test_config_set_and_get(self, config_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rc_set = main(
            ["--config", str(config_path), "config", "set", "output.directory", "./e2e_results"]
        )
        assert rc_set == ExitCode.SUCCESS

        assert config_path.exists()
        rc_get = main(["--config", str(config_path), "config", "get", "output.directory"])
        assert rc_get == ExitCode.SUCCESS

    def test_config_list_when_no_config(
        self, config_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main(["--config", str(config_path), "config", "list"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "No configuration" in out

    def test_config_get_nonexistent_key(
        self, config_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rc = main(["--config", str(config_path), "config", "get", "nonexistent.key"])
        assert rc == ExitCode.VALIDATION_ERROR


# ===================================================================
# 6. Error-Path Validation
# ===================================================================


class TestErrorPathValidation:
    """CLI error handling for invalid inputs."""

    def test_missing_study_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["validate", "/tmp/nonexistent_e2e_study.yaml"])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "not found" in out.lower()

    def test_invalid_yaml_syntax(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text("{invalid: yaml: [broken}", encoding="utf-8")
        rc = main(["validate", str(bad)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "Invalid YAML" in out

    def test_invalid_yaml_structure(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        scalar = tmp_path / "scalar.yaml"
        scalar.write_text("just a string", encoding="utf-8")
        rc = main(["validate", str(scalar)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out or "Invalid" in out

    def test_unknown_command(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["imaginary-command"])
        assert exc.value.code == ExitCode.VALIDATION_ERROR

    def test_missing_required_argument(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["validate"])
        assert exc.value.code == ExitCode.VALIDATION_ERROR

    def test_validate_with_unresolvable_dataset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from infrastructure.persistence.errors import StudyNotFoundError

        def _fail(self: Any, identifier: str) -> Dataset:
            raise StudyNotFoundError(f"Dataset not found: '{identifier}'")

        monkeypatch.setattr(DefaultDatasetResolver, "resolve", _fail)
        study = _e2e_study_yaml(tmp_path / "unresolvable.yaml")
        rc = main(["validate", str(study)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "invalid" in out.lower()

    def test_run_with_missing_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["run", "/tmp/missing_e2e_study.yaml"])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "not found" in out.lower()


# ===================================================================
# 7. Workflow Failure Handling
# ===================================================================


class TestWorkflowFailureHandling:
    """Graceful handling of failure scenarios across workflows."""

    def test_validate_invalid_horizon_returns_error(
        self, tmp_path: Path, mock_resolver: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        study = tmp_path / "bad_horizon.yaml"
        study.write_text(
            'metadata:\n  name: "Bad Study"\ndataset:\n  identifier: "E2E_TEST_v1"\n'
            "cohorts:\n  horizon_years: [-5]\nallocation_policy:\n"
            '  type: "ConstantAllocationPolicy"\n    equity_allocation: [0.75]\n'
            "withdrawal_policy:\n  type: \"ConstantWithdrawalPolicy\"\n  withdrawal_rate: [0.04]\n",
            encoding="utf-8",
        )
        rc = main(["validate", str(study)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "invalid" in out.lower()

    def test_run_with_invalid_yaml_reports_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bad = tmp_path / "bad_run.yaml"
        bad.write_text("{bad: yaml", encoding="utf-8")
        rc = main(["run", str(bad)])
        assert rc == ExitCode.VALIDATION_ERROR
        out = capsys.readouterr().out
        assert "Invalid YAML" in out

    def test_list_with_missing_db_reports_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            "cli.commands.list_command._DEFAULT_DB_PATH",
            "/tmp/__e2e_missing_db__/studies.db",
        )
        rc = main(["list"])
        assert rc == ExitCode.ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_export_with_missing_db_reports_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            "cli.commands.export_command._DEFAULT_DB_PATH",
            "/tmp/__e2e_missing_db__/studies.db",
        )
        rc = main(["export", "SomeStudy"])
        assert rc == ExitCode.DATABASE_ERROR or rc == ExitCode.ERROR

    def test_config_validate_reports_individual_errors(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cfg = tmp_path / "incomplete_config.yaml"
        cfg.write_text(
            "database:\n  path: test.db\noutput:\n  default_format: csv\n",
            encoding="utf-8",
        )
        rc = main(["config", "validate", "--file", str(cfg)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        out = capsys.readouterr().out
        assert "validation failed" in out.lower()


# ===================================================================
# 8. Regression Coverage
# ===================================================================


class TestRegressionCoverage:
    """Regression tests for previously delivered functionality."""

    def test_cli_exit_code_contract(self) -> None:
        assert ExitCode.SUCCESS.value == 0
        assert ExitCode.ERROR.value == 1
        assert ExitCode.VALIDATION_ERROR.value == 2
        assert ExitCode.CONFIGURATION_ERROR.value == 3
        assert ExitCode.DATABASE_ERROR.value == 4

    def test_command_registry_unchanged(self) -> None:
        from cli.commands import COMMANDS

        assert set(COMMANDS.keys()) == {
            "validate",
            "run",
            "list",
            "export",
            "optimize",
            "compare",
            "config",
        }

    def test_main_function_signature(self) -> None:
        import inspect

        sig = inspect.signature(main)
        assert "argv" in sig.parameters
        assert sig.parameters["argv"].default is None

    def test_framework_fixtures_compose_with_e2e_fixtures(
        self,
        integration_db_path: Path,
        integration_repo: SQLiteRepository,
        e2e_dataset: Dataset,
    ) -> None:
        assert integration_db_path.name == "integration_test.db"
        assert integration_repo.db_path is not None
        assert len(e2e_dataset.snapshots) == _E2E_DATASET_MONTHS

    def test_default_dataset_resolver_contract(self) -> None:
        resolver = DefaultDatasetResolver()
        assert hasattr(resolver, "resolve")
        assert callable(resolver.resolve)

    def test_create_persistence_context_contract(self) -> None:
        ctx = create_persistence_context()
        assert ctx.dataset_resolver is not None
        assert ctx.policy_codecs is not None
        assert ctx.simulation_result_codec is not None

    def test_invoke_cli_from_framework(
        self, tmp_path: Path, mock_resolver: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        study = _e2e_study_yaml(tmp_path / "framework.yaml")
        rc = main(["validate", str(study)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Validation: PASSED" in out
