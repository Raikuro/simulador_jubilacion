"""Study YAML generation and cell success-rate computation for the ERN E2E.

The harness writes one study YAML per grid cell (weight x rate x horizon).
Each study uses the ERN per-horizon dataset, a static equity/bond allocation,
and the ``FixedRealWithdrawalPolicy`` at the cell's annual withdrawal rate.
"""

from __future__ import annotations

from pathlib import Path

from tests.e2e.cli_harness import CliHarness, CliResult

from .constants import DATASET_SPEC, cell_name


def write_study_yaml(
    path: Path,
    weight: float,
    horizon_years: int,
    rate: float,
) -> str:
    """Write a per-cell study YAML and return its metadata name."""
    identifier, _ = DATASET_SPEC[horizon_years]
    name = cell_name(weight, horizon_years, rate)
    description = (
        f"ERN SWR Part 1 replication cell: {int(weight * 100)}/{int((1 - weight) * 100)} "
        f"allocation, {horizon_years}y, {rate * 100:.2f}% real withdrawal."
    )
    yaml_text = f"""metadata:
  name: "{name}"
  version: "1.0"
  description: "{description}"

dataset:
  identifier: "{identifier}"

cohorts:
  type: "monthly_rolling"
  window_years: {horizon_years}

allocation_policies:
  - name: "Static {int(weight * 100)}/{int((1 - weight) * 100)}"
    type: "ConstantAllocationPolicy"
    equity_ratio: {weight}

withdrawal_policy:
  type: "FixedRealWithdrawalPolicy"
  withdrawal_rate: {rate}

parameters:
  equity_allocation: [{weight}]
"""
    path.write_text(yaml_text, encoding="utf-8")
    return name


def cell_success_rate(
    harness: CliHarness,
    study_yaml: Path,
    workers: int = 4,
) -> float:
    """Run one cell study and return the observable success rate (percent).

    The rate is derived exclusively from the CLI completion summary
    (``Units Run`` / ``Units Failed``), i.e. from public observable output.
    """
    result: CliResult = harness.run_study(study_yaml, workers=workers)
    if result.exit_code != 0 or result.units_run is None or result.units_failed is None:
        raise RuntimeError(
            f"sim-retire run failed (exit={result.exit_code}): "
            f"{result.stderr or result.stdout}"
        )
    total = result.units_run
    failed = result.units_failed
    if failed > total:
        raise RuntimeError(
            f"CLI reported {failed} failed units of {total} (inconsistent output)."
        )
    return 100.0 * (total - failed) / total
