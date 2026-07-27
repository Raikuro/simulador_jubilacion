"""Command registry."""

from cli.commands.base import BaseCommand
from cli.commands.validate_command import ValidateCommand

COMMANDS: dict[str, type[BaseCommand]] = {
    "validate": ValidateCommand,
}
