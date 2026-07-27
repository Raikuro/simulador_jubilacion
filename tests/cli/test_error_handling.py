"""Tests for exit codes and error formatting."""

from __future__ import annotations

import pytest

from cli.error_handling import ExitCode, format_error, handle_exception


class TestExitCode:
    def test_success_is_zero(self) -> None:
        assert ExitCode.SUCCESS == 0

    def test_error_is_one(self) -> None:
        assert ExitCode.ERROR == 1

    def test_validation_error_is_two(self) -> None:
        assert ExitCode.VALIDATION_ERROR == 2

    def test_interrupted_is_130(self) -> None:
        assert ExitCode.INTERRUPTED == 130


class TestFormatError:
    def test_format_error_default_exit_code(self) -> None:
        msg = format_error("Something went wrong")
        assert msg == "ERROR: Something went wrong"

    def test_format_error_custom_exit_code(self) -> None:
        msg = format_error("Bad input", ExitCode.VALIDATION_ERROR)
        assert msg == "ERROR: Bad input"


class TestHandleException:
    def test_handle_exception_prints_to_stderr(self, capsys: pytest.CaptureFixture) -> None:
        exc = ValueError("Invalid value")
        rc = handle_exception(exc)
        assert rc == ExitCode.ERROR
        stderr = capsys.readouterr().err
        assert "Invalid value" in stderr

    def test_handle_exception_returns_error_code(self) -> None:
        rc = handle_exception(RuntimeError("fail"))
        assert rc == ExitCode.ERROR
