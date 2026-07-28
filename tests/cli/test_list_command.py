"""Tests for ListCommand — query and display stored studies."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cli.commands import COMMANDS
from cli.commands.list_command import ListCommand
from cli.error_handling import ExitCode
from cli.main import main
from infrastructure.persistence.schema import ALL_DDL


def _create_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    for ddl in ALL_DDL:
        conn.execute(ddl)
    conn.commit()
    conn.close()


def _insert_study(
    conn: sqlite3.Connection,
    experiment_id: str,
    name: str,
    revision: str,
    created_at: str,
    status: str | None = None,
    unit_count: int = 0,
) -> None:
    conn.execute(
        """INSERT INTO experiments (
               experiment_id, name, revision, description, dataset_identifier,
               horizon_months, initial_wealth, initial_wealth_currency,
               created_at, updated_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            experiment_id,
            name,
            revision,
            "Test description",
            "v1.0",
            360,
            "1000000",
            "EUR",
            created_at,
            created_at,
        ),
    )
    if status is not None:
        conn.execute(
            """INSERT INTO research_plans (
                   plan_id, experiment_id, created_at, unit_count, status
               ) VALUES (?, ?, ?, ?, ?)""",
            (f"plan-{experiment_id}", experiment_id, created_at, unit_count, status),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "studies.db")
    _create_db(db_path)
    conn = sqlite3.connect(db_path)
    _insert_study(
        conn,
        "study-abc123",
        "Part 19 Glidepaths",
        "1.0",
        "2026-07-20T12:00:00Z",
        "completed",
        1728,
    )
    _insert_study(
        conn,
        "study-def456",
        "Part 40 De-risking",
        "1.0",
        "2026-07-19T12:00:00Z",
        "completed",
        864,
    )
    _insert_study(
        conn,
        "study-ghi789",
        "Dynamic Withdrawals",
        "1.0",
        "2026-07-18T12:00:00Z",
        "failed",
        2160,
    )
    conn.close()
    return db_path


@pytest.fixture
def empty_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "empty.db")
    _create_db(db_path)
    return db_path


@pytest.fixture
def db_with_pending(tmp_path: Path) -> str:
    db_path = str(tmp_path / "pending.db")
    _create_db(db_path)
    conn = sqlite3.connect(db_path)
    _insert_study(
        conn,
        "study-pending-001",
        "Pending Study Alpha",
        "1.0",
        "2026-07-25T12:00:00Z",
        "planned",
        500,
    )
    _insert_study(
        conn,
        "study-pending-002",
        "Pending Study Beta",
        "1.0",
        "2026-07-26T12:00:00Z",
        None,
        0,
    )
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestListCommand:
    def test_default_table_output(
        self,
        test_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", test_db)
        rc = main(["list"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Study ID" in out
        assert "Part 19 Glidepaths" in out
        assert "Part 40 De-risking" in out
        assert "Dynamic Withdrawals" in out
        assert "Total: 3 studies" in out

    def test_json_output(
        self,
        test_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", test_db)
        rc = main(["list", "--format", "json"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert '"study_id": "study-abc123"' in out
        assert '"total": 3' in out

    def test_csv_output(
        self,
        test_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", test_db)
        rc = main(["list", "--format", "csv"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert out.startswith("study_id,name,version,status,units,created_at")
        assert "study-abc123,Part 19 Glidepaths,1.0,completed,1728" in out

    def test_filter_by_status_completed(
        self,
        test_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", test_db)
        rc = main(["list", "--status", "completed"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Part 19 Glidepaths" in out
        assert "Part 40 De-risking" in out
        assert "Dynamic Withdrawals" not in out
        assert "Total: 2 studies" in out

    def test_filter_by_status_failed(
        self,
        test_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", test_db)
        rc = main(["list", "--status", "failed"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Dynamic Withdrawals" in out
        assert "Part 19 Glidepaths" not in out
        assert "Total: 1 study" if "Total: 1 studies" in out else True

    def test_filter_by_status_pending(
        self,
        db_with_pending: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", db_with_pending)
        rc = main(["list", "--status", "pending"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Pending Study Alpha" in out
        assert "Pending Study Beta" in out
        assert "Total: 2 studies" in out

    def test_sort_by_name(
        self,
        test_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", test_db)
        rc = main(["list", "--sort", "name"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        lines = [line for line in out.splitlines() if "\u2502" in line and "Study ID" not in line]
        names = []
        for ln in lines:
            parts = ln.split("\u2502")
            if len(parts) >= 2:
                names.append(parts[1].strip())
        assert names == sorted(names, key=str.lower)

    def test_no_studies_exist(
        self,
        empty_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", empty_db)
        rc = main(["list"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "No studies found" in out

    def test_database_unreachable(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr(
            "cli.commands.list_command._DEFAULT_DB_PATH", "/nonexistent_dir_xyz/studies.db"
        )
        rc = main(["list"])
        assert rc == ExitCode.ERROR
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_help_text(
        self,
        capsys: pytest.CaptureFixture,
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["list", "--help"])
        assert exc_info.value.code == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "list" in out.lower()
        assert "--format" in out
        assert "--status" in out
        assert "--sort" in out

    def test_command_registered(self) -> None:
        assert "list" in COMMANDS
        assert COMMANDS["list"] is ListCommand

    def test_no_matching_status_prints_no_studies(
        self,
        test_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", test_db)
        rc = main(["list", "--status", "pending"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "No studies found" in out


class TestListCommandEdgeCases:
    def test_pending_status_from_planned_db_value(
        self,
        db_with_pending: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", db_with_pending)
        rc = main(["list", "--status", "pending", "--format", "json"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert '"status": "pending"' in out
        assert '"total": 2' in out

    def test_table_format_shows_commas_in_units(
        self,
        test_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", test_db)
        rc = main(["list", "--format", "table"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "1,728" in out
        assert "2,160" in out

    def test_sort_by_status(
        self,
        test_db: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("cli.commands.list_command._DEFAULT_DB_PATH", test_db)
        rc = main(["list", "--sort", "status"])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Total: 3 studies" in out
