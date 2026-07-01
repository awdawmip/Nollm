"""DA1 deterministic Memory Admission orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from nollm.dream_geometry.cortex import (
    ADMISSION_CURRENT_DC1_1,
    CompilationReceipt,
    CompiledGrowthProposal,
    CortexStore,
    canonical_json as cortex_json,
    compile_growth,
    payload_fingerprint as cortex_fingerprint,
)
from nollm.dream_geometry.evidence import MemorySubstrateStore
from nollm.dream_geometry.field import (
    CoverPolicy,
    GravityPolicy,
    TraceSeed,
    build_local_covers,
    calculate_gravity_snapshot,
    propagate_trace,
    seed_to_trace,
)
from nollm.dream_geometry.field.types import cell_ref_key, stable_id
from nollm.dream_geometry.geometry import CoverageDirection, compute_distribution, make_hex_cell
from nollm.dream_geometry.protocol.contracts import GrowthBasis, TraceState

from .errors import (
    DA1_ADMISSION_ID_PAYLOAD_CONFLICT,
    DA1_ADMISSION_RECORD_COMMIT_FAILED,
    DA1_CORTEX_COMMIT_FAILED,
    DA1_CORTEX_PREVIEW_COMMIT_MISMATCH,
    DA1_DUPLICATE_PLACEMENT,
    DA1_INVALID_FINE_TO_COARSE_PARTITION,
    DA1_LEGACY_PROPOSAL_NOT_ADMISSIBLE,
    DA1_MULTI_STEP_RAY_DEFERRED,
    DA1_PLACEMENT_AXIS_MISMATCH,
    DA1_PLACEMENT_STEP_MISMATCH,
    DA1_PREFLIGHT_PROJECTION_FAILURE,
    DA1_PROPOSAL_ALREADY_ADMITTED,
    DA1_REPLAY_PROJECTION_MISMATCH,
    DA1_SUBJECT_SHARD_MISMATCH,
    DA1_UNVERIFIED_CROSS_CHART_LINK,
    DA1Rejection,
    reject,
)
from .store import AdmissionStore
from .types import (
    FIELD_PROFILE_ID,
    AdmissionOutcome,
    AdmissionPlacementPlan,
    AdmissionProjection,
    AdmissionReceipt,
    AdmissionRecord,
    AdmissionRequest,
    AxisPlacement,
    axial_from_payload,
    chart_from_payload,
    fingerprint,
    make_record,
    placement_plan_payload,
    projection_fingerprint_payload,
    receipt_from_record,
    request_fingerprint,
)


@dataclass(frozen=True)
class PreflightResult:
    request: AdmissionRequest
    proposal: CompiledGrowthProposal
    projection: AdmissionProjection
    request_fingerprint: str


class OverlayEvidenceReader:
    """Read the pending shard from memory while delegating other reads to DE1."""

    def __init__(self, pending_shard, evidence_store: MemorySubstrateStore):
        self.pending_shard = pending_shard
        self.evidence_store = evidence_store

    def get_dream_shard(self, shard_id: str):
        if shard_id == self.pending_shard.shard_id:
            return self.pending_shard
        return self.evidence_store.get_dream_shard(shard_id)

    def get_interpretation(self, interpretation_id: str):
        return self.evidence_store.get_interpretation(interpretation_id)


class MemoryAdmissionOrchestrator:
    """DA1 zero-write preflight followed by ordered DE1 -> DC1 -> DA1 commit."""

    def __init__(self, evidence_store: MemorySubstrateStore, cortex_store: CortexStore, admission_store: AdmissionStore):
        self.evidence_store = evidence_store
        self.cortex_store = cortex_store
        self.admission_store = admission_store

    def preflight(self, request: AdmissionRequest) -> PreflightResult:
        req_fp = request_fingerprint(request)
        if self.admission_store.has_admission_record(request.admission_id):
            existing = self.admission_store.get_admission_record(request.admission_id)
            if existing.request_fingerprint != req_fp:
                reject(DA1_ADMISSION_ID_PAYLOAD_CONFLICT, "same admission_id has different request fingerprint")
        overlay = OverlayEvidenceReader(request.dream_shard, self.evidence_store)
        try:
            proposal = compile_growth(request.growth_submission, overlay)
        except DA1Rejection:
            raise
        except Exception as exc:
            raise exc
        if proposal.subject_shard_id != request.dream_shard.shard_id:
            reject(DA1_SUBJECT_SHARD_MISMATCH, "proposal subject does not match DreamShard")
        self._validate_single_step(proposal)
        self._validate_placements(proposal, request.placement_plan)
        admitted = self.admission_store.find_by_proposal_id(proposal.proposal_id)
        if admitted is not None and admitted.admission_id != request.admission_id:
            reject(DA1_PROPOSAL_ALREADY_ADMITTED, "proposal already admitted by different admission_id")
        projection = self._build_projection(proposal, request.placement_plan, None)
        if self.admission_store.has_admission_record(request.admission_id):
            existing = self.admission_store.get_admission_record(request.admission_id)
            self._validate_record_projection(existing, projection)
        return PreflightResult(request, proposal, projection, req_fp)

    def admit(self, request: AdmissionRequest) -> AdmissionReceipt:
        preflight = self.preflight(request)
        if self.admission_store.has_admission_record(request.admission_id):
            existing = self.admission_store.get_admission_record(request.admission_id)
            return receipt_from_record(existing, AdmissionOutcome.idempotent)
        try:
            self.evidence_store.put_dream_shard(request.dream_shard)
            commit_result = self.cortex_store.compile_growth(request.growth_submission)
        except DA1Rejection:
            raise
        except Exception as exc:
            raise DA1Rejection((DA1_CORTEX_COMMIT_FAILED,), f"cortex commit failed: {exc}", "cortex_commit_failed") from exc
        if cortex_json(commit_result.proposal) != cortex_json(preflight.proposal):
            reject(DA1_CORTEX_PREVIEW_COMMIT_MISMATCH, "committed proposal differs from preflight proposal")
        if commit_result.receipt.normalized_payload_fingerprint != cortex_fingerprint(preflight.proposal):
            reject(DA1_CORTEX_PREVIEW_COMMIT_MISMATCH, "committed receipt differs from preflight proposal")
        try:
            view = self.cortex_store.stored_growth_proposal(preflight.proposal.proposal_id)
        except Exception as exc:
            raise DA1Rejection((DA1_LEGACY_PROPOSAL_NOT_ADMISSIBLE,), f"proposal admission unavailable: {exc}") from exc
        if view.admission != ADMISSION_CURRENT_DC1_1:
            reject(DA1_LEGACY_PROPOSAL_NOT_ADMISSIBLE, "only current DC1.1 proposals are admissible")
        projection = self._build_projection(preflight.proposal, request.placement_plan, commit_result.receipt)
        record = make_record(request, projection, commit_result.receipt)
        try:
            write = self.admission_store.put_admission_record(record)
        except DA1Rejection:
            raise
        except Exception as exc:
            raise DA1Rejection((DA1_ADMISSION_RECORD_COMMIT_FAILED,), f"admission record commit failed: {exc}", "admission_record_commit_failed") from exc
        return receipt_from_record(record, AdmissionOutcome.idempotent if write.idempotent else AdmissionOutcome.committed)

    def replay_record(self, record: AdmissionRecord) -> AdmissionProjection:
        self.admission_store.validate_record_references(record)
        proposal = self.cortex_store.get_growth_proposal(record.proposal_id)
        plan = placement_plan_from_payload(record.placement_plan_payload)
        projection = self._build_projection(proposal, plan, None)
        self._validate_record_projection(record, projection)
        return projection

    def validate_replay_record(self, record: AdmissionRecord) -> None:
        self.replay_record(record)

    def _validate_single_step(self, proposal: CompiledGrowthProposal) -> None:
        for axis in proposal.axes:
            if len(axis.ray) != 1:
                reject(DA1_MULTI_STEP_RAY_DEFERRED, "DA1 admits exactly one GrowthStep per AxisRay")

    def _validate_placements(self, proposal: CompiledGrowthProposal, plan: AdmissionPlacementPlan) -> None:
        expected = {(axis.axis_id, axis.ray[0].step_id) for axis in proposal.axes}
        observed = {(placement.axis_id, placement.step_id) for placement in plan.axis_placements}
        if len(observed) != len(plan.axis_placements):
            reject(DA1_DUPLICATE_PLACEMENT, "duplicate axis placement")
        if {axis for axis, _ in expected} != {axis for axis, _ in observed}:
            reject(DA1_PLACEMENT_AXIS_MISMATCH, "placement axes must match accepted proposal axes")
        if expected != observed:
            reject(DA1_PLACEMENT_STEP_MISMATCH, "placement steps must match accepted proposal steps")

    def _build_projection(
        self,
        proposal: CompiledGrowthProposal,
        plan: AdmissionPlacementPlan,
        receipt: CompilationReceipt | None,
    ) -> AdmissionProjection:
        source_traces = []
        derived_traces = []
        residuals = []
        by_axis = {placement.axis_id: placement for placement in plan.axis_placements}
        try:
            for axis in sorted(proposal.axes, key=lambda item: item.axis_id):
                step = axis.ray[0]
                placement = by_axis[axis.axis_id]
                self._validate_chart_link(placement)
                distribution = compute_distribution(
                    placement.source_cell,
                    placement.fine_to_coarse_targets,
                    CoverageDirection.fine_to_coarse,
                )
                seed = TraceSeed(
                    _trace_seed_id(proposal.proposal_id, axis.axis_id, step.step_id, placement),
                    proposal.subject_shard_id,
                    proposal.proposal_id,
                    placement.source_cell,
                    axis.axis_id,
                    _basis(step.basis),
                    _basis_refs(step.basis_refs),
                    1.0,
                    _support_key(proposal.proposal_id, axis.axis_id, step.step_id),
                    0.0,
                    0.0,
                    0.0,
                    1,
                    TraceState.accepted,
                )
                trace = seed_to_trace(seed)
                result = propagate_trace(trace, distribution, placement.verified_chart_link)
                source_traces.append(trace)
                derived_traces.extend(result.derived_traces)
                residuals.append(result.residual)
        except DA1Rejection:
            raise
        except Exception as exc:
            raise DA1Rejection((DA1_PREFLIGHT_PROJECTION_FAILURE,), f"projection failed: {exc}") from exc
        source_tuple = tuple(sorted(source_traces, key=lambda item: item.trace_id))
        derived_tuple = tuple(sorted(derived_traces, key=lambda item: item.trace_id))
        residual_tuple = tuple(sorted(residuals, key=lambda item: item.residual_id))
        covers = build_local_covers(derived_tuple, CoverPolicy())
        gravity = calculate_gravity_snapshot(covers, GravityPolicy())
        projection = AdmissionProjection(proposal, receipt, source_tuple, derived_tuple, residual_tuple, covers, gravity, "")
        projection_fp = fingerprint(projection_fingerprint_payload(projection))
        return AdmissionProjection(proposal, receipt, source_tuple, derived_tuple, residual_tuple, covers, gravity, projection_fp)

    def _validate_chart_link(self, placement: AxisPlacement) -> None:
        source_fp = placement.source_cell.chart_fingerprint
        target_fps = {cell.chart_fingerprint for cell in placement.fine_to_coarse_targets}
        if len(target_fps) != 1:
            reject(DA1_INVALID_FINE_TO_COARSE_PARTITION, "target partition must share one chart fingerprint")
        target_fp = next(iter(target_fps))
        if target_fp == source_fp and placement.verified_chart_link is not None:
            reject(DA1_UNVERIFIED_CROSS_CHART_LINK, "same-chart placement must not include chart link")
        if target_fp != source_fp:
            link = placement.verified_chart_link
            if link is None or link.source_chart_fingerprint != source_fp or link.target_chart_fingerprint != target_fp:
                reject(DA1_UNVERIFIED_CROSS_CHART_LINK, "cross-chart placement requires correct verified link")

    def _validate_record_projection(self, record: AdmissionRecord, projection: AdmissionProjection) -> None:
        if record.projection_fingerprint != projection.projection_fingerprint:
            reject(DA1_REPLAY_PROJECTION_MISMATCH, "projection fingerprint mismatch")
        if record.source_trace_ids != tuple(trace.trace_id for trace in projection.source_traces):
            reject(DA1_REPLAY_PROJECTION_MISMATCH, "source trace id mismatch")
        if record.derived_trace_ids != tuple(trace.trace_id for trace in projection.derived_traces):
            reject(DA1_REPLAY_PROJECTION_MISMATCH, "derived trace id mismatch")
        if record.residual_ids != tuple(residual.residual_id for residual in projection.residuals):
            reject(DA1_REPLAY_PROJECTION_MISMATCH, "residual id mismatch")
        if record.cover_ids != tuple(cover.cover_id for cover in projection.covers):
            reject(DA1_REPLAY_PROJECTION_MISMATCH, "cover id mismatch")


def placement_plan_from_payload(payload: dict[str, Any]) -> AdmissionPlacementPlan:
    placements = []
    for item in payload["axis_placements"]:
        placements.append(
            AxisPlacement(
                item["axis_id"],
                item["step_id"],
                _cell_from_replay_payload(item["source_cell"]),
                tuple(_cell_from_replay_payload(cell) for cell in item["fine_to_coarse_targets"]),
                None,
            )
        )
    return AdmissionPlacementPlan(payload["plan_id"], tuple(placements))


def _cell_from_replay_payload(payload: dict[str, Any]):
    return make_hex_cell(chart_from_payload(payload["chart"]), axial_from_payload(payload))


def _basis(value: object) -> GrowthBasis:
    if isinstance(value, GrowthBasis):
        return value
    return GrowthBasis(str(value))


def _basis_refs(refs: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(sorted(stable_id("basis_ref:da1", str(ref)) for ref in refs))


def _support_key(proposal_id: str, axis_id: str, step_id: str) -> str:
    return "support:" + sha256(f"{proposal_id}|{axis_id}|{step_id}|{FIELD_PROFILE_ID}".encode("utf-8")).hexdigest()[:32]


def _trace_seed_id(proposal_id: str, axis_id: str, step_id: str, placement: AxisPlacement) -> str:
    return "trace:" + sha256(
        (
            proposal_id
            + "|"
            + axis_id
            + "|"
            + step_id
            + "|"
            + cell_ref_key(placement.source_cell)
            + "|"
            + ",".join(cell_ref_key(cell) for cell in placement.fine_to_coarse_targets)
            + "|"
            + FIELD_PROFILE_ID
        ).encode("utf-8")
    ).hexdigest()[:32]


__all__ = ["MemoryAdmissionOrchestrator", "OverlayEvidenceReader", "PreflightResult", "placement_plan_from_payload"]
