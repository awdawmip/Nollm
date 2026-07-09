from __future__ import annotations

from nollm.grf.bridge_kernel import BridgeKernel
from nollm.grf.cell_address import CellAddress
from nollm.grf.coverage_template import COVERAGE_DOWN, COVERAGE_UP, LATERAL, CoverageTemplateCompiler
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.placement import GeometryMark, PlacementRecord
from nollm.grf.relation_field import RelationField


def placement(shard_id: str, patch_id: str, layer: int, q: int, r: int, source: str) -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart_a", layer, q, r)
    mark = GeometryMark("mark_" + shard_id, shard_id, "eisenstein_exact_v1", "chart_a", cell, "validation_fixture", "high", 0, "rf:test")
    return PlacementRecord("placement_" + shard_id, shard_id, "candidate_" + shard_id, "decision_" + shard_id, mark, "island_" + shard_id, patch_id, (source,), "eisenstein_exact_v1", "grf1cde_v1")


def relation_field() -> RelationField:
    compiler = CoverageTemplateCompiler()
    templates = (
        compiler.compile("eisenstein_exact_v1", COVERAGE_UP),
        compiler.compile("eisenstein_exact_v1", COVERAGE_DOWN),
        compiler.compile("eisenstein_exact_v1", LATERAL),
    )
    placements = (
        placement("shard_a", "patch_a", 1, 0, 0, "source:a"),
        placement("shard_b", "patch_b", 0, 0, 0, "source:b"),
        placement("shard_c", "patch_c", 1, 1, 0, "source:c"),
    )
    bridges = (BridgeKernel("bridge_ab", "patch_a", "patch_c", Q16_ONE // 2, "normal", 1, 2, ("shard:a", "shard:c")),)
    return RelationField(templates, bridges, placements)
