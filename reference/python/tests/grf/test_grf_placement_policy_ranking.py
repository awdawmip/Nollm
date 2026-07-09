from __future__ import annotations

from nollm.grf.evidence import EvidenceShardRecord
from nollm.grf.placement_policy import GRFPlacementPolicy, extended_scores
from nollm.grf.source_window import SourceWindowRecord


def test_policy_ranking_uses_extended_q16_integer_scores() -> None:
    shard = EvidenceShardRecord("shard:policy:rank", "ranking content", "2026-07-09T00:00:00Z", "validation_fixture", ("source:policy:rank",), "trusted", "captured")
    window = SourceWindowRecord("source:policy:rank", "validation_fixture", ("fixture",), "2026-07-09T00:00:00Z")

    ranked, decision, report = GRFPlacementPolicy().evaluate(shard, window)

    assert decision.decision == "place"
    assert report.selected_candidate_id == ranked[0].candidate_id
    assert report.deterministic_q16 is True
    assert "source_window_affinity_q16" in report.score_fields
    assert "fallback_stability_q16" in report.score_fields
    assert all(isinstance(value, int) for candidate in ranked for value in extended_scores(candidate).values())
    assert any("selected_cell" in item for item in report.explanations)
