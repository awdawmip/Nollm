"""BA1 Batch Admission Coordinator.

Allowed: host-explicit DeferredAdmissionCandidate selections, host-explicit
promotion decisions, all-member zero-write preflight, and serial delegation to
DA1 MemoryAdmissionOrchestrator.
Forbidden: candidate discovery, automatic proposal or placement generation,
batch persistence, Field assembly, recall, runtime, OpenClaw, LLM/NLP, caches,
databases, or global queues.
"""

from .coordinator import BatchAdmissionCoordinator
from .errors import (
    BA1_CANDIDATE_NOT_ELIGIBLE,
    BA1_CANDIDATE_UNAVAILABLE,
    BA1_DECISION_MEMBER_MISMATCH,
    BA1_DECISION_NEXT_ACTION_INVALID,
    BA1_DECISION_NOT_PROMOTE,
    BA1_DUPLICATE_ADMISSION,
    BA1_DUPLICATE_CANDIDATE,
    BA1_DUPLICATE_DECISION,
    BA1_DUPLICATE_MEMBER,
    BA1_DUPLICATE_PLACEMENT_PLAN,
    BA1_DUPLICATE_PROPOSAL,
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
)
from .types import (
    BatchAdmissionMember,
    BatchAdmissionReceipt,
    BatchAdmissionRequest,
    BatchAdmissionWindow,
    BatchMemberReceipt,
    BatchWindowStatus,
    PromotionDecider,
    PromotionDecision,
    PromotionDecisionKind,
    PromotionReason,
    batch_request_fingerprint,
)

__all__ = [
    "BA1_CANDIDATE_NOT_ELIGIBLE",
    "BA1_CANDIDATE_UNAVAILABLE",
    "BA1_DECISION_MEMBER_MISMATCH",
    "BA1_DECISION_NEXT_ACTION_INVALID",
    "BA1_DECISION_NOT_PROMOTE",
    "BA1_DUPLICATE_ADMISSION",
    "BA1_DUPLICATE_CANDIDATE",
    "BA1_DUPLICATE_DECISION",
    "BA1_DUPLICATE_MEMBER",
    "BA1_DUPLICATE_PLACEMENT_PLAN",
    "BA1_DUPLICATE_PROPOSAL",
    "BA1_DUPLICATE_SHARD",
    "BA1_EVIDENCE_UNAVAILABLE",
    "BA1_GEOMETRY_PROFILE_MISMATCH",
    "BA1_INVALID_REQUEST",
    "BA1_MEMBER_PREFLIGHT_REJECTED",
    "BA1_REQUEST_SHARD_MISMATCH",
    "BA1_WINDOW_MEMBER_SET_MISMATCH",
    "BA1_WINDOW_NOT_READY",
    "BA1CommitInterrupted",
    "BA1Rejection",
    "BatchAdmissionCoordinator",
    "BatchAdmissionMember",
    "BatchAdmissionReceipt",
    "BatchAdmissionRequest",
    "BatchAdmissionWindow",
    "BatchMemberReceipt",
    "BatchWindowStatus",
    "PromotionDecider",
    "PromotionDecision",
    "PromotionDecisionKind",
    "PromotionReason",
    "batch_request_fingerprint",
]
