from __future__ import annotations

import json
from dataclasses import replace

import pytest

from nollm.dream_geometry.admission import (
    AdmissionOutcome,
    AdmissionPlacementPlan,
    AxisPlacement,
    DA1Rejection,
    MemoryAdmissionOrchestrator,
    open_store as open_admission_store,
)
from nollm.dream_geometry.admission.errors import (
    DA1_ADMISSION_ID_PAYLOAD_CONFLICT,
    DA1_ADMISSION_RECORD_COMMIT_FAILED,
    DA1_CORTEX_COMMIT_FAILED,
    DA1_INTERNAL_FIELD_DETAIL_EXPOSED,
    DA1_MULTI_STEP_RAY_DEFERRED,
    DA1_PLACEMENT_AXIS_MISMATCH,
    DA1_PLACEMENT_STEP_MISMATCH,
    DA1_PROPOSAL_ALREADY_ADMITTED,
    DA1_REPLAY_PROJECTION_MISMATCH,
    DA1_UNVERIFIED_CROSS_CHART_LINK,
)
from nollm.dream_geometry.cortex import open_store as open_cortex_store
from nollm.dream_geometry.evidence import open_store as open_evidence_store
from nollm.dream_geometry.geometry import AxialCoord, LocalChart, Vec2, make_hex_cell
from nollm.dream_geometry.protocol.contracts import CoverState
from tests.fixtures.da1.fixture import ADMISSION_ID, PROPOSAL_ID, build_environment, build_request, tree_manifest


def test_a01_success_calls_public_chain_and_replays(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_environment(tmp_path)
    receipt = orchestrator.admit(build_request())

    assert receipt.outcome is AdmissionOutcome.committed
    assert receipt.subject_shard_id == "shard:da1:synthetic-weather"
    assert receipt.proposal_id == PROPOSAL_ID
    assert receipt.source_trace_count == 2
    assert receipt.derived_trace_count == 2
    assert receipt.residual_count == 2
    assert receipt.cover_state_counts == {"candidate": 0, "stable": 1, "crystallized": 0}
    assert evidence.get_dream_shard(receipt.subject_shard_id).shard_id == receipt.subject_shard_id
    assert cortex.get_growth_proposal(PROPOSAL_ID).proposal_id == PROPOSAL_ID
    record = admission.get_admission_record(ADMISSION_ID)
    projection = orchestrator.replay_record(record)
    assert projection.projection_fingerprint == record.projection_fingerprint
    assert all(cover.state is not CoverState.crystallized for cover in projection.covers)


def test_a02_dc1_rejection_is_zero_write(tmp_path) -> None:
    _evidence, _cortex, _admission, orchestrator = build_environment(tmp_path)
    before = {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")}
    request = build_request()
    bad = dict(request.growth_submission)
    bad["axes"] = []
    with pytest.raises(Exception):
        orchestrator.admit(replace(request, growth_submission=bad))
    assert {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")} == before


def test_a03_to_a05_placement_and_multi_step_rejections_are_zero_write(tmp_path) -> None:
    _evidence, _cortex, _admission, orchestrator = build_environment(tmp_path)
    request = build_request()
    before = {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")}

    missing_axis = replace(request, placement_plan=AdmissionPlacementPlan("apl_da1_synthetic_weather", request.placement_plan.axis_placements[:1]))
    with pytest.raises(DA1Rejection) as axis_error:
        orchestrator.admit(missing_axis)
    assert axis_error.value.reason_codes == (DA1_PLACEMENT_AXIS_MISMATCH,)

    wrong_step = replace(
        request.placement_plan.axis_placements[0],
        step_id="step_da1_wrong",
    )
    wrong_step_request = replace(request, placement_plan=AdmissionPlacementPlan("apl_da1_synthetic_weather", (wrong_step, request.placement_plan.axis_placements[1])))
    with pytest.raises(DA1Rejection) as step_error:
        orchestrator.admit(wrong_step_request)
    assert step_error.value.reason_codes == (DA1_PLACEMENT_STEP_MISMATCH,)

    bad_growth = dict(request.growth_submission)
    bad_axes = list(bad_growth["axes"])
    bad_axes[0] = dict(bad_axes[0])
    bad_axes[0]["ray"] = list(bad_axes[0]["ray"]) + [
            {
                "step_id": "step_da1_location_second",
                "expression": "synthetic",
                "basis": "deterministic_projection",
                "basis_refs": [
                    {"ref_type": "step", "input_step_id": "step_da1_location"},
                    {"ref_type": "rule", "rule_id": "rule_da1_projection", "rule_version": "1", "rule_label": "synthetic projection", "source_ref": "protocol:v2:da1"},
                ],
                "rationale": None,
            }
    ]
    bad_growth["axes"] = bad_axes
    with pytest.raises(DA1Rejection) as ray_error:
        orchestrator.admit(replace(request, growth_submission=bad_growth))
    assert ray_error.value.reason_codes == (DA1_MULTI_STEP_RAY_DEFERRED,)

    assert {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")} == before


def test_a07_cross_chart_without_link_is_zero_write(tmp_path) -> None:
    _evidence, _cortex, _admission, orchestrator = build_environment(tmp_path)
    request = build_request()
    source_chart = LocalChart("da1:fine", 0, 1.0, 0.0, Vec2(0.0, 0.0))
    target_chart = LocalChart("da1:coarse", 0, 1.0, 0.0, Vec2(0.0, 0.0))
    placement = AxisPlacement(
        "location",
        "step_da1_location",
        make_hex_cell(source_chart, AxialCoord(0, 0)),
        (make_hex_cell(target_chart, AxialCoord(0, 0)),),
        None,
    )
    plan = AdmissionPlacementPlan("apl_da1_synthetic_weather", (placement, request.placement_plan.axis_placements[1]))
    before = {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")}
    with pytest.raises(DA1Rejection) as error:
        orchestrator.admit(replace(request, placement_plan=plan))
    assert error.value.reason_codes == (DA1_UNVERIFIED_CROSS_CHART_LINK,)
    assert {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")} == before


def test_a08_to_a11_idempotency_conflict_and_input_order(tmp_path) -> None:
    _evidence, _cortex, admission, orchestrator = build_environment(tmp_path)
    request = build_request()
    first = orchestrator.admit(request)
    before = {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")}
    second = orchestrator.admit(request)
    assert second.outcome is AdmissionOutcome.idempotent
    assert second.projection_fingerprint == first.projection_fingerprint
    assert {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")} == before

    changed = build_request(axes=(("location", "Kunming"), ("phenomenon", "synthetic")))
    with pytest.raises(DA1Rejection) as conflict:
        orchestrator.admit(changed)
    assert conflict.value.reason_codes == (DA1_ADMISSION_ID_PAYLOAD_CONFLICT,)

    reused = build_request(admission_id="adm_da1_reuse", proposal_id=PROPOSAL_ID)
    with pytest.raises(DA1Rejection) as proposal_reuse:
        orchestrator.admit(reused)
    assert proposal_reuse.value.reason_codes == (DA1_PROPOSAL_ALREADY_ADMITTED,)
    assert len(admission.records()) == 1

    _e2, _c2, _a2, other = build_environment(tmp_path / "order")
    ordered = other.admit(build_request(plan_order="reverse"))
    assert ordered.projection_fingerprint == first.projection_fingerprint


def test_a13_to_a16_field_projection_and_receipt_redaction(tmp_path) -> None:
    _evidence, _cortex, admission, orchestrator = build_environment(tmp_path)
    receipt = orchestrator.admit(build_request())
    record = admission.get_admission_record(ADMISSION_ID)
    projection = orchestrator.replay_record(record)

    for trace, residual in zip(projection.source_traces, projection.residuals):
        derived_mass = sum(child.mass for child in projection.derived_traces if child.parent_trace_id == trace.trace_id)
        assert abs((derived_mass + residual.mass) - trace.mass) < 1e-9
    assert projection.gravity_snapshot.snapshot_id
    rendered_receipt = json.dumps(receipt.to_mapping(), sort_keys=True)
    forbidden_tokens = ("potential", "mass", "cell", "chart", "cover_id", "trace:", "kernel", "path")
    assert not any(token in rendered_receipt for token in forbidden_tokens), DA1_INTERNAL_FIELD_DETAIL_EXPOSED
    assert not any(path.name.startswith(("trace", "cover", "gravity")) for path in (tmp_path / "admission").rglob("*") if path.is_file())


def test_a17_a18_partial_failure_retry(tmp_path) -> None:
    evidence = open_evidence_store(tmp_path / "evidence")
    cortex = open_cortex_store(tmp_path / "cortex", evidence)
    admission = open_admission_store(tmp_path / "admission", evidence, cortex)

    class FailingCortex:
        root = cortex.root

        def __init__(self):
            self.failed = False

        def compile_growth(self, submission):
            if not self.failed:
                self.failed = True
                raise RuntimeError("synthetic cortex failure")
            return cortex.compile_growth(submission)

        def get_growth_proposal(self, proposal_id):
            return cortex.get_growth_proposal(proposal_id)

        def stored_growth_proposal(self, proposal_id):
            return cortex.stored_growth_proposal(proposal_id)

        def receipts(self):
            return cortex.receipts()

    with pytest.raises(DA1Rejection) as cortex_error:
        MemoryAdmissionOrchestrator(evidence, FailingCortex(), admission).admit(build_request())
    assert cortex_error.value.reason_codes == (DA1_CORTEX_COMMIT_FAILED,)
    assert tree_manifest(tmp_path / "evidence")
    assert not admission.has_admission_record(ADMISSION_ID)
    retry = MemoryAdmissionOrchestrator(evidence, cortex, admission).admit(build_request())
    assert retry.outcome is AdmissionOutcome.committed

    other_root = tmp_path / "record_failure"
    evidence2 = open_evidence_store(other_root / "evidence")
    cortex2 = open_cortex_store(other_root / "cortex", evidence2)
    admission2 = open_admission_store(other_root / "admission", evidence2, cortex2)

    class FailingAdmission:
        root = admission2.root

        def has_admission_record(self, admission_id):
            return admission2.has_admission_record(admission_id)

        def get_admission_record(self, admission_id):
            return admission2.get_admission_record(admission_id)

        def find_by_proposal_id(self, proposal_id):
            return admission2.find_by_proposal_id(proposal_id)

        def put_admission_record(self, record):
            raise RuntimeError("synthetic admission failure")

        def validate_record_references(self, record):
            return admission2.validate_record_references(record)

    with pytest.raises(DA1Rejection) as admission_error:
        MemoryAdmissionOrchestrator(evidence2, cortex2, FailingAdmission()).admit(build_request())
    assert admission_error.value.reason_codes == (DA1_ADMISSION_RECORD_COMMIT_FAILED,)
    assert tree_manifest(other_root / "evidence")
    assert tree_manifest(other_root / "cortex")
    assert not admission2.has_admission_record(ADMISSION_ID)
    assert MemoryAdmissionOrchestrator(evidence2, cortex2, admission2).admit(build_request()).outcome is AdmissionOutcome.committed


def test_a19_a20_reopen_replay_and_tamper_rejection(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_environment(tmp_path)
    orchestrator.admit(build_request())
    reopened = open_admission_store(tmp_path / "admission", evidence, cortex, orchestrator.validate_replay_record)
    assert reopened.get_admission_record(ADMISSION_ID).projection_fingerprint

    record_path = next((tmp_path / "admission" / "records").glob("*.json"))
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    payload["projection_fingerprint"] = "sha256:" + "0" * 64
    record_path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True), encoding="utf-8")
    with pytest.raises(DA1Rejection) as mismatch:
        open_admission_store(tmp_path / "admission", evidence, cortex, orchestrator.validate_replay_record)
    assert mismatch.value.reason_codes == (DA1_REPLAY_PROJECTION_MISMATCH,)
