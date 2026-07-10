"""Validate direct geometry storage without a route lookup."""

from __future__ import annotations

from tempfile import TemporaryDirectory
from pathlib import Path

from nollm.grf.cell_address import CellAddress
from nollm.grf.geometry_storage import partition_id


def main() -> None:
    cell = CellAddress("eisenstein_exact_v1", "chart:validation", 0, -17, 31)
    assert partition_id(cell) == (-2, 1)
    print("geometry native storage validation passed")


if __name__ == "__main__":
    main()
