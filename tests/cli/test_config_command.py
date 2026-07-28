"""Test configuration command."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from cli.commands.config_command import ConfigCommand, Configuration
from cli.error_handling import ExitCode


def test_config_load_yaml():
    """Test configuration loading from YAML."""
    config_data = {"database": {"path": "test.db"}, "output": {"default_format": "csv"}}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = Path(f.name)

    try:
        from cli.commands.config_command import _load_config_yaml
        loaded = _load_config_yaml(temp_path)

        assert loaded["database"]["path"] == "test.db"
        assert loaded["output"]["default_format"] == "csv"
    finally:
        temp_path.unlink()


def test_config_from_dict():
    """Test Configuration.from_dict() creates proper model."""
    data = {
        "database": {"path": "~/.sim-retire/config.yaml"},
        "output": {"default_format": "csv", "default_directory": "./results/"},
        "execution": {"default_workers": 4, "max_workers": 16},
        "logging": {"level": "INFO", "file": "~/.sim-retire/sim-retire.log"}
    }

    config = Configuration.from_dict(data)

    assert config.database["path"] == "~/.sim-retire/config.yaml"
    assert config.output["default_format"] == "csv"
    assert config.execution["default_workers"] == 4
    assert config.logging["level"] == "INFO"


def test_config_to_dict():
    """Test Configuration.to_dict() serializes properly."""
    config = Configuration(
        database={"path": "test.db"},
        output={"default_format": "csv"},
        execution={"default_workers": 4},
        logging={"level": "INFO"}
    )

    data = config.to_dict()

    assert data["database"]["path"] == "test.db"
    assert data["output"]["default_format"] == "csv"
    assert data["execution"]["default_workers"] == 4
    assert data["logging"]["level"] == "INFO"


def test_config_validate():
    """Test Configuration.validate() checks all required fields."""
    config = Configuration(
        database={"path": "test.db"},
        output={"default_format": "csv", "default_directory": "./results/"},
        execution={"default_workers": 4},
        logging={"level": "INFO"}
    )

    errors = config.validate()
    assert errors == []

    config_missing = Configuration(
        database={},
        output={},
        execution={},
        logging={}
    )

    errors = config_missing.validate()
    assert "database section is required" in errors
    assert "database.path must be a string" in errors
    assert "output.default_format must be a string" in errors
    assert "output.default_directory must be a string" in errors
    assert "execution.default_workers must be an integer" in errors
    assert "logging.level must be a string" in errors


def test_config_set_get_integration():
    """Test end-to-end config set/get operations."""
    with patch('pathlib.Path.exists', return_value=False), \
         patch('pathlib.Path.mkdir'), \
         patch('pathlib.Path.write_text') as mock_write, \
         patch('pathlib.Path.read_text', return_value=''):

        command = ConfigCommand()

        # Test setting a value
        args = type('Args', (), {})()
        args.key = "output.directory"
        args.value = "./custom_dir"

        result = command._set_config_value(args)
        assert result == ExitCode.SUCCESS

        # Verify write_text was called with proper YAML
        mock_write.assert_called()
        # Write_text is called with (content, encoding='utf-8')
        # So we need to access call_args[0][0] for content
        written_content = mock_write.call_args[0][0]
        data = yaml.safe_load(written_content)
        assert data["output"]["directory"] == "./custom_dir"


def test_config_get_integration():
    """Test end-to-end config get operations."""
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value='output:\n  directory: ./custom_dir\ndatabase:\n  path: test.db'):

        args = type('Args', (), {})()
        args.key = "output.directory"

        command = ConfigCommand()
        result = command._get_config_value(args)
        assert result == ExitCode.SUCCESS


def test_config_list_integration():
    """Test end-to-end config list operations."""
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value='output:\n  directory: ./custom_dir\ndatabase:\n  path: test.db'):

        command = ConfigCommand()
        result = command._list_config_values()
        assert result == ExitCode.SUCCESS


def test_config_validate_integration():
    """Test end-to-end config validation with YAML."""
    config_yaml = """
database:
  path: ~/.sim-retire/config.yaml
output:
  default_format: csv
  default_directory: ./results/
execution:
  default_workers: 4
  max_workers: 16
  timeout_seconds: 3600
logging:
  level: INFO
  file: ~/.sim-retire/sim-retire.log
"""

    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value=config_yaml), \
         patch.object(Configuration, 'validate', return_value=[]):

        args = type('Args', (), {})()
        args.file = None

        command = ConfigCommand()
        result = command._validate_config(args)
        assert result == ExitCode.SUCCESS


def test_config_parse_key():
    """Test key parsing from dot notation."""
    from cli.commands.config_command import _parse_key

    category, key = _parse_key("output.directory")
    assert category == "output"
    assert key == "directory"

    category, key = _parse_key("database.path")
    assert category == "database"
    assert key == "path"


def test_config_resolve_nested_dict():
    """Test nested dictionary resolution."""
    from cli.commands.config_command import _resolve_nested_dict

    data = {
        "output": {
            "directory": "./results",
            "format": "csv"
        },
        "database": {
            "path": "test.db"
        }
    }

    assert _resolve_nested_dict(data, "output.directory") == "./results"
    assert _resolve_nested_dict(data, "output.format") == "csv"
    assert _resolve_nested_dict(data, "database.path") == "test.db"
    assert _resolve_nested_dict(data, "nonexistent.key") is None


def test_config_set_nested_dict():
    """Test nested dictionary setting with dot notation."""
    from cli.commands.config_command import _set_nested_dict

    data = {}
    _set_nested_dict(data, "output.directory", "./results")

    assert data["output"]["directory"] == "./results"

    _set_nested_dict(data, "output.format", "csv")
    assert data["output"]["format"] == "csv"


def test_config_value_yaml_parsing():
    """Test that config values can be parsed as YAML."""
    from cli.commands.config_command import _load_config_yaml

    yaml_content = """
database:
  path: test.db
  auto_backup: true
output:
  default_format: csv
  default_directory: ./results/
execution:
  default_workers: 4
  max_workers: 16
  timeout_seconds: 3600
logging:
  level: INFO
  file: ~/.sim-retire/sim-retire.log
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = Path(f.name)

    try:
        loaded = _load_config_yaml(temp_path)
        assert loaded["database"]["auto_backup"] is True
        assert loaded["output"]["default_format"] == "csv"
    finally:
        temp_path.unlink()


def test_config_error_handling():
    """Test configuration error handling."""
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', side_effect=Exception("Read error")):

        args = type('Args', (), {})()
        args.key = "output.directory"

        command = ConfigCommand()
        result = command._get_config_value(args)
        assert result == ExitCode.CONFIGURATION_ERROR


def test_config_validate_error():
    """Test validation error handling."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: [")
        temp_path = Path(f.name)
    
    try:
        args = type('Args', (), {})()
        args.file = str(temp_path)
        
        command = ConfigCommand()
        
        result = command._validate_config(args)
        assert result == ExitCode.CONFIGURATION_ERROR
    finally:
        temp_path.unlink()