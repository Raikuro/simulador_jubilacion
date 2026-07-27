"""Tests for BaseCommand and ExecutionContext."""

from __future__ import annotations

import argparse

import pytest

from cli.commands.base import BaseCommand, ExecutionContext


class TestBaseCommand:
    def test_execute_raises_not_implemented(self) -> None:
        cmd = BaseCommand()
        ctx = ExecutionContext()
        args = argparse.Namespace()
        with pytest.raises(NotImplementedError):
            cmd.execute(ctx, args)

    def test_configure_parser_is_noop_by_default(self) -> None:
        cmd = BaseCommand()
        parser = argparse.ArgumentParser()
        cmd.configure_parser(parser)
        assert True  # No exception means it's a no-op

    def test_name_and_help_text_default_to_empty(self) -> None:
        assert BaseCommand.name == ""
        assert BaseCommand.help_text == ""


class TestExecutionContext:
    def test_default_construction(self) -> None:
        ctx = ExecutionContext()
        assert ctx.verbose is False
        assert ctx.debug is False
        assert ctx.data_dir is None

    def test_custom_construction(self) -> None:
        ctx = ExecutionContext(verbose=True, debug=True, data_dir="/data")
        assert ctx.verbose is True
        assert ctx.debug is True
        assert ctx.data_dir == "/data"

    def test_frozen_immutable(self) -> None:
        ctx = ExecutionContext()
        with pytest.raises(AttributeError):
            ctx.verbose = True  # type: ignore[misc]

    def test_partial_custom(self) -> None:
        ctx = ExecutionContext(verbose=True)
        assert ctx.verbose is True
        assert ctx.debug is False
        assert ctx.data_dir is None



