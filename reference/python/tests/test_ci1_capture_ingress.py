from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

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
    CaptureError,
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


def test_ci1_1_t02_full_receipt_idempotency_for_none_and_minimal_lineage(tmp_path) -> None:
    for diagnostics in (CaptureDiagnostics.on_failure, CaptureDiagnostics.off):
        root = tmp_path / diagnostics.value
        evidence = open_store(root / "evidence")
        ingress = CaptureIngress(root / "ci1")
        policy = replace(_policy(), policy_id="cp_retry_" + diagnostics.value, diagnostics=diagnostics)
        first = ingress.capture(_request("cap_retry_" + diagnostics.value), policy, evidence)
        before = {"evidence": tree_manifest(root / "evidence"), "ci1": tree_manifest(root / "ci1")}

        assert ingress.capture(_request("cap_retry_" + diagnostics.value), policy, evidence) == first
        assert ingress.capture(_request("cap_retry_" + diagnostics.value), policy, evidence) == first
        assert len(evidence.read_ledger()) == 1
        assert {"evidence": tree_manifest(root / "evidence"), "ci1": tree_manifest(root / "ci1")} == before

    minimal_root = tmp_path / "minimal"
    evidence = open_store(minimal_root / "evidence")
    ingress = CaptureIngress(minimal_root / "ci1")
    policy = replace(_policy(), policy_id="cp_retry_minimal", lineage=CaptureLineage.minimal)
    first = ingress.capture(_request("cap_retry_minimal"), policy, evidence)
    before = {"evidence": tree_manifest(minimal_root / "evidence"), "ci1": tree_manifest(minimal_root / "ci1")}
    assert ingress.capture(_request("cap_retry_minimal"), policy, evidence) == first
    assert len(evidence.read_ledger()) == 1
    assert {"evidence": tree_manifest(minimal_root / "evidence"), "ci1": tree_manifest(minimal_root / "ci1")} == before


def test_ci1_1_t03_candidate_local_failures_are_not_public_candidates(monkeypatch, tmp_path) -> None:
    for failpoint in ("visibility", "candidate", "identity", "diagnostic"):
        root = tmp_path / failpoint
        evidence = open_store(root / "evidence")
        ingress = CaptureIngress(root / "ci1")
        request = _deferred_request("cap_fail_" + failpoint)
        policy = _deferred_policy("cp_fail_" + failpoint, verbose=failpoint == "diagnostic")

        if failpoint == "visibility":
            monkeypatch.setattr(ingress.state_store, "append_visibility", _fail)
        elif failpoint == "candidate":
            monkeypatch.setattr(ingress.state_store, "put_candidate", _fail)
        elif failpoint == "identity":
            monkeypatch.setattr(ingress.state_store, "put_capture_identity", _fail)
        else:
            monkeypatch.setattr(ingress.state_store, "put_diagnostic", _fail)

        try:
            ingress.capture(request, policy, evidence)
            raise AssertionError("expected commit failure")
        except CaptureError as exc:
            assert exc.code == "CI1_COMMIT_FAILED"

        shard_id = "shard:ci1:" + sha256(request.capture_id.encode("utf-8")).hexdigest()[:32]
        assert evidence.get_dream_shard(shard_id).content == request.content
        assert len(evidence.read_ledger()) == 1
        with pytest.raises(CaptureError):
            ingress.state_store.get_receipt_by_capture_id(request.capture_id)
        for candidate_id in _candidate_ids(root / "ci1"):
            with pytest.raises(CaptureError):
                ingress.state_store.get_candidate(candidate_id)

        retry = CaptureIngress(root / "ci1").capture(request, policy, evidence)
        assert retry.status is CaptureStatus.deferred
        assert len(evidence.read_ledger()) == 1
        assert retry.deferred_candidate_id is not None
        assert CaptureIngress(root / "ci1").state_store.get_candidate(retry.deferred_candidate_id).shard_id == retry.shard_id


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


def _deferred_request(capture_id: str):
    return replace(
        _request(capture_id),
        deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
        diagnostic_retention_until="2026-07-03T00:00:00Z",
    )


def _deferred_policy(policy_id: str, *, verbose: bool = False) -> CapturePolicy:
    return CapturePolicy(
        policy_id,
        persistence=CapturePersistence.persistent,
        lineage=CaptureLineage.minimal,
        diagnostics=CaptureDiagnostics.verbose if verbose else CaptureDiagnostics.on_failure,
        allowed_visibility_scopes=(VisibilityScope.session_window,),
        promotion_mode=PromotionMode.manual,
    )


def _fail(*_args, **_kwargs):
    raise RuntimeError("synthetic ci1 commit failure")


def _candidate_ids(root: Path) -> tuple[str, ...]:
    candidate_root = root / "candidates"
    if not candidate_root.exists():
        return ()
    import json

    return tuple(json.loads(path.read_text(encoding="utf-8"))["candidate_id"] for path in sorted(candidate_root.glob("*.json")))


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
