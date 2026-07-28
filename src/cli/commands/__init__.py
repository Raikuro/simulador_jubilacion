"""Command registry."""

from cli.commands.base import BaseCommand
from cli.commands.compare_command import CompareCommand
from cli.commands.export_command import ExportCommand
from cli.commands.list_command import ListCommand
from cli.commands.optimize_command import OptimizeCommand
from cli.commands.run_command import RunCommand
from cli.commands.validate_command import ValidateCommand

COMMANDS: dict[str, type[BaseCommand]] = {
    "validate": ValidateCommand,
    "run": RunCommand,
    "list": ListCommand,
    "export": ExportCommand,
    "optimize": OptimizeCommand,
    "compare": CompareCommand,
}
