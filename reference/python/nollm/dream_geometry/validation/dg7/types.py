"""DG7 immutable receipt types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RuntimeCaptureReceiptView:
    label: str
    capture_id: str
    status: str
    shard_id: str
    deferred_candidate_id: str
    visibility_scope: str


@dataclass(frozen=True, slots=True)
class RuntimeIsolationSummary:
    captured_unadmitted_c_excluded: bool
    admitted_unassembled_d_excluded: bool
    snapshot_replayed_trace_manifest_matches_dg6_expansion: bool
    recall_is_independent_of_dg6_view: bool
    unexpected_write_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimePositiveVerificationReceipt:
    receipt_kind: str
    scenario_id: str
    scenario_version: str
    status: str
    capture_receipts: tuple[RuntimeCaptureReceiptView, ...]
    admission_receipt_ids: tuple[str, ...]
    admitted_unassembled_d_admission_id: str
    snapshot_id: str
    snapshot_source_admission_ids: tuple[str, ...]
    snapshot_source_shard_ids: tuple[str, ...]
    dg6_projection_id: str
    dg6_plan_id: str
    dg6_input_trace_count: int
    dg6_view_entry_count: int
    dg6_expansion_trace_ids: tuple[str, ...]
    recall_envelope: dict[str, Any]
    c_miss_envelope: dict[str, Any]
    isolation: RuntimeIsolationSummary
    output_fingerprint: str


__all__ = [
    "RuntimeCaptureReceiptView",
    "RuntimeIsolationSummary",
    "RuntimePositiveVerificationReceipt",
]
