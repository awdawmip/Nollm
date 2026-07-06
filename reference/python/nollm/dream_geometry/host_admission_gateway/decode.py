"""Strict HAG1 request decoding."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from nollm.dream_geometry.admission import FIELD_PROFILE_ID, placement_plan_from_payload
from nollm.dream_geometry.batch_admission import (
    PromotionDecider,
    PromotionDecision,
    PromotionDecisionKind,
    PromotionReason,
)

from .errors import HAGError, HAG_INVALID_REQUEST
from .types import GatewayAdmission, GatewayAdmissionRequest, GatewayMember, GatewayPromotionDecision, GatewayWindow


KIND = "nollm_hag_admission_request"
VERSION = "1"

TOP_FIELDS = frozenset({"kind", "version", "request_id", "submitted_at", "window", "members"})
WINDOW_FIELDS = frozenset(
    {
        "window_id",
        "member_shard_ids",
        "source_window_refs",
        "opened_at",
        "closed_at",
        "shared_policy_ref",
        "shared_geometry_profile_ref",
        "status",
    }
)
MEMBER_FIELDS = frozenset({"member_id", "candidate_id", "promotion_decision", "admission"})
DECISION_FIELDS = frozenset({"decision_id", "candidate_id", "shard_id", "decision", "reasons", "decided_by", "recorded_at", "next_action"})
ADMISSION_FIELDS = frozenset({"admission_id", "shard_id", "growth_submission", "placement_plan", "recorded_at"})
PLACEMENT_FIELDS = frozenset({"plan_id", "axis_placements"})

FORBIDDEN_KEYS = frozenset(
    {
        "workspace",
        "repo_root",
        "store_root",
        "path",
        "file_path",
        "root_path",
        "dream_shard",
        "raw_dream_shard",
        "content",
        "embedding",
        "similarity",
        "rank",
        "truth_score",
        "importance_score",
        "global_search",
        "global_discovery",
        "query",
        "recall",
        "assembly",
        "field",
        "runtime",
        "network",
        "cache",
        "database",
        "auto_admit",
        "auto_axis",
        "auto_chart",
        "auto_cell",
        "auto_cover",
        "auto_anchor",
    }
)
FORBIDDEN_PREFIXES = ("auto_", "global_")
ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$")


def load_json_text(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except ValueError as exc:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected") from exc
    if not isinstance(payload, dict):
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    return payload


def decode_admission_payload(payload: dict[str, Any]) -> GatewayAdmissionRequest:
    _reject_forbidden_recursive(payload)
    _exact_fields(payload, TOP_FIELDS)
    _require_literal(payload, "kind", KIND)
    _require_literal(payload, "version", VERSION)
    request_id = _required_id(payload, "request_id")
    submitted_at = _required_timestamp(payload, "submitted_at")

    window_payload = _required_object(payload, "window")
    _exact_fields(window_payload, WINDOW_FIELDS)
    window = GatewayWindow(
        _required_id(window_payload, "window_id"),
        tuple(_required_id_list(window_payload, "member_shard_ids")),
        tuple(_required_id_list(window_payload, "source_window_refs")),
        _required_timestamp(window_payload, "opened_at"),
        _optional_timestamp(window_payload, "closed_at"),
        _required_id(window_payload, "shared_policy_ref"),
        _required_id(window_payload, "shared_geometry_profile_ref"),
        _required_string(window_payload, "status"),
    )
    if window.status != "ready_for_selection" or window.shared_geometry_profile_ref != FIELD_PROFILE_ID:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")

    raw_members = payload.get("members")
    if not isinstance(raw_members, list) or not raw_members:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    members = tuple(_decode_member(item) for item in raw_members)
    _validate_cross_member_identity(window, members)
    return GatewayAdmissionRequest(request_id, submitted_at, window, members, payload)


def _decode_member(payload: object) -> GatewayMember:
    if not isinstance(payload, dict):
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    _exact_fields(payload, MEMBER_FIELDS)
    decision_payload = _required_object(payload, "promotion_decision")
    admission_payload = _required_object(payload, "admission")
    _exact_fields(decision_payload, DECISION_FIELDS)
    _exact_fields(admission_payload, ADMISSION_FIELDS)

    decision = GatewayPromotionDecision(
        _required_id(decision_payload, "decision_id"),
        _required_id(decision_payload, "candidate_id"),
        _required_id(decision_payload, "shard_id"),
        _required_string(decision_payload, "decision"),
        tuple(_required_id_list(decision_payload, "reasons")),
        _required_string(decision_payload, "decided_by"),
        _required_timestamp(decision_payload, "recorded_at"),
        _required_string(decision_payload, "next_action"),
    )
    if decision.decision != "promote" or decision.decided_by == "cortex_suggestion" or decision.next_action != "request_growth_submission":
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    _coerce_ba1_decision(decision)

    placement = _required_object(admission_payload, "placement_plan")
    _exact_fields(placement, PLACEMENT_FIELDS)
    _required_id(placement, "plan_id")
    if not isinstance(placement.get("axis_placements"), (list, tuple)) or not placement.get("axis_placements"):
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    try:
        placement_plan_from_payload(placement)
    except Exception as exc:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected") from exc

    admission = GatewayAdmission(
        _required_id(admission_payload, "admission_id"),
        _required_id(admission_payload, "shard_id"),
        _required_object(admission_payload, "growth_submission"),
        placement,
        _required_timestamp(admission_payload, "recorded_at"),
    )
    member = GatewayMember(_required_id(payload, "member_id"), _required_id(payload, "candidate_id"), decision, admission)
    if member.candidate_id != decision.candidate_id or decision.shard_id != admission.shard_id:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    return member


def _validate_cross_member_identity(window: GatewayWindow, members: tuple[GatewayMember, ...]) -> None:
    fields = {
        "member": [item.member_id for item in members],
        "candidate": [item.candidate_id for item in members],
        "shard": [item.admission.shard_id for item in members],
        "decision": [item.promotion_decision.decision_id for item in members],
        "admission": [item.admission.admission_id for item in members],
        "placement": [item.admission.placement_plan["plan_id"] for item in members],
    }
    if any(len(set(values)) != len(values) for values in fields.values()):
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    if set(window.member_shard_ids) != {item.admission.shard_id for item in members}:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")


def _coerce_ba1_decision(decision: GatewayPromotionDecision) -> PromotionDecision:
    return PromotionDecision(
        decision.decision_id,
        decision.candidate_id,
        decision.shard_id,
        PromotionDecisionKind(decision.decision),
        tuple(PromotionReason(item) for item in decision.reasons),
        PromotionDecider(decision.decided_by),
        decision.recorded_at,
        decision.next_action,
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError("duplicate key")
        seen.add(key)
        result[key] = value
    return result


def _reject_forbidden_recursive(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_KEYS or any(key.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
                raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
            _reject_forbidden_recursive(item)
    elif isinstance(value, list):
        for item in value:
            _reject_forbidden_recursive(item)


def _exact_fields(payload: dict[str, Any], allowed: frozenset[str]) -> None:
    if set(payload) != allowed:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")


def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    return value


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    return value


def _required_id(payload: dict[str, Any], key: str) -> str:
    value = _required_string(payload, key)
    if value.strip() != value or not ID_RE.fullmatch(value) or any(char in value for char in ("/", "\\", "\x00", "\x7f")):
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    if any(ord(char) < 32 for char in value):
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    return value


def _required_id_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    ids = [_required_id({key: item}, key) for item in value]
    if len(set(ids)) != len(ids):
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    return ids


def _required_timestamp(payload: dict[str, Any], key: str) -> str:
    value = _required_string(payload, key)
    if RFC3339_RE.fullmatch(value) is None:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected") from exc
    return value


def _optional_timestamp(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")
    return _required_timestamp(payload, key)


def _require_literal(payload: dict[str, Any], key: str, expected: str) -> None:
    if payload.get(key) != expected:
        raise HAGError(HAG_INVALID_REQUEST, "request was rejected")


__all__ = ["decode_admission_payload", "load_json_text"]
