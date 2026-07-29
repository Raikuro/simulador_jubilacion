"""CLI performance benchmarks.

Measures CLI startup overhead and command execution times
through the public ``main()`` interface.
"""

from __future__ import annotations

import gc
import time
from pathlib import Path

import pytest
import yaml

from cli.error_handling import ExitCode
from cli.main import main

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MINIMAL_STUDY_YAML = """\
metadata:
  name: "CLI Benchmark"
dataset:
  identifier: "v1"
cohorts:
  type: "monthly_rolling"
  window_years: 1
allocation_policies:
  - name: "p"
    type: "ConstantAllocationPolicy"
    equity_ratio: 0.75
withdrawal_policy:
  type: "ConstantInflationAdjustedWithdrawalPolicy"
  withdrawal_rate: 0.04
parameters:
  equity_allocation: [0.50]
"""


# ===================================================================
# 1. CLI Startup Overhead
# ===================================================================


class TestCliStartupOverhead:
    """Measure CLI command dispatch overhead independent of command logic."""

    def test_help_startup_time(self) -> None:
        gc.collect()
        t0 = time.perf_counter()
        with pytest.raises(SystemExit):
            main(["--help"])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] cli --help (startup + help): {elapsed:.4f}s")

    def test_version_startup_time(self) -> None:
        gc.collect()
        t0 = time.perf_counter()
        rc = main(["--version"])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] cli --version: {elapsed:.4f}s")
        assert rc == ExitCode.SUCCESS

    def test_unknown_command_still_parses(self) -> None:
        gc.collect()
        t0 = time.perf_counter()
        with pytest.raises(SystemExit):
            main(["nonexistent-command"])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] cli unknown-command: {elapsed:.4f}s")


# ===================================================================
# 2. CLI Validate Performance
# ===================================================================


class TestCliValidatePerformance:
    """Time the validate command through the full CLI pipeline."""

    @pytest.fixture
    def study_path(self, tmp_path: Path) -> Path:
        p = tmp_path / "bench_study.yaml"
        p.write_text(_MINIMAL_STUDY_YAML, encoding="utf-8")
        return p

    @pytest.fixture
    def config_path(self, tmp_path: Path) -> Path:
        p = tmp_path / "bench_config.yaml"
        p.write_text(
            yaml.dump(
                {
                    "database": {"path": "test.db"},
                    "output": {"default_format": "csv", "default_directory": "./out"},
                    "execution": {"default_workers": 4},
                    "logging": {"level": "INFO"},
                },
                default_flow_style=False,
            ),
            encoding="utf-8",
        )
        return p

    def test_validate_study_time(
        self, study_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        gc.collect()
        t0 = time.perf_counter()
        rc = main(["validate", str(study_path)])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] cli validate study: {elapsed:.4f}s")
        # Expected: dataset not resolvable -> validation error
        assert rc != ExitCode.SUCCESS

    def test_validate_study_with_config_flag(
        self,
        study_path: Path,
        config_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        gc.collect()
        t0 = time.perf_counter()
        rc = main(["--config", str(config_path), "validate", str(study_path)])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] cli --config + validate: {elapsed:.4f}s")
        assert rc != ExitCode.SUCCESS


# ===================================================================
# 3. CLI Config Command Performance
# ===================================================================


class TestCliConfigPerformance:
    """Time config subcommand execution through the CLI."""

    @pytest.fixture
    def cfg_path(self, tmp_path: Path) -> Path:
        return tmp_path / "perf_config.yaml"

    def test_config_validate_valid(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cfg = tmp_path / "valid_config.yaml"
        cfg.write_text(
            yaml.dump(
                {
                    "database": {"path": "t.db"},
                    "output": {"default_format": "csv", "default_directory": "./r"},
                    "execution": {"default_workers": 4},
                    "logging": {"level": "INFO"},
                },
                default_flow_style=False,
            ),
            encoding="utf-8",
        )
        gc.collect()
        t0 = time.perf_counter()
        rc = main(["config", "validate", "--file", str(cfg)])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] config validate valid: {elapsed:.4f}s")
        assert rc == ExitCode.SUCCESS

    def test_config_validate_invalid(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cfg = tmp_path / "bad_config.yaml"
        cfg.write_text("database:\n  path: 123\n", encoding="utf-8")
        gc.collect()
        t0 = time.perf_counter()
        rc = main(["config", "validate", "--file", str(cfg)])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] config validate invalid: {elapsed:.4f}s")
        assert rc == ExitCode.CONFIGURATION_ERROR

    def test_config_list_empty(
        self, cfg_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "cli.commands.config_command._DEFAULT_CONFIG_PATH", cfg_path
        )
        gc.collect()
        t0 = time.perf_counter()
        rc = main(["config", "list"])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] config list (no config): {elapsed:.4f}s")
        assert rc == ExitCode.SUCCESS

    def test_config_set_and_get_round_trip(
        self, cfg_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "cli.commands.config_command._DEFAULT_CONFIG_PATH", cfg_path
        )
        gc.collect()
        t0 = time.perf_counter()
        rc_set = main(["config", "set", "output.directory", "./perf"])
        assert rc_set == ExitCode.SUCCESS
        rc_get = main(["config", "get", "output.directory"])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] config set+get round-trip: {elapsed:.4f}s")
        assert rc_get == ExitCode.SUCCESS


# ===================================================================
# 4. CLI List Performance
# ===================================================================


class TestCliListPerformance:
    """Time the list command with and without a populated database."""

    def test_list_no_database(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "cli.commands.list_command._DEFAULT_DB_PATH",
            "/tmp/__perf_nonexistent__/studies.db",
        )
        gc.collect()
        t0 = time.perf_counter()
        rc = main(["list"])
        elapsed = time.perf_counter() - t0
        print(f"\n[BENCHMARK] list (no database): {elapsed:.4f}s")
        assert rc != ExitCode.SUCCESS
