from __future__ import annotations

import ast
import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from nollm.dream_geometry.capture import (
    CandidateTrigger,
    CaptureDiagnostics,
    CaptureError,
    CaptureIngress,
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    CaptureStateStore,
    CaptureStatus,
    CaptureVisibility,
    DeferredCandidateRequest,
    PromotionMode,
    VisibilityScope,
)
from nollm.dream_geometry.evidence import open_store
from nollm.dream_geometry.protocol.contracts import OriginKind


def test_cx101_ephemeral_captured_deferred_and_persistent_explicit_boundaries(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    ingress = CaptureIngress(tmp_path / "ci1")

    ephemeral = ingress.capture(
        _request("cap_cx_ephemeral", "ephemeral", ("turn:cx",), VisibilityScope.current_turn),
        _policy(
            "cp_cx_ephemeral",
            persistence=CapturePersistence.ephemeral,
            allowed=(VisibilityScope.current_turn,),
            diagnostics=CaptureDiagnostics.off,
        ),
        evidence,
    )
    captured = ingress.capture(
        _request("cap_cx_captured", "captured", ("session:cx",), VisibilityScope.session_window),
        _policy("cp_cx_captured", allowed=(VisibilityScope.session_window,)),
        evidence,
    )
    deferred = ingress.capture(
        replace(
            _request("cap_cx_deferred", "deferred", ("source:cx",), VisibilityScope.source_window),
            deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
        ),
        _policy(
            "cp_cx_deferred",
            persistence=CapturePersistence.persistent,
            lineage=CaptureLineage.minimal,
            allowed=(VisibilityScope.source_window,),
            promotion_mode=PromotionMode.manual,
        ),
        evidence,
    )
    persistent = ingress.capture(
        _request("cap_cx_persistent", "persistent", ("explicit:cx",), VisibilityScope.persistent_explicit),
        _policy(
            "cp_cx_persistent",
            persistence=CapturePersistence.persistent,
            allowed=(VisibilityScope.persistent_explicit,),
        ),
        evidence,
    )

    visibility = CaptureVisibility(ingress.state_store, evidence)

    assert ephemeral.status is CaptureStatus.ephemeral
    assert ephemeral.shard_id is None
    assert captured.status is CaptureStatus.captured
    assert deferred.status is CaptureStatus.deferred
    assert persistent.status is CaptureStatus.captured
    assert len(evidence.read_ledger()) == 3
    assert visibility.session_window_ids("session:cx") == (captured.shard_id,)
    assert visibility.source_window_ids("source:cx") == (deferred.shard_id,)
    assert visibility.session_window_ids("explicit:cx") == ()
    assert visibility.persistent_explicit((persistent.shard_id, persistent.shard_id))[0].content == "persistent"
    assert ingress.state_store.get_candidate(deferred.deferred_candidate_id).shard_id == deferred.shard_id
    assert not _contains_forbidden_formal_tokens(tmp_path / "ci1")


def test_cx102_retry_and_reopen_preserve_receipts_and_visibility(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    ingress = CaptureIngress(tmp_path / "ci1")
    request = replace(
        _request("cap_cx_reopen", "reopen deferred", ("session:reopen",), VisibilityScope.session_window),
        deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.manual_window,)),
    )
    policy = _policy(
        "cp_cx_reopen",
        persistence=CapturePersistence.persistent,
        lineage=CaptureLineage.minimal,
        allowed=(VisibilityScope.session_window,),
        promotion_mode=PromotionMode.manual,
    )
    first = ingress.capture(request, policy, evidence)
    before = (_manifest(tmp_path / "evidence"), _manifest(tmp_path / "ci1"))

    reopened_evidence = open_store(tmp_path / "evidence")
    reopened_ingress = CaptureIngress(tmp_path / "ci1")
    second = reopened_ingress.capture(request, policy, reopened_evidence)

    assert second == first
    assert len(reopened_evidence.read_ledger()) == 1
    assert (_manifest(tmp_path / "evidence"), _manifest(tmp_path / "ci1")) == before
    assert CaptureVisibility(reopened_ingress.state_store, reopened_evidence).session_window("session:reopen")[0].content == "reopen deferred"
    assert reopened_ingress.state_store.get_candidate(first.deferred_candidate_id).shard_id == first.shard_id


@pytest.mark.parametrize("failpoint", ("visibility", "candidate", "receipt", "identity", "diagnostic"))
def test_cx103_local_failures_do_not_publish_success_receipts_or_public_candidates(monkeypatch, tmp_path, failpoint: str) -> None:
    root = tmp_path / failpoint
    evidence = open_store(root / "evidence")
    ingress = CaptureIngress(root / "ci1")
    request = replace(
        _request("cap_cx_fail_" + failpoint, "failure " + failpoint, ("session:failure",), VisibilityScope.session_window),
        deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
        diagnostic_retention_until="2026-07-03T00:00:00Z",
    )
    policy = _policy(
        "cp_cx_fail_" + failpoint,
        persistence=CapturePersistence.persistent,
        lineage=CaptureLineage.minimal,
        diagnostics=CaptureDiagnostics.verbose if failpoint == "diagnostic" else CaptureDiagnostics.on_failure,
        allowed=(VisibilityScope.session_window,),
        promotion_mode=PromotionMode.manual,
    )

    if failpoint == "visibility":
        monkeypatch.setattr(ingress.state_store, "append_visibility", _fail)
    elif failpoint == "candidate":
        monkeypatch.setattr(ingress.state_store, "put_candidate", _fail)
    elif failpoint == "receipt":
        monkeypatch.setattr(ingress.state_store, "put_receipt", _fail)
    elif failpoint == "identity":
        monkeypatch.setattr(ingress.state_store, "put_capture_identity", _fail)
    else:
        monkeypatch.setattr(ingress.state_store, "put_diagnostic", _fail)

    with pytest.raises(CaptureError) as exc:
        ingress.capture(request, policy, evidence)

    assert exc.value.code == "CI1_COMMIT_FAILED"
    assert len(evidence.read_ledger()) == 1
    with pytest.raises(CaptureError):
        ingress.state_store.get_receipt_by_capture_id(request.capture_id)
    for candidate_id in _candidate_ids(root / "ci1"):
        with pytest.raises(CaptureError):
            ingress.state_store.get_candidate(candidate_id)

    retry = CaptureIngress(root / "ci1").capture(request, policy, evidence)
    assert retry.status is CaptureStatus.deferred
    assert len(evidence.read_ledger()) == 1
    assert CaptureStateStore(root / "ci1").get_candidate(retry.deferred_candidate_id).shard_id == retry.shard_id


def test_cx104_visibility_surface_has_no_global_discovery_and_is_read_only(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    ingress = CaptureIngress(tmp_path / "ci1")
    first = ingress.capture(_request("cap_cx_read_1", "one", ("session:read",), VisibilityScope.session_window), _policy("cp_cx_read"), evidence)
    second = ingress.capture(_request("cap_cx_read_2", "two", ("session:read",), VisibilityScope.session_window), _policy("cp_cx_read"), evidence)
    before = (_manifest(tmp_path / "evidence"), _manifest(tmp_path / "ci1"))
    visibility = CaptureVisibility(ingress.state_store, evidence)

    assert visibility.session_window_ids("session:read") == (first.shard_id, second.shard_id)
    assert [shard.content for shard in visibility.session_window("session:read")] == ["one", "two"]
    assert not hasattr(visibility, "list_all")
    assert not hasattr(visibility, "search")
    assert not hasattr(visibility, "rank")
    assert not hasattr(visibility, "recent_global")
    assert (_manifest(tmp_path / "evidence"), _manifest(tmp_path / "ci1")) == before


def test_cx105_capture_lane_remains_isolated_from_formal_paths(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    receipt = CaptureIngress(tmp_path / "ci1").capture(
        _request("cap_cx_formal", "formal isolation", ("session:formal",), VisibilityScope.session_window),
        _policy("cp_cx_formal"),
        evidence,
    )

    assert receipt.shard_id is not None
    assert not _contains_forbidden_formal_tokens(tmp_path / "ci1")
    assert not any((tmp_path / name).exists() for name in ("admission", "assembly", "recall", "integration", "field", "geometry"))
    with pytest.raises(AttributeError):
        _ = receipt.record
    with pytest.raises(AttributeError):
        _ = receipt.projection_fingerprint
    _assert_capture_imports_do_not_cross_formal_paths()


def _request(capture_id: str, content: str, refs: tuple[str, ...], scope: VisibilityScope):
    return __import__("nollm.dream_geometry.capture", fromlist=["CaptureRequest"]).CaptureRequest(
        capture_id,
        content,
        CaptureOrigin(OriginKind.user_utterance, "turn:cx", refs[0], "user"),
        "2026-07-02T12:34:56+08:00",
        refs,
        scope,
    )


def _policy(
    policy_id: str,
    *,
    persistence: CapturePersistence = CapturePersistence.captured,
    lineage: CaptureLineage = CaptureLineage.none,
    diagnostics: CaptureDiagnostics = CaptureDiagnostics.on_failure,
    allowed: tuple[VisibilityScope, ...] = (VisibilityScope.session_window,),
    promotion_mode: PromotionMode = PromotionMode.disabled,
) -> CapturePolicy:
    return CapturePolicy(
        policy_id,
        persistence=persistence,
        lineage=lineage,
        diagnostics=diagnostics,
        allowed_visibility_scopes=allowed,
        promotion_mode=promotion_mode,
    )


def _fail(*_args, **_kwargs):
    raise RuntimeError("synthetic cx1 commit failure")


def _candidate_ids(root: Path) -> tuple[str, ...]:
    candidate_root = root / "candidates"
    if not candidate_root.exists():
        return ()
    return tuple(json.loads(path.read_text(encoding="utf-8"))["candidate_id"] for path in sorted(candidate_root.glob("*.json")))


def _manifest(root: Path) -> tuple[tuple[str, str], ...]:
    if not root.exists():
        return ()
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))


def _contains_forbidden_formal_tokens(root: Path) -> bool:
    forbidden = ("GrowthProposal", "PlacementPlan", "AdmissionRecord", "FieldSnapshot", "RecallUniverse", "VerifiedChartLink")
    if not root.exists():
        return False
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.json"))
    return any(token in text for token in forbidden)


def _assert_capture_imports_do_not_cross_formal_paths() -> None:
    source = Path(__file__).resolve().parents[1] / "nollm" / "dream_geometry" / "capture"
    forbidden_modules = {"admission", "geometry", "field", "assembly", "recall", "adapters"}
    for path in source.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(name.startswith("nollm.dream_geometry." + module) for name in names for module in forbidden_modules), path
