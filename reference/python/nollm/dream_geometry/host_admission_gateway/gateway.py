"""HAG1 file-first explicit admission gateway."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from nollm.dream_geometry.admission import AdmissionRequest, placement_plan_from_payload
from nollm.dream_geometry.batch_admission import PromotionDecider, PromotionDecision, PromotionDecisionKind, PromotionReason
from nollm.dream_geometry.capture import CandidateStatus, CaptureStateStore
from nollm.dream_geometry.evidence import open_store as open_evidence_store
from nollm.dream_geometry.host_execution import (
    HX1ExecutionError,
    HostAdmissionBinding,
    HostExecutionContext,
    HostPlanBindings,
    execute_host_plan,
    receipt_to_mapping,
)

from .decode import decode_admission_payload, load_json_text
from .errors import (
    HAG_ADMISSION_INTERRUPTED,
    HAG_ADMISSION_REJECTED,
    HAGError,
    HAG_INTERNAL_ERROR,
    HAG_INVALID_REQUEST,
    HAG_REOPEN_MISMATCH,
    HAG_WORKSPACE_NOT_OWNED,
)
from .serialization import error_envelope, fingerprint, ok_envelope
from .types import GatewayAdmissionRequest, GatewayMember


HX1_MARKER_NAME = ".hx1_host_execution_root.json"
NON_INFERENCES = (
    "no_automatic_admission",
    "no_global_discovery",
    "no_anchor_creation",
    "no_truth_confirmation",
    "no_dg6_recall_influence",
)


def admit_from_text(workspace: Path, text: str) -> dict[str, Any]:
    request_id: str | None = None
    try:
        decoded = decode_admission_payload(load_json_text(text))
        request_id = decoded.request_id
        result = admit(workspace, decoded)
        return ok_envelope(decoded.request_id, result)
    except HAGError as exc:
        return error_envelope(request_id, exc.code, exc.message)
    except Exception:
        return error_envelope(request_id, HAG_INTERNAL_ERROR)


def admit(workspace: Path, decoded: GatewayAdmissionRequest) -> dict[str, Any]:
    workspace = Path(workspace).resolve()
    _require_owned_workspace(workspace)
    actuals = _resolve_actual_identities(workspace, decoded)
    evidence = open_evidence_store(workspace / "evidence")
    shards = _read_actual_shards(evidence, actuals)
    projections = _derive_projections(decoded)
    plan = _plan(decoded, projections)
    bindings = _bindings(decoded, projections, shards)
    context = HostExecutionContext(
        workspace,
        decoded.submitted_at,
        batch_window_id=decoded.window.window_id,
        batch_policy_id=decoded.window.shared_policy_ref,
        batch_source_ref=decoded.window.source_window_refs[0],
        finite_set_id="hag1_explicit_admission_set_" + _safe_suffix(decoded.request_id),
        enable_dg6_verification=False,
    )
    try:
        receipt = execute_host_plan(plan, bindings, context)
    except HX1ExecutionError as exc:
        raise _hag_from_hx1(exc) from exc
    mapping = receipt_to_mapping(receipt)
    if mapping["status"] != "completed" or mapping["completed_stages"] != ["admission"]:
        raise HAGError(HAG_ADMISSION_REJECTED, "admission was rejected")
    return {
        "window_id": decoded.window.window_id,
        "request_fingerprint": fingerprint(decoded.raw_payload),
        "admission_ids": list(mapping["admission_receipt_ids"]),
        "members": [
            {
                "member_id": member.member_id,
                "candidate_id": member.candidate_id,
                "shard_id": member.admission.shard_id,
                "admission_id": member.admission.admission_id,
                "cx2_projection": {
                    "projection_version": "1",
                    "candidate_ref": projections[member.member_id]["candidate_ref"],
                    "shard_ref": projections[member.member_id]["shard_ref"],
                },
            }
            for member in decoded.members
        ],
        "host_execution": {
            "plan_id": mapping["plan_id"],
            "status": mapping["status"],
            "completed_stages": mapping["completed_stages"],
            "execution_input_fingerprint": mapping["execution_input_fingerprint"],
            "output_fingerprint": mapping["output_fingerprint"],
        },
    }


def _plan(decoded: GatewayAdmissionRequest, projections: dict[str, dict[str, str]]) -> dict[str, Any]:
    return {
        "plan_kind": "nollm_cortex_action_plan",
        "plan_version": "1",
        "plan_id": "cx2_hag1_" + _safe_suffix(fingerprint(decoded.raw_payload)),
        "intent": "admission",
        "capture_refs": (),
        "promotion_decisions": tuple(
            {
                "decision_id": member.promotion_decision.decision_id,
                "candidate_id": projections[member.member_id]["candidate_ref"],
                "shard_id": projections[member.member_id]["shard_ref"],
                "decision": "promote",
                "reasons": member.promotion_decision.reasons,
                "decided_by": member.promotion_decision.decided_by,
            }
            for member in decoded.members
        ),
        "admission_request_refs": tuple(
            {
                "request_id": _admission_request_ref(member),
                "decision_id": member.promotion_decision.decision_id,
                "shard_id": projections[member.member_id]["shard_ref"],
                "proposal_ref": str(member.admission.growth_submission.get("proposal_id", "")),
                "placement_plan_ref": str(member.admission.placement_plan.get("plan_id", "")),
            }
            for member in decoded.members
        ),
        "explicit_assembly": None,
        "recall_request": None,
        "derived_views": (),
        "non_inferences": NON_INFERENCES,
    }


def _resolve_actual_identities(workspace: Path, decoded: GatewayAdmissionRequest) -> dict[str, object]:
    capture_state = CaptureStateStore(workspace / "capture")
    actuals: dict[str, object] = {}
    for member in decoded.members:
        try:
            candidate = capture_state.get_candidate(member.candidate_id)
        except Exception as exc:
            raise HAGError(HAG_ADMISSION_REJECTED, "admission was rejected") from exc
        if candidate.status is not CandidateStatus.deferred or candidate.candidate_id != member.candidate_id:
            raise HAGError(HAG_ADMISSION_REJECTED, "admission was rejected")
        if candidate.shard_id != member.admission.shard_id:
            raise HAGError(HAG_ADMISSION_REJECTED, "admission was rejected")
        actuals[member.member_id] = candidate
    return actuals


def _read_actual_shards(evidence, actuals: dict[str, object]) -> dict[str, object]:
    shards: dict[str, object] = {}
    for member_id, candidate in actuals.items():
        try:
            shard = evidence.get_dream_shard(candidate.shard_id)
        except Exception as exc:
            raise HAGError(HAG_ADMISSION_REJECTED, "admission was rejected") from exc
        if shard.shard_id != candidate.shard_id:
            raise HAGError(HAG_ADMISSION_REJECTED, "admission was rejected")
        shards[member_id] = shard
    return shards


def _bindings(decoded: GatewayAdmissionRequest, projections: dict[str, dict[str, str]], shards: dict[str, object]) -> HostPlanBindings:
    bindings = []
    for member in decoded.members:
        projection = projections[member.member_id]
        shard = shards[member.member_id]
        admission_request = AdmissionRequest(
            member.admission.admission_id,
            shard,
            member.admission.growth_submission,
            placement_plan_from_payload(member.admission.placement_plan),
            member.admission.recorded_at,
        )
        bindings.append(
            HostAdmissionBinding(
                _admission_request_ref(member),
                member.promotion_decision.decision_id,
                projection["candidate_ref"],
                member.admission.admission_id,
                member.member_id,
                PromotionDecision(
                    member.promotion_decision.decision_id,
                    member.candidate_id,
                    shard.shard_id,
                    PromotionDecisionKind.promote,
                    tuple(PromotionReason(item) for item in member.promotion_decision.reasons),
                    PromotionDecider(member.promotion_decision.decided_by),
                    member.promotion_decision.recorded_at,
                    member.promotion_decision.next_action,
                ),
                admission_request,
                str(member.admission.growth_submission.get("proposal_id", "")),
                str(member.admission.placement_plan.get("plan_id", "")),
                member.candidate_id,
                projection["shard_ref"],
            )
        )
    return HostPlanBindings(admission_bindings=tuple(bindings))


def _require_owned_workspace(workspace: Path) -> None:
    marker = workspace / HX1_MARKER_NAME
    if not marker.exists() or not marker.is_file():
        raise HAGError(HAG_WORKSPACE_NOT_OWNED, "workspace is not owned")
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise HAGError(HAG_WORKSPACE_NOT_OWNED, "workspace is not owned") from exc
    if payload != {"owner": "hx1", "marker_version": "1"}:
        raise HAGError(HAG_WORKSPACE_NOT_OWNED, "workspace is not owned")


def _hag_from_hx1(exc: HX1ExecutionError) -> HAGError:
    if exc.reason_code == "HX1_REOPEN_MISMATCH":
        return HAGError(HAG_REOPEN_MISMATCH, "request reopen mismatch")
    if exc.reason_code == "HX1_WORK_ROOT_REJECTED":
        return HAGError(HAG_WORKSPACE_NOT_OWNED, "workspace is not owned")
    if exc.failed_stage == "admission" and "INTERRUPTED" in exc.reason_code:
        return HAGError(HAG_ADMISSION_INTERRUPTED, "admission was interrupted")
    if exc.reason_code in {"HX1_ADMISSION_REJECTED", "HX1_ADMISSION_STATE_MISMATCH", "HX1_INVALID_BINDINGS", "HX1_INVALID_PLAN"}:
        return HAGError(HAG_ADMISSION_REJECTED, "admission was rejected")
    return HAGError(HAG_ADMISSION_REJECTED, "admission was rejected")


def _admission_request_ref(member: GatewayMember) -> str:
    return "admreq_" + _safe_suffix(member.member_id + ":" + member.admission.admission_id)


def _derive_projections(decoded: GatewayAdmissionRequest) -> dict[str, dict[str, str]]:
    projections = {}
    candidate_refs: set[str] = set()
    shard_refs: set[str] = set()
    for member in decoded.members:
        projection = _projection_for(member.candidate_id, member.admission.shard_id)
        if projection["candidate_ref"] in candidate_refs or projection["shard_ref"] in shard_refs:
            raise HAGError(HAG_ADMISSION_REJECTED, "admission was rejected")
        candidate_refs.add(projection["candidate_ref"])
        shard_refs.add(projection["shard_ref"])
        projections[member.member_id] = projection
    return projections


def _projection_for(actual_candidate_id: str, actual_shard_id: str) -> dict[str, str]:
    candidate_payload = {
        "projection_kind": "hag1_cx2_candidate_ref",
        "projection_version": "1",
        "actual_candidate_id": actual_candidate_id,
    }
    shard_payload = {
        "projection_kind": "hag1_cx2_shard_ref",
        "projection_version": "1",
        "actual_candidate_id": actual_candidate_id,
        "actual_shard_id": actual_shard_id,
    }
    return {
        "candidate_ref": "dac_" + _safe_suffix(_canonical_projection_json(candidate_payload)),
        "shard_ref": "shard_" + _safe_suffix(_canonical_projection_json(shard_payload)),
    }


def _canonical_projection_json(payload: dict[str, str]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _safe_suffix(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:32]


__all__ = ["admit", "admit_from_text"]
