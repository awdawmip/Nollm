from __future__ import annotations

import pytest

from nollm.grf.evidence_island import EvidenceIsland, EvidenceShardRef


def shard(shard_id: str) -> EvidenceShardRef:
    return EvidenceShardRef(shard_id, ("source:window:a",), "observed", "available")


def test_evidence_island_requires_non_empty_unique_shards() -> None:
    with pytest.raises(ValueError):
        EvidenceIsland("island_empty", (), (), "validation_fixture", "floating")
    with pytest.raises(ValueError):
        EvidenceIsland("island_dup", (shard("s1"), shard("s1")), (), "validation_fixture", "floating")


def test_evidence_island_serialization_is_stable_and_not_topic_owner() -> None:
    island = EvidenceIsland("island_a", (shard("s2"), shard("s1")), ("source:window:b", "source:window:a"), "same_session_window", "floating")
    first = island.to_mapping()
    second = island.to_mapping()
    assert first == second
    assert [item["shard_id"] for item in first["shard_refs"]] == ["s1", "s2"]
    assert "parent" not in first
    assert "topic" not in first
    assert "semantic_edge" not in first
    assert first["not_topic_folder"] is True
    assert first["not_truth_owner"] is True


def test_evidence_island_state_transition_is_explicit() -> None:
    island = EvidenceIsland("island_a", (shard("s1"),), (), "manual_group", "floating")
    assert island.transition("patch_candidate").state == "patch_candidate"
    with pytest.raises(ValueError):
        island.transition("stitched")
