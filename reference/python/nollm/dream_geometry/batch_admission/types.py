"""BA1 immutable public value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Any

from nollm.dream_geometry.admission import AdmissionReceipt, AdmissionRequest, request_fingerprint


RFC3339_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$"
)


class BatchWindowStatus(Enum):
    open = "open"
    ready_for_selection = "ready_for_selection"
    submitted = "submitted"
    closed = "closed"


class PromotionDecisionKind(Enum):
    promote = "promote"
    defer = "defer"
    do_not_admit = "do_not_admit"


class PromotionReason(Enum):
    explicit_pin = "explicit_pin"
    task_dependency = "task_dependency"
    source_backed_fact = "source_backed_fact"
    revision_event = "revision_event"
    reuse_observed = "reuse_observed"
    session_closure = "session_closure"
    recall_miss_receipt = "recall_miss_receipt"
    manual_batch_selection = "manual_batch_selection"


class PromotionDecider(Enum):
    host_rule = "host_rule"
    user = "user"
    human_operator = "human_operator"
    cortex_suggestion = "cortex_suggestion"


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    decision_id: str
    candidate_id: str
    shard_id: str
    decision: PromotionDecisionKind
    reasons: tuple[PromotionReason, ...]
    decided_by: PromotionDecider
    recorded_at: str
    next_action: str

    def __post_init__(self) -> None:
        _require_prefixed_id(self.decision_id, "pmd_", "decision_id")
        _require_candidate_id(self.candidate_id)
        _require_id(self.shard_id, "shard_id")
        if not isinstance(self.decision, PromotionDecisionKind):
            raise ValueError("decision must be PromotionDecisionKind")
        if not isinstance(self.reasons, tuple) or not self.reasons:
            raise ValueError("reasons must be a non-empty tuple")
        for reason in self.reasons:
            if not isinstance(reason, PromotionReason):
                raise ValueError("reasons must contain PromotionReason values")
        reasons = tuple(sorted(self.reasons, key=lambda item: item.value))
        if len(set(reasons)) != len(reasons):
            raise ValueError("reasons must be unique")
        object.__setattr__(self, "reasons", reasons)
        if not isinstance(self.decided_by, PromotionDecider):
            raise ValueError("decided_by must be PromotionDecider")
        validate_rfc3339_timestamp(self.recorded_at)
        if not isinstance(self.next_action, str) or not self.next_action:
            raise ValueError("next_action must be non-empty string")


@dataclass(frozen=True, slots=True)
class BatchAdmissionWindow:
    window_id: str
    member_shard_ids: tuple[str, ...]
    source_window_refs: tuple[str, ...]
    opened_at: str
    closed_at: str | None
    shared_policy_ref: str
    shared_geometry_profile_ref: str
    status: BatchWindowStatus

    def __post_init__(self) -> None:
        _require_prefixed_id(self.window_id, "baw_", "window_id")
        _require_unique_string_tuple(self.member_shard_ids, "member_shard_ids")
        object.__setattr__(self, "member_shard_ids", tuple(sorted(self.member_shard_ids)))
        _require_unique_string_tuple(self.source_window_refs, "source_window_refs", allow_empty=True)
        object.__setattr__(self, "source_window_refs", tuple(sorted(self.source_window_refs)))
        validate_rfc3339_timestamp(self.opened_at)
        if self.closed_at is not None:
            validate_rfc3339_timestamp(self.closed_at)
        _require_id(self.shared_policy_ref, "shared_policy_ref")
        _require_id(self.shared_geometry_profile_ref, "shared_geometry_profile_ref")
        if not isinstance(self.status, BatchWindowStatus):
            raise ValueError("status must be BatchWindowStatus")


@dataclass(frozen=True, slots=True)
class BatchAdmissionMember:
    member_id: str
    candidate_id: str
    promotion_decision: PromotionDecision
    admission_request: AdmissionRequest

    def __post_init__(self) -> None:
        _require_prefixed_id(self.member_id, "bam_", "member_id")
        _require_candidate_id(self.candidate_id)
        if not isinstance(self.promotion_decision, PromotionDecision):
            raise ValueError("promotion_decision must be PromotionDecision")
        if not isinstance(self.admission_request, AdmissionRequest):
            raise ValueError("admission_request must be AdmissionRequest")


@dataclass(frozen=True, slots=True)
class BatchAdmissionRequest:
    window: BatchAdmissionWindow
    members: tuple[BatchAdmissionMember, ...]
    submitted_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.window, BatchAdmissionWindow):
            raise ValueError("window must be BatchAdmissionWindow")
        if not isinstance(self.members, tuple) or not self.members:
            raise ValueError("members must be a non-empty tuple")
        for member in self.members:
            if not isinstance(member, BatchAdmissionMember):
                raise ValueError("members must contain BatchAdmissionMember values")
        validate_rfc3339_timestamp(self.submitted_at)


@dataclass(frozen=True, slots=True)
class BatchMemberReceipt:
    member_id: str
    candidate_id: str
    shard_id: str
    admission_receipt: AdmissionReceipt


@dataclass(frozen=True, slots=True)
class BatchAdmissionReceipt:
    window_id: str
    request_fingerprint: str
    submitted_at: str
    final_window_status: BatchWindowStatus
    member_receipts: tuple[BatchMemberReceipt, ...]


def batch_request_fingerprint(request: BatchAdmissionRequest) -> str:
    return fingerprint(
        {
            "window": window_payload(request.window),
            "members": tuple(
                {
                    "member_id": member.member_id,
                    "candidate_id": member.candidate_id,
                    "decision": decision_payload(member.promotion_decision),
                    "admission_request_fingerprint": request_fingerprint(member.admission_request),
                }
                for member in sorted(request.members, key=lambda item: item.member_id)
            ),
            "submitted_at": request.submitted_at,
        }
    )


def window_payload(window: BatchAdmissionWindow) -> dict[str, Any]:
    return {
        "window_id": window.window_id,
        "member_shard_ids": window.member_shard_ids,
        "source_window_refs": window.source_window_refs,
        "opened_at": window.opened_at,
        "closed_at": window.closed_at,
        "shared_policy_ref": window.shared_policy_ref,
        "shared_geometry_profile_ref": window.shared_geometry_profile_ref,
        "status": window.status.value,
    }


def decision_payload(decision: PromotionDecision) -> dict[str, Any]:
    return {
        "decision_id": decision.decision_id,
        "candidate_id": decision.candidate_id,
        "shard_id": decision.shard_id,
        "decision": decision.decision.value,
        "reasons": tuple(reason.value for reason in decision.reasons),
        "decided_by": decision.decided_by.value,
        "recorded_at": decision.recorded_at,
        "next_action": decision.next_action,
    }


def stable_json(payload: object) -> str:
    return json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint(payload: object) -> str:
    return "sha256:" + sha256(stable_json(payload).encode("utf-8")).hexdigest()


def validate_rfc3339_timestamp(value: str) -> None:
    if not isinstance(value, str) or RFC3339_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ValueError("timestamp must match RFC3339 with timezone")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be valid RFC3339") from exc


def _normalize(payload: object) -> object:
    if hasattr(payload, "value"):
        return getattr(payload, "value")
    if isinstance(payload, (str, int, bool)) or payload is None:
        return payload
    if isinstance(payload, tuple | list):
        return [_normalize(item) for item in payload]
    if isinstance(payload, dict):
        return {str(key): _normalize(value) for key, value in payload.items()}
    return str(payload)


def _require_prefixed_id(value: str, prefix: str, label: str) -> None:
    _require_id(value, label)
    if not value.startswith(prefix):
        raise ValueError(f"{label} must start with {prefix}")


def _require_candidate_id(value: str) -> None:
    _require_id(value, "candidate_id")
    if not (value.startswith("dac_") or value.startswith("dac:")):
        raise ValueError("candidate_id must start with dac_ or dac:")


def _require_id(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{label} must be non-empty string")
    if any(char in value for char in ("/", "\\", "\x00", "\x7f")) or any(ord(char) < 32 for char in value):
        raise ValueError(f"{label} must be path-safe")


def _require_unique_string_tuple(values: tuple[str, ...], label: str, *, allow_empty: bool = False) -> None:
    if not isinstance(values, tuple) or (not allow_empty and not values):
        raise ValueError(f"{label} must be a tuple")
    for value in values:
        _require_id(value, label)
    if len(set(values)) != len(values):
        raise ValueError(f"{label} must be unique")


__all__ = [
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
    "decision_payload",
    "fingerprint",
    "stable_json",
    "validate_rfc3339_timestamp",
    "window_payload",
]
