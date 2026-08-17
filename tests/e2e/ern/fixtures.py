"""Grid-study CLI invocation and per-cell output parsing for the ERN E2E.

The E2E runs the full ERN SWR grid as ONE study (``examples/studies/ern_grid.yaml``)
through a single ``sim-retire run --no-persist --summary-only`` subprocess.  The
CLI prints one machine-parseable ``cell: ...`` line per parameter configuration;
this module parses those lines back into per-cell statistics for oracle
comparison.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from tests.e2e.cli_harness import CliHarness, CliResult

_CELL_LINE_RE = re.compile(r"^cell: (.*)$", re.MULTILINE)

_CELL_HEADER = "Per-Cell Results (grid):"

_CELL_FIELDS = (
    "equity_allocation",
    "withdrawal_rate",
    "horizon_years",
    "units_run",
    "units_failed",
    "success_rate",
)


@dataclass(frozen=True)
class PerCellStats:
    """Aggregate statistics for one grid cell, parsed from the CLI summary."""

    units_run: int
    units_failed: int
    success_rate: float

    @property
    def success_percent(self) -> float:
        return self.success_rate * 100


def parse_per_cell_lines(
    stdout: str,
) -> dict[tuple[float, float, int], PerCellStats]:
    """Parse the CLI's machine-parseable per-cell summary lines.

    Each line has the stable layout
    ``cell: equity_allocation=<w> withdrawal_rate=<r> horizon_years=<h>
    units_run=<n> units_failed=<m> success_rate=<s>`` and is keyed by
    ``(equity_allocation, withdrawal_rate, horizon_years)``.

    Raises
    ------
    ValueError
        If any cell line is malformed, missing a required field, or duplicated.
    """
    parsed: dict[tuple[float, float, int], PerCellStats] = {}
    for match in _CELL_LINE_RE.finditer(stdout):
        fields: dict[str, str] = {}
        for token in match.group(1).split():
            name, sep, value = token.partition("=")
            if not sep or not name or not value:
                raise ValueError(f"Malformed per-cell token: {token!r}")
            if name in fields:
                raise ValueError(f"Duplicate field {name!r} in cell line")
            fields[name] = value
        missing = [name for name in _CELL_FIELDS if name not in fields]
        if missing:
            raise ValueError(f"Cell line missing fields {missing}: {match.group(1)!r}")
        key = (
            float(fields["equity_allocation"]),
            float(fields["withdrawal_rate"]),
            int(fields["horizon_years"]),
        )
        if key in parsed:
            raise ValueError(f"Duplicate cell {key!r}")
        parsed[key] = PerCellStats(
            units_run=int(fields["units_run"]),
            units_failed=int(fields["units_failed"]),
            success_rate=float(fields["success_rate"]),
        )
    return parsed


def run_grid_study(
    harness: CliHarness,
    study_yaml: Path,
    workers: int | str,
    timeout: int = 3600,
    fast_path: bool = False,
    reference_chained: bool = False,
    reference_independent: bool = False,
) -> tuple[CliResult, dict[tuple[float, float, int], PerCellStats]]:
    """Run one grid study through the public CLI and return its per-cell lines.

    The study runs as a single subprocess in non-persistent, summary-only mode
    (no study database, no per-month timeline materialization).  The per-cell
    statistics come exclusively from the CLI's observable stdout.

    ``fast_path``, ``reference_chained`` and ``reference_independent`` select
    the corresponding execution modes; at most one may be set.  With none set,
    the run uses the public default (Reference Chained for plans that benefit
    from horizon chaining, which the ERN grid is).
    """
    if sum((fast_path, reference_chained, reference_independent)) > 1:
        raise ValueError(
            "fast_path, reference_chained and reference_independent are mutually exclusive"
        )
    args = ["run", str(study_yaml), "--workers", str(workers)]
    args += ["--no-persist", "--summary-only"]
    if fast_path:
        args.append("--fast-path")
    elif reference_chained:
        args.append("--reference-chained")
    elif reference_independent:
        args.append("--reference-independent")
    result: CliResult = harness.run(args, timeout=timeout)
    if result.exit_code != 0:
        raise RuntimeError(
            f"sim-retire run failed (exit={result.exit_code}): {result.stderr or result.stdout}"
        )
    if _CELL_HEADER not in result.stdout:
        raise RuntimeError(f"sim-retire run printed no '{_CELL_HEADER}' section in its summary.")
    cells = parse_per_cell_lines(result.stdout)
    if not cells:
        raise RuntimeError(
            f"No per-cell lines parsed from sim-retire run (exit={result.exit_code})."
        )
    for key, stats in cells.items():
        expected_rate = 1 - stats.units_failed / stats.units_run
        if abs(stats.success_rate - expected_rate) > 1e-4:
            raise RuntimeError(
                f"cell {key}: success_rate={stats.success_rate} inconsistent with "
                f"units_failed/units_run={expected_rate:.6f}"
            )
    return result, cells
