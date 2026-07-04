"""Fixed DG7 explicit host scenario."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nollm.dream_geometry.adapters import RecallInvocation
from nollm.dream_geometry.admission import AdmissionPlacementPlan, AdmissionRequest, AxisPlacement, FIELD_PROFILE_ID
from nollm.dream_geometry.batch_admission import (
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
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    CaptureRequest,
    DeferredCandidateRequest,
    PromotionMode,
    VisibilityScope,
)
from nollm.dream_geometry.cortex import compile_query
from nollm.dream_geometry.evidence import DreamShard
from nollm.dream_geometry.field import VerifiedChartLink
from nollm.dream_geometry.geometry import AxialCoord, LocalChart, Vec2, make_hex_cell
from nollm.dream_geometry.geometry.transform import SimilarityTransform, TransformWitness, validate_transform
from nollm.dream_geometry.protocol.contracts import GrowthBasis, OriginKind
from nollm.dream_geometry.recall import RecallPolicy

FIXED_SCENARIO_ID = "fixed-dg7-v1"
SCENARIO_VERSION = "2026-07-04.dg7.v1"
RECORDED_AT = "2026-07-04T09:00:00+08:00"


@dataclass(frozen=True, slots=True)
class DG7ReferenceScenario:
    scenario_id: str
    scenario_version: str
    fixed_reference_time: str
    capture_requests: tuple[tuple[str, CaptureRequest, CapturePolicy], ...]
    explicit_assembly_admission_ids: tuple[str, ...]
    recall_invocation: RecallInvocation
    c_miss_invocation: RecallInvocation
    recall_policy: RecallPolicy


def build_reference_scenario(scenario_id: str = FIXED_SCENARIO_ID) -> DG7ReferenceScenario:
    if scenario_id != FIXED_SCENARIO_ID:
        raise ValueError("unknown DG7 scenario")
    return DG7ReferenceScenario(
        scenario_id=FIXED_SCENARIO_ID,
        scenario_version=SCENARIO_VERSION,
        fixed_reference_time=RECORDED_AT,
        capture_requests=tuple(_capture_request(label, content) for label, content in _CONTENTS),
        explicit_assembly_admission_ids=("adm_dg7_a", "adm_dg7_b"),
        recall_invocation=RecallInvocation("req_dg7_kunming_rain", "recall", kunming_rain_probe()),
        c_miss_invocation=RecallInvocation("req_dg7_oslo_snow", "recall", oslo_snow_probe()),
        recall_policy=RecallPolicy(min_required_axis_matches=2, max_lateral_hops=2),
    )


def admission_request(label: str, shard: DreamShard) -> AdmissionRequest:
    admission_id = f"adm_dg7_{label}"
    proposal_id = f"gp_dg7_{label}"
    axes = (("location", "Kunming"), ("phenomenon", "rain")) if label != "c" else (("location", "Oslo"), ("phenomenon", "snow"))
    growth_axes: list[dict[str, Any]] = []
    placements = []
    source_chart = LocalChart("dg7:fine", 0, 1.0, 0.0, Vec2(0.0, 0.0))
    target_chart = LocalChart("dg7:coarse", 0, 1.0, 0.0, Vec2(0.0, 0.0)) if label == "d" else source_chart
    source = make_hex_cell(source_chart, AxialCoord(0, 0))
    target = make_hex_cell(target_chart, AxialCoord(0, 0))
    link = VerifiedChartLink(source.chart_fingerprint, target.chart_fingerprint, _verified_transform()) if label == "d" else None
    for axis_id, expression in axes:
        start = shard.content.index(expression)
        step_id = f"step_{proposal_id}_{axis_id}"
        growth_axes.append(
            {
                "axis_id": axis_id,
                "ray": [
                    {
                        "step_id": step_id,
                        "expression": expression,
                        "basis": GrowthBasis.explicit_in_shard.value,
                        "basis_refs": [
                            {
                                "ref_type": "text_span",
                                "record_id": shard.shard_id,
                                "start_char": start,
                                "end_char": start + len(expression),
                                "quoted_text": expression,
                            }
                        ],
                        "rationale": None,
                    }
                ],
            }
        )
        placements.append(AxisPlacement(axis_id, step_id, source, (target,), link))
    return AdmissionRequest(
        admission_id,
        shard,
        {
            "contract_version": "dc1.v1",
            "proposal_id": proposal_id,
            "subject_shard_id": shard.shard_id,
            "submitted_at": RECORDED_AT,
            "budget": {"max_axes": 4, "max_total_steps": 8, "max_ray_steps": 4},
            "do_not_infer": ["dg7 explicit positive verification only"],
            "forbidden_inferences": ["no semantic fallback", "no hidden capture recall"],
            "possible_conflict_refs": [],
            "axes": growth_axes,
        },
        AdmissionPlacementPlan(f"apl_dg7_{label}", tuple(placements)),
        RECORDED_AT,
    )


def batch_request(members: tuple[BatchAdmissionMember, ...]) -> BatchAdmissionRequest:
    return BatchAdmissionRequest(
        BatchAdmissionWindow(
            "baw_dg7_reference",
            tuple(sorted(member.admission_request.dream_shard.shard_id for member in members)),
            ("source:dg7",),
            RECORDED_AT,
            None,
            "policy:dg7:reference",
            FIELD_PROFILE_ID,
            BatchWindowStatus.ready_for_selection,
        ),
        members,
        RECORDED_AT,
    )


def batch_member(label: str, member_id: str, candidate_id: str, shard: DreamShard, request: AdmissionRequest) -> BatchAdmissionMember:
    return BatchAdmissionMember(
        member_id,
        candidate_id,
        PromotionDecision(
            f"pmd_dg7_{label}",
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


def kunming_rain_probe():
    return compile_query(_query_payload("probe_dg7_kunming_rain", "Kunming rain", (("location", "Kunming"), ("phenomenon", "rain"))))


def oslo_snow_probe():
    return compile_query(_query_payload("probe_dg7_oslo_snow", "Oslo snow", (("location", "Oslo"), ("phenomenon", "snow"))))


def _capture_request(label: str, content: str) -> tuple[str, CaptureRequest, CapturePolicy]:
    request = CaptureRequest(
        f"cap_dg7_{label}",
        content,
        CaptureOrigin(OriginKind.user_utterance, f"turn:dg7:{label}", "source:dg7", "user"),
        RECORDED_AT,
        ("source:dg7",),
        VisibilityScope.source_window,
        DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
    )
    policy = CapturePolicy(
        f"cp_dg7_{label}",
        persistence=CapturePersistence.persistent,
        lineage=CaptureLineage.minimal,
        diagnostics=CaptureDiagnostics.on_failure,
        allowed_visibility_scopes=(VisibilityScope.source_window,),
        promotion_mode=PromotionMode.manual,
    )
    return label, request, policy


def _query_payload(probe_id: str, query_text: str, axes: tuple[tuple[str, str], ...]) -> dict[str, Any]:
    rendered_axes = []
    for axis_id, expression in axes:
        start = query_text.index(expression)
        rendered_axes.append(
            {
                "axis_id": axis_id,
                "ray": [
                    {
                        "step_id": f"step_{probe_id}_{axis_id}",
                        "expression": expression,
                        "basis": "explicit_in_query",
                        "basis_refs": [{"ref_type": "text_span", "record_id": probe_id, "start_char": start, "end_char": start + len(expression), "quoted_text": expression}],
                        "rationale": None,
                    }
                ],
            }
        )
    return {
        "contract_version": "dc1.v1",
        "probe_id": probe_id,
        "query_text": query_text,
        "reference_instant": RECORDED_AT,
        "requires_runtime_resolution": False,
        "ephemeral": True,
        "budget": {"max_axes": 4, "max_charts": 8, "max_layers": 4, "max_cells_per_layer": 32},
        "do_not_infer": ["dg7 explicit positive verification only"],
        "forbidden_inferences": ["no semantic fallback"],
        "axes": rendered_axes,
    }


def _verified_transform():
    return validate_transform(
        SimilarityTransform(1.0, 0.0, Vec2(0.0, 0.0)),
        (
            TransformWitness(Vec2(0.0, 0.0), Vec2(0.0, 0.0)),
            TransformWitness(Vec2(1.0, 0.0), Vec2(1.0, 0.0)),
            TransformWitness(Vec2(0.0, 1.0), Vec2(0.0, 1.0)),
        ),
        1.0,
    )


_CONTENTS = (
    ("a", "Kunming rain dg7 alpha."),
    ("b", "Kunming rain dg7 beta."),
    ("c", "Oslo snow dg7 captured control."),
    ("d", "Kunming rain dg7 admitted but excluded."),
)


__all__ = [
    "DG7ReferenceScenario",
    "FIXED_SCENARIO_ID",
    "RECORDED_AT",
    "SCENARIO_VERSION",
    "admission_request",
    "batch_member",
    "batch_request",
    "build_reference_scenario",
    "kunming_rain_probe",
    "oslo_snow_probe",
]
