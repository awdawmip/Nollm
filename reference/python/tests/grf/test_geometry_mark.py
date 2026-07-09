from __future__ import annotations

import json

import pytest

from nollm.grf.cell_address import CellAddress
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.placement import GeometryMark


def test_geometry_mark_declares_non_truth_and_inherits_relation_field() -> None:
    cell = CellAddress("eisenstein_exact_v1", "chart_a", 1, 0, 0)
    mark = GeometryMark("mark_a", "shard_a", "eisenstein_exact_v1", "chart_a", cell, "validation_fixture", "medium", Q16_ONE // 8, "rf:a")
    rendered = mark.to_mapping()
    assert rendered["not_fact_confirmation"] is True
    assert rendered["not_truth_score"] is True
    assert rendered["inherits_relation_field"] is True
    assert "parent" not in rendered
    assert "edge" not in rendered
    assert "semantic_relation" not in rendered
    assert "truth_score" not in rendered


def test_geometry_mark_rejects_cell_profile_chart_mismatch() -> None:
    cell = CellAddress("aligned_baseline_v1", "chart_a", 1, 0, 0)
    with pytest.raises(ValueError):
        GeometryMark("mark_a", "shard_a", "eisenstein_exact_v1", "chart_a", cell, "validation_fixture", "medium", 0, "rf:a")
