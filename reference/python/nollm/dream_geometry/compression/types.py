"""Immutable DG5 evidence-preserving compression value objects."""

from __future__ import annotations

from dataclasses import dataclass

from nollm.dream_geometry.field.types import TraceCompaction

from .errors import CompressionPlanningError


@dataclass(frozen=True, slots=True)
class CompressionPolicy:
    policy_id: str = "dg5_exact_transport_view"
    policy_version: str = "1"
    mode: str = "view_only"
    require_exact_transport_identity: bool = True

    def __post_init__(self) -> None:
        if self.mode != "view_only" or self.require_exact_transport_identity is not True:
            raise CompressionPlanningError("DG5_INVALID_POLICY", "DG5 only supports exact transport view-only compression")
        if self.policy_id != "dg5_exact_transport_view" or self.policy_version != "1":
            raise CompressionPlanningError("DG5_INVALID_POLICY", "unknown DG5 compression policy")


@dataclass(frozen=True, slots=True)
class CompressionPlan:
    plan_id: str
    policy_id: str
    policy_version: str
    mode: str
    input_trace_ids: tuple[str, ...]
    input_trace_fingerprints: tuple[tuple[str, str], ...]
    compactions: tuple[TraceCompaction, ...]
    passthrough_trace_ids: tuple[str, ...]
    input_trace_count: int
    compacted_member_count: int
    output_view_entry_count: int
    estimated_view_entry_reduction: int
    plan_fingerprint: str


@dataclass(frozen=True, slots=True)
class CompactedTraceEntry:
    entry_id: str
    entry_kind: str
    trace_id: str | None
    trace_fingerprint: str | None
    compaction: TraceCompaction | None
    member_trace_ids: tuple[str, ...]
    aggregate_mass: float

    def __post_init__(self) -> None:
        if self.entry_kind not in {"compacted_transport_view", "passthrough_trace_view"}:
            raise CompressionPlanningError("DG5_VIEW_MANIFEST_INVALID", "unknown compacted trace view entry kind")


@dataclass(frozen=True, slots=True)
class CompactedTraceView:
    plan: CompressionPlan
    entries: tuple[CompactedTraceEntry, ...]
    entry_count: int
    source_trace_count: int
    view_fingerprint: str
