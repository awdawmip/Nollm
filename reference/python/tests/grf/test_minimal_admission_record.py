from __future__ import annotations

import json

from nollm.grf.admission import MinimalAdmissionRecord
from nollm.grf.cell_address import CellAddress
from nollm.grf.placement import GeometryMark, PlacementRecord


def placement() -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart_a", 1, 0, 0)
    mark = GeometryMark("mark_a", "shard_a", "eisenstein_exact_v1", "chart_a", cell, "validation_fixture", "high", 0, "rf:a")
    return PlacementRecord("placement_a", "shard_a", "candidate_a", "decision_a", mark, "island_a", "patch_a", ("source:window:a",), "eisenstein_exact_v1", "grf1cde_v1")


def test_minimal_admission_does_not_copy_edges_or_confirm_truth() -> None:
    record = MinimalAdmissionRecord("admission_a", "shard_a", placement(), "2026-07-09T10:00:00+08:00", "validation_fixture")
    rendered = record.to_mapping()
    assert rendered["admission_is_not_memory_existence_proof"] is True
    assert rendered["coverage_edges_inherited_from_profile"] is True
    assert rendered["does_not_copy_coverage_edge_list"] is True
    assert rendered["does_not_copy_semantic_edge_list"] is True
    text = json.dumps(rendered, sort_keys=True)
    assert "coverage_edge_list" not in text.replace("does_not_copy_coverage_edge_list", "")
    assert "semantic_edge_list" not in text.replace("does_not_copy_semantic_edge_list", "")
