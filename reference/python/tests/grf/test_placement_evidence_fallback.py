from __future__ import annotations

import pytest

from nollm.grf.cell_address import CellAddress
from nollm.grf.placement import GeometryMark, PlacementRecord


def mark() -> GeometryMark:
    cell = CellAddress("eisenstein_exact_v1", "chart_a", 1, 0, 0)
    return GeometryMark("mark_a", "shard_a", "eisenstein_exact_v1", "chart_a", cell, "validation_fixture", "high", 0, "rf:a")


def test_placement_record_requires_source_fallback_and_profile_replay() -> None:
    with pytest.raises(ValueError):
        PlacementRecord("placement_a", "shard_a", "candidate_a", "decision_a", mark(), "island_a", "patch_a", (), "eisenstein_exact_v1", "v1")
    with pytest.raises(ValueError):
        PlacementRecord("placement_a", "shard_a", "candidate_a", "decision_a", mark(), "island_a", "patch_a", ("source:window:a",), "aligned_baseline_v1", "v1")


def test_placement_record_does_not_copy_coverage_entries() -> None:
    record = PlacementRecord("placement_a", "shard_a", "candidate_a", "decision_a", mark(), "island_a", "patch_a", ("source:window:a",), "eisenstein_exact_v1", "v1")
    assert record.to_mapping()["does_not_copy_coverage_entries"] is True
