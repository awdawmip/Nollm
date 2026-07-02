from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from nollm.dream_geometry.capture import (
    CandidateTrigger,
    CaptureDiagnostics,
    CaptureIngress,
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    CaptureStatus,
    DeferredCandidateRequest,
    PromotionMode,
    VisibilityScope,
)
from nollm.dream_geometry.evidence import open_store
from nollm.dream_geometry.protocol.contracts import OriginKind


def test_c101_default_lightweight_capture_writes_de1_only_plus_visibility(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    ingress = CaptureIngress(tmp_path / "ci1")
    receipt = ingress.capture(_request(), _policy(), evidence)

    assert receipt.status is CaptureStatus.captured
    assert receipt.shard_id is not None
    assert receipt.minimal_ledger_event_id is not None
    assert receipt.deferred_candidate_id is None
    shard = evidence.get_dream_shard(receipt.shard_id)
    assert shard.content == "Host supplied raw capture."
    assert shard.context_refs == ("session:alpha", "source:weather")
    assert len(evidence.read_ledger()) == 1
    assert ingress.state_store.receipt_count() == 0
    assert ingress.state_store.candidate_count() == 0
    assert not _contains_token(tmp_path / "ci1", ("GrowthProposal", "PlacementPlan", "AdmissionRecord", "FieldSnapshot"))


def test_c102_ephemeral_zero_landing(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    before_evidence = tree_manifest(tmp_path / "evidence")
    before_ci1 = tree_manifest(tmp_path / "ci1")
    policy = CapturePolicy(
        "cp_ephemeral",
        persistence=CapturePersistence.ephemeral,
        lineage=CaptureLineage.none,
        diagnostics=CaptureDiagnostics.off,
        allowed_visibility_scopes=(VisibilityScope.current_turn,),
    )

    receipt = CaptureIngress(tmp_path / "ci1").capture(replace(_request(), requested_visibility_scope=VisibilityScope.current_turn), policy, evidence)

    assert receipt.status is CaptureStatus.ephemeral
    assert receipt.shard_id is None
    assert receipt.minimal_ledger_event_id is None
    assert receipt.deferred_candidate_id is None
    assert tree_manifest(tmp_path / "evidence") == before_evidence
    assert tree_manifest(tmp_path / "ci1") == before_ci1


def test_c103_minimal_deferred_candidate(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    request = replace(
        _request("cap_deferred"),
        deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin, CandidateTrigger.manual_window)),
    )
    policy = CapturePolicy(
        "cp_deferred",
        persistence=CapturePersistence.persistent,
        lineage=CaptureLineage.minimal,
        diagnostics=CaptureDiagnostics.on_failure,
        allowed_visibility_scopes=(VisibilityScope.source_window,),
        promotion_mode=PromotionMode.manual,
    )
    request = replace(request, requested_visibility_scope=VisibilityScope.source_window)
    ingress = CaptureIngress(tmp_path / "ci1")

    receipt = ingress.capture(request, policy, evidence)

    assert receipt.status is CaptureStatus.deferred
    assert receipt.shard_id is not None
    assert receipt.deferred_candidate_id is not None
    assert ingress.state_store.receipt_count() == 1
    candidate = ingress.state_store.get_candidate(receipt.deferred_candidate_id)
    assert candidate.shard_id == receipt.shard_id
    assert candidate.trigger_refs == (CandidateTrigger.explicit_pin, CandidateTrigger.manual_window)
    assert candidate.promotion_attempt_refs == ()
    assert candidate.source_window_refs == ("session:alpha", "source:weather")
    assert "proposal" not in _all_text(tmp_path / "ci1").lower()
    assert "placement" not in _all_text(tmp_path / "ci1").lower()


def test_c107_idempotency_and_capture_identity_conflict(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    ingress = CaptureIngress(tmp_path / "ci1")
    request = _request("cap_retry")
    policy = replace(_policy(), policy_id="cp_retry", diagnostics=CaptureDiagnostics.off)
    first = ingress.capture(request, policy, evidence)
    before = {
        "evidence": tree_manifest(tmp_path / "evidence"),
        "ci1": tree_manifest(tmp_path / "ci1"),
        "ledger_count": len(evidence.read_ledger()),
    }

    retry = ingress.capture(request, policy, evidence)
    changed = ingress.capture(replace(request, content="Different raw capture."), policy, evidence)

    assert retry.receipt_id == first.receipt_id
    assert retry.shard_id == first.shard_id
    assert len(evidence.read_ledger()) == before["ledger_count"]
    assert tree_manifest(tmp_path / "evidence") == before["evidence"]
    assert tree_manifest(tmp_path / "ci1") == before["ci1"]
    assert changed.status is CaptureStatus.rejected
    assert changed.shard_id is None
    assert len(evidence.read_ledger()) == before["ledger_count"]


def _request(capture_id: str = "cap_default") -> object:
    return __import__("nollm.dream_geometry.capture", fromlist=["CaptureRequest"]).CaptureRequest(
        capture_id,
        "Host supplied raw capture.",
        CaptureOrigin(OriginKind.user_utterance, "turn:opaque", "session:alpha", "user"),
        "2026-07-02T12:34:56+08:00",
        ("session:alpha", "source:weather"),
        VisibilityScope.session_window,
    )


def _policy() -> CapturePolicy:
    return CapturePolicy(
        "cp_default",
        persistence=CapturePersistence.captured,
        lineage=CaptureLineage.none,
        diagnostics=CaptureDiagnostics.on_failure,
        allowed_visibility_scopes=(VisibilityScope.session_window,),
    )


def tree_manifest(root: Path) -> tuple[tuple[str, str], ...]:
    if not root.exists():
        return ()
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))


def _all_text(root: Path) -> str:
    if not root.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.json"))


def _contains_token(root: Path, tokens: tuple[str, ...]) -> bool:
    text = _all_text(root)
    return any(token in text for token in tokens)
