from __future__ import annotations

import json

import pytest

from nollm.grf.cell_address import CellAddress
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.placement import PlacementCandidate


def scores() -> dict[str, int]:
    return {
        "local_fit_q16": Q16_ONE,
        "density_cost_q16": 0,
        "coverage_gain_q16": Q16_ONE // 2,
        "stitch_potential_q16": Q16_ONE // 4,
        "residual_cost_q16": 0,
        "compute_cost_q16": Q16_ONE // 8,
    }


def candidate(**overrides) -> PlacementCandidate:
    values = {
        "candidate_id": "candidate_a",
        "shard_id": "shard_a",
        "island_id": "island_a",
        "patch_id": "patch_a",
        "target_cell": CellAddress("eisenstein_exact_v1", "chart_a", 1, 0, 0),
        "scores": scores(),
        "confidence_band": "high",
        "source_window_refs": ("source:window:a",),
        "evidence_refs": ("shard_a",),
    }
    values.update(overrides)
    return PlacementCandidate(**values)


def test_candidate_requires_all_integer_scores_and_evidence() -> None:
    with pytest.raises(ValueError):
        candidate(scores={**scores(), "local_fit_q16": 1.5})  # type: ignore[dict-item]
    with pytest.raises(ValueError):
        candidate(evidence_refs=())
    with pytest.raises(ValueError):
        bad = scores()
        del bad["compute_cost_q16"]
        candidate(scores=bad)


def test_candidate_serialization_has_no_semantic_edge_parent_topic_or_truth_score() -> None:
    rendered = candidate().to_mapping()
    text = json.dumps(rendered, sort_keys=True)
    for forbidden in ("semantic_edge", "parent", "topic", "truth_score"):
        assert forbidden not in text
