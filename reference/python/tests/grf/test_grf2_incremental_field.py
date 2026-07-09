from __future__ import annotations

from nollm.grf.cell_address import CellAddress
from nollm.grf.incremental_field import IncrementalFieldBuilder
from nollm.grf.placement import GeometryMark, PlacementRecord


def _placement(shard_id: str, q: int) -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart_inc", 0, q, 0)
    mark = GeometryMark(f"mark:{shard_id}", shard_id, "eisenstein_exact_v1", "chart_inc", cell, "grf2_test", "high", 0, "rf:grf2")
    return PlacementRecord(f"placement:{shard_id}", shard_id, f"candidate:{shard_id}", f"decision:{shard_id}", mark, f"island:{shard_id}", f"patch:{shard_id}", (shard_id,), "eisenstein_exact_v1", "grf2")


def test_incremental_rebuild_matches_full_rebuild_and_tracks_local_invalidations() -> None:
    builder = IncrementalFieldBuilder()
    first = _placement("shard:a", 0)
    second = _placement("shard:b", 1)
    report = builder.add_placement(first)
    builder.add_placement(second)

    incremental = builder.relation_field()
    full = builder.full_rebuild()

    assert report.local_impact_only is True
    assert report.deterministic is True
    assert incremental.placements == full.placements
    assert tuple(path.shard_id for path in incremental.shards_at(first.geometry_mark.cell)) == ("shard:a",)
