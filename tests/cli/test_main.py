"""Tests for CLI entry point and command dispatch."""

from __future__ import annotations

import argparse
from collections.abc import Iterator

import pytest

from cli.commands import COMMANDS
from cli.commands.base import BaseCommand, ExecutionContext
from cli.error_handling import ExitCode
from cli.main import main


# ---------------------------------------------------------------------------
# Test command fixtures
# ---------------------------------------------------------------------------


class _EchoCommand(BaseCommand):
    name = "echo"
    help_text = "Echo back the message argument"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("message", type=str, help="Message to echo")

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        print(args.message)
        return ExitCode.SUCCESS


class _FailingCommand(BaseCommand):
    name = "fail"
    help_text = "A command that always fails"

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        raise RuntimeError("Intentional failure")


class _InterruptibleCommand(BaseCommand):
    name = "interrupt"
    help_text = "A command that simulates Ctrl+C"

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        raise KeyboardInterrupt


@pytest.fixture(autouse=True)
def _register_and_cleanup_commands() -> Iterator[None]:
    test_commands = {"echo": _EchoCommand, "fail": _FailingCommand, "interrupt": _InterruptibleCommand}
    COMMANDS.update(test_commands)
    yield
    for key in test_commands:
        COMMANDS.pop(key, None)


# ---------------------------------------------------------------------------
# Help and version
# ---------------------------------------------------------------------------


class TestHelpAndVersion:
    def test_no_args_prints_help_and_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([])
        assert rc == ExitCode.SUCCESS
        stdout = capsys.readouterr().out
        assert "usage:" in stdout.lower()

    def test_help_flag_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == ExitCode.SUCCESS
        stdout = capsys.readouterr().out
        assert "usage:" in stdout.lower()

    def test_version_prints_version_and_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["--version"])
        assert rc == ExitCode.SUCCESS
        stdout = capsys.readouterr().out.strip()
        assert len(stdout) > 0


# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------


class TestSharedOptions:
    def test_verbose_flag(self) -> None:
        rc = main(["--verbose", "echo", "hello"])
        assert rc == ExitCode.SUCCESS

    def test_debug_flag(self) -> None:
        rc = main(["--debug", "echo", "hello"])
        assert rc == ExitCode.SUCCESS

    def test_data_dir_option(self) -> None:
        rc = main(["--data-dir", "/tmp/data", "echo", "hello"])
        assert rc == ExitCode.SUCCESS


# ---------------------------------------------------------------------------
# Command dispatch
# ---------------------------------------------------------------------------


class TestCommandDispatch:
    def test_known_command_executes_and_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["echo", "Hello World"])
        assert rc == ExitCode.SUCCESS
        stdout = capsys.readouterr().out.strip()
        assert stdout == "Hello World"

    def test_unknown_command_exits_two(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["bogus"])
        assert exc_info.value.code == ExitCode.VALIDATION_ERROR
        stderr = capsys.readouterr().err
        assert "bogus" in stderr

    def test_command_with_args_parsed_correctly(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["echo", "custom message"])
        assert rc == ExitCode.SUCCESS
        stdout = capsys.readouterr().out.strip()
        assert stdout == "custom message"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_failing_command_returns_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["fail"])
        assert rc == ExitCode.ERROR
        stderr = capsys.readouterr().err
        assert "Intentional failure" in stderr

    def test_keyboard_interrupt_returns_130(self) -> None:
        rc = main(["interrupt"])
        assert rc == ExitCode.INTERRUPTED
