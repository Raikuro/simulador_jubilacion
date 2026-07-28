"""CLI entry point — parser, dispatch, and error handling."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import version

from cli.commands import COMMANDS
from cli.commands.base import ExecutionContext
from cli.error_handling import ExitCode


def _get_version() -> str:
    try:
        return version("retirement-simulator")
    except Exception:
        return "0.1.0"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sim-retire",
        description="FIRE Backtesting Framework CLI",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to dataset directory",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="~/.sim-retire/config.yaml",
        help="Path to configuration file (default: ~/.sim-retire/config.yaml)",
    )
    subparsers = parser.add_subparsers(dest="command", title="Commands")
    for name, cmd_cls in sorted(COMMANDS.items()):
        sub = subparsers.add_parser(name, help=cmd_cls.help_text)
        cmd_cls().configure_parser(sub)
    return parser


def _create_context(args: argparse.Namespace) -> ExecutionContext:
    return ExecutionContext(
        verbose=args.verbose,
        debug=args.debug,
        data_dir=args.data_dir,
        config_file=args.config,
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(_get_version())
        return ExitCode.SUCCESS

    if args.command is None:
        parser.print_help()
        return ExitCode.SUCCESS

    cmd_cls = COMMANDS.get(args.command)
    if cmd_cls is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return ExitCode.VALIDATION_ERROR

    context = _create_context(args)
    try:
        return cmd_cls().execute(context, args)
    except KeyboardInterrupt:
        print(file=sys.stderr)
        return ExitCode.INTERRUPTED
    except Exception as exc:
        from cli.error_handling import handle_exception

        return handle_exception(exc)
