"""ListCommand — query and display stored studies."""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from cli.commands.base import BaseCommand, ExecutionContext
from cli.error_handling import ExitCode

_DEFAULT_DB_PATH = "~/.sim-retire/studies.db"


@dataclass(frozen=True)
class StudyInfo:
    study_id: str
    name: str
    version: str
    status: str
    units: int
    created_at: str


def _normalize_status(db_status: str | None) -> str:
    if db_status is None or db_status == "planned":
        return "pending"
    return db_status


def _fetch_studies(
    db_path: str, status_filter: str, sort: str
) -> list[StudyInfo]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT
                e.experiment_id,
                e.name,
                e.revision,
                rp.status,
                rp.unit_count,
                e.created_at
            FROM experiments e
            LEFT JOIN (
                SELECT experiment_id, status, unit_count, created_at,
                       ROW_NUMBER() OVER (
                           PARTITION BY experiment_id ORDER BY created_at DESC
                       ) AS rn
                FROM research_plans
            ) rp ON e.experiment_id = rp.experiment_id AND rp.rn = 1
            """
        ).fetchall()
    finally:
        conn.close()

    studies = [
        StudyInfo(
            study_id=r[0],
            name=r[1],
            version=r[2],
            status=_normalize_status(r[3]),
            units=r[4] if r[4] is not None else 0,
            created_at=r[5],
        )
        for r in rows
    ]

    if status_filter != "all":
        studies = [s for s in studies if s.status == status_filter]

    if sort == "date":
        studies.sort(key=lambda s: s.created_at, reverse=True)
    elif sort == "name":
        studies.sort(key=lambda s: s.name.lower())
    elif sort == "status":
        studies.sort(key=lambda s: s.status)

    return studies


def _fmt_units(units: int) -> str:
    return f"{units:,}"


def _print_table(studies: list[StudyInfo]) -> None:
    print(
        f"{'Study ID':<16} \u2502 {'Name':<25} \u2502 {'Version':<7} \u2502"
        f" {'Status':<9} \u2502 {'Units':>5} \u2502 Date Created"
    )
    print(
        "\u2500" * 16 + "\u2500\u253c\u2500" + "\u2500" * 25
        + "\u2500\u253c\u2500" + "\u2500" * 7
        + "\u2500\u253c\u2500" + "\u2500" * 9
        + "\u2500\u253c\u2500" + "\u2500" * 5
        + "\u2500\u253c\u2500" + "\u2500" * 12
    )
    for s in studies:
        print(
            f"{s.study_id:<16} \u2502 {s.name:<25} \u2502 {s.version:<7} \u2502"
            f" {s.status:<9} \u2502 {_fmt_units(s.units):>5} \u2502 {s.created_at[:10]}"
        )
    print(f"\nTotal: {len(studies)} studies")


def _print_json(studies: list[StudyInfo]) -> None:
    data = {
        "studies": [
            {
                "study_id": s.study_id,
                "name": s.name,
                "version": s.version,
                "status": s.status,
                "units": s.units,
                "created_at": s.created_at[:10],
            }
            for s in studies
        ],
        "total": len(studies),
    }
    print(json.dumps(data, indent=2))


def _print_csv(studies: list[StudyInfo]) -> None:
    print("study_id,name,version,status,units,created_at")
    for s in studies:
        safe_name = s.name.replace(",", "\\,")
        print(
            f"{s.study_id},{safe_name},{s.version},{s.status},"
            f"{s.units},{s.created_at[:10]}"
        )


class ListCommand(BaseCommand):
    name = "list"
    help_text = "List stored studies"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--format",
            choices=["table", "json", "csv"],
            default="table",
            help="Output format",
        )
        parser.add_argument(
            "--status",
            choices=["all", "completed", "failed", "pending"],
            default="all",
            help="Filter by study status",
        )
        parser.add_argument(
            "--sort",
            choices=["date", "name", "status"],
            default="date",
            help="Sort order",
        )

    def execute(
        self, context: ExecutionContext, args: argparse.Namespace
    ) -> int:
        db_path = str(Path(_DEFAULT_DB_PATH).expanduser())

        try:
            studies = _fetch_studies(db_path, args.status, args.sort)
        except sqlite3.OperationalError as exc:
            print(f"ERROR: Database error: {exc}")
            return ExitCode.ERROR

        if not studies:
            print("No studies found")
            return ExitCode.SUCCESS

        if args.format == "json":
            _print_json(studies)
        elif args.format == "csv":
            _print_csv(studies)
        else:
            _print_table(studies)

        return ExitCode.SUCCESS
