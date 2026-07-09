from __future__ import annotations

from nollm.grf.capture import GRFCaptureRequest
from nollm.grf.facade import GRFFacade
from nollm.grf.placement_policy import GRFPlacementPolicy
from nollm.grf.evidence import EvidenceShardRecord
from nollm.grf.source_window import SourceWindowRecord


def test_policy_defer_and_reject_preserve_evidence(tmp_path) -> None:
    shard = EvidenceShardRecord("shard:policy:reject", "false friend content", "2026-07-09T00:00:00Z", "validation_fixture", ("source:policy:reject",), "trusted", "captured")
    window = SourceWindowRecord("source:policy:reject", "validation_fixture", ("fixture",), "2026-07-09T00:00:00Z")
    _, reject_decision, reject_report = GRFPlacementPolicy().evaluate(shard, window, false_friend_risk=True)
    _, defer_decision, defer_report = GRFPlacementPolicy().evaluate(shard, window, force_defer=True)

    assert reject_decision.decision == "reject"
    assert reject_decision.rejection_reason == "false_friend_risk"
    assert defer_decision.decision == "defer"
    assert reject_report.decision == "reject"
    assert defer_report.decision == "defer"

    facade = GRFFacade(tmp_path)
    receipt = facade.capture(GRFCaptureRequest("capture:policy:reject", "false friend content", "validation_fixture", (window.window_id,), "2026-07-09T00:00:00Z"))
    result = facade.admit(receipt.shard_id, window.window_id, {"policy_id": "grf_deterministic_policy_v1", "false_friend_risk": True}, "2026-07-09T00:00:01Z")
    assert result.rejection_record is not None
    assert facade.store.read_evidence_shard(receipt.shard_id).content == "false friend content"
