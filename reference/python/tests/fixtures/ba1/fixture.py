from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

from nollm.dream_geometry.admission import (
    AdmissionPlacementPlan,
    AdmissionRequest,
    AxisPlacement,
    FIELD_PROFILE_ID,
    MemoryAdmissionOrchestrator,
    open_store as open_admission_store,
)
from nollm.dream_geometry.batch_admission import (
    BatchAdmissionCoordinator,
    BatchAdmissionMember,
    BatchAdmissionRequest,
    BatchAdmissionWindow,
    BatchWindowStatus,
    PromotionDecider,
    PromotionDecision,
    PromotionDecisionKind,
    PromotionReason,
)
from nollm.dream_geometry.capture import (
    CandidateTrigger,
    CaptureDiagnostics,
    CaptureIngress,
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    DeferredCandidateRequest,
    PromotionMode,
    VisibilityScope,
)
from nollm.dream_geometry.cortex import open_store as open_cortex_store
from nollm.dream_geometry.evidence import DreamShard, open_store as open_evidence_store
from nollm.dream_geometry.protocol.contracts import OriginKind
from tests.fixtures.da1.fixture import build_request as build_da1_request


RECORDED_AT = "2026-07-02T10:00:00+00:00"


def build_ba1_environment(root: Path, *, count: int = 2):
    evidence = open_evidence_store(root / "evidence")
    capture = CaptureIngress(root / "capture")
    captured = tuple(_capture_deferred(capture, evidence, index) for index in range(1, count + 1))
    cortex = open_cortex_store(root / "cortex", evidence)
    admission = open_admission_store(root / "admission", evidence, cortex)
    orchestrator = MemoryAdmissionOrchestrator(evidence, cortex, admission)
    coordinator = BatchAdmissionCoordinator(capture.state_store, evidence, orchestrator)
    members = tuple(_member(index, candidate_id, shard, admission_request(shard, index)) for index, (candidate_id, shard) in enumerate(captured, start=1))
    request = batch_request(members)
    return evidence, cortex, admission, capture.state_store, coordinator, request


def batch_request(
    members: tuple[BatchAdmissionMember, ...],
    *,
    window_id: str = "baw_ba1_synthetic",
    submitted_at: str = RECORDED_AT,
    member_shard_ids: tuple[str, ...] | None = None,
) -> BatchAdmissionRequest:
    return BatchAdmissionRequest(
        BatchAdmissionWindow(
            window_id,
            member_shard_ids if member_shard_ids is not None else tuple(member.admission_request.dream_shard.shard_id for member in members),
            ("source:ba1",),
            RECORDED_AT,
            None,
            "policy:ba1:synthetic",
            FIELD_PROFILE_ID,
            BatchWindowStatus.ready_for_selection,
        ),
        members,
        submitted_at,
    )


def admission_request(shard: DreamShard, index: int, *, admission_id: str | None = None, proposal_id: str | None = None) -> AdmissionRequest:
    request = build_da1_request(
        admission_id=admission_id or f"adm_ba1_synthetic_{index}",
        proposal_id=proposal_id or f"gp_ba1_synthetic_{index}",
    )
    growth = _growth_for_shard(request.growth_submission, shard, proposal_id or f"gp_ba1_synthetic_{index}")
    placements = tuple(
        AxisPlacement(placement.axis_id, placement.step_id, placement.source_cell, placement.fine_to_coarse_targets, placement.verified_chart_link)
        for placement in request.placement_plan.axis_placements
    )
    return replace(
        request,
        dream_shard=shard,
        growth_submission=growth,
        placement_plan=AdmissionPlacementPlan(f"apl_ba1_synthetic_{index}", placements),
        recorded_at=RECORDED_AT,
    )


def tree_manifest(root: Path) -> tuple[tuple[str, str], ...]:
    root = Path(root)
    if not root.exists():
        return ()
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))


def _capture_deferred(capture: CaptureIngress, evidence, index: int) -> tuple[str, DreamShard]:
    request = __import__("nollm.dream_geometry.capture", fromlist=["CaptureRequest"]).CaptureRequest(
        f"cap_ba1_synthetic_{index}",
        "Kunming rain synthetic shard.",
        CaptureOrigin(OriginKind.user_utterance, f"turn:ba1:{index}", "source:ba1", "user"),
        RECORDED_AT,
        ("source:ba1",),
        VisibilityScope.source_window,
        DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
    )
    policy = CapturePolicy(
        f"cp_ba1_synthetic_{index}",
        persistence=CapturePersistence.persistent,
        lineage=CaptureLineage.minimal,
        diagnostics=CaptureDiagnostics.on_failure,
        allowed_visibility_scopes=(VisibilityScope.source_window,),
        promotion_mode=PromotionMode.manual,
    )
    receipt = capture.capture(request, policy, evidence)
    return receipt.deferred_candidate_id, evidence.get_dream_shard(receipt.shard_id)


def _member(index: int, candidate_id: str, shard: DreamShard, request: AdmissionRequest) -> BatchAdmissionMember:
    return BatchAdmissionMember(
        f"bam_ba1_{index:02d}",
        candidate_id,
        PromotionDecision(
            f"pmd_ba1_{index:02d}",
            candidate_id,
            shard.shard_id,
            PromotionDecisionKind.promote,
            (PromotionReason.explicit_pin, PromotionReason.manual_batch_selection),
            PromotionDecider.human_operator,
            RECORDED_AT,
            "request_growth_submission",
        ),
        request,
    )


def _growth_for_shard(growth: dict[str, Any], shard: DreamShard, proposal_id: str) -> dict[str, Any]:
    rendered = {
        "contract_version": growth["contract_version"],
        "proposal_id": proposal_id,
        "subject_shard_id": shard.shard_id,
        "submitted_at": RECORDED_AT,
        "budget": dict(growth["budget"]),
        "do_not_infer": list(growth["do_not_infer"]),
        "forbidden_inferences": list(growth["forbidden_inferences"]),
        "possible_conflict_refs": list(growth["possible_conflict_refs"]),
        "axes": [],
    }
    axes = []
    for axis in growth["axes"]:
        copied_axis = {"axis_id": axis["axis_id"], "ray": []}
        for step in axis["ray"]:
            copied_refs = []
            for ref in step["basis_refs"]:
                copied = dict(ref)
                if copied.get("ref_type") == "text_span":
                    copied["record_id"] = shard.shard_id
                copied_refs.append(copied)
            copied_axis["ray"].append(
                {
                    "step_id": step["step_id"],
                    "expression": step["expression"],
                    "basis": step["basis"],
                    "basis_refs": copied_refs,
                    "rationale": step["rationale"],
                }
            )
        axes.append(copied_axis)
    rendered["axes"] = axes
    return rendered
