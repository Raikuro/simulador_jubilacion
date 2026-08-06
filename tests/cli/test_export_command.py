"""Tests for ExportCommand — export stored study results to file.

All database access goes through SQLiteRepository (no direct sqlite3 in CLI layer).
Test data is inserted via raw SQL to simulate a realistic database state.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from cli.commands import COMMANDS
from cli.commands.export_command import ExportCommand
from cli.error_handling import ExitCode
from cli.main import main
from infrastructure.persistence.schema import ALL_DDL


def _create_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    for ddl in ALL_DDL:
        conn.execute(ddl)
    conn.commit()
    conn.close()


def _to_canonical_json(data: dict[str, Any]) -> str:
    """Match SQLiteRepository's canonical JSON format."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _setup_full_test_data(conn: sqlite3.Connection) -> None:
    """Insert a complete experiment with plan, execution result, and simulation results."""
    experiment_id = "study-export-001"
    plan_id = "plan-export-001"
    result_id = "result-export-001"

    conn.execute(
        """INSERT INTO experiments (
               experiment_id, name, revision, description, dataset_identifier,
               horizon_months, initial_wealth, initial_wealth_currency,
               created_at, updated_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            experiment_id,
            "Export Test Study",
            "1.0",
            "Test study for export",
            "ACWI_EUR_2024",
            360,
            "1000000",
            "EUR",
            "2026-07-25T12:00:00Z",
            "2026-07-25T12:00:00Z",
        ),
    )

    param_configs = [
        ("param-1", _to_canonical_json({"equity_allocation": "0.75"})),
        ("param-2", _to_canonical_json({"equity_allocation": "0.50"})),
    ]
    for pid, pjson in param_configs:
        phash = str(hash(pjson))
        conn.execute(
            "INSERT INTO parameter_configurations "
            "(param_config_id, params_json, params_hash, created_at) "
            "VALUES (?, ?, ?, ?)",
            (pid, pjson, phash, "2026-07-25T12:00:00Z"),
        )

    policy_id = "policy-alloc-001"
    policy_json = _to_canonical_json({"equity_allocation": "0.75"})
    conn.execute(
        "INSERT INTO policies (policy_id, policy_type, params_json, params_hash, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            policy_id,
            "AllocationPolicy",
            policy_json,
            str(hash(policy_json)),
            "2026-07-25T12:00:00Z",
        ),
    )

    cohort_ids: list[str] = []
    cohort_dates = ["2020-01-01", "2020-02-01"]
    for i, cd in enumerate(cohort_dates):
        cid = f"cohort-{i}"
        conn.execute(
            "INSERT INTO cohorts (cohort_id, experiment_id, start_date, cohort_ref, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (cid, experiment_id, cd, f"monthly-{cd}", "2026-07-25T12:00:00Z"),
        )
        cohort_ids.append(cid)

    conn.execute(
        "INSERT INTO research_plans (plan_id, experiment_id, created_at, unit_count, status) "
        "VALUES (?, ?, ?, ?, ?)",
        (plan_id, experiment_id, "2026-07-25T12:00:00Z", 2, "completed"),
    )

    for unit_idx, (cid, pcid) in enumerate(
        [(cohort_ids[0], "param-1"), (cohort_ids[1], "param-2")]
    ):
        portfolio_json = _to_canonical_json({
            "holdings": [
                {"asset_class_id": "initial", "units": "1000000"}
            ]
        })
        conn.execute(
            """INSERT INTO planned_units (
                   unit_id, plan_id, unit_index, cohort_id, param_config_id,
                   allocation_policy_id, withdrawal_policy_id, initial_portfolio_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"unit-{unit_idx}",
                plan_id,
                unit_idx,
                cid,
                pcid,
                policy_id,
                policy_id,
                portfolio_json,
            ),
        )

    conn.execute(
        """INSERT INTO execution_results (
               result_id, plan_id, executed_at, duration_seconds,
               success_count, failure_count, total_units
           ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (result_id, plan_id, "2026-07-25T13:00:00Z", 120.5, 1, 1, 2),
    )

    for unit_idx in range(2):
        for month_idx in range(3):
            monthly = {
                "date": f"2020-0{1 + month_idx}-01",
                "period_index": month_idx,
                "drawdown": -0.05 * month_idx,
                "cumulative_return": 0.02 * month_idx,
                "cumulative_inflation": 0.01 * month_idx,
                "market_snapshot": {
                    "date": f"2020-0{1 + month_idx}-01",
                    "index_levels": {"initial": "1000"},
                    "inflation": "0.01",
                    "inflation_cumulative": "0.01",
                    "is_ath": True,
                    "is_underwater": False,
                    "running_ath": "1000",
                },
                "portfolio_holdings": [
                    {"asset_class_id": "initial", "units": str(1000000 + unit_idx * 10000)}
                ],
                "withdrawal_decision": "3333.33",
                "allocation": None,
                "allocation_target": None,
                "allocation_drift": None,
                "rebalance_result": None,
                "events": [],
            }
            stats = None
            is_final = 1 if month_idx == 2 else 0
            if is_final:
                success_val = unit_idx == 0
                stats = {
                    "final_wealth_amount": "1200000",
                    "final_wealth_currency": "EUR",
                    "max_drawdown": -0.10,
                    "success": success_val,
                    "failure_month": None if success_val else 24,
                    "months_simulated": 360,
                    "execution_time_seconds": 60.0,
                }

            conn.execute(
                """INSERT INTO simulation_results (
                       execution_result_id, unit_index, month_index,
                       monthly_payload_json, statistics_payload_json, final_month
                   ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    result_id,
                    unit_idx,
                    month_idx,
                    _to_canonical_json(monthly),
                    _to_canonical_json(stats) if stats else None,
                    is_final,
                ),
            )

    conn.commit()


def _setup_experiment_only(conn: sqlite3.Connection) -> None:
    """Insert an experiment with no plans or results."""
    conn.execute(
        """INSERT INTO experiments (
               experiment_id, name, revision, description, dataset_identifier,
               horizon_months, initial_wealth, initial_wealth_currency,
               created_at, updated_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "study-no-results",
            "No Results Study",
            "1.0",
            "Study without results",
            "ACWI_EUR_2024",
            360,
            "1000000",
            "EUR",
            "2026-07-25T12:00:00Z",
            "2026-07-25T12:00:00Z",
        ),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def export_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "export_test.db")
    _create_db(db_path)
    conn = sqlite3.connect(db_path)
    _setup_full_test_data(conn)
    conn.close()
    return db_path


@pytest.fixture
def experiment_only_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "experiment_only.db")
    _create_db(db_path)
    conn = sqlite3.connect(db_path)
    _setup_experiment_only(conn)
    conn.close()
    return db_path


@pytest.fixture
def empty_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "empty.db")
    _create_db(db_path)
    return db_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExportCommand:
    def test_default_csv_export(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        out_dir = tmp_path / "export_out"
        rc = main(["export", "study-export-001", "--output", str(out_dir)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Exporting study-export-001" in out
        assert "Format: CSV" in out
        assert "Rows Written: 6" in out

        csv_path = out_dir / "study-export-001_export.csv"
        assert csv_path.exists()
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 6
        assert rows[0]["cohort_start_date"] == "2020-01-01"
        assert rows[0]["month_index"] == "0"
        assert rows[0]["success"] == "1"

    def test_json_export_full(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        out_dir = tmp_path / "json_full"
        rc = main(["export", "study-export-001", "--format", "json", "--output", str(out_dir)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Format: JSON" in out
        assert "Metrics: full" in out

        json_path = out_dir / "study-export-001_export.json"
        assert json_path.exists()
        with open(json_path) as f:
            data = json.load(f)
        assert data["study_id"] == "study-export-001"
        assert data["name"] == "Export Test Study"
        assert data["total_units"] == 2
        assert data["success_rate"] == 0.5
        assert len(data["rows"]) == 6
        assert "parameter_keys" in data

    def test_json_export_summary(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        out_dir = tmp_path / "json_summary"
        rc = main(
            [
                "export",
                "study-export-001",
                "--format",
                "json",
                "--metrics",
                "summary",
                "--output",
                str(out_dir),
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Metrics: summary" in out

        json_path = out_dir / "study-export-001_export.json"
        assert json_path.exists()
        with open(json_path) as f:
            data = json.load(f)
        assert data["study_id"] == "study-export-001"
        assert data["total_units"] == 2
        assert data["success_rate"] == 0.5
        assert "rows" not in data

    def test_export_with_output_path(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        output_file = tmp_path / "custom_output.csv"
        rc = main(["export", "study-export-001", "--output", str(output_file)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert str(output_file) in out
        assert output_file.exists()

    def test_study_not_found(
        self,
        empty_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", empty_db)
        rc = main(["export", "nonexistent-study"])
        assert rc == ExitCode.ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out
        assert "nonexistent-study" in out

    def test_no_results(
        self,
        experiment_only_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", experiment_only_db)
        rc = main(["export", "study-no-results"])
        assert rc == ExitCode.ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_database_unreachable(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "cli.commands.export_command._DEFAULT_DB_PATH",
            "/nonexistent_dir_xyz/studies.db",
        )
        rc = main(["export", "study-abc123"])
        assert rc == ExitCode.DATABASE_ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_help_text(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["export", "--help"])
        assert exc_info.value.code == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "export" in out.lower()
        assert "--format" in out
        assert "--output" in out
        assert "--metrics" in out
        assert "study_id" in out

    def test_command_registered(self) -> None:
        assert "export" in COMMANDS
        assert COMMANDS["export"] is ExportCommand

    def test_csv_content_is_valid(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        out_dir = tmp_path / "csv_validate"
        rc = main(["export", "study-export-001", "--format", "csv", "--output", str(out_dir)])
        assert rc == ExitCode.SUCCESS

        csv_path = out_dir / "study-export-001_export.csv"
        content = csv_path.read_text()
        assert content.startswith(
            "cohort_start_date,equity_allocation,month_index,portfolio_value,withdrawal,success"
        )
        lines = content.strip().splitlines()
        assert len(lines) == 7  # header + 6 data rows

    def test_json_content_is_valid(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        out_dir = tmp_path / "json_validate"
        rc = main(["export", "study-export-001", "--format", "json", "--output", str(out_dir)])
        assert rc == ExitCode.SUCCESS

        json_path = out_dir / "study-export-001_export.json"
        data = json.loads(json_path.read_text())
        assert data["study_id"] == "study-export-001"
        assert data["name"] == "Export Test Study"
        assert data["revision"] == "1.0"
        assert data["duration_seconds"] == 120.5
        assert data["total_units"] == 2
        assert data["success_count"] == 1
        assert data["failure_count"] == 1
        assert data["parameter_keys"] == ["equity_allocation"]

        rows = data["rows"]
        assert len(rows) == 6
        for r in rows:
            assert "cohort_start_date" in r
            assert "equity_allocation" in r
            assert "month_index" in r
            assert "portfolio_value" in r
            assert "withdrawal" in r
            assert "success" in r

    def test_csv_has_parameter_columns(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        out_dir = tmp_path / "csv_params"
        rc = main(["export", "study-export-001", "--format", "csv", "--output", str(out_dir)])
        assert rc == ExitCode.SUCCESS

        csv_path = out_dir / "study-export-001_export.csv"
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert reader.fieldnames is not None
        assert "equity_allocation" in reader.fieldnames
        assert rows[0]["equity_allocation"] == "0.75"
        assert rows[3]["equity_allocation"] == "0.50"

    def test_json_output_contains_rows_object(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        out_dir = tmp_path / "json_rows"
        rc = main(
            [
                "export",
                "study-export-001",
                "--format",
                "json",
                "--metrics",
                "full",
                "--output",
                str(out_dir),
            ]
        )
        assert rc == ExitCode.SUCCESS

        json_path = out_dir / "study-export-001_export.json"
        data = json.loads(json_path.read_text())
        assert isinstance(data["rows"], list)
        assert len(data["rows"]) == 6
        row = data["rows"][0]
        assert row["cohort_start_date"] == "2020-01-01"
        assert row["month_index"] == 0
        assert row["success"] == 1

    def test_output_dir_created_automatically(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        out_dir = tmp_path / "new_dir" / "nested"
        assert not out_dir.exists()
        rc = main(["export", "study-export-001", "--output", str(out_dir)])
        assert rc == ExitCode.SUCCESS
        assert out_dir.exists()
        assert (out_dir / "study-export-001_export.csv").exists()


class TestExportEdgeCases:
    def test_empty_database(
        self,
        empty_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", empty_db)
        rc = main(["export", "any-study"])
        assert rc == ExitCode.ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_aggregated_metrics_shows_notice_and_falls_back(
        self,
        export_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", export_db)
        out_dir = tmp_path / "aggregated"
        rc = main(
            [
                "export",
                "study-export-001",
                "--format",
                "json",
                "--metrics",
                "aggregated",
                "--output",
                str(out_dir),
            ]
        )
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "aggregated format not yet implemented" in out

        json_path = out_dir / "study-export-001_export.json"
        data = json.loads(json_path.read_text())
        assert "rows" in data

    def test_csv_empty_rows_not_written(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        db_path = str(tmp_path / "no_data.db")
        _create_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            """INSERT INTO experiments (
                   experiment_id, name, revision, description, dataset_identifier,
                   horizon_months, initial_wealth, initial_wealth_currency,
                   created_at, updated_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "study-empty",
                "Empty Study",
                "1.0",
                "No data",
                "v1.0",
                360,
                "1000000",
                "EUR",
                "2026-07-25T12:00:00Z",
                "2026-07-25T12:00:00Z",
            ),
        )
        conn.execute(
            """INSERT INTO research_plans (
                   plan_id, experiment_id, created_at, unit_count, status
               ) VALUES (?, ?, ?, ?, ?)""",
            ("plan-empty", "study-empty", "2026-07-25T12:00:00Z", 1, "planned"),
        )
        conn.commit()
        conn.close()

        monkeypatch.setattr("cli.commands.export_command._DEFAULT_DB_PATH", db_path)
        rc = main(["export", "study-empty"])
        assert rc == ExitCode.ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out
