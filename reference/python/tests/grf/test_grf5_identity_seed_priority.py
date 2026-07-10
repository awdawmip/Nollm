from __future__ import annotations

from nollm.grf.cell_address import CellAddress
from nollm.grf.coverage_template import LATERAL, CoverageTemplateCompiler
from nollm.grf.placement import GeometryMark, PlacementRecord
from nollm.grf.recall import QueryProbe, RecallBudget, resolve_grf_recall
from nollm.grf.relation_field import RelationField


def _placement(shard_id: str) -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart:seed", 0, 0, 0)
    mark = GeometryMark(f"mark:{shard_id}", shard_id, cell.profile_id, cell.chart_id, cell, "test", "high", 0, "field:seed")
    return PlacementRecord(f"placement:{shard_id}", shard_id, f"candidate:{shard_id}", f"decision:{shard_id}", mark, f"island:{shard_id}", f"patch:{shard_id}", (shard_id,), cell.profile_id, "seed")


def test_identity_seed_wins_when_multiple_shards_share_a_cell() -> None:
    compiler = CoverageTemplateCompiler()
    field = RelationField((compiler.compile("eisenstein_exact_v1", LATERAL),), (), (_placement("shard:a"), _placement("shard:z")))
    digest = resolve_grf_recall(QueryProbe("query:seed", "shard_id", "shard:z", (LATERAL,), RecallBudget(0, 1, 0, 0, 0, 1)), field)
    assert digest.selected_shards == ("shard:z",)
    assert digest.coverage_reports[0].source_fallback_ref == "shard:z"
