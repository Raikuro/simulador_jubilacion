"""Unit tests for the black-box CLI harness (fast, runs by default)."""

from __future__ import annotations

import pytest

from tests.e2e.cli_harness import CliResult, locate_cli


def _result(stdout: str, exit_code: int = 0) -> CliResult:
    return CliResult(exit_code=exit_code, stdout=stdout, stderr="")


def test_locate_cli_finds_venv_script() -> None:
    cli = locate_cli()
    assert cli.is_file()
    assert cli.name == "sim-retire"


def test_units_run_and_failed_parsed() -> None:
    stdout = (
        "\u2501\u2501\u2501\n"
        "Execution Complete\n"
        "Status:         COMPLETED WITH ERRORS\n"
        "Units Run:      1,739\n"
        "Units Failed:   25\n"
        "Execution Time: 49s\n"
    )
    result = _result(stdout)
    assert result.units_run == 1739
    assert result.units_failed == 25
    assert result.status == "COMPLETED WITH ERRORS"


def test_units_missing_when_not_present() -> None:
    result = _result("Status: SUCCESS\n")
    assert result.units_run is None
    assert result.units_failed is None
    assert result.status == "SUCCESS"


@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        ("Units Failed:   0", 0),
        ("Units Failed:   1,167", 1167),
        ("Units Failed:   1,739", 1739),
    ],
)
def test_units_failed_formats(stdout: str, expected: int) -> None:
    assert _result(stdout).units_failed == expected
