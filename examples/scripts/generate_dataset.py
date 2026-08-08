"""Generate a synthetic monthly market dataset for the CLI examples.

Produces a deterministic, realistic-looking historical dataset covering
January 1990 through December 2024 (420 monthly snapshots) with two asset
classes ("equity", "bond") and monthly inflation.

The output is written to ``examples/data/market_monthly.json`` and can be
used with ``sim-retire --data-dir examples/data``.

Usage:
    python examples/scripts/generate_dataset.py
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

EQUITY_SNAPSHOT = Decimal("100.0")
BOND_SNAPSHOT = Decimal("100.0")
ANNUAL_INFLATION = Decimal("0.030")

YEARS = range(1990, 2025)
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "market_monthly.json"


def _monthly(annual_rate: Decimal) -> Decimal:
    return (Decimal("1") + annual_rate) ** (Decimal("1") / Decimal("12"))


def _build_snapshots() -> list[dict[str, object]]:
    equity_index = Decimal("100.0")
    bond_index = Decimal("100.0")
    inflation_index = Decimal("1.0")

    snapshots: list[dict[str, object]] = []
    for year in YEARS:
        for month in range(1, 13):
            equity_index *= _monthly(Decimal("0.08"))
            bond_index *= _monthly(Decimal("0.035"))
            inflation_index *= _monthly(ANNUAL_INFLATION)
            snapshots.append(
                {
                    "date": f"{year:04d}-{month:02d}-01",
                    "inflation": str(_monthly(ANNUAL_INFLATION) - Decimal("1.0")),
                    "inflation_cumulative": str(inflation_index),
                    "is_ath": True,
                    "is_underwater": False,
                    "running_ath": str(equity_index),
                    "index_levels": {
                        "equity": str(equity_index),
                        "bond": str(bond_index),
                    },
                }
            )
    return snapshots


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "1.0",
        "frequency": "monthly",
        "snapshots": _build_snapshots(),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload['snapshots'])} snapshots to {OUTPUT}")


if __name__ == "__main__":
    main()
