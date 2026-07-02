from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from nollm.dream_geometry.admission import AdmissionOutcome, AdmissionPlacementPlan, DA1Rejection
from nollm.dream_geometry.admission.errors import DA1_PLACEMENT_AXIS_MISMATCH
from nollm.dream_geometry.batch_admission import (
    BatchAdmissionCoordinator,
    BA1_DECISION_MEMBER_MISMATCH,
    BA1_DUPLICATE_ADMISSION,
    BA1_DUPLICATE_CANDIDATE,
    BA1_DUPLICATE_DECISION,
    BA1_DUPLICATE_PLACEMENT_PLAN,
    BA1_DUPLICATE_PROPOSAL,
    BA1_MEMBER_PREFLIGHT_REJECTED,
    BA1_REQUEST_SHARD_MISMATCH,
    BA1CommitInterrupted,
    BA1Rejection,
    batch_request_fingerprint,
)
from nollm.dream_geometry.capture import CaptureIngress
from nollm.dream_geometry.cortex import open_store as open_cortex_store
from nollm.dream_geometry.admission import MemoryAdmissionOrchestrator, open_store as open_admission_store
from tests.fixtures.ba1.fixture import build_ba1_environment, batch_request, tree_manifest


def _state_manifest(root: Path) -> dict[str, dict[str, str]]:
    return {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission", "capture")}


def test_ba101_two_deferred_candidates_admit_independently_and_keep_capture_state(tmp_path) -> None:
    evidence, _cortex, admission, capture_state, coordinator, request = build_ba1_environment(tmp_path)
    before_capture = tree_manifest(tmp_path / "capture")

    receipt = coordinator.submit(request)

    assert [member.member_id for member in receipt.member_receipts] == ["bam_ba1_01", "bam_ba1_02"]
    assert [item.admission_receipt.outcome for item in receipt.member_receipts] == [AdmissionOutcome.committed, AdmissionOutcome.committed]
    assert len(admission.records()) == 2
    for member_receipt in receipt.member_receipts:
        record = admission.get_admission_record(member_receipt.admission_receipt.admission_id)
        MemoryAdmissionOrchestrator(evidence, _cortex, admission).replay_record(record)
    assert tree_manifest(tmp_path / "capture") == before_capture
    assert capture_state.candidate_count() == 2
    assert not any((tmp_path / name).exists() for name in ("field", "recall", "assembly", "batch"))
    assert not hasattr(receipt, "dream_shards")
    assert not hasattr(receipt, "placement_plan")
    assert not hasattr(receipt, "field_snapshot")


def test_ba102_member_input_order_is_canonical_and_idempotent_fingerprint_is_stable(tmp_path) -> None:
    _evidence, _cortex, admission, _capture_state, coordinator, request = build_ba1_environment(tmp_path)
    reversed_request = replace(request, members=tuple(reversed(request.members)))

    first = coordinator.submit(reversed_request)
    second = coordinator.submit(request)

    assert [item.member_id for item in first.member_receipts] == ["bam_ba1_01", "bam_ba1_02"]
    assert [item.member_id for item in second.member_receipts] == ["bam_ba1_01", "bam_ba1_02"]
    assert first.request_fingerprint == second.request_fingerprint == batch_request_fingerprint(request)
    assert [item.admission_receipt.outcome for item in second.member_receipts] == [AdmissionOutcome.idempotent, AdmissionOutcome.idempotent]
    assert len(admission.records()) == 2
    assert [record.projection_fingerprint for record in admission.records()] == [item.admission_receipt.projection_fingerprint for item in first.member_receipts]


@pytest.mark.parametrize(
    "case,expected",
    (
        ("decision_mismatch", BA1_DECISION_MEMBER_MISMATCH),
        ("request_shard_mismatch", BA1_REQUEST_SHARD_MISMATCH),
        ("duplicate_candidate", BA1_DUPLICATE_CANDIDATE),
        ("duplicate_admission", BA1_DUPLICATE_ADMISSION),
        ("da1_preflight", BA1_MEMBER_PREFLIGHT_REJECTED),
    ),
)
def test_ba103_preflight_rejections_are_zero_da1_commit(tmp_path, case: str, expected: str) -> None:
    _evidence, _cortex, admission, _capture_state, coordinator, request = build_ba1_environment(tmp_path)
    bad_members = list(request.members)
    if case == "decision_mismatch":
        decision = replace(bad_members[1].promotion_decision, candidate_id=bad_members[0].candidate_id)
        bad_members[1] = replace(bad_members[1], promotion_decision=decision)
    elif case == "request_shard_mismatch":
        req = replace(bad_members[1].admission_request, dream_shard=bad_members[0].admission_request.dream_shard)
        bad_members[1] = replace(bad_members[1], admission_request=req)
        bad_members = [bad_members[1]]
    elif case == "duplicate_candidate":
        decision = replace(bad_members[1].promotion_decision, candidate_id=bad_members[0].candidate_id, shard_id=bad_members[1].admission_request.dream_shard.shard_id)
        bad_members[1] = replace(bad_members[1], candidate_id=bad_members[0].candidate_id, promotion_decision=decision)
    elif case == "duplicate_admission":
        req = replace(bad_members[1].admission_request, admission_id=bad_members[0].admission_request.admission_id)
        bad_members[1] = replace(bad_members[1], admission_request=req)
    else:
        req = replace(
            bad_members[1].admission_request,
            placement_plan=AdmissionPlacementPlan("apl_ba1_bad", bad_members[1].admission_request.placement_plan.axis_placements[:1]),
        )
        bad_members[1] = replace(bad_members[1], admission_request=req)
    window_shards = request.window.member_shard_ids if case != "request_shard_mismatch" else (request.members[1].admission_request.dream_shard.shard_id,)
    bad = batch_request(tuple(bad_members), member_shard_ids=window_shards)
    before = {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission", "capture")}

    with pytest.raises(BA1Rejection) as error:
        coordinator.submit(bad)

    assert expected in error.value.reason_codes
    if expected == BA1_MEMBER_PREFLIGHT_REJECTED:
        assert DA1_PLACEMENT_AXIS_MISMATCH in error.value.reason_codes
    assert {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission", "capture")} == before
    assert len(admission.records()) == 0


def test_ba1_c1_t01_duplicate_decision_id_is_zero_commit_rejection(tmp_path) -> None:
    _evidence, _cortex, admission, _capture_state, coordinator, request = build_ba1_environment(tmp_path)
    bad_members = list(request.members)
    bad_members[1] = replace(
        bad_members[1],
        promotion_decision=replace(
            bad_members[1].promotion_decision,
            decision_id=bad_members[0].promotion_decision.decision_id,
        ),
    )
    bad = batch_request(tuple(bad_members), member_shard_ids=request.window.member_shard_ids)
    before = _state_manifest(tmp_path)

    with pytest.raises(BA1Rejection) as error:
        coordinator.submit(bad)

    assert BA1_DUPLICATE_DECISION in error.value.reason_codes
    assert _state_manifest(tmp_path) == before
    assert len(admission.records()) == 0


def test_ba1_c1_t02_duplicate_compiled_proposal_id_is_zero_commit_rejection(tmp_path) -> None:
    _evidence, _cortex, admission, _capture_state, coordinator, request = build_ba1_environment(tmp_path)
    bad_members = list(request.members)
    growth_submission = dict(bad_members[1].admission_request.growth_submission)
    growth_submission["proposal_id"] = bad_members[0].admission_request.growth_submission["proposal_id"]
    bad_members[1] = replace(
        bad_members[1],
        admission_request=replace(bad_members[1].admission_request, growth_submission=growth_submission),
    )
    bad = batch_request(tuple(bad_members), member_shard_ids=request.window.member_shard_ids)
    before = _state_manifest(tmp_path)

    with pytest.raises(BA1Rejection) as error:
        coordinator.submit(bad)

    assert BA1_DUPLICATE_PROPOSAL in error.value.reason_codes
    assert _state_manifest(tmp_path) == before
    assert len(admission.records()) == 0


def test_ba1_c1_t03_duplicate_placement_plan_id_is_zero_commit_rejection(tmp_path) -> None:
    _evidence, _cortex, admission, _capture_state, coordinator, request = build_ba1_environment(tmp_path)
    bad_members = list(request.members)
    bad_plan = AdmissionPlacementPlan(
        bad_members[0].admission_request.placement_plan.plan_id,
        bad_members[1].admission_request.placement_plan.axis_placements,
    )
    bad_members[1] = replace(
        bad_members[1],
        admission_request=replace(bad_members[1].admission_request, placement_plan=bad_plan),
    )
    bad = batch_request(tuple(bad_members), member_shard_ids=request.window.member_shard_ids)
    before = _state_manifest(tmp_path)

    with pytest.raises(BA1Rejection) as error:
        coordinator.submit(bad)

    assert BA1_DUPLICATE_PLACEMENT_PLAN in error.value.reason_codes
    assert _state_manifest(tmp_path) == before
    assert len(admission.records()) == 0


def test_ba1_c1_t04_malformed_lower_preflight_is_normalized(tmp_path) -> None:
    _evidence, _cortex, admission, _capture_state, coordinator, request = build_ba1_environment(tmp_path)
    bad_member = replace(
        request.members[0],
        admission_request=replace(request.members[0].admission_request, growth_submission={}),
    )
    bad = batch_request((bad_member,), member_shard_ids=(request.members[0].admission_request.dream_shard.shard_id,))
    before = _state_manifest(tmp_path)

    with pytest.raises(BA1Rejection) as error:
        coordinator.submit(bad)

    assert BA1_MEMBER_PREFLIGHT_REJECTED in error.value.reason_codes
    assert "DC1_MISSING_REQUIRED_FIELD" in error.value.reason_codes
    assert _state_manifest(tmp_path) == before
    assert len(admission.records()) == 0


def test_ba104_reopen_retry_uses_da1_idempotency_without_new_records(tmp_path) -> None:
    evidence, cortex, admission, capture_state, coordinator, request = build_ba1_environment(tmp_path)
    first = coordinator.submit(request)
    before = {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission", "capture")}
    reopened_admission = open_admission_store(tmp_path / "admission", evidence, cortex, MemoryAdmissionOrchestrator(evidence, cortex, admission).validate_replay_record)
    reopened = BatchAdmissionCoordinator(capture_state, evidence, MemoryAdmissionOrchestrator(evidence, cortex, reopened_admission))

    second = reopened.submit(request)

    assert [item.admission_receipt.outcome for item in second.member_receipts] == [AdmissionOutcome.idempotent, AdmissionOutcome.idempotent]
    assert [item.admission_receipt.projection_fingerprint for item in second.member_receipts] == [item.admission_receipt.projection_fingerprint for item in first.member_receipts]
    assert {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission", "capture")} == before


def test_ba105_commit_interruption_reports_completed_member_and_retries(tmp_path, monkeypatch) -> None:
    evidence, cortex, admission, capture_state, coordinator, request = build_ba1_environment(tmp_path)
    original_put = admission.put_admission_record

    def fail_second(record):
        if record.admission_id == request.members[1].admission_request.admission_id:
            raise RuntimeError("synthetic BA1 second member failure")
        return original_put(record)

    monkeypatch.setattr(admission, "put_admission_record", fail_second)
    with pytest.raises(BA1CommitInterrupted) as interrupted:
        coordinator.submit(request)

    assert interrupted.value.failed_member_id == "bam_ba1_02"
    assert [item.member_id for item in interrupted.value.completed_member_receipts] == ["bam_ba1_01"]
    assert admission.has_admission_record(request.members[0].admission_request.admission_id)
    assert not admission.has_admission_record(request.members[1].admission_request.admission_id)

    monkeypatch.undo()
    retry = BatchAdmissionCoordinator(capture_state, evidence, MemoryAdmissionOrchestrator(evidence, cortex, admission)).submit(request)
    assert [item.admission_receipt.outcome for item in retry.member_receipts] == [AdmissionOutcome.idempotent, AdmissionOutcome.committed]
    assert len(evidence.read_ledger()) == 2
    assert tree_manifest(tmp_path / "capture")


def test_ba106_cross_candidate_evidence_pair_rejects_and_capture_store_is_not_mutated(tmp_path, monkeypatch) -> None:
    _evidence, _cortex, _admission, capture_state, coordinator, request = build_ba1_environment(tmp_path)
    bad = list(request.members)
    bad[0] = replace(bad[0], admission_request=replace(bad[0].admission_request, dream_shard=bad[1].admission_request.dream_shard))
    bad = [bad[0]]
    before_capture = tree_manifest(tmp_path / "capture")

    monkeypatch.setattr(CaptureIngress, "capture", _forbidden)
    monkeypatch.setattr(capture_state, "put_candidate", _forbidden)
    monkeypatch.setattr(capture_state, "put_capture_identity", _forbidden)
    monkeypatch.setattr(capture_state, "append_visibility", _forbidden)
    monkeypatch.setattr(capture_state, "put_receipt", _forbidden)

    with pytest.raises(BA1Rejection) as error:
        coordinator.preflight(batch_request(tuple(bad), member_shard_ids=(request.members[0].admission_request.dream_shard.shard_id,)))

    assert BA1_REQUEST_SHARD_MISMATCH in error.value.reason_codes
    assert tree_manifest(tmp_path / "capture") == before_capture


def test_ba107_dependency_and_drift_boundary() -> None:
    source = Path(__file__).resolve().parents[1] / "nollm" / "dream_geometry" / "batch_admission"
    forbidden_imports = {"cortex", "geometry", "field", "assembly", "recall", "adapters"}
    forbidden_tokens = ("glob(", "rglob(", ".records(", "FieldSnapshot", "RecallUniverse", "GrowthTrace", "CoarseCover", "GravitySnapshot", "datetime.now", "utcnow")
    for path in source.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden_tokens), path
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(name.startswith("nollm.dream_geometry." + module) for name in names for module in forbidden_imports), path


def _forbidden(*_args, **_kwargs):
    raise AssertionError("BA1 must not mutate CI1 capture state")
