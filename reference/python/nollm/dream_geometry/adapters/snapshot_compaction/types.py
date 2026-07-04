"""Immutable DG6 snapshot compaction adapter value objects."""

from __future__ import annotations

from dataclasses import dataclass

from nollm.dream_geometry.compression import CompactedTraceView, CompressionPlan

from .errors import DG6AdapterError


@dataclass(frozen=True, slots=True)
class SnapshotCompactionAdapterPolicy:
    policy_id: str = "dg6_snapshot_compaction_adapter"
    policy_version: str = "1"
    mode: str = "view_only"
    require_snapshot_fingerprint_match: bool = True
    require_exact_trace_manifest: bool = True
    require_dg5_bound_plan: bool = True

    def __post_init__(self) -> None:
        if (
            self.policy_id != "dg6_snapshot_compaction_adapter"
            or self.policy_version != "1"
            or self.mode != "view_only"
            or self.require_snapshot_fingerprint_match is not True
            or self.require_exact_trace_manifest is not True
            or self.require_dg5_bound_plan is not True
        ):
            raise DG6AdapterError("DG6_INVALID_POLICY", "DG6 only supports the fixed view-only adapter policy")


@dataclass(frozen=True, slots=True)
class SnapshotCompactionProjection:
    projection_id: str
    adapter_policy_id: str
    adapter_policy_version: str
    mode: str
    source_snapshot_id: str
    source_snapshot_fingerprint: str
    source_trace_ids: tuple[str, ...]
    source_trace_fingerprints: tuple[tuple[str, str], ...]
    compression_plan: CompressionPlan
    compacted_trace_view: CompactedTraceView
    projection_fingerprint: str
