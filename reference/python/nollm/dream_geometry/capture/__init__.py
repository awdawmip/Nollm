"""CI1 Capture Ingress / Deferred Admission Foundation.

Allowed: host-explicit capture requests, DE1 public DreamShard writes, minimal
physical visibility windows, and deferred admission candidate records.
Forbidden: GrowthProposal, PlacementPlan, geometry, field, recall, adapters,
runtime, OpenClaw, LLM/NLP, embeddings, search, caches, or automatic admission.
"""

from .errors import CaptureError
from .ingress import CaptureIngress
from .policy import policy_fingerprint, request_fingerprint
from .state_store import CaptureStateStore
from .types import (
    CandidateStatus,
    CandidateTrigger,
    CaptureDiagnostics,
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    CaptureReceipt,
    CaptureRequest,
    CaptureStatus,
    DeferredAdmissionCandidate,
    DeferredCandidateRequest,
    PromotionMode,
    RetentionClass,
    VisibilityScope,
)
from .visibility import CaptureVisibility

__all__ = [
    "CandidateStatus",
    "CandidateTrigger",
    "CaptureDiagnostics",
    "CaptureError",
    "CaptureIngress",
    "CaptureLineage",
    "CaptureOrigin",
    "CapturePersistence",
    "CapturePolicy",
    "CaptureReceipt",
    "CaptureRequest",
    "CaptureStateStore",
    "CaptureStatus",
    "CaptureVisibility",
    "DeferredAdmissionCandidate",
    "DeferredCandidateRequest",
    "PromotionMode",
    "RetentionClass",
    "VisibilityScope",
    "policy_fingerprint",
    "request_fingerprint",
]
