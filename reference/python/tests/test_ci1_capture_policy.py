from __future__ import annotations

import json
from dataclasses import replace

import pytest

from nollm.dream_geometry.capture import (
    CandidateTrigger,
    CaptureDiagnostics,
    CaptureIngress,
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    CaptureRequest,
    CaptureStatus,
    DeferredCandidateRequest,
    VisibilityScope,
)
from nollm.dream_geometry.evidence import open_store
from nollm.dream_geometry.protocol.contracts import OriginKind


def test_c104_replayable_rejected_before_successful_writes(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    policy = CapturePolicy("cp_replayable", lineage=CaptureLineage.replayable, diagnostics=CaptureDiagnostics.on_failure)
    receipt = CaptureIngress(tmp_path / "ci1").capture(_request(), policy, evidence)

    assert receipt.status is CaptureStatus.rejected
    assert receipt.error is not None
    assert receipt.error.code == "CI1_REPLAYABLE_FORBIDDEN"
    assert len(evidence.read_ledger()) == 0
    assert not (tmp_path / "ci1" / "visibility").exists()
    assert not (tmp_path / "ci1" / "candidates").exists()
    assert not (tmp_path / "ci1" / "receipts").exists()
    assert _diagnostic_payloads(tmp_path / "ci1")[0]["message_class"] == "replayable_reserved_for_da1"
    assert "Host supplied raw capture." not in json.dumps(_diagnostic_payloads(tmp_path / "ci1"))


def test_c105_three_diagnostics_modes(tmp_path) -> None:
    request = _request("cap_diag")
    off = CaptureIngress(tmp_path / "off")
    off.capture(request, CapturePolicy("cp_off", diagnostics=CaptureDiagnostics.off), open_store(tmp_path / "evidence_off"))
    off.capture(replace(request, capture_id="cap_bad_off", recorded_at="2026-07-02 12:34:56+08:00"), CapturePolicy("cp_off", diagnostics=CaptureDiagnostics.off), open_store(tmp_path / "evidence_off_bad"))
    assert _diagnostic_payloads(tmp_path / "off") == []

    failure = CaptureIngress(tmp_path / "failure")
    failure.capture(request, CapturePolicy("cp_failure", diagnostics=CaptureDiagnostics.on_failure), open_store(tmp_path / "evidence_failure"))
    failure.capture(replace(request, capture_id="cap_bad_failure", recorded_at="2026-07-02 12:34:56+08:00"), CapturePolicy("cp_failure", diagnostics=CaptureDiagnostics.on_failure), open_store(tmp_path / "evidence_failure_bad"))
    diagnostics = _diagnostic_payloads(tmp_path / "failure")
    assert len(diagnostics) == 1
    assert diagnostics[0]["error_code"] == "CI1_INVALID_REQUEST"
    assert diagnostics[0]["expires_at"] is None

    verbose_request = replace(request, capture_id="cap_verbose", diagnostic_retention_until="2026-07-03T00:00:00Z")
    verbose = CaptureIngress(tmp_path / "verbose")
    verbose.capture(verbose_request, CapturePolicy("cp_verbose", diagnostics=CaptureDiagnostics.verbose), open_store(tmp_path / "evidence_verbose"))
    payload = _diagnostic_payloads(tmp_path / "verbose")[0]
    rendered = json.dumps(payload, sort_keys=True)
    assert payload["expires_at"] == "2026-07-03T00:00:00Z"
    assert "Host supplied raw capture." not in rendered
    assert "turn:opaque" not in rendered
    assert "session:alpha" not in rendered
    assert all(token not in rendered for token in ("axis", "geometry", "field", "recall", "summary", "score"))


@pytest.mark.parametrize("recorded_at", ("2026-07-02T12:34:56Z", "2026-07-02T12:34:56+08:00"))
def test_c106_strict_rfc3339_accepts_valid_forms(tmp_path, recorded_at: str) -> None:
    receipt = CaptureIngress(tmp_path / "ci1").capture(replace(_request(), recorded_at=recorded_at), CapturePolicy("cp_time"), open_store(tmp_path / "evidence"))
    assert receipt.status is CaptureStatus.captured


@pytest.mark.parametrize(
    "recorded_at",
    (
        "2026-07-02 12:34:56+08:00",
        "2026-07-02T12:34:56+0800",
        "20260702T123456+08:00",
        "2026-07-02T12:34:56+00:60",
        "2026-07-02T12:34:56-00:60",
        "2026-07-02T12:34:56",
    ),
)
def test_c106_strict_rfc3339_rejects_invalid_forms_with_no_success_writes(tmp_path, recorded_at: str) -> None:
    evidence = open_store(tmp_path / "evidence")
    receipt = CaptureIngress(tmp_path / "ci1").capture(replace(_request(), recorded_at=recorded_at), CapturePolicy("cp_time"), evidence)
    assert receipt.status is CaptureStatus.rejected
    assert len(evidence.read_ledger()) == 0
    assert not (tmp_path / "ci1" / "visibility").exists()
    assert not (tmp_path / "ci1" / "candidates").exists()
    assert not (tmp_path / "ci1" / "receipts").exists()


def test_candidate_policy_must_match_fixed_gate(tmp_path) -> None:
    request = replace(_request(), deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)))
    receipt = CaptureIngress(tmp_path / "ci1").capture(request, CapturePolicy("cp_bad_candidate"), open_store(tmp_path / "evidence"))
    assert receipt.status is CaptureStatus.rejected
    assert receipt.error is not None
    assert receipt.error.code == "CI1_CANDIDATE_FORBIDDEN"


def _request(capture_id: str = "cap_policy") -> CaptureRequest:
    return CaptureRequest(
        capture_id,
        "Host supplied raw capture.",
        CaptureOrigin(OriginKind.tool_observation, "turn:opaque", "session:alpha", "tool"),
        "2026-07-02T12:34:56+08:00",
        ("session:alpha",),
        VisibilityScope.session_window,
    )


def _diagnostic_payloads(root) -> list[dict]:
    path = root / "diagnostics"
    if not path.exists():
        return []
    return [json.loads(item.read_text(encoding="utf-8")) for item in sorted(path.glob("*.json"))]
