"""Command registry."""

from cli.commands.base import BaseCommand

COMMANDS: dict[str, type[BaseCommand]] = {}
