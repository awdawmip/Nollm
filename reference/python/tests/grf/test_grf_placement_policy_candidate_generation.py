from __future__ import annotations

from nollm.grf.evidence import EvidenceShardRecord
from nollm.grf.placement_policy import PlacementCandidateGenerator
from nollm.grf.source_window import SourceWindowRecord


def test_policy_candidate_generation_is_bounded_deterministic_and_evidence_bound() -> None:
    shard = EvidenceShardRecord("shard:policy:1", "policy content", "2026-07-09T00:00:00Z", "validation_fixture", ("source:policy:1",), "trusted", "captured")
    window = SourceWindowRecord("source:policy:1", "validation_fixture", ("fixture",), "2026-07-09T00:00:00Z")
    generator = PlacementCandidateGenerator()

    first = generator.generate(shard, window)
    second = generator.generate(shard, window)

    assert first == second
    assert 1 <= len(first) <= 5
    assert all(candidate.evidence_refs == (shard.shard_id,) for candidate in first)
    payload = first[0].to_mapping()
    assert "semantic_edge" not in payload
    assert "topic" not in payload
    assert "parent" not in payload
