"""ExportCommand — export stored study results to file.

All database access goes through SQLiteRepository (no direct sqlite3 usage).
Uses get_export_data() for flat read-only data retrieval without requiring
a PersistenceReconstructionContext.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cli.commands.base import BaseCommand, ExecutionContext
from cli.error_handling import ExitCode
from infrastructure.persistence.errors import PersistenceError
from infrastructure.persistence.sqlite_repository import SQLiteRepository

_DEFAULT_DB_PATH = "~/.sim-retire/studies.db"
_DEFAULT_OUTPUT_DIR = "./results/"


def _ensure_output_dir(output_dir: str) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_csv(export_data: dict[str, Any], output_path: Path) -> None:
    rows = export_data.get("rows", [])
    if not rows:
        output_path.write_text("")
        return

    param_keys = export_data.get("parameter_keys", [])
    fieldnames = (
        ["cohort_start_date"]
        + param_keys
        + ["month_index", "portfolio_value", "withdrawal", "success"]
    )

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json_full(export_data: dict[str, Any], output_path: Path) -> None:
    total_units = export_data.get("total_units", 0)
    success_count = export_data.get("success_count", 0)
    success_rate = round(success_count / total_units, 4) if total_units > 0 else 0.0

    output = {
        "study_id": export_data.get("study_id", ""),
        "name": export_data.get("name", ""),
        "revision": export_data.get("revision", ""),
        "created_at": export_data.get("created_at", ""),
        "executed_at": export_data.get("executed_at", ""),
        "duration_seconds": export_data.get("duration_seconds", 0),
        "success_rate": success_rate,
        "total_units": total_units,
        "success_count": export_data.get("success_count", 0),
        "failure_count": export_data.get("failure_count", 0),
        "parameter_keys": export_data.get("parameter_keys", []),
        "rows": export_data.get("rows", []),
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)


def _write_json_summary(export_data: dict[str, Any], output_path: Path) -> None:
    total_units = export_data.get("total_units", 0)
    success_count = export_data.get("success_count", 0)
    failure_count = export_data.get("failure_count", 0)
    success_rate = round(success_count / total_units, 4) if total_units > 0 else 0.0

    output = {
        "study_id": export_data.get("study_id", ""),
        "name": export_data.get("name", ""),
        "revision": export_data.get("revision", ""),
        "created_at": export_data.get("created_at", ""),
        "executed_at": export_data.get("executed_at", ""),
        "duration_seconds": export_data.get("duration_seconds", 0),
        "success_rate": success_rate,
        "total_units": total_units,
        "success_count": success_count,
        "failure_count": failure_count,
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)


def _format_file_size(path: Path) -> str:
    size = path.stat().st_size
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


class ExportCommand(BaseCommand):
    name = "export"
    help_text = "Export stored study results to file"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("study_id", type=str, help="Identifier of stored study")
        parser.add_argument(
            "--format",
            choices=["csv", "json"],
            default="csv",
            help="Export format",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=_DEFAULT_OUTPUT_DIR,
            help="Output file directory or path",
        )
        parser.add_argument(
            "--metrics",
            choices=["full", "summary", "aggregated"],
            default="full",
            help="What to export",
        )

    def execute(
        self, context: ExecutionContext, args: argparse.Namespace
    ) -> int:
        db_path = str(Path(_DEFAULT_DB_PATH).expanduser())

        try:
            repo = SQLiteRepository(db_path)
        except PersistenceError as exc:
            print(f"ERROR: Database error: {exc}")
            return ExitCode.DATABASE_ERROR

        try:
            export_data = repo.get_export_data(args.study_id)
        except PersistenceError as exc:
            print(f"ERROR: Database error: {exc}")
            return ExitCode.DATABASE_ERROR

        if export_data is None:
            print(f"ERROR: No completed results found for study '{args.study_id}'")
            return ExitCode.ERROR

        rows = export_data.get("rows", [])
        if not rows:
            print(f"ERROR: No data rows found for study '{args.study_id}'")
            return ExitCode.ERROR

        output_path_input = args.output
        output_path = Path(output_path_input)

        if output_path.is_dir() or not output_path.suffix:
            out_dir = _ensure_output_dir(str(output_path))
            ext = "csv" if args.format == "csv" else "json"
            filename = f"{args.study_id}_export.{ext}"
            output_path = out_dir / filename
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        fmt = args.format
        metrics = args.metrics

        print(f"Exporting {args.study_id}...")
        print()

        if metrics == "aggregated":
            print("Note: aggregated format not yet implemented, using full")
            print()

        try:
            if fmt == "csv":
                _write_csv(export_data, output_path)
            elif fmt == "json":
                if metrics == "summary":
                    _write_json_summary(export_data, output_path)
                else:
                    _write_json_full(export_data, output_path)
        except OSError as exc:
            print(f"ERROR: Failed to write output file: {exc}")
            return ExitCode.ERROR

        file_size = _format_file_size(output_path)
        num_rows = len(rows)
        print(f"Format: {fmt.upper()}")
        print(f"Metrics: {metrics}")
        print(f"Output: {output_path}")
        print()
        print(f"Rows Written: {num_rows:,}")
        print(f"File Size: {file_size}")

        return ExitCode.SUCCESS
