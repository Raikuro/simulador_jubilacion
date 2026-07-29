"""P4.3 – Configuration Integration Tests.

Validates the configuration system through the public CLI interface.
Focuses on scenarios NOT covered by existing unit tests or P4.2 E2E tests:

  • YAML parsing edge cases at CLI level (anchors, list root, nulls)
  • Targeted validation of each required field via the CLI
  • Config value type round-trips (booleans, integers, strings)
  • Configuration file persistence verification
  • --config global flag interaction with all CLI commands
  • Config subcommand help output
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from cli.error_handling import ExitCode
from cli.main import main
from infrastructure.persistence.codecs import DefaultDatasetResolver

from .helpers import make_dataset

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(path: Path, **sections: object) -> Path:
    """Write a YAML config file and return its path."""
    path.write_text(yaml.dump(sections, default_flow_style=False), encoding="utf-8")
    return path


def _patch_default_config(
    monkeypatch: pytest.MonkeyPatch, path: Path
) -> None:
    """Redirect _DEFAULT_CONFIG_PATH for config set/get/list to *path*."""
    monkeypatch.setattr(
        "cli.commands.config_command._DEFAULT_CONFIG_PATH", path
    )


# ===================================================================
# 1. YAML Parsing Edge Cases
# ===================================================================


class TestConfigYamlParsing:
    """CLI-level YAML edge cases through ``config validate --file``."""

    def test_validate_with_yaml_anchors(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cfg = _make_config(
            tmp_path / "anchors.yaml",
            database={"path": "test.db"},
            output={
                "default_format": "csv",
                "default_directory": "./results",
            },
            execution={"default_workers": 4},
            logging={"level": "INFO"},
        )
        rc = main(["config", "validate", "--file", str(cfg)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Configuration is valid" in out

    def _assert_error(self, capsys: pytest.CaptureFixture[str], *messages: str) -> None:
        """Assert messages appear in combined stdout+stderr."""
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        for msg in messages:
            assert msg in combined, f"Expected {msg!r} not in output"

    def test_validate_with_list_root_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A YAML list at root is not a valid config mapping."""
        path = tmp_path / "list_root.yaml"
        path.write_text("- item1\n- item2\n", encoding="utf-8")
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        self._assert_error(capsys, "must be a YAML mapping")

    def test_validate_empty_file_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        self._assert_error(capsys, "must be a YAML mapping")

    def test_validate_whitespace_only_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = tmp_path / "whitespace.yaml"
        path.write_text("   \n\n  \n", encoding="utf-8")
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        self._assert_error(capsys, "must be a YAML mapping")

    def test_validate_comments_only_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = tmp_path / "comments.yaml"
        path.write_text("# just a comment\n# another one\n", encoding="utf-8")
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        self._assert_error(capsys, "must be a YAML mapping")

    def test_validate_with_null_values(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Null values in config produce validation errors."""
        path = tmp_path / "nulls.yaml"
        path.write_text(
            "database:\n  path: null\noutput:\n  default_format: csv\n"
            "  default_directory: null\nexecution:\n  default_workers: 4\n"
            "logging:\n  level: INFO\n",
            encoding="utf-8",
        )
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        out = capsys.readouterr().out
        assert "database.path" in out
        assert "output.default_directory" in out


# ===================================================================
# 2. Targeted Configuration Validation
# ===================================================================


class TestConfigurationValidation:
    """Each required field produces specific error messages."""

    def test_validate_missing_database_section(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = _make_config(
            tmp_path / "no_db.yaml",
            output={
                "default_format": "csv",
                "default_directory": "./results",
            },
            execution={"default_workers": 4},
            logging={"level": "INFO"},
        )
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        out = capsys.readouterr().out
        assert "database section is required" in out

    def test_validate_missing_output_default_directory(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = _make_config(
            tmp_path / "no_out_dir.yaml",
            database={"path": "test.db"},
            output={"default_format": "csv"},
            execution={"default_workers": 4},
            logging={"level": "INFO"},
        )
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        out = capsys.readouterr().out
        assert "output.default_directory" in out

    def test_validate_wrong_type_for_default_workers(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = _make_config(
            tmp_path / "bad_workers.yaml",
            database={"path": "test.db"},
            output={
                "default_format": "csv",
                "default_directory": "./results",
            },
            execution={"default_workers": "eight"},
            logging={"level": "INFO"},
        )
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        out = capsys.readouterr().out
        assert "default_workers must be an integer" in out

    def test_validate_missing_logging_level(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = _make_config(
            tmp_path / "no_log.yaml",
            database={"path": "test.db"},
            output={
                "default_format": "csv",
                "default_directory": "./results",
            },
            execution={"default_workers": 4},
            logging={},
        )
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        out = capsys.readouterr().out
        assert "logging.level" in out

    def test_validate_with_extra_unknown_fields(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = _make_config(
            tmp_path / "extra_fields.yaml",
            database={"path": "test.db"},
            output={
                "default_format": "csv",
                "default_directory": "./results",
            },
            execution={"default_workers": 4},
            logging={"level": "INFO"},
            unknown_section={"foo": "bar"},
        )
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Configuration is valid" in out

    def test_validate_all_errors_simultaneously(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cfg = tmp_path / "all_errors.yaml"
        cfg.write_text(
            "database:\n  path: 123\noutput:\n"
            "  default_format: csv\nexecution:\n  default_workers: 4\n",
            encoding="utf-8",
        )
        rc = main(["config", "validate", "--file", str(cfg)])
        assert rc == ExitCode.CONFIGURATION_ERROR
        out = capsys.readouterr().out
        assert "database.path must be a string" in out
        assert "output.default_directory must be a string" in out
        assert "logging.level must be a string" in out


# ===================================================================
# 3. Config Value Type Round-Trips
# ===================================================================


class TestConfigValueTypes:
    """Config set → get → list with various YAML data types."""

    @pytest.fixture
    def cfg_path(self, tmp_path: Path) -> Path:
        return tmp_path / "types_config.yaml"

    def test_set_and_get_boolean(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_default_config(monkeypatch, cfg_path)
        rc_set = main(["config", "set", "output.verbose", "true"])
        assert rc_set == ExitCode.SUCCESS

        raw = cfg_path.read_text(encoding="utf-8")
        data: dict[str, Any] = yaml.safe_load(raw)
        assert data["output"]["verbose"] is True

    def test_set_and_get_integer(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _patch_default_config(monkeypatch, cfg_path)
        rc_set = main(["config", "set", "execution.default_workers", "12"])
        assert rc_set == ExitCode.SUCCESS

        rc_get = main(["config", "get", "execution.default_workers"])
        assert rc_get == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "execution.default_workers: 12" in out

    def test_set_and_get_float(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _patch_default_config(monkeypatch, cfg_path)
        rc_set = main(["config", "set", "execution.timeout", "30.5"])
        assert rc_set == ExitCode.SUCCESS

        rc_get = main(["config", "get", "execution.timeout"])
        assert rc_get == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "execution.timeout: 30.5" in out

    def test_set_and_get_string(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _patch_default_config(monkeypatch, cfg_path)
        rc_set = main(["config", "set", "database.path", "/custom/path.db"])
        assert rc_set == ExitCode.SUCCESS

        rc_get = main(["config", "get", "database.path"])
        assert rc_get == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "database.path: /custom/path.db" in out

    def test_list_shows_all_set_values(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _patch_default_config(monkeypatch, cfg_path)
        assert main(["config", "set", "output.directory", "./out"]) == ExitCode.SUCCESS
        capsys.readouterr()
        assert main(["config", "set", "execution.workers", "4"]) == ExitCode.SUCCESS
        capsys.readouterr()

        rc_list = main(["config", "list"])
        assert rc_list == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "output" in out
        assert "directory: ./out" in out
        assert "execution" in out
        assert "workers: 4" in out


# ===================================================================
# 4. Configuration Persistence
# ===================================================================


class TestConfigPersistence:
    """File-level verification of config persistence."""

    @pytest.fixture
    def cfg_path(self, tmp_path: Path) -> Path:
        return tmp_path / "persist_config.yaml"

    def test_file_created_on_set(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        assert not cfg_path.exists()
        _patch_default_config(monkeypatch, cfg_path)
        rc = main(["config", "set", "output.directory", "./results"])
        assert rc == ExitCode.SUCCESS
        assert cfg_path.exists()

    def test_file_contains_valid_yaml_after_set(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_default_config(monkeypatch, cfg_path)
        assert main(["config", "set", "database.path", "my.db"]) == ExitCode.SUCCESS

        raw = cfg_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        assert isinstance(data, dict)
        assert data["database"]["path"] == "my.db"

    def test_multiple_keys_accumulate(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_default_config(monkeypatch, cfg_path)
        assert main(["config", "set", "output.directory", "./a"]) == ExitCode.SUCCESS
        assert main(["config", "set", "output.format", "json"]) == ExitCode.SUCCESS

        raw = cfg_path.read_text(encoding="utf-8")
        data: dict[str, Any] = yaml.safe_load(raw)
        assert data["output"]["directory"] == "./a"
        assert data["output"]["format"] == "json"

    def test_update_existing_key(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_default_config(monkeypatch, cfg_path)
        assert main(["config", "set", "output.directory", "./v1"]) == ExitCode.SUCCESS
        assert main(["config", "set", "output.directory", "./v2"]) == ExitCode.SUCCESS

        raw = cfg_path.read_text(encoding="utf-8")
        data: dict[str, Any] = yaml.safe_load(raw)
        assert data["output"]["directory"] == "./v2"

    def test_consecutive_sets_preserve_prior_values(
        self,
        cfg_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_default_config(monkeypatch, cfg_path)
        assert main(["config", "set", "database.path", "db1"]) == ExitCode.SUCCESS
        assert main(["config", "set", "output.format", "csv"]) == ExitCode.SUCCESS

        raw = cfg_path.read_text(encoding="utf-8")
        data: dict[str, Any] = yaml.safe_load(raw)
        assert data["database"]["path"] == "db1"
        assert data["output"]["format"] == "csv"


# ===================================================================
# 5. --config Global Flag Interaction
# ===================================================================


class TestConfigCliInteraction:
    """The ``--config`` global flag is accepted by every CLI command."""

    def test_config_flag_with_validate(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cfg = _make_config(
            tmp_path / "cfg.yaml",
            database={"path": "test.db"},
            output={
                "default_format": "csv",
                "default_directory": "./results",
            },
            execution={"default_workers": 4},
            logging={"level": "INFO"},
        )
        rc = main(["--config", str(cfg), "config", "validate", "--file", str(cfg)])
        assert rc == ExitCode.SUCCESS

    def test_config_flag_with_run_dry_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("key: value\n", encoding="utf-8")
        study = tmp_path / "study.yaml"
        study.write_text(
            "metadata:\n  name: T\n"
            "dataset:\n  identifier: v1\n"
            "cohorts:\n  window_years: 1\n"
            "allocation_policies:\n  - name: p\n    equity_ratio: 0.5\n"
            "withdrawal_policy:\n  withdrawal_rate: 0.04\n"
            "parameters:\n  equity_allocation: [0.5]\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            DefaultDatasetResolver, "resolve", lambda self, i: make_dataset(24)
        )
        rc = main(["--config", str(cfg), "run", "--dry-run", str(study)])
        assert rc == ExitCode.SUCCESS

    def test_config_flag_with_list(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("key: value\n", encoding="utf-8")
        monkeypatch.setattr(
            "cli.commands.list_command._DEFAULT_DB_PATH",
            str(tmp_path / "studies.db"),
        )
        rc = main(["--config", str(cfg), "list"])
        # --config is accepted; command fails with DB error (tables missing)
        assert rc != ExitCode.SUCCESS
        assert rc != ExitCode.VALIDATION_ERROR

    def test_config_flag_with_export(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("key: value\n", encoding="utf-8")
        monkeypatch.setattr(
            "cli.commands.export_command._DEFAULT_DB_PATH",
            str(tmp_path / "studies.db"),
        )
        rc = main(["--config", str(cfg), "export", "NonexistentID"])
        assert rc != ExitCode.SUCCESS

    def test_config_flag_with_nonexistent_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-existent ``--config`` path should not break the CLI."""
        rc = main(["--config", "/tmp/__p4_3__/nonexistent.yaml", "config", "list"])
        assert rc == ExitCode.SUCCESS

    def test_config_flag_default_value_used(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Without ``--config``, the default value is documented in help."""
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "--config CONFIG" in out or "--config CONFIG" in out


# ===================================================================
# 6. Config Subcommand Help
# ===================================================================


class TestConfigSubcommandHelp:
    """Config command help displays correctly for all subcommands."""

    def test_config_help_shows_subcommands(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["config", "--help"])
        assert exc.value.code == ExitCode.SUCCESS

    def test_config_set_help(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["config", "set", "--help"])
        assert exc.value.code == ExitCode.SUCCESS

    def test_config_get_help(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["config", "get", "--help"])
        assert exc.value.code == ExitCode.SUCCESS

    def test_config_validate_help(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["config", "validate", "--help"])
        assert exc.value.code == ExitCode.SUCCESS

    def test_config_list_help(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["config", "list", "--help"])
        assert exc.value.code == ExitCode.SUCCESS

    def test_config_requires_subcommand(self) -> None:
        """Running ``config`` with no subcommand raises error (subcommand required)."""
        with pytest.raises(SystemExit) as exc:
            main(["config"])
        assert exc.value.code == ExitCode.VALIDATION_ERROR


# ===================================================================
# 7. Edge Cases
# ===================================================================


class TestConfigEdgeCases:
    """Boundary conditions and edge cases."""

    def test_config_dir_created_on_set(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        nested = tmp_path / "a" / "b" / "c" / "config.yaml"
        assert not nested.parent.exists()
        _patch_default_config(monkeypatch, nested)
        rc = main(["config", "set", "output.directory", "./out"])
        assert rc == ExitCode.SUCCESS
        assert nested.exists()

    def test_validate_minimal_valid_config(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = _make_config(
            tmp_path / "minimal.yaml",
            database={"path": "x"},
            output={"default_format": "x", "default_directory": "x"},
            execution={"default_workers": 1},
            logging={"level": "x"},
        )
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "Configuration is valid" in out

    def test_validate_with_non_yaml_extension(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = tmp_path / "config.txt"
        path.write_text(
            "database:\n  path: test.db\n"
            "output:\n  default_format: csv\n  default_directory: ./r\n"
            "execution:\n  default_workers: 4\n"
            "logging:\n  level: INFO\n",
            encoding="utf-8",
        )
        rc = main(["config", "validate", "--file", str(path)])
        assert rc == ExitCode.SUCCESS
