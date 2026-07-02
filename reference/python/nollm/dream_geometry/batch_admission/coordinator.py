"""BA1 host-explicit Batch Admission coordination."""

from __future__ import annotations

from dataclasses import dataclass, replace

from nollm.dream_geometry.admission import (
    FIELD_PROFILE_ID,
    AdmissionRequest,
    DA1Rejection,
    MemoryAdmissionOrchestrator,
    PreflightResult,
)
from nollm.dream_geometry.capture import CaptureStateStore
from nollm.dream_geometry.evidence import DreamShard, MemorySubstrateStore

from .errors import (
    BA1_CANDIDATE_NOT_ELIGIBLE,
    BA1_CANDIDATE_UNAVAILABLE,
    BA1_DECISION_MEMBER_MISMATCH,
    BA1_DECISION_NEXT_ACTION_INVALID,
    BA1_DECISION_NOT_PROMOTE,
    BA1_DUPLICATE_ADMISSION,
    BA1_DUPLICATE_CANDIDATE,
    BA1_DUPLICATE_MEMBER,
    BA1_DUPLICATE_SHARD,
    BA1_EVIDENCE_UNAVAILABLE,
    BA1_GEOMETRY_PROFILE_MISMATCH,
    BA1_INVALID_REQUEST,
    BA1_MEMBER_PREFLIGHT_REJECTED,
    BA1_REQUEST_SHARD_MISMATCH,
    BA1_WINDOW_MEMBER_SET_MISMATCH,
    BA1_WINDOW_NOT_READY,
    BA1CommitInterrupted,
    BA1Rejection,
    reject,
)
from .types import (
    BatchAdmissionMember,
    BatchAdmissionReceipt,
    BatchAdmissionRequest,
    BatchMemberReceipt,
    BatchWindowStatus,
    PromotionDecisionKind,
    batch_request_fingerprint,
)


@dataclass(frozen=True, slots=True)
class PreparedBatchMember:
    member: BatchAdmissionMember
    candidate: object
    shard: DreamShard
    request: AdmissionRequest
    preflight: PreflightResult


class BatchAdmissionCoordinator:
    def __init__(
        self,
        capture_state_store: CaptureStateStore,
        evidence_store: MemorySubstrateStore,
        admission_orchestrator: MemoryAdmissionOrchestrator,
    ) -> None:
        self.capture_state_store = capture_state_store
        self.evidence_store = evidence_store
        self.admission_orchestrator = admission_orchestrator

    def preflight(self, request: BatchAdmissionRequest) -> tuple[PreparedBatchMember, ...]:
        _validate_batch_shape(request)
        prepared = []
        actual_shards = []
        for member in _canonical_members(request):
            try:
                candidate = self.capture_state_store.get_candidate(member.candidate_id)
            except Exception as exc:
                raise BA1Rejection((BA1_CANDIDATE_UNAVAILABLE,), f"candidate unavailable: {member.candidate_id}", "preflight") from exc
            if getattr(candidate, "status", None).value not in {"deferred", "candidate"}:
                reject(BA1_CANDIDATE_NOT_ELIGIBLE, f"candidate not eligible: {member.candidate_id}")
            try:
                shard = self.evidence_store.get_dream_shard(candidate.shard_id)
            except Exception as exc:
                raise BA1Rejection((BA1_EVIDENCE_UNAVAILABLE,), f"DreamShard unavailable: {candidate.shard_id}", "preflight") from exc
            _validate_member_relationship(member, candidate, shard)
            sanitized = replace(member.admission_request, dream_shard=shard)
            if sanitized != member.admission_request:
                reject(BA1_REQUEST_SHARD_MISMATCH, f"admission request shard does not equal DE1 shard: {member.member_id}")
            try:
                member_preflight = self.admission_orchestrator.preflight(sanitized)
            except DA1Rejection as exc:
                raise BA1Rejection((BA1_MEMBER_PREFLIGHT_REJECTED, *exc.reason_codes), f"DA1 preflight rejected member {member.member_id}: {exc.detail}") from exc
            prepared.append(PreparedBatchMember(member, candidate, shard, sanitized, member_preflight))
            actual_shards.append(shard.shard_id)
        if tuple(sorted(actual_shards)) != request.window.member_shard_ids:
            reject(BA1_WINDOW_MEMBER_SET_MISMATCH, "window member_shard_ids do not match member candidates")
        return tuple(prepared)

    def submit(self, request: BatchAdmissionRequest) -> BatchAdmissionReceipt:
        prepared = self.preflight(request)
        completed: list[BatchMemberReceipt] = []
        for item in prepared:
            try:
                admission_receipt = self.admission_orchestrator.admit(item.request)
            except Exception as exc:
                raise BA1CommitInterrupted(request.window.window_id, tuple(completed), item.member.member_id, exc) from exc
            completed.append(BatchMemberReceipt(item.member.member_id, item.member.candidate_id, item.shard.shard_id, admission_receipt))
        return BatchAdmissionReceipt(
            request.window.window_id,
            batch_request_fingerprint(request),
            request.submitted_at,
            BatchWindowStatus.closed,
            tuple(completed),
        )


def _validate_batch_shape(request: BatchAdmissionRequest) -> None:
    if request.window.status is not BatchWindowStatus.ready_for_selection or request.window.closed_at is not None:
        reject(BA1_WINDOW_NOT_READY, "window must be ready_for_selection and open")
    if request.window.shared_geometry_profile_ref != FIELD_PROFILE_ID:
        reject(BA1_GEOMETRY_PROFILE_MISMATCH, "window geometry profile must match DA1 field profile")
    members = request.members
    _reject_duplicates(tuple(member.member_id for member in members), BA1_DUPLICATE_MEMBER, "member_id")
    _reject_duplicates(tuple(member.candidate_id for member in members), BA1_DUPLICATE_CANDIDATE, "candidate_id")
    _reject_duplicates(tuple(member.admission_request.admission_id for member in members), BA1_DUPLICATE_ADMISSION, "admission_id")
    _reject_duplicates(tuple(member.admission_request.dream_shard.shard_id for member in members), BA1_DUPLICATE_SHARD, "shard_id")
    for member in members:
        decision = member.promotion_decision
        if decision.decision is not PromotionDecisionKind.promote:
            reject(BA1_DECISION_NOT_PROMOTE, f"member decision is not promote: {member.member_id}")
        if decision.next_action != "request_growth_submission":
            reject(BA1_DECISION_NEXT_ACTION_INVALID, f"member next_action is not BA1 eligible: {member.member_id}")
        if decision.candidate_id != member.candidate_id:
            reject(BA1_DECISION_MEMBER_MISMATCH, f"decision candidate mismatch: {member.member_id}")


def _validate_member_relationship(member: BatchAdmissionMember, candidate: object, shard: DreamShard) -> None:
    decision = member.promotion_decision
    if candidate.candidate_id != member.candidate_id or decision.candidate_id != candidate.candidate_id:
        reject(BA1_DECISION_MEMBER_MISMATCH, f"candidate mismatch: {member.member_id}")
    if candidate.shard_id != shard.shard_id or decision.shard_id != shard.shard_id:
        reject(BA1_DECISION_MEMBER_MISMATCH, f"shard mismatch: {member.member_id}")
    if member.admission_request.dream_shard != shard:
        reject(BA1_REQUEST_SHARD_MISMATCH, f"admission request DreamShard mismatch: {member.member_id}")


def _canonical_members(request: BatchAdmissionRequest) -> tuple[BatchAdmissionMember, ...]:
    return tuple(sorted(request.members, key=lambda item: item.member_id))


def _reject_duplicates(values: tuple[str, ...], code: str, label: str) -> None:
    if len(set(values)) != len(values):
        reject(code, f"duplicate {label}")


__all__ = ["BatchAdmissionCoordinator", "PreparedBatchMember"]
