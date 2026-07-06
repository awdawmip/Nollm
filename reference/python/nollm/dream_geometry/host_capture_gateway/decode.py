"""Strict HCG1 request decoding."""

from __future__ import annotations

import json
from typing import Any

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
    RetentionClass,
    VisibilityScope,
)
from nollm.dream_geometry.protocol.contracts import OriginKind

from .errors import HCGError, HCG_INVALID_JSON, HCG_INVALID_REQUEST, HCG_UNSUPPORTED_CAPTURE_MODE, HCG_UNSUPPORTED_READ_SELECTOR
from .types import GatewayCaptureRequest, GatewayReadRequest


CAPTURE_KIND = "nollm_hcg_capture_request"
READ_KIND = "nollm_hcg_read_request"
WIRE_VERSION = "1"

CAPTURE_TOP_FIELDS = frozenset({"kind", "version", "request_id", "capture", "policy"})
CAPTURE_REQUEST_FIELDS = frozenset(
    {
        "capture_id",
        "content",
        "origin",
        "recorded_at",
        "context_refs",
        "requested_visibility_scope",
        "deferred_candidate_request",
        "diagnostic_retention_until",
    }
)
ORIGIN_FIELDS = frozenset({"kind", "reference", "context_reference", "role_label"})
CANDIDATE_FIELDS = frozenset({"requested", "trigger_refs"})
POLICY_FIELDS = frozenset(
    {
        "policy_id",
        "policy_version",
        "persistence",
        "lineage",
        "diagnostics",
        "allowed_visibility_scopes",
        "retention_class",
        "promotion_mode",
    }
)
READ_TOP_FIELDS = frozenset({"kind", "version", "request_id", "selector"})
READ_SELECTOR_FIELDS = frozenset({"scope", "context_ref", "shard_ids"})
FORBIDDEN_READ_SELECTOR_FIELDS = frozenset(
    {
        "query_text",
        "query",
        "keyword",
        "semantic_query",
        "embedding",
        "similarity",
        "nearest",
        "offset",
        "cursor",
        "sort",
        "rank",
        "recent",
        "all",
        "scan",
        "search",
        "anchor",
        "chart",
        "cell",
        "cover",
        "trace",
        "route",
        "geometry",
        "admission_id",
        "field_policy",
        "field_snapshot",
        "recall_policy",
        "recall_budget",
        "limit",
        "runtime",
        "session",
        "global",
        "path",
        "url",
        "command",
    }
)


def load_json_text(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except ValueError as exc:
        raise HCGError(HCG_INVALID_JSON, "invalid JSON") from exc
    if not isinstance(payload, dict):
        raise HCGError(HCG_INVALID_REQUEST, "request must be an object")
    return payload


def decode_capture_payload(payload: dict[str, Any]) -> GatewayCaptureRequest:
    _exact_fields(payload, CAPTURE_TOP_FIELDS)
    _require_literal(payload, "kind", CAPTURE_KIND)
    _require_literal(payload, "version", WIRE_VERSION)
    request_id = _required_string(payload, "request_id")
    request_payload = _required_object(payload, "capture")
    policy_payload = _required_object(payload, "policy")
    _exact_fields(request_payload, CAPTURE_REQUEST_FIELDS)
    _exact_fields(policy_payload, POLICY_FIELDS)

    origin_payload = _required_object(request_payload, "origin")
    _exact_fields(origin_payload, ORIGIN_FIELDS, optional={"reference", "context_reference", "role_label"})
    candidate_payload = _required_object(request_payload, "deferred_candidate_request")
    _exact_fields(candidate_payload, CANDIDATE_FIELDS)

    scope = VisibilityScope(_required_string(request_payload, "requested_visibility_scope"))
    persistence = CapturePersistence(_required_string(policy_payload, "persistence"))
    if persistence is CapturePersistence.ephemeral or scope is VisibilityScope.current_turn:
        raise HCGError(HCG_UNSUPPORTED_CAPTURE_MODE, "capture mode is not supported by HCG1")

    requested = _required_bool(candidate_payload, "requested")
    triggers = tuple(CandidateTrigger(item) for item in _required_string_list(candidate_payload, "trigger_refs"))
    if requested and not triggers:
        raise HCGError(HCG_INVALID_REQUEST, "deferred capture requires explicit triggers")
    if not requested and triggers:
        raise HCGError(HCG_INVALID_REQUEST, "non-deferred capture must not include triggers")

    request = CaptureRequest(
        _required_string(request_payload, "capture_id"),
        _required_string(request_payload, "content"),
        CaptureOrigin(
            OriginKind(_required_string(origin_payload, "kind")),
            _optional_string(origin_payload, "reference"),
            _optional_string(origin_payload, "context_reference"),
            _optional_string(origin_payload, "role_label"),
        ),
        _required_string(request_payload, "recorded_at"),
        tuple(_required_string_list(request_payload, "context_refs")),
        scope,
        DeferredCandidateRequest(requested, triggers),
        _optional_string(request_payload, "diagnostic_retention_until"),
    )
    policy = CapturePolicy(
        _required_string(policy_payload, "policy_id"),
        _optional_string(policy_payload, "policy_version") or "1",
        persistence,
        CaptureLineage(_required_string(policy_payload, "lineage")),
        CaptureDiagnostics(_required_string(policy_payload, "diagnostics")),
        tuple(VisibilityScope(item) for item in _required_string_list(policy_payload, "allowed_visibility_scopes")),
        RetentionClass(_optional_string(policy_payload, "retention_class") or "session"),
        PromotionMode(_optional_string(policy_payload, "promotion_mode") or "disabled"),
    )
    return GatewayCaptureRequest(request_id, request, policy)


def decode_read_payload(payload: dict[str, Any]) -> GatewayReadRequest:
    _exact_fields(payload, READ_TOP_FIELDS)
    _require_literal(payload, "kind", READ_KIND)
    _require_literal(payload, "version", WIRE_VERSION)
    request_id = _required_string(payload, "request_id")
    selector = _required_object(payload, "selector")
    unknown_forbidden = FORBIDDEN_READ_SELECTOR_FIELDS.intersection(selector)
    if unknown_forbidden:
        raise HCGError(HCG_UNSUPPORTED_READ_SELECTOR, "read selector is not supported")
    _exact_fields(selector, READ_SELECTOR_FIELDS, optional={"context_ref", "shard_ids"})
    scope = _required_string(selector, "scope")
    if scope in {"session_window", "source_window"}:
        if "shard_ids" in selector:
            raise HCGError(HCG_UNSUPPORTED_READ_SELECTOR, "read selector is not supported")
        return GatewayReadRequest(request_id, scope, _required_string(selector, "context_ref"), ())
    if scope == "persistent_explicit":
        if "context_ref" in selector:
            raise HCGError(HCG_UNSUPPORTED_READ_SELECTOR, "read selector is not supported")
        return GatewayReadRequest(request_id, scope, None, tuple(_required_string_list(selector, "shard_ids")))
    raise HCGError(HCG_UNSUPPORTED_READ_SELECTOR, "read selector is not supported")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError("duplicate key")
        seen.add(key)
        result[key] = value
    return result


def _exact_fields(payload: dict[str, Any], allowed: frozenset[str], *, optional: set[str] | None = None) -> None:
    optional = optional or set()
    required = allowed - optional
    if set(payload) - allowed or required - set(payload):
        raise HCGError(HCG_INVALID_REQUEST, "request shape is invalid")


def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise HCGError(HCG_INVALID_REQUEST, "request shape is invalid")
    return value


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise HCGError(HCG_INVALID_REQUEST, "request shape is invalid")
    return value


def _require_literal(payload: dict[str, Any], key: str, expected: str) -> None:
    if payload.get(key) != expected:
        raise HCGError(HCG_INVALID_REQUEST, "request shape is invalid")


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise HCGError(HCG_INVALID_REQUEST, "request shape is invalid")
    return value


def _required_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if type(value) is not bool:
        raise HCGError(HCG_INVALID_REQUEST, "request shape is invalid")
    return value


def _required_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise HCGError(HCG_INVALID_REQUEST, "request shape is invalid")
    return value


__all__ = ["decode_capture_payload", "decode_read_payload", "load_json_text"]
