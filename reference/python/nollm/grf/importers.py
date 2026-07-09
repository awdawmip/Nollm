"""Import-only migration boundary for GRF prototype inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capture import GRFCaptureRequest
from .cell_address import CellAddress
from .evidence import EvidenceShardRecord, ORIGIN_KINDS
from .source_window import SourceWindowRecord

MIGRATION_BOUNDARY_MODE = "migration_boundary_import_only"


@dataclass(frozen=True)
class CaptureImportResult:
    mode: str
    capture_request: GRFCaptureRequest
    source_window: SourceWindowRecord
    ignored_fields: tuple[str, ...]


@dataclass(frozen=True)
class MinimalPlacementAdmissionFixture:
    shard_id: str
    source_window_id: str
    policy_hint: dict[str, object]
    recorded_at: str


def import_hcg_like_capture(payload: dict[str, Any]) -> CaptureImportResult:
    if payload.get("kind") != "nollm_hcg_capture_request" or payload.get("version") != "1":
        raise ValueError("unsupported HCG-like capture envelope")
    capture = _mapping(payload.get("capture"), "capture")
    origin = _mapping(capture.get("origin"), "origin")
    recorded_at = _text(capture.get("recorded_at"), "recorded_at")
    context_refs = tuple(str(item) for item in capture.get("context_refs", ()))
    context_reference = origin.get("context_reference")
    refs = tuple(item for item in (*context_refs, context_reference, origin.get("reference")) if isinstance(item, str) and item)
    window_id = str(context_reference or f"source:hcg:{payload['request_id']}")
    request = GRFCaptureRequest(
        _text(capture.get("capture_id"), "capture_id"),
        _text(capture.get("content"), "content"),
        _origin_kind(origin.get("kind"), origin.get("role_label")),
        (window_id,),
        recorded_at,
    )
    window = SourceWindowRecord(window_id, "validation_fixture", refs or (str(payload["request_id"]),), recorded_at, policy_ref=MIGRATION_BOUNDARY_MODE)
    return CaptureImportResult(MIGRATION_BOUNDARY_MODE, request, window, _ignored(payload, {"kind", "version", "request_id", "capture"}))


def import_oca_like_capture(payload: dict[str, Any]) -> CaptureImportResult:
    recorded_at = _text(payload.get("recorded_at"), "recorded_at")
    context_reference = _text(payload.get("context_reference"), "context_reference")
    window = SourceWindowRecord(context_reference, "validation_fixture", (str(payload.get("origin_reference", "")), context_reference), recorded_at, policy_ref=MIGRATION_BOUNDARY_MODE)
    request = GRFCaptureRequest(
        _text(payload.get("capture_id"), "capture_id"),
        _text(payload.get("content"), "content"),
        _origin_kind(None, payload.get("role_label")),
        (window.window_id,),
        recorded_at,
    )
    return CaptureImportResult(MIGRATION_BOUNDARY_MODE, request, window, _ignored(payload, {"request_id", "capture_id", "content", "origin_reference", "context_reference", "recorded_at", "role_label"}))


def import_v2_dream_shard_like(payload: dict[str, Any]) -> EvidenceShardRecord:
    return EvidenceShardRecord(
        _text(payload.get("shard_id"), "shard_id"),
        _text(payload.get("content"), "content"),
        _text(payload.get("created_at"), "created_at"),
        _origin_kind(payload.get("origin_kind"), None),
        tuple(str(item) for item in payload.get("source_window_refs", ())),
        str(payload.get("trust_state", "imported")),
        str(payload.get("usage_state", "captured")),
    )


def import_minimal_placement_admission_fixture(payload: dict[str, Any]) -> MinimalPlacementAdmissionFixture:
    policy_hint = dict(payload.get("policy_hint", {"policy_id": "validation_fixture_policy"}))
    target = policy_hint.get("target_cell")
    if isinstance(target, dict):
        policy_hint["target_cell"] = CellAddress(target["profile_id"], target["chart_id"], target["layer"], target["q"], target["r"], target.get("phase"))
    return MinimalPlacementAdmissionFixture(_text(payload.get("shard_id"), "shard_id"), _text(payload.get("source_window_id"), "source_window_id"), policy_hint, _text(payload.get("recorded_at"), "recorded_at"))


def _origin_kind(kind: object, role_label: object) -> str:
    if isinstance(kind, str) and kind in ORIGIN_KINDS:
        return kind
    role_map = {
        "user": "user_utterance",
        "assistant": "assistant_output",
        "system": "imported_text",
        "tool": "tool_result",
        "validation_fixture": "validation_fixture",
    }
    if isinstance(kind, str) and kind in role_map:
        return role_map[kind]
    if isinstance(role_label, str) and role_label in role_map:
        return role_map[role_label]
    raise ValueError("unsupported origin kind")


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")
    return value


def _ignored(payload: dict[str, Any], supported: set[str]) -> tuple[str, ...]:
    return tuple(sorted(str(key) for key in payload if key not in supported))
