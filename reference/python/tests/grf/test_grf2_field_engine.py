from __future__ import annotations

from nollm.grf.cell_address import CellAddress
from nollm.grf.field_engine import CellRegistry, PlacementIndex
from nollm.grf.placement import GeometryMark, PlacementRecord


def _placement(shard_id: str, q: int = 0, r: int = 0) -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart_field", 0, q, r)
    mark = GeometryMark(f"mark:{shard_id}", shard_id, "eisenstein_exact_v1", "chart_field", cell, "grf2_test", "high", 0, "rf:grf2")
    return PlacementRecord(f"placement:{shard_id}", shard_id, f"candidate:{shard_id}", f"decision:{shard_id}", mark, f"island:{shard_id}", f"patch:{shard_id}", (shard_id,), "eisenstein_exact_v1", "grf2")


def test_cell_registry_and_placement_index_keep_identities_separate() -> None:
    registry = CellRegistry(dense_threshold=2, overloaded_threshold=3, migration_threshold=4)
    index = PlacementIndex(registry)
    first = _placement("shard:a")
    second = _placement("shard:b")
    index.insert(first)
    index.insert(second)

    state = registry.cell_state(first.geometry_mark.cell)
    assert state.density_state == "dense"
    payload = state.to_mapping()
    assert payload["cell_stores_shard_content"] is False
    assert payload["cell_stores_semantic_edge"] is False
    assert payload["cell_copies_coverage_relation"] is False
    assert index.query_by_cell(first.geometry_mark.cell) == (first, second)
    assert index.placement_id_for_shard("shard:a") == first.placement_id


def test_density_pressure_thresholds_are_deterministic() -> None:
    registry = CellRegistry(dense_threshold=2, overloaded_threshold=3, migration_threshold=4)
    index = PlacementIndex(registry)
    cell = CellAddress("eisenstein_exact_v1", "chart_field", 0, 0, 0)
    assert registry.density_pressure(cell) == "normal"
    for shard_id in ("a", "b"):
        index.insert(_placement(shard_id))
    assert registry.density_pressure(cell) == "dense"
    index.insert(_placement("c"))
    assert registry.density_pressure(cell) == "overloaded"
    index.insert(_placement("d"))
    assert registry.density_pressure(cell) == "migration_candidate"
