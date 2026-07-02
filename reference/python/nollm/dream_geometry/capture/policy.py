"""CI1 policy validation and canonical fingerprints."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any

from nollm.dream_geometry.protocol.contracts import OriginKind

from .errors import (
    CI1_CANDIDATE_FORBIDDEN,
    CI1_INVALID_POLICY,
    CI1_INVALID_REQUEST,
    CI1_REPLAYABLE_FORBIDDEN,
    CI1_VISIBILITY_SCOPE_FORBIDDEN,
    CaptureError,
)
from .types import (
    CandidateTrigger,
    CaptureDiagnostics,
    CaptureLineage,
    CapturePersistence,
    CapturePolicy,
    CaptureRequest,
    PromotionMode,
    RetentionClass,
    VisibilityScope,
    enum_value,
)


STRICT_RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$")


def validate_capture_request(request: CaptureRequest) -> None:
    _require_id(request.capture_id, "cap_", "capture_id")
    if not isinstance(request.content, str) or not request.content.strip():
        raise CaptureError(CI1_INVALID_REQUEST, "content_empty")
    if not isinstance(request.origin.kind, OriginKind):
        raise CaptureError(CI1_INVALID_REQUEST, "origin_kind_invalid")
    for value in (request.origin.reference, request.origin.context_reference, request.origin.role_label):
        if value is not None and not isinstance(value, str):
            raise CaptureError(CI1_INVALID_REQUEST, "origin_field_invalid")
    validate_strict_rfc3339(request.recorded_at, "recorded_at")
    if not isinstance(request.requested_visibility_scope, VisibilityScope):
        raise CaptureError(CI1_INVALID_REQUEST, "visibility_scope_invalid")
    _validate_refs(request.context_refs, "context_ref")
    if not isinstance(request.deferred_candidate_request.requested, bool):
        raise CaptureError(CI1_INVALID_REQUEST, "candidate_request_invalid")
    for trigger in request.deferred_candidate_request.trigger_refs:
        if not isinstance(trigger, CandidateTrigger):
            raise CaptureError(CI1_INVALID_REQUEST, "candidate_trigger_invalid")
    if len(set(request.deferred_candidate_request.trigger_refs)) != len(request.deferred_candidate_request.trigger_refs):
        raise CaptureError(CI1_INVALID_REQUEST, "candidate_trigger_duplicate")
    if request.diagnostic_retention_until is not None:
        validate_strict_rfc3339(request.diagnostic_retention_until, "diagnostic_retention_until")


def validate_capture_policy(policy: CapturePolicy) -> None:
    _require_id(policy.policy_id, "cp_", "policy_id")
    if policy.policy_version != "1":
        raise CaptureError(CI1_INVALID_POLICY, "policy_version_invalid")
    if not isinstance(policy.persistence, CapturePersistence):
        raise CaptureError(CI1_INVALID_POLICY, "persistence_invalid")
    if not isinstance(policy.lineage, CaptureLineage):
        raise CaptureError(CI1_INVALID_POLICY, "lineage_invalid")
    if not isinstance(policy.diagnostics, CaptureDiagnostics):
        raise CaptureError(CI1_INVALID_POLICY, "diagnostics_invalid")
    if not policy.allowed_visibility_scopes or any(not isinstance(scope, VisibilityScope) for scope in policy.allowed_visibility_scopes):
        raise CaptureError(CI1_INVALID_POLICY, "allowed_visibility_invalid")
    if len(set(policy.allowed_visibility_scopes)) != len(policy.allowed_visibility_scopes):
        raise CaptureError(CI1_INVALID_POLICY, "allowed_visibility_duplicate")
    if not isinstance(policy.retention_class, RetentionClass):
        raise CaptureError(CI1_INVALID_POLICY, "retention_invalid")
    if not isinstance(policy.promotion_mode, PromotionMode):
        raise CaptureError(CI1_INVALID_POLICY, "promotion_invalid")
    if policy.lineage is CaptureLineage.replayable:
        raise CaptureError(CI1_REPLAYABLE_FORBIDDEN, "replayable_reserved_for_da1")


def validate_request_policy_pair(request: CaptureRequest, policy: CapturePolicy) -> None:
    validate_capture_request(request)
    validate_capture_policy(policy)
    if request.requested_visibility_scope not in policy.allowed_visibility_scopes:
        raise CaptureError(CI1_VISIBILITY_SCOPE_FORBIDDEN, "visibility_scope_not_allowed")
    if policy.persistence is CapturePersistence.ephemeral:
        if set(policy.allowed_visibility_scopes) != {VisibilityScope.current_turn}:
            raise CaptureError(CI1_VISIBILITY_SCOPE_FORBIDDEN, "ephemeral_visibility_must_be_current_turn")
        if request.requested_visibility_scope is not VisibilityScope.current_turn:
            raise CaptureError(CI1_VISIBILITY_SCOPE_FORBIDDEN, "ephemeral_visibility_must_be_current_turn")
        if policy.lineage is not CaptureLineage.none or policy.diagnostics is not CaptureDiagnostics.off:
            raise CaptureError(CI1_INVALID_POLICY, "ephemeral_requires_no_durable_controls")
        if request.deferred_candidate_request.requested:
            raise CaptureError(CI1_CANDIDATE_FORBIDDEN, "ephemeral_candidate_forbidden")
    elif request.requested_visibility_scope is VisibilityScope.current_turn:
        raise CaptureError(CI1_VISIBILITY_SCOPE_FORBIDDEN, "current_turn_is_ephemeral_only")
    if policy.diagnostics is CaptureDiagnostics.verbose and request.diagnostic_retention_until is None:
        raise CaptureError(CI1_INVALID_REQUEST, "verbose_diagnostics_expiry_required")
    if request.deferred_candidate_request.requested:
        if policy.persistence not in {CapturePersistence.captured, CapturePersistence.persistent}:
            raise CaptureError(CI1_CANDIDATE_FORBIDDEN, "candidate_requires_persistence")
        if policy.lineage is not CaptureLineage.minimal:
            raise CaptureError(CI1_CANDIDATE_FORBIDDEN, "candidate_requires_minimal_lineage")
        if policy.promotion_mode not in {PromotionMode.manual, PromotionMode.rule_assisted}:
            raise CaptureError(CI1_CANDIDATE_FORBIDDEN, "candidate_requires_manual_or_rule_assisted")
        if not request.deferred_candidate_request.trigger_refs:
            raise CaptureError(CI1_CANDIDATE_FORBIDDEN, "candidate_triggers_required")


def validate_strict_rfc3339(value: str, label: str) -> None:
    if not isinstance(value, str) or STRICT_RFC3339.match(value) is None:
        raise CaptureError(CI1_INVALID_REQUEST, label + "_invalid_rfc3339")
    if value.endswith("Z"):
        parsed_value = value[:-1] + "+00:00"
    else:
        hour = int(value[-6:-4])
        minute = int(value[-2:])
        if hour > 23 or minute > 59:
            raise CaptureError(CI1_INVALID_REQUEST, label + "_invalid_offset")
        parsed_value = value
    try:
        datetime.fromisoformat(parsed_value)
    except ValueError as exc:
        raise CaptureError(CI1_INVALID_REQUEST, label + "_invalid_rfc3339") from exc


def canonical_request_payload(request: CaptureRequest) -> dict[str, Any]:
    return {
        "capture_id": request.capture_id,
        "content": request.content,
        "origin": {
            "kind": request.origin.kind.value,
            "reference": request.origin.reference,
            "context_reference": request.origin.context_reference,
            "role_label": request.origin.role_label,
        },
        "recorded_at": request.recorded_at,
        "context_refs": tuple(sorted(request.context_refs)),
        "requested_visibility_scope": request.requested_visibility_scope.value,
        "deferred_candidate_request": {
            "requested": request.deferred_candidate_request.requested,
            "trigger_refs": tuple(sorted(trigger.value for trigger in request.deferred_candidate_request.trigger_refs)),
        },
        "diagnostic_retention_until": request.diagnostic_retention_until,
    }


def canonical_policy_payload(policy: CapturePolicy) -> dict[str, Any]:
    return {
        "policy_id": policy.policy_id,
        "policy_version": policy.policy_version,
        "persistence": policy.persistence.value,
        "lineage": policy.lineage.value,
        "diagnostics": policy.diagnostics.value,
        "allowed_visibility_scopes": tuple(sorted(scope.value for scope in policy.allowed_visibility_scopes)),
        "retention_class": policy.retention_class.value,
        "promotion_mode": policy.promotion_mode.value,
    }


def stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint(payload: Any) -> str:
    return "sha256:" + sha256(stable_json(payload).encode("utf-8")).hexdigest()


def request_fingerprint(request: CaptureRequest) -> str:
    return fingerprint(canonical_request_payload(request))


def policy_fingerprint(policy: CapturePolicy) -> str:
    return fingerprint(canonical_policy_payload(policy))


def _require_id(value: str, prefix: str, label: str) -> None:
    if not isinstance(value, str) or not value.startswith(prefix) or value.strip() != value:
        raise CaptureError(CI1_INVALID_REQUEST if label == "capture_id" else CI1_INVALID_POLICY, label + "_invalid")
    if any(ord(char) < 32 for char in value) or any(char in value for char in ("/", "\\", "\x7f")):
        raise CaptureError(CI1_INVALID_REQUEST if label == "capture_id" else CI1_INVALID_POLICY, label + "_path_unsafe")


def _validate_refs(values: tuple[str, ...], label: str) -> None:
    if not isinstance(values, tuple):
        raise CaptureError(CI1_INVALID_REQUEST, label + "_invalid")
    for value in values:
        if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value) or any(char in value for char in ("/", "\\", "\x7f")):
            raise CaptureError(CI1_INVALID_REQUEST, label + "_invalid")
    if len(set(values)) != len(values):
        raise CaptureError(CI1_INVALID_REQUEST, label + "_duplicate")


__all__ = [
    "canonical_policy_payload",
    "canonical_request_payload",
    "fingerprint",
    "policy_fingerprint",
    "request_fingerprint",
    "stable_json",
    "validate_capture_policy",
    "validate_capture_request",
    "validate_request_policy_pair",
    "validate_strict_rfc3339",
]
