"""Tests for grid plan building in ``cli.builders``.

Covers:
- ``build_dataset_family`` canonical resolution and prefix rejection
- parameter -> policy wiring (equity_allocation, withdrawal_rate)
- horizon axis -> per-unit horizons
- literal policy fallback when parameters are absent
- real ERN construction: exactly 313,020 units with 5x9x4 configs x 1739 cohorts
- shorter ERN horizons are prefix slices of the canonical trajectory
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from cli.builders import (
    build_dataset_family,
    build_grid_research_plan,
    build_parameter_configs,
)
from cli.policies import ConstantAllocationPolicy, FixedRealWithdrawalPolicy
from engine.domain.model.asset import AssetClass
from engine.domain.model.dataset import Dataset
from engine.domain.model.market_snapshot import MarketSnapshot
from engine.domain.model.money import Currency, Money
from infrastructure.persistence.context import _dataset_to_dict
from infrastructure.persistence.dataset_cache import clear_default_dataset_cache
from research.domain.cohort.generator import CohortGenerator
from research.domain.cohort.specification import CohortSpecification
from research.domain.experiment.definition import ExperimentDefinition
from research.domain.parameter.configuration import ParameterConfiguration
from research.domain.plan import ResearchPlan

EQ = AssetClass(id="equity", name="", description="")
BD = AssetClass(id="bond", name="", description="")

ERN_DATA_DIR = Path("data/ern").resolve()

_DEFAULT_WEALTH = Money(Decimal("1000000"), Currency.EUR)


@pytest.fixture(autouse=True)
def _isolated_default_cache() -> Iterator[None]:
    clear_default_dataset_cache()
    yield
    clear_default_dataset_cache()


# ---------------------------------------------------------------------------
# Synthetic dataset factories (written to a temp data dir)
# ---------------------------------------------------------------------------


def _snapshot(month: int, equity: Decimal = Decimal("100.00")) -> MarketSnapshot:
    return MarketSnapshot(
        date=date(2000 + (month - 1) // 12, (month - 1) % 12 + 1, 1),
        index_levels={EQ: equity, BD: equity / Decimal("2")},
        inflation=Decimal("0.00"),
        inflation_cumulative=Decimal("0.00"),
        is_ath=True,
        is_underwater=False,
        running_ath=equity,
    )


def _make_dataset(num_months: int, equity: Decimal = Decimal("100.00")) -> Dataset:
    return Dataset(
        snapshots=tuple(_snapshot(m, equity) for m in range(1, num_months + 1)),
        frequency="monthly",
        version="1.0",
    )


def _write_dataset(data_dir: Path, identifier: str, dataset: Dataset) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / f"{identifier}.json").write_text(
        json.dumps(_dataset_to_dict(dataset)), encoding="utf-8"
    )


def _write_prefix_consistent_family(data_dir: Path) -> None:
    """h36 (48 snapshots) and h48 (60 snapshots) sharing one trajectory."""
    long_series = _make_dataset(60)
    _write_dataset(data_dir, "ern_h48", long_series)
    _write_dataset(data_dir, "ern_h36", long_series.slice(date(2000, 1, 1), 48))


def _experiment_def(
    dataset: Dataset, cohorts: tuple[CohortSpecification, ...], horizon_months: int
) -> ExperimentDefinition:
    return ExperimentDefinition(
        name="grid",
        description="grid test",
        dataset=dataset,
        horizon_months=horizon_months,
        initial_wealth=_DEFAULT_WEALTH,
        cohorts=cohorts,
        allocation_policies=(ConstantAllocationPolicy(equity_allocation=Decimal("0.75")),),
        withdrawal_policies=(FixedRealWithdrawalPolicy(withdrawal_rate=Decimal("0.04")),),
    )


# ---------------------------------------------------------------------------
# build_dataset_family
# ---------------------------------------------------------------------------


class TestBuildDatasetFamily:
    def test_resolves_longest_dataset_as_canonical(self, tmp_path: Path) -> None:
        _write_prefix_consistent_family(tmp_path)

        family = build_dataset_family(
            [
                {"identifier": "ern_h36", "horizon_years": 3},
                {"identifier": "ern_h48", "horizon_years": 4},
            ],
            str(tmp_path),
        )

        assert len(family.canonical.snapshots) == 60
        assert set(family.horizons) == {3, 4}

    def test_rejects_prefix_inconsistent_family(self, tmp_path: Path) -> None:
        long_series = _make_dataset(60)
        bad_short = _make_dataset(48, equity=Decimal("99.00"))
        _write_dataset(tmp_path, "ern_h48", long_series)
        _write_dataset(tmp_path, "ern_bad_h36", bad_short)

        with pytest.raises(ValueError, match="not a prefix of the canonical trajectory"):
            build_dataset_family(
                [
                    {"identifier": "ern_h48", "horizon_years": 4},
                    {"identifier": "ern_bad_h36", "horizon_years": 3},
                ],
                str(tmp_path),
            )

    def test_rejects_duplicate_horizon_years(self, tmp_path: Path) -> None:
        _write_prefix_consistent_family(tmp_path)

        with pytest.raises(ValueError, match="duplicate horizon_years"):
            build_dataset_family(
                [
                    {"identifier": "ern_h36", "horizon_years": 3},
                    {"identifier": "ern_h48", "horizon_years": 3},
                ],
                str(tmp_path),
            )

    def test_rejects_invalid_entry(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="horizon_years must be a positive integer"):
            build_dataset_family([{"identifier": "ern_h36", "horizon_years": 0}], str(tmp_path))


# ---------------------------------------------------------------------------
# build_grid_research_plan — parameter -> policy wiring
# ---------------------------------------------------------------------------


class TestGridPlanParameterToPolicyWiring:
    def _build(self, tmp_path: Path, configs: tuple[ParameterConfiguration, ...]) -> ResearchPlan:
        _write_prefix_consistent_family(tmp_path)
        family = build_dataset_family(
            [
                {"identifier": "ern_h36", "horizon_years": 3},
                {"identifier": "ern_h48", "horizon_years": 4},
            ],
            str(tmp_path),
        )
        cohorts = CohortGenerator.generate_rolling_monthly(family.canonical, 48)
        exp_def = _experiment_def(family.canonical, cohorts, 48)
        return build_grid_research_plan(
            exp_def,
            family,
            cohorts,
            configs,
            ConstantAllocationPolicy(equity_allocation=Decimal("0.75")),
            FixedRealWithdrawalPolicy(withdrawal_rate=Decimal("0.04")),
            default_horizon_years=4,
        )

    def test_equity_allocation_param_resolves_to_constant_policy(self, tmp_path: Path) -> None:
        plan = self._build(tmp_path, (ParameterConfiguration({"equity_allocation": 0.25}),))

        for unit in plan:
            assert isinstance(unit.allocation_policy, ConstantAllocationPolicy)
            assert unit.allocation_policy.equity_allocation == Decimal("0.25")

    def test_withdrawal_rate_param_resolves_to_fixed_real_policy(self, tmp_path: Path) -> None:
        plan = self._build(tmp_path, (ParameterConfiguration({"withdrawal_rate": 0.05}),))

        for unit in plan:
            assert isinstance(unit.withdrawal_policy, FixedRealWithdrawalPolicy)
            assert unit.withdrawal_policy.withdrawal_rate == Decimal("0.05")

    def test_different_configs_create_different_policies(self, tmp_path: Path) -> None:
        plan = self._build(
            tmp_path,
            (
                ParameterConfiguration({"equity_allocation": 0.75, "withdrawal_rate": 0.04}),
                ParameterConfiguration({"equity_allocation": 0.50, "withdrawal_rate": 0.05}),
            ),
        )

        unit_a = plan.units[0]
        unit_b = plan.units[1]
        alloc_a = cast(ConstantAllocationPolicy, unit_a.allocation_policy)
        alloc_b = cast(ConstantAllocationPolicy, unit_b.allocation_policy)
        withd_a = cast(FixedRealWithdrawalPolicy, unit_a.withdrawal_policy)
        withd_b = cast(FixedRealWithdrawalPolicy, unit_b.withdrawal_policy)
        assert alloc_a.equity_allocation != alloc_b.equity_allocation
        assert withd_a.withdrawal_rate != withd_b.withdrawal_rate

    def test_horizon_axis_produces_correct_per_unit_horizons(self, tmp_path: Path) -> None:
        plan = self._build(
            tmp_path,
            (
                ParameterConfiguration({"horizon_years": 3}),
                ParameterConfiguration({"horizon_years": 4}),
            ),
        )

        horizons = {unit.horizon_months for unit in plan}
        assert horizons == {36, 48}

    def test_literal_policies_fallback_when_param_absent(self, tmp_path: Path) -> None:
        plan = self._build(tmp_path, (ParameterConfiguration({"glidepath_duration": 10}),))

        unit = plan.units[0]
        alloc = cast(ConstantAllocationPolicy, unit.allocation_policy)
        withd = cast(FixedRealWithdrawalPolicy, unit.withdrawal_policy)
        assert alloc.equity_allocation == Decimal("0.75")
        assert withd.withdrawal_rate == Decimal("0.04")
        assert unit.horizon_months == 48


# ---------------------------------------------------------------------------
# Real ERN grid construction
# ---------------------------------------------------------------------------


class TestErnGridConstruction:
    def test_grid_produces_exactly_313020_units(self) -> None:
        family = build_dataset_family(
            [
                {"identifier": "ern_swr_h360", "horizon_years": 30},
                {"identifier": "ern_swr_h480", "horizon_years": 40},
                {"identifier": "ern_swr_h600", "horizon_years": 50},
                {"identifier": "ern_swr_h720", "horizon_years": 60},
            ],
            str(ERN_DATA_DIR),
        )
        cohorts = CohortGenerator.generate_rolling_monthly(family.canonical, 720)
        configs = build_parameter_configs(
            {
                "equity_allocation": [1.0, 0.75, 0.5, 0.25, 0.0],
                "withdrawal_rate": [
                    0.03,
                    0.0325,
                    0.035,
                    0.0375,
                    0.04,
                    0.0425,
                    0.045,
                    0.0475,
                    0.05,
                ],
                "horizon_years": [30, 40, 50, 60],
            }
        )
        exp_def = _experiment_def(family.canonical, cohorts, 720)
        plan = build_grid_research_plan(
            exp_def,
            family,
            cohorts,
            configs,
            ConstantAllocationPolicy(equity_allocation=Decimal("0.75")),
            FixedRealWithdrawalPolicy(withdrawal_rate=Decimal("0.04")),
            default_horizon_years=60,
        )

        assert len(cohorts) == 1739
        assert len(configs) == 180
        assert len(plan) == 313_020
        assert len(plan) == 5 * 9 * 4 * 1739

    def test_grid_parameter_combinations_are_exact(self) -> None:
        family = build_dataset_family(
            [
                {"identifier": "ern_swr_h360", "horizon_years": 30},
                {"identifier": "ern_swr_h480", "horizon_years": 40},
                {"identifier": "ern_swr_h600", "horizon_years": 50},
                {"identifier": "ern_swr_h720", "horizon_years": 60},
            ],
            str(ERN_DATA_DIR),
        )
        cohorts = CohortGenerator.generate_rolling_monthly(family.canonical, 720)
        configs = build_parameter_configs(
            {
                "equity_allocation": [1.0, 0.75, 0.5, 0.25, 0.0],
                "withdrawal_rate": [
                    0.03,
                    0.0325,
                    0.035,
                    0.0375,
                    0.04,
                    0.0425,
                    0.045,
                    0.0475,
                    0.05,
                ],
                "horizon_years": [30, 40, 50, 60],
            }
        )
        exp_def = _experiment_def(family.canonical, cohorts, 720)
        plan = build_grid_research_plan(
            exp_def,
            family,
            cohorts,
            configs,
            ConstantAllocationPolicy(equity_allocation=Decimal("0.75")),
            FixedRealWithdrawalPolicy(withdrawal_rate=Decimal("0.04")),
            default_horizon_years=60,
        )

        weights = {p.get("equity_allocation") for p in configs}
        rates = {p.get("withdrawal_rate") for p in configs}
        horizons = {p.get("horizon_years") for p in configs}
        assert weights == {1.0, 0.75, 0.5, 0.25, 0.0}
        assert rates == {
            0.03,
            0.0325,
            0.035,
            0.0375,
            0.04,
            0.0425,
            0.045,
            0.0475,
            0.05,
        }
        assert horizons == {30, 40, 50, 60}
        identities = {(u.cohort.start_date, u.parameter_config) for u in plan}
        assert len(identities) == len(plan)

    def test_shorter_horizons_are_prefix_slices_of_canonical(self) -> None:
        family = build_dataset_family(
            [
                {"identifier": "ern_swr_h360", "horizon_years": 30},
                {"identifier": "ern_swr_h480", "horizon_years": 40},
                {"identifier": "ern_swr_h600", "horizon_years": 50},
                {"identifier": "ern_swr_h720", "horizon_years": 60},
            ],
            str(ERN_DATA_DIR),
        )
        cohorts = CohortGenerator.generate_rolling_monthly(family.canonical, 720)
        configs = build_parameter_configs(
            {
                "equity_allocation": [1.0],
                "withdrawal_rate": [0.04],
                "horizon_years": [30, 60],
            }
        )
        exp_def = _experiment_def(family.canonical, cohorts, 720)
        plan = build_grid_research_plan(
            exp_def,
            family,
            cohorts,
            configs,
            ConstantAllocationPolicy(equity_allocation=Decimal("0.75")),
            FixedRealWithdrawalPolicy(withdrawal_rate=Decimal("0.04")),
            default_horizon_years=60,
        )

        sample_cohort = cohorts[0]
        short_units = [u for u in plan if u.parameter_config.get("horizon_years") == 30]
        long_units = [u for u in plan if u.parameter_config.get("horizon_years") == 60]
        assert short_units[0].cohort.start_date == sample_cohort.start_date
        assert long_units[0].cohort.start_date == sample_cohort.start_date
        assert short_units[0].horizon_months == 360
        assert long_units[0].horizon_months == 720
        assert short_units[0].dataset.snapshots == long_units[0].dataset.snapshots[:360]
        # The declared h360 trajectory must be value-identical to the prefix slice.
        assert short_units[0].dataset.snapshots == tuple(family.horizons[30].snapshots[:360])


# ---------------------------------------------------------------------------
# CLI plumbing (real ERN data + example grid YAML)
# ---------------------------------------------------------------------------


class TestErnGridCli:
    GRID_YAML = Path("examples/studies/ern_grid.yaml").resolve()

    def test_run_dry_run_reports_313020_units(self, capsys: pytest.CaptureFixture[str]) -> None:
        from cli.main import main

        rc = main(["--data-dir", str(ERN_DATA_DIR), "run", "--dry-run", str(self.GRID_YAML)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Cohorts:        1739" in out
        assert "Parameters:     180" in out
        assert "Total Units:    313,020 simulations" in out

    def test_validate_understands_grid_plan(self, capsys: pytest.CaptureFixture[str]) -> None:
        from cli.main import main

        rc = main(["--data-dir", str(ERN_DATA_DIR), "validate", str(self.GRID_YAML)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Cohorts: 1739 valid" in out
        assert "Parameters: 180 valid" in out
        assert "Plan: 313,020 unique simulation units" in out
        assert "Validation: PASSED" in out
