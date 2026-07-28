"""Command registry."""

from cli.commands.base import BaseCommand
from cli.commands.list_command import ListCommand
from cli.commands.run_command import RunCommand
from cli.commands.validate_command import ValidateCommand

COMMANDS: dict[str, type[BaseCommand]] = {
    "validate": ValidateCommand,
    "run": RunCommand,
    "list": ListCommand,
}
