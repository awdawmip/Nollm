"""CI1 Capture Ingress immutable public objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from nollm.dream_geometry.protocol.contracts import OriginKind


class CapturePersistence(Enum):
    ephemeral = "ephemeral"
    captured = "captured"
    persistent = "persistent"


class CaptureLineage(Enum):
    none = "none"
    minimal = "minimal"
    replayable = "replayable"


class CaptureDiagnostics(Enum):
    off = "off"
    on_failure = "on_failure"
    verbose = "verbose"


class VisibilityScope(Enum):
    current_turn = "current_turn"
    session_window = "session_window"
    source_window = "source_window"
    persistent_explicit = "persistent_explicit"


class RetentionClass(Enum):
    transient = "transient"
    session = "session"
    durable = "durable"


class PromotionMode(Enum):
    disabled = "disabled"
    manual = "manual"
    rule_assisted = "rule_assisted"


class CaptureStatus(Enum):
    ephemeral = "ephemeral"
    captured = "captured"
    deferred = "deferred"
    rejected = "rejected"


class CandidateStatus(Enum):
    deferred = "deferred"
    candidate = "candidate"


class CandidateTrigger(Enum):
    explicit_pin = "explicit_pin"
    task_dependency = "task_dependency"
    revision_event = "revision_event"
    reuse_observed = "reuse_observed"
    recall_miss = "recall_miss"
    manual_window = "manual_window"


@dataclass(frozen=True, slots=True)
class CaptureOrigin:
    kind: OriginKind
    reference: str | None = None
    context_reference: str | None = None
    role_label: str | None = None


@dataclass(frozen=True, slots=True)
class DeferredCandidateRequest:
    requested: bool = False
    trigger_refs: tuple[CandidateTrigger, ...] = ()


@dataclass(frozen=True, slots=True)
class CaptureRequest:
    capture_id: str
    content: str
    origin: CaptureOrigin
    recorded_at: str
    context_refs: tuple[str, ...]
    requested_visibility_scope: VisibilityScope
    deferred_candidate_request: DeferredCandidateRequest = DeferredCandidateRequest()
    diagnostic_retention_until: str | None = None


@dataclass(frozen=True, slots=True)
class CapturePolicy:
    policy_id: str
    policy_version: str = "1"
    persistence: CapturePersistence = CapturePersistence.captured
    lineage: CaptureLineage = CaptureLineage.none
    diagnostics: CaptureDiagnostics = CaptureDiagnostics.on_failure
    allowed_visibility_scopes: tuple[VisibilityScope, ...] = (VisibilityScope.session_window,)
    retention_class: RetentionClass = RetentionClass.session
    promotion_mode: PromotionMode = PromotionMode.disabled


@dataclass(frozen=True, slots=True)
class CaptureErrorInfo:
    code: str
    stage: str
    message_class: str


@dataclass(frozen=True, slots=True)
class CaptureReceipt:
    receipt_id: str
    capture_id: str
    status: CaptureStatus
    shard_id: str | None
    recorded_at: str
    policy_fingerprint: str
    visibility_scope: VisibilityScope
    deferred_candidate_id: str | None
    minimal_ledger_event_id: str | None
    error: CaptureErrorInfo | None = None


@dataclass(frozen=True, slots=True)
class DeferredAdmissionCandidate:
    candidate_id: str
    shard_id: str
    status: CandidateStatus
    trigger_refs: tuple[CandidateTrigger, ...]
    created_at: str
    policy_fingerprint: str
    source_window_refs: tuple[str, ...]
    promotion_attempt_refs: tuple[str, ...] = ()


def enum_value(value: object) -> Any:
    return value.value if isinstance(value, Enum) else value


__all__ = [
    "CandidateStatus",
    "CandidateTrigger",
    "CaptureDiagnostics",
    "CaptureErrorInfo",
    "CaptureLineage",
    "CaptureOrigin",
    "CapturePersistence",
    "CapturePolicy",
    "CaptureReceipt",
    "CaptureRequest",
    "CaptureStatus",
    "DeferredAdmissionCandidate",
    "DeferredCandidateRequest",
    "PromotionMode",
    "RetentionClass",
    "VisibilityScope",
]
