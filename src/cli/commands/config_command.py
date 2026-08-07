"""ConfigCommand — manage CLI configuration settings."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cli.commands.base import BaseCommand, ExecutionContext
from cli.error_handling import ExitCode

_DEFAULT_CONFIG_PATH = Path("~/.sim-retire/config.yaml").expanduser()


def resolve_config_path(
    context: ExecutionContext | None = None,
    explicit: str | None = None,
) -> Path:
    """Resolve the effective configuration file path.

    Precedence: an explicit CLI path (``--config`` or a subcommand ``--file``)
    wins over the global ``--config`` propagated through ``ExecutionContext``,
    which in turn wins over the packaged default ``~/.sim-retire/config.yaml``.
    """
    if explicit:
        return Path(explicit).expanduser()
    if context is not None and context.config_file:
        return Path(context.config_file).expanduser()
    return _DEFAULT_CONFIG_PATH


def load_configuration(
    context: ExecutionContext | None = None,
) -> Configuration:
    """Load and parse the effective configuration for a CLI invocation.

    Missing/invalid files degrade to an empty ``Configuration`` so other commands
    can apply ``CLI args > config file > defaults`` precedence without failing.
    """
    config_file = resolve_config_path(context)
    try:
        data = _load_config_yaml(config_file)
    except ValueError:
        data = {}
    return Configuration.from_dict(data)


@dataclass
class Configuration:
    """Configuration model for the CLI."""

    database: dict[str, Any]
    output: dict[str, Any]
    execution: dict[str, Any]
    logging: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Configuration:
        """Create a Configuration from a dictionary."""
        return cls(
            database=data.get("database", {}),
            output=data.get("output", {}),
            execution=data.get("execution", {}),
            logging=data.get("logging", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Configuration to dictionary."""
        return {
            "database": self.database,
            "output": self.output,
            "execution": self.execution,
            "logging": self.logging,
        }

    def validate(self) -> list[str]:
        """Validate configuration and return a list of errors."""
        errors: list[str] = []

        if not self.database:
            errors.append("database section is required")

        if not isinstance(self.database.get("path"), str):
            errors.append("database.path must be a string")

        if not isinstance(self.output.get("default_format"), str):
            errors.append("output.default_format must be a string")

        if not isinstance(self.output.get("default_directory"), str):
            errors.append("output.default_directory must be a string")

        if not isinstance(self.execution.get("default_workers"), int):
            errors.append("execution.default_workers must be an integer")

        if not isinstance(self.logging.get("level"), str):
            errors.append("logging.level must be a string")

        return errors


def _load_config_yaml(file_path: Path | None) -> dict[str, Any]:
    """Load configuration from a YAML file."""
    path = file_path or _DEFAULT_CONFIG_PATH

    if not path.exists():
        return {}

    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError(f"Configuration file {path} must be a YAML mapping")
        return data
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in configuration file {path}: {exc}") from exc


def _parse_key(key: str) -> tuple[str, str]:
    """Parse a dot notation key into category and key parts."""
    parts = key.split(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid key format: {key}. Use format 'category.key'")
    return parts[0], parts[1]


def _resolve_nested_dict(data: dict[str, Any], key: str) -> Any:
    """Resolve a nested dictionary using dot notation."""
    current = data

    for part in key.split("."):
        if part not in current:
            return None
        current = current[part]

    return current


def _set_nested_dict(data: dict[str, Any], key: str, value: Any) -> None:
    """Set a nested dictionary using dot notation."""
    current = data

    for i, part in enumerate(key.split(".")):
        if i == len(key.split(".")) - 1:
            current[part] = value
        else:
            if part not in current:
                current[part] = {}
            current = current[part]


class ConfigCommand(BaseCommand):
    name = "config"
    help_text = "Manage and validate configuration settings"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        subparsers = parser.add_subparsers(dest="action", required=True)

        # Set action
        set_parser = subparsers.add_parser("set", help="Set configuration value")
        set_parser.add_argument(
            "key",
            help="Configuration key (e.g., output.directory)",
        )
        set_parser.add_argument(
            "value",
            help="Configuration value",
        )

        # Get action
        get_parser = subparsers.add_parser("get", help="Get configuration value")
        get_parser.add_argument(
            "key",
            help="Configuration key (e.g., output.directory)",
        )

        # Validate action
        validate_parser = subparsers.add_parser("validate", help="Validate configuration")
        validate_parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Configuration file path",
        )

        # List action
        subparsers.add_parser("list", help="List all configuration values")

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        if args.action == "set":
            return self._set_config_value(args, context)
        elif args.action == "get":
            return self._get_config_value(args, context)
        elif args.action == "validate":
            return self._validate_config(args, context)
        elif args.action == "list":
            return self._list_config_values(context)
        else:
            print("ERROR: Unknown action", file=sys.stderr)
            return ExitCode.ERROR

    def _set_config_value(
        self,
        args: argparse.Namespace,
        context: ExecutionContext | None = None,
    ) -> int:
        """Set configuration value."""
        try:
            category, key = _parse_key(args.key)

            # Try to parse value as YAML first, otherwise treat as string
            try:
                value = yaml.safe_load(args.value)
            except yaml.YAMLError:
                value = args.value

            config_file = resolve_config_path(context)

            # Load existing configuration if file exists
            config_data: dict[str, Any] = {}

            if config_file.exists():
                raw = config_file.read_text(encoding="utf-8")
                config_data = yaml.safe_load(raw) or {}

            if category not in config_data:
                config_data[category] = {}

            config_data[category][key] = value

            # Save configuration to file
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text(
                yaml.dump(config_data, default_flow_style=False), encoding="utf-8"
            )

            print(f"Set {args.key} = {value}")
            return ExitCode.SUCCESS

        except Exception as exc:
            print(f"ERROR: Failed to set configuration: {exc}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

    def _get_config_value(
        self,
        args: argparse.Namespace,
        context: ExecutionContext | None = None,
    ) -> int:
        """Get configuration value."""
        try:
            config_file = resolve_config_path(context)

            # Load configuration
            config_data = _load_config_yaml(config_file)

            value = _resolve_nested_dict(config_data, args.key)

            if value is None:
                print(f"Key not found: {args.key}")
                return ExitCode.VALIDATION_ERROR

            # Format output based on value type
            if isinstance(value, (str, int, float)):
                print(f"{args.key}: {value}")
            elif isinstance(value, bool):
                print(f"{args.key}: {str(value).lower()}")
            elif isinstance(value, (dict, list)):
                print(yaml.dump({args.key: value}, default_flow_style=False))
            else:
                print(f"{args.key}: {value}")

            return ExitCode.SUCCESS

        except Exception as exc:
            print(f"ERROR: Failed to get configuration: {exc}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

    def _validate_config(
        self,
        args: argparse.Namespace,
        context: ExecutionContext | None = None,
    ) -> int:
        """Validate configuration."""
        try:
            config_file = resolve_config_path(context, explicit=args.file)
            config_data = _load_config_yaml(config_file)

            config = Configuration.from_dict(config_data)

            errors = config.validate()

            if errors:
                print("ERROR: Configuration validation failed:")
                for error in errors:
                    print(f"  - {error}")
                return ExitCode.CONFIGURATION_ERROR

            print("Configuration is valid")
            return ExitCode.SUCCESS

        except Exception as exc:
            print(f"ERROR: Failed to validate configuration: {exc}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

    def _list_config_values(self, context: ExecutionContext | None = None) -> int:
        """List all configuration values."""
        try:
            config_file = resolve_config_path(context)

            # Load configuration
            config_data = _load_config_yaml(config_file)

            if not config_data:
                print("No configuration file found")
                return ExitCode.SUCCESS

            # Print configuration values
            print("Configuration values:")
            for category, values in config_data.items():
                print(f"  {category}:")
                self._print_dict(values, indent=4)

            return ExitCode.SUCCESS

        except Exception as exc:
            print(f"ERROR: Failed to list configuration: {exc}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

    def _print_dict(self, data: dict[str, Any], indent: int) -> None:
        """Print a dictionary recursively."""
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{' ' * indent}{key}:")
                self._print_dict(value, indent + 2)
            else:
                if isinstance(value, str):
                    display_value = value
                elif isinstance(value, bool):
                    display_value = str(value).lower()
                else:
                    display_value = value
                print(f"{' ' * indent}{key}: {display_value}")
