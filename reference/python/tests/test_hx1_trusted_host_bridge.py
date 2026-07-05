from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json

from nollm.dream_geometry.admission import MemoryAdmissionOrchestrator, open_store as open_admission_store
from nollm.dream_geometry.adapters import RecallInvocation
from nollm.dream_geometry.admission import AdmissionPlacementPlan, AdmissionRequest, AxisPlacement
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
from nollm.dream_geometry.capture.policy import policy_fingerprint
from nollm.dream_geometry.cortex import compile_query
from nollm.dream_geometry.cortex import open_store as open_cortex_store
from nollm.dream_geometry.evidence import DreamShard, OriginDescriptor, TemporalContext
from nollm.dream_geometry.evidence import open_store as open_evidence_store
from nollm.dream_geometry.geometry import AxialCoord, LocalChart, Vec2, make_hex_cell
from nollm.dream_geometry.host_execution import (
    HostAdmissionBinding,
    HostCaptureBinding,
    HostDG6VerificationBinding,
    HostExecutionContext,
    HostPlanBindings,
    HostRecallBinding,
    execute_host_plan,
    receipt_to_mapping,
)
from nollm.dream_geometry.batch_admission import PromotionDecider, PromotionDecision as BA1Decision
from nollm.dream_geometry.batch_admission import PromotionDecisionKind, PromotionReason
from nollm.dream_geometry.protocol.contracts import GrowthBasis, OriginKind, UsageState
from nollm.dream_geometry.validation.cx2.types import (
    AdmissionRequestRef,
    CaptureRef,
    CortexActionPlan,
    DerivedViewRef,
    ExplicitAssembly,
    PromotionDecision,
    RecallRequest,
)


RECORDED_AT = "2026-07-05T09:00:00+08:00"
NON_INFERENCES = (
    "no_automatic_admission",
    "no_global_discovery",
    "no_anchor_creation",
    "no_truth_confirmation",
    "no_dg6_recall_influence",
)


def test_hx1_01_mixed_explicit_real_chain_isolates_c_and_d(tmp_path) -> None:
    setup_preexisting_d(tmp_path / "work")
    fixture = hx1_fixture(tmp_path / "work")
    receipt = execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    mapping = receipt_to_mapping(receipt)
    rendered = json.dumps(mapping, sort_keys=True)

    assert mapping["status"] == "completed"
    assert mapping["completed_stages"] == ["capture", "admission", "assembly", "recall"]
    assert mapping["admission_receipt_ids"] == ["adm_hx1_a", "adm_hx1_b"]
    assert mapping["explicit_assembly_admission_ids"] == ["adm_hx1_a", "adm_hx1_b"]
    assert mapping["snapshot_source_admission_ids"] == ["adm_hx1_a", "adm_hx1_b"]
    assert mapping["execution_input_fingerprint"].startswith("sha256:")
    assert mapping["dg6_projection_id"]
    assert mapping["recall_public_envelope"]["status"] == "resolved"
    assert "hx1 captured control" not in rendered
    assert "hx1 admitted but excluded" not in rendered
    assert _admission_record_exists(tmp_path / "work", "adm_hx1_d")
    assert not _admission_record_exists(tmp_path / "work", "adm_hx1_c")
    _assert_no_forbidden_dirs(tmp_path / "work")


def hx1_fixture(work_root):
    labels = ("a", "b", "c")
    capture_bindings = tuple(HostCaptureBinding(f"cap_hx1_{label}", *_capture(label)) for label in labels)
    admission_bindings = tuple(_admission_binding(label) for label in ("a", "b"))
    plan = CortexActionPlan(
        "nollm_cortex_action_plan",
        "1",
        "cx2_hx1_mixed",
        "mixed_explicit",
        capture_refs=tuple(CaptureRef(f"cap_hx1_{label}", f"shard_hx1_{label}", "captured", "candidate", "tentative", "source_window") for label in labels),
        promotion_decisions=tuple(
            PromotionDecision(
                f"pmd_hx1_{label}",
                f"dac_hx1_{label}",
                f"shard_hx1_{label}",
                "promote",
                ("explicit_pin", "manual_batch_selection"),
                "human_operator",
            )
            for label in ("a", "b")
        ),
        admission_request_refs=tuple(
            AdmissionRequestRef(
                f"admreq_hx1_{label}",
                f"pmd_hx1_{label}",
                f"shard_hx1_{label}",
                f"gp_hx1_{label}",
                f"apl_hx1_{label}",
            )
            for label in ("a", "b")
        ),
        explicit_assembly=ExplicitAssembly(("adm_hx1_a", "adm_hx1_b"), "host", "explicit finite host workset"),
        recall_request=RecallRequest("query:hx1:kunming-rain", "verification", "workset:hx1:a-b", 4, 2),
        derived_views=(DerivedViewRef("dg6_compacted_view", "view:hx1:dg6", "verification_only"),),
        non_inferences=NON_INFERENCES,
    )
    bindings = HostPlanBindings(
        capture_bindings,
        admission_bindings,
        HostRecallBinding("query:hx1:kunming-rain", "workset:hx1:a-b", RecallInvocation("req_hx1_kunming_rain", "recall", _query_probe())),
        HostDG6VerificationBinding("view:hx1:dg6"),
    )
    return {"plan": plan, "bindings": bindings, "context": HostExecutionContext(work_root, RECORDED_AT)}


def setup_preexisting_d(work_root):
    plan, bindings, context = capture_only_fixture(work_root, "d", plan_id="cx2_hx1_capture_d")
    execute_host_plan(plan, bindings, context)
    admission_plan = admission_only_plan("d", plan_id="cx2_hx1_admission_d")
    execute_host_plan(admission_plan, HostPlanBindings(admission_bindings=(_admission_binding("d"),)), context)


def capture_only_fixture(work_root, label: str = "e", *, plan_id: str = "cx2_hx1_capture_only"):
    request, policy = _capture(label)
    plan = CortexActionPlan(
        "nollm_cortex_action_plan",
        "1",
        plan_id,
        "capture_only",
        capture_refs=(CaptureRef(f"cap_hx1_{label}", f"shard_hx1_{label}", "captured", "candidate", "tentative", "source_window"),),
        non_inferences=NON_INFERENCES,
    )
    return plan, HostPlanBindings((HostCaptureBinding(f"cap_hx1_{label}", request, policy),)), HostExecutionContext(work_root, RECORDED_AT)


def admission_only_plan(label: str, *, plan_id: str | None = None) -> CortexActionPlan:
    return CortexActionPlan(
        "nollm_cortex_action_plan",
        "1",
        plan_id or f"cx2_hx1_admission_{label}",
        "admission",
        promotion_decisions=(
            PromotionDecision(
                f"pmd_hx1_{label}",
                f"dac_hx1_{label}",
                f"shard_hx1_{label}",
                "promote",
                ("explicit_pin", "manual_batch_selection"),
                "human_operator",
            ),
        ),
        admission_request_refs=(
            AdmissionRequestRef(
                f"admreq_hx1_{label}",
                f"pmd_hx1_{label}",
                f"shard_hx1_{label}",
                f"gp_hx1_{label}",
                f"apl_hx1_{label}",
            ),
        ),
        non_inferences=NON_INFERENCES,
    )


def _capture(label: str):
    request = CaptureRequest(
        f"cap_hx1_{label}",
        _content(label),
        CaptureOrigin(OriginKind.user_utterance, f"turn:hx1:{label}", "source:hx1", "user"),
        RECORDED_AT,
        ("source:hx1",),
        VisibilityScope.source_window,
        DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
    )
    policy = CapturePolicy(
        f"cp_hx1_{label}",
        persistence=CapturePersistence.persistent,
        lineage=CaptureLineage.minimal,
        diagnostics=CaptureDiagnostics.on_failure,
        allowed_visibility_scopes=(VisibilityScope.source_window,),
        promotion_mode=PromotionMode.manual,
    )
    return request, policy


def _admission_binding(label: str) -> HostAdmissionBinding:
    request, policy = _capture(label)
    shard = _expected_shard(request)
    actual_candidate_id = _candidate_id(request, policy)
    decision = BA1Decision(
        f"pmd_hx1_{label}",
        actual_candidate_id,
        shard.shard_id,
        PromotionDecisionKind.promote,
        (PromotionReason.explicit_pin, PromotionReason.manual_batch_selection),
        PromotionDecider.human_operator,
        RECORDED_AT,
        "request_growth_submission",
    )
    admission = _admission_request(label, shard)
    return HostAdmissionBinding(
        f"admreq_hx1_{label}",
        f"pmd_hx1_{label}",
        f"dac_hx1_{label}",
        admission.admission_id,
        f"bam_hx1_{label}",
        decision,
        admission,
        f"gp_hx1_{label}",
        f"apl_hx1_{label}",
        actual_candidate_id,
        f"shard_hx1_{label}",
    )


def _admission_request(label: str, shard: DreamShard) -> AdmissionRequest:
    axes = (("location", "Kunming"), ("phenomenon", "rain")) if label != "c" else (("location", "Oslo"), ("phenomenon", "snow"))
    chart = LocalChart("hx1:fine", 0, 1.0, 0.0, Vec2(0.0, 0.0))
    source = make_hex_cell(chart, AxialCoord(0, 0))
    growth_axes = []
    placements = []
    for axis_id, expression in axes:
        start = shard.content.index(expression)
        step_id = f"step_gp_hx1_{label}_{axis_id}"
        growth_axes.append(
            {
                "axis_id": axis_id,
                "ray": [
                    {
                        "step_id": step_id,
                        "expression": expression,
                        "basis": GrowthBasis.explicit_in_shard.value,
                        "basis_refs": [{"ref_type": "text_span", "record_id": shard.shard_id, "start_char": start, "end_char": start + len(expression), "quoted_text": expression}],
                        "rationale": None,
                    }
                ],
            }
        )
        placements.append(AxisPlacement(axis_id, step_id, source, (source,), None))
    return AdmissionRequest(
        f"adm_hx1_{label}",
        shard,
        {
            "contract_version": "dc1.v1",
            "proposal_id": f"gp_hx1_{label}",
            "subject_shard_id": shard.shard_id,
            "submitted_at": RECORDED_AT,
            "budget": {"max_axes": 4, "max_total_steps": 8, "max_ray_steps": 4},
            "do_not_infer": ["hx1 explicit bridge validation only"],
            "forbidden_inferences": ["no semantic fallback"],
            "possible_conflict_refs": [],
            "axes": growth_axes,
        },
        AdmissionPlacementPlan(f"apl_hx1_{label}", tuple(placements)),
        RECORDED_AT,
    )


def _query_probe():
    query_text = "Kunming rain"
    axes = []
    for axis_id, expression in (("location", "Kunming"), ("phenomenon", "rain")):
        start = query_text.index(expression)
        axes.append(
            {
                "axis_id": axis_id,
                "ray": [
                    {
                        "step_id": f"step_probe_hx1_{axis_id}",
                        "expression": expression,
                        "basis": "explicit_in_query",
                        "basis_refs": [{"ref_type": "text_span", "record_id": "probe_hx1_kunming_rain", "start_char": start, "end_char": start + len(expression), "quoted_text": expression}],
                        "rationale": None,
                    }
                ],
            }
        )
    return compile_query(
        {
            "contract_version": "dc1.v1",
            "probe_id": "probe_hx1_kunming_rain",
            "query_text": query_text,
            "reference_instant": RECORDED_AT,
            "requires_runtime_resolution": False,
            "ephemeral": True,
            "budget": {"max_axes": 4, "max_charts": 8, "max_layers": 4, "max_cells_per_layer": 32},
            "do_not_infer": ["hx1 explicit bridge validation only"],
            "forbidden_inferences": ["no semantic fallback"],
            "axes": axes,
        }
    )


def _expected_shard(request: CaptureRequest) -> DreamShard:
    shard_id = "shard:ci1:" + sha256(request.capture_id.encode("utf-8")).hexdigest()[:32]
    return DreamShard(
        shard_id,
        request.content,
        OriginDescriptor(request.origin.kind, request.origin.reference, request.origin.context_reference, request.origin.role_label),
        TemporalContext(request.recorded_at, None, request.recorded_at, None),
        request.context_refs,
        UsageState.tentative,
    )


def _candidate_id(request: CaptureRequest, policy: CapturePolicy) -> str:
    return "dac:" + sha256((request.capture_id + "|" + policy_fingerprint(policy)).encode("utf-8")).hexdigest()[:32]


def _content(label: str) -> str:
    return {
        "a": "Kunming rain hx1 alpha.",
        "b": "Kunming rain hx1 beta.",
        "c": "Oslo snow hx1 captured control.",
        "d": "Kunming rain hx1 admitted but excluded.",
        "e": "Kunming rain hx1 capture only.",
    }[label]


def _assert_no_forbidden_dirs(work_root) -> None:
    for name in ("field", "assembly", "recall", "cache", "database", "global-field"):
        assert not (work_root / name).exists()


def _admission_record_exists(work_root, admission_id: str) -> bool:
    evidence = open_evidence_store(work_root / "evidence")
    cortex = open_cortex_store(work_root / "cortex", evidence)
    replay_only = MemoryAdmissionOrchestrator(evidence, cortex, _ReplayValidatedReferences())
    admission = open_admission_store(work_root / "admission", evidence, cortex, replay_only.validate_replay_record)
    try:
        admission.get_admission_record(admission_id)
    except FileNotFoundError:
        return False
    return True


class _ReplayValidatedReferences:
    def validate_record_references(self, record) -> None:
        return None


__all__ = ["admission_only_plan", "capture_only_fixture", "hx1_fixture", "replace", "setup_preexisting_d"]
