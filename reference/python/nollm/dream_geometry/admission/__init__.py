"""DA1 Memory Admission / Write Orchestrator Foundation.

Allowed: deterministic zero-write preflight, ordered DE1/DC1/AdmissionRecord
commit, and admission-local replay projection.
Forbidden: LLM/NLP, Query, Recall, DI1, runtime, OpenClaw, databases, caches,
automatic placement, or Field snapshot persistence.
"""

from .errors import DA1Rejection
from .orchestrator import MemoryAdmissionOrchestrator, OverlayEvidenceReader, PreflightResult, placement_plan_from_payload
from .store import AdmissionStore, AdmissionWriteResult, open_store
from .types import (
    CONTRACT_VERSION,
    FIELD_PROFILE_ID,
    AdmissionOutcome,
    AdmissionPlacementPlan,
    AdmissionProjection,
    AdmissionReceipt,
    AdmissionRecord,
    AdmissionRequest,
    AxisPlacement,
    canonical_json,
    fingerprint,
    placement_plan_payload,
    request_fingerprint,
)

__all__ = [
    "CONTRACT_VERSION",
    "FIELD_PROFILE_ID",
    "AdmissionOutcome",
    "AdmissionPlacementPlan",
    "AdmissionProjection",
    "AdmissionReceipt",
    "AdmissionRecord",
    "AdmissionRequest",
    "AdmissionStore",
    "AdmissionWriteResult",
    "AxisPlacement",
    "DA1Rejection",
    "MemoryAdmissionOrchestrator",
    "OverlayEvidenceReader",
    "PreflightResult",
    "canonical_json",
    "fingerprint",
    "open_store",
    "placement_plan_from_payload",
    "placement_plan_payload",
    "request_fingerprint",
]
