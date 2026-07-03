from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from nollm.dream_geometry.adapters import IntegrationReadContext, RecallInvocation
from nollm.dream_geometry.admission import (
    AdmissionPlacementPlan,
    AdmissionRequest,
    AxisPlacement,
    FIELD_PROFILE_ID,
    MemoryAdmissionOrchestrator,
    open_store as open_admission_store,
)
from nollm.dream_geometry.assembly import AdmissionReplaySource, FieldAssemblyResult, FiniteAdmissionSet, assemble_field_snapshot
from nollm.dream_geometry.batch_admission import (
    BatchAdmissionCoordinator,
    BatchAdmissionMember,
    BatchAdmissionReceipt,
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
    CaptureReceipt,
    DeferredCandidateRequest,
    PromotionMode,
    VisibilityScope,
)
from nollm.dream_geometry.cortex import compile_query, open_store as open_cortex_store
from nollm.dream_geometry.evidence import DreamShard, open_store as open_evidence_store
from nollm.dream_geometry.field import VerifiedChartLink
from nollm.dream_geometry.geometry import AxialCoord, LocalChart, Vec2, make_hex_cell
from nollm.dream_geometry.geometry.transform import SimilarityTransform, TransformWitness, validate_transform
from nollm.dream_geometry.protocol.contracts import GrowthBasis, OriginKind
from nollm.dream_geometry.recall import RecallDigest, RecallPolicy, resolve_recall


RECORDED_AT = "2026-07-03T10:00:00+08:00"
DX2_MISS_MESSAGE = "当前显式 AdmissionRecord / FieldSnapshot 范围内，没有满足条件的正式几何证据。"


@dataclass(frozen=True, slots=True)
class DX2Cycle:
    root: Path
    evidence: Any
    cortex: Any
    admission: Any
    orchestrator: MemoryAdmissionOrchestrator
    capture: CaptureIngress
    ba1_request: BatchAdmissionRequest
    ba1_receipt: BatchAdmissionReceipt
    receipts: dict[str, CaptureReceipt]
    shards: dict[str, DreamShard]
    candidate_ids: dict[str, str]
    admission_ids: tuple[str, str]
    d_admission_id: str
    assembly: FieldAssemblyResult
    reversed_assembly: FieldAssemblyResult
    policy: RecallPolicy
    recall_digest: RecallDigest
    c_miss_digest: RecallDigest
    invocation: RecallInvocation
    context: IntegrationReadContext
    state_after_capture: dict[str, tuple[tuple[str, str], ...]]
    state_before_assembly: dict[str, tuple[tuple[str, str], ...]]
    state_after_assembly: dict[str, tuple[tuple[str, str], ...]]


def build_dx2_cycle(root: Path) -> DX2Cycle:
    evidence = open_evidence_store(root / "evidence")
    capture = CaptureIngress(root / "capture")
    captured = {
        "a": _capture_deferred(capture, evidence, "a", "Kunming rain dx2 alpha."),
        "b": _capture_deferred(capture, evidence, "b", "Kunming rain dx2 beta."),
        "c": _capture_deferred(capture, evidence, "c", "Oslo snow dx2 captured control."),
        "d": _capture_deferred(capture, evidence, "d", "Kunming rain dx2 unrelated admitted."),
    }
    receipts = {label: receipt for label, (receipt, _shard) in captured.items()}
    shards = {label: shard for label, (_receipt, shard) in captured.items()}
    candidate_ids = {label: receipt.deferred_candidate_id or "" for label, receipt in receipts.items()}
    state_after_capture = state_manifest(root)

    cortex = open_cortex_store(root / "cortex", evidence)
    admission = open_admission_store(root / "admission", evidence, cortex)
    orchestrator = MemoryAdmissionOrchestrator(evidence, cortex, admission)
    coordinator = BatchAdmissionCoordinator(capture.state_store, evidence, orchestrator)

    a_request = admission_request("a", shards["a"])
    b_request = admission_request("b", shards["b"])
    members = (
        batch_member("a", "bam_dx2_01", candidate_ids["a"], shards["a"], a_request),
        batch_member("b", "bam_dx2_02", candidate_ids["b"], shards["b"], b_request),
    )
    ba1_request = batch_request(members)
    ba1_receipt = coordinator.submit(ba1_request)

    d_request = admission_request("d", shards["d"], admission_id="adm_dx2_unrelated_d", proposal_id="gp_dx2_unrelated_d")
    orchestrator.admit(d_request)

    reopened_admission = open_admission_store(root / "admission", evidence, cortex, orchestrator.validate_replay_record)
    reopened_orchestrator = MemoryAdmissionOrchestrator(evidence, cortex, reopened_admission)
    admission_ids = tuple(item.admission_receipt.admission_id for item in ba1_receipt.member_receipts)

    state_before_assembly = state_manifest(root)
    assembly = assemble_dx2_set(evidence, cortex, reopened_admission, reopened_orchestrator, admission_ids)
    reversed_assembly = assemble_dx2_set(evidence, cortex, reopened_admission, reopened_orchestrator, tuple(reversed(admission_ids)))
    state_after_assembly = state_manifest(root)

    policy = RecallPolicy(min_required_axis_matches=2, max_lateral_hops=2)
    recall_digest = resolve_recall(kunming_rain_probe(), assembly.universe, evidence, policy=policy)
    c_miss_digest = resolve_recall(oslo_snow_probe(), assembly.universe, evidence, policy=policy)
    context = IntegrationReadContext(evidence, assembly.universe, None, policy)
    invocation = RecallInvocation("req_dx2_kunming_rain", "recall", kunming_rain_probe())

    return DX2Cycle(
        root,
        evidence,
        cortex,
        reopened_admission,
        reopened_orchestrator,
        capture,
        ba1_request,
        ba1_receipt,
        receipts,
        shards,
        candidate_ids,
        admission_ids,
        d_request.admission_id,
        assembly,
        reversed_assembly,
        policy,
        recall_digest,
        c_miss_digest,
        invocation,
        context,
        state_after_capture,
        state_before_assembly,
        state_after_assembly,
    )


def assemble_dx2_set(evidence: Any, cortex: Any, admission: Any, orchestrator: MemoryAdmissionOrchestrator, admission_ids: tuple[str, ...]) -> FieldAssemblyResult:
    return assemble_field_snapshot(FiniteAdmissionSet("dx2_ba1_receipt_explicit_set", admission_sources(evidence, cortex, admission, orchestrator, admission_ids)))


def admission_sources(evidence: Any, cortex: Any, admission: Any, orchestrator: MemoryAdmissionOrchestrator, admission_ids: tuple[str, ...]) -> tuple[AdmissionReplaySource, ...]:
    receipts = {receipt.receipt_id: receipt for receipt in cortex.receipts()}
    sources = []
    for admission_id in admission_ids:
        record = admission.get_admission_record(admission_id)
        sources.append(AdmissionReplaySource(record, evidence, cortex, orchestrator.replay_record, receipts[record.compilation_receipt_id], None))
    return tuple(sources)


def admission_request(label: str, shard: DreamShard, *, admission_id: str | None = None, proposal_id: str | None = None) -> AdmissionRequest:
    admission_id = admission_id or f"adm_dx2_{label}"
    proposal_id = proposal_id or f"gp_dx2_{label}"
    axes = (("location", "Kunming"), ("phenomenon", "rain")) if label != "c" else (("location", "Oslo"), ("phenomenon", "snow"))
    growth_axes = []
    placements = []
    source_chart = LocalChart("dx2:fine", 0, 1.0, 0.0, Vec2(0.0, 0.0))
    target_chart = LocalChart("dx2:coarse", 0, 1.0, 0.0, Vec2(0.0, 0.0)) if label == "d" else source_chart
    source = make_hex_cell(source_chart, AxialCoord(0, 0))
    target = make_hex_cell(target_chart, AxialCoord(0, 0))
    link = VerifiedChartLink(source.chart_fingerprint, target.chart_fingerprint, verified_transform()) if label == "d" else None
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
            "do_not_infer": ["dx2 synthetic validation only"],
            "forbidden_inferences": ["no semantic fallback", "no hidden capture recall"],
            "possible_conflict_refs": [],
            "axes": growth_axes,
        },
        AdmissionPlacementPlan(f"apl_dx2_{label}", tuple(placements)),
        RECORDED_AT,
    )


def batch_request(members: tuple[BatchAdmissionMember, ...]) -> BatchAdmissionRequest:
    return BatchAdmissionRequest(
        BatchAdmissionWindow(
            "baw_dx2_synthetic",
            tuple(sorted(member.admission_request.dream_shard.shard_id for member in members)),
            ("source:dx2",),
            RECORDED_AT,
            None,
            "policy:dx2:synthetic",
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
            f"pmd_dx2_{label}",
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
    return compile_query(query_payload("probe_dx2_kunming_rain", "Kunming rain", (("location", "Kunming"), ("phenomenon", "rain"))))


def oslo_snow_probe():
    return compile_query(query_payload("probe_dx2_oslo_snow", "Oslo snow", (("location", "Oslo"), ("phenomenon", "snow"))))


def query_payload(probe_id: str, query_text: str, axes: tuple[tuple[str, str], ...]) -> dict[str, Any]:
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
        "do_not_infer": ["dx2 synthetic validation only"],
        "forbidden_inferences": ["no semantic fallback"],
        "axes": rendered_axes,
    }


def state_manifest(root: Path) -> dict[str, tuple[tuple[str, str], ...]]:
    return {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission", "capture")}


def tree_manifest(root: Path) -> tuple[tuple[str, str], ...]:
    root = Path(root)
    if not root.exists():
        return ()
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))


def verified_transform():
    return validate_transform(
        SimilarityTransform(1.0, 0.0, Vec2(0.0, 0.0)),
        (
            TransformWitness(Vec2(0.0, 0.0), Vec2(0.0, 0.0)),
            TransformWitness(Vec2(1.0, 0.0), Vec2(1.0, 0.0)),
            TransformWitness(Vec2(0.0, 1.0), Vec2(0.0, 1.0)),
        ),
        1.0,
    )


def _capture_deferred(capture: CaptureIngress, evidence: Any, label: str, content: str) -> tuple[CaptureReceipt, DreamShard]:
    request = __import__("nollm.dream_geometry.capture", fromlist=["CaptureRequest"]).CaptureRequest(
        f"cap_dx2_{label}",
        content,
        CaptureOrigin(OriginKind.user_utterance, f"turn:dx2:{label}", "source:dx2", "user"),
        RECORDED_AT,
        ("source:dx2",),
        VisibilityScope.source_window,
        DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
    )
    policy = CapturePolicy(
        f"cp_dx2_{label}",
        persistence=CapturePersistence.persistent,
        lineage=CaptureLineage.minimal,
        diagnostics=CaptureDiagnostics.on_failure,
        allowed_visibility_scopes=(VisibilityScope.source_window,),
        promotion_mode=PromotionMode.manual,
    )
    receipt = capture.capture(request, policy, evidence)
    return receipt, evidence.get_dream_shard(receipt.shard_id)
