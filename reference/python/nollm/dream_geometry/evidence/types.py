"""DE1 Memory Substrate immutable value objects and canonical payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from nollm.dream_geometry.protocol.contracts import (
    InterpretationAuthoringMode,
    InterpretationKind,
    LedgerEventKind,
    OriginKind,
    RevisionRelation,
    UsageState,
)

FORMAT_VERSION = "de1"


@dataclass(frozen=True)
class OriginDescriptor:
    kind: OriginKind
    reference: str | None
    context_reference: str | None
    role_label: str | None

    def __post_init__(self) -> None:
        _require_enum(self.kind, OriginKind, "kind")
        _require_optional_text(self.reference, "reference")
        _require_optional_text(self.context_reference, "context_reference")
        _require_optional_text(self.role_label, "role_label")


@dataclass(frozen=True)
class TemporalContext:
    captured_at: str | None
    source_time_expression: str | None
    reference_instant: str | None
    locale_hint: str | None

    def __post_init__(self) -> None:
        _require_optional_rfc3339(self.captured_at, "captured_at")
        _require_optional_text(self.source_time_expression, "source_time_expression")
        _require_optional_rfc3339(self.reference_instant, "reference_instant")
        _require_optional_text(self.locale_hint, "locale_hint")


@dataclass(frozen=True)
class DreamShard:
    shard_id: str
    content: str
    origin: OriginDescriptor
    temporal_context: TemporalContext
    context_refs: tuple[str, ...]
    initial_usage_state: UsageState
    format_version: str = FORMAT_VERSION

    def __post_init__(self) -> None:
        _require_id(self.shard_id, "shard_id")
        _require_non_empty_text(self.content, "content")
        _require_type(self.origin, OriginDescriptor, "origin")
        _require_type(self.temporal_context, TemporalContext, "temporal_context")
        object.__setattr__(self, "context_refs", _canonical_refs(self.context_refs, "context_ref"))
        _require_enum(self.initial_usage_state, UsageState, "initial_usage_state")
        _require_format(self.format_version)


@dataclass(frozen=True)
class InterpretationRecord:
    interpretation_id: str
    subject_shard_id: str
    kind: InterpretationKind
    statement: str
    authoring_mode: InterpretationAuthoringMode
    basis_refs: tuple[str, ...]
    context_refs: tuple[str, ...]
    initial_usage_state: UsageState
    format_version: str = FORMAT_VERSION

    def __post_init__(self) -> None:
        _require_id(self.interpretation_id, "interpretation_id")
        _require_id(self.subject_shard_id, "subject_shard_id")
        _require_enum(self.kind, InterpretationKind, "kind")
        _require_non_empty_text(self.statement, "statement")
        _require_enum(self.authoring_mode, InterpretationAuthoringMode, "authoring_mode")
        object.__setattr__(self, "basis_refs", _canonical_refs(self.basis_refs, "basis_ref"))
        object.__setattr__(self, "context_refs", _canonical_refs(self.context_refs, "context_ref"))
        _require_enum(self.initial_usage_state, UsageState, "initial_usage_state")
        _require_format(self.format_version)


@dataclass(frozen=True)
class RevisionEdge:
    from_record_id: str
    to_record_id: str
    relation: RevisionRelation
    basis_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_id(self.from_record_id, "from_record_id")
        _require_id(self.to_record_id, "to_record_id")
        if self.from_record_id == self.to_record_id:
            raise ValueError("revision self edge is not allowed")
        _require_enum(self.relation, RevisionRelation, "relation")
        object.__setattr__(self, "basis_refs", _canonical_refs(self.basis_refs, "basis_ref"))


@dataclass(frozen=True)
class RevisionThread:
    thread_id: str
    member_record_ids: tuple[str, ...]
    edges: tuple[RevisionEdge, ...]
    context_refs: tuple[str, ...]
    format_version: str = FORMAT_VERSION

    def __post_init__(self) -> None:
        _require_id(self.thread_id, "thread_id")
        members = _canonical_refs(self.member_record_ids, "member_record_id")
        if not members:
            raise ValueError("revision thread requires members")
        object.__setattr__(self, "member_record_ids", members)
        edges = tuple(sorted(self.edges, key=lambda edge: (edge.from_record_id, edge.to_record_id, edge.relation.value, edge.basis_refs)))
        for edge in edges:
            _require_type(edge, RevisionEdge, "edge")
            if edge.from_record_id not in members or edge.to_record_id not in members:
                raise ValueError("revision edge must reference thread members")
        _reject_replacement_cycle(edges)
        object.__setattr__(self, "edges", edges)
        object.__setattr__(self, "context_refs", _canonical_refs(self.context_refs, "context_ref"))
        _require_format(self.format_version)


@dataclass(frozen=True)
class UsageStateTransition:
    transition_id: str
    target_record_id: str
    expected_from_state: UsageState | None
    to_state: UsageState
    reason_refs: tuple[str, ...]
    recorded_at: str | None
    format_version: str = FORMAT_VERSION

    def __post_init__(self) -> None:
        _require_id(self.transition_id, "transition_id")
        _require_id(self.target_record_id, "target_record_id")
        if self.expected_from_state is not None:
            _require_enum(self.expected_from_state, UsageState, "expected_from_state")
            if self.expected_from_state is self.to_state:
                raise ValueError("usage state transition must change state")
        _require_enum(self.to_state, UsageState, "to_state")
        object.__setattr__(self, "reason_refs", _canonical_refs(self.reason_refs, "reason_ref"))
        _require_optional_rfc3339(self.recorded_at, "recorded_at")
        _require_format(self.format_version)


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    ordinal: int
    event_kind: LedgerEventKind
    record_id: str
    payload_key: str
    recorded_at: str | None

    def __post_init__(self) -> None:
        _require_id(self.event_id, "event_id")
        if not isinstance(self.ordinal, int) or isinstance(self.ordinal, bool) or self.ordinal < 0:
            raise ValueError("ordinal must be a non-negative integer")
        _require_enum(self.event_kind, LedgerEventKind, "event_kind")
        _require_id(self.record_id, "record_id")
        _require_non_empty_text(self.payload_key, "payload_key")
        _require_optional_rfc3339(self.recorded_at, "recorded_at")


def canonical_payload(record: object) -> dict[str, Any]:
    if isinstance(record, OriginDescriptor):
        return {
            "kind": record.kind.value,
            "reference": record.reference,
            "context_reference": record.context_reference,
            "role_label": record.role_label,
        }
    if isinstance(record, TemporalContext):
        return {
            "captured_at": record.captured_at,
            "source_time_expression": record.source_time_expression,
            "reference_instant": record.reference_instant,
            "locale_hint": record.locale_hint,
        }
    if isinstance(record, DreamShard):
        return {
            "record_type": "dream_shard",
            "format_version": record.format_version,
            "shard_id": record.shard_id,
            "content": record.content,
            "origin": canonical_payload(record.origin),
            "temporal_context": canonical_payload(record.temporal_context),
            "context_refs": record.context_refs,
            "initial_usage_state": record.initial_usage_state.value,
        }
    if isinstance(record, InterpretationRecord):
        return {
            "record_type": "interpretation_record",
            "format_version": record.format_version,
            "interpretation_id": record.interpretation_id,
            "subject_shard_id": record.subject_shard_id,
            "kind": record.kind.value,
            "statement": record.statement,
            "authoring_mode": record.authoring_mode.value,
            "basis_refs": record.basis_refs,
            "context_refs": record.context_refs,
            "initial_usage_state": record.initial_usage_state.value,
        }
    if isinstance(record, RevisionEdge):
        return {
            "from_record_id": record.from_record_id,
            "to_record_id": record.to_record_id,
            "relation": record.relation.value,
            "basis_refs": record.basis_refs,
        }
    if isinstance(record, RevisionThread):
        return {
            "record_type": "revision_thread",
            "format_version": record.format_version,
            "thread_id": record.thread_id,
            "member_record_ids": record.member_record_ids,
            "edges": tuple(canonical_payload(edge) for edge in record.edges),
            "context_refs": record.context_refs,
        }
    if isinstance(record, UsageStateTransition):
        return {
            "record_type": "usage_state_transition",
            "format_version": record.format_version,
            "transition_id": record.transition_id,
            "target_record_id": record.target_record_id,
            "expected_from_state": record.expected_from_state.value if record.expected_from_state is not None else None,
            "to_state": record.to_state.value,
            "reason_refs": record.reason_refs,
            "recorded_at": record.recorded_at,
        }
    if isinstance(record, LedgerEvent):
        return {
            "event_id": record.event_id,
            "ordinal": record.ordinal,
            "event_kind": record.event_kind.value,
            "record_id": record.record_id,
            "payload_key": record.payload_key,
            "recorded_at": record.recorded_at,
        }
    raise TypeError(f"unsupported canonical payload type: {type(record).__name__}")


def canonical_json(record: object) -> str:
    return json.dumps(canonical_payload(record), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def payload_key(record: object) -> str:
    return "sha256:" + sha256(canonical_json(record).encode("utf-8")).hexdigest()


def record_id(record: object) -> str:
    if isinstance(record, DreamShard):
        return record.shard_id
    if isinstance(record, InterpretationRecord):
        return record.interpretation_id
    if isinstance(record, RevisionThread):
        return record.thread_id
    if isinstance(record, UsageStateTransition):
        return record.transition_id
    if isinstance(record, LedgerEvent):
        return record.event_id
    raise TypeError(f"unsupported record type: {type(record).__name__}")


def _require_id(value: str, label: str) -> None:
    _require_non_empty_text(value, label)
    if value.strip() != value:
        raise ValueError(f"{label} must not contain surrounding whitespace")
    if any(ord(char) < 32 for char in value) or any(char in value for char in ("/", "\\", "\x7f")):
        raise ValueError(f"{label} must be path-safe")
    if value in {".", ".."} or ".." in value.split(":"):
        raise ValueError(f"{label} must not contain path traversal")


def _require_non_empty_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty")


def _require_optional_text(value: str | None, label: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{label} must be a string or None")


def _require_optional_rfc3339(value: str | None, label: str) -> None:
    if value is None:
        return
    _require_non_empty_text(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be RFC3339") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must be RFC3339 with timezone")


def _require_type(value: object, expected_type: type, label: str) -> None:
    if not isinstance(value, expected_type):
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_enum(value: object, expected_type: type, label: str) -> None:
    if not isinstance(value, expected_type):
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_format(format_version: str) -> None:
    if format_version != FORMAT_VERSION:
        raise ValueError("unsupported format_version")


def _canonical_refs(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{label}s must be a tuple")
    for value in values:
        _require_id(value, label)
    ordered = tuple(sorted(values))
    if len(set(ordered)) != len(ordered):
        raise ValueError(f"duplicate {label}")
    return ordered


def _reject_replacement_cycle(edges: tuple[RevisionEdge, ...]) -> None:
    graph: dict[str, set[str]] = {}
    for edge in edges:
        if edge.relation in {RevisionRelation.supersedes, RevisionRelation.withdraws}:
            graph.setdefault(edge.from_record_id, set()).add(edge.to_record_id)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ValueError("revision replacement cycle")
        if node in visited:
            return
        visiting.add(node)
        for target in graph.get(node, ()):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in tuple(graph):
        visit(node)


__all__ = [
    "FORMAT_VERSION",
    "DreamShard",
    "InterpretationRecord",
    "LedgerEvent",
    "OriginDescriptor",
    "RevisionEdge",
    "RevisionThread",
    "TemporalContext",
    "UsageStateTransition",
    "canonical_json",
    "canonical_payload",
    "payload_key",
    "record_id",
]
