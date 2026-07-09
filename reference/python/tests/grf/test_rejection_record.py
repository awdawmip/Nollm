from __future__ import annotations

import pytest

from nollm.grf.placement import RejectionRecord


def test_rejection_record_keeps_source_fallback() -> None:
    record = RejectionRecord("rejection_a", "candidate_a", "shard_a", "2026-07-09T10:00:00+08:00", "validation_fixture", "false_friend_risk", ("source:window:a",))
    assert record.to_mapping()["source_fallback_refs"] == ("source:window:a",)


def test_rejection_record_rejects_unknown_reason() -> None:
    with pytest.raises(ValueError):
        RejectionRecord("rejection_a", "candidate_a", "shard_a", "2026-07-09T10:00:00+08:00", "validation_fixture", "semantic_match", ("source:window:a",))
