"""Bounded direct-Cell write/read scale check; intentionally no semantic lookup metric."""

from __future__ import annotations

from nollm.grf.cell_address import CellAddress
from nollm.grf.field_engine import CellStore
from nollm.grf.placement import GeometryMark, PlacementRecord


def main() -> None:
    store = CellStore()
    for index in range(100_000):
        cell = CellAddress("eisenstein_exact_v1", "chart:scale", 0, index, -index)
        mark = GeometryMark(f"mark:{index}", f"shard:{index}", cell.profile_id, cell.chart_id, cell, "validation", "medium", 0, "field:geometry")
        store.insert(PlacementRecord(f"placement:{index}", f"shard:{index}", f"candidate:{index}", f"decision:{index}", mark, f"island:{index}", f"patch:{index}", (f"source:{index}",), cell.profile_id, "geometry_native_v1", False))
    assert store.placement_count() == 100_000
    assert len(store.at(CellAddress("eisenstein_exact_v1", "chart:scale", 0, 99999, -99999))) == 1
    print("core realignment scale validation passed: 100000 direct cell operations")


if __name__ == "__main__":
    main()
