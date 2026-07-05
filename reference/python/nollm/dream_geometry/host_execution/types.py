"""Immutable HX1 host execution values."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nollm.dream_geometry.admission import AdmissionRequest
from nollm.dream_geometry.batch_admission import PromotionDecision
from nollm.dream_geometry.capture import CapturePolicy, CaptureRequest


@dataclass(frozen=True, slots=True)
class HostCaptureBinding:
    capture_id: str
    request: CaptureRequest
    policy: CapturePolicy


@dataclass(frozen=True, slots=True)
class HostAdmissionBinding:
    request_id: str
    decision_id: str
    candidate_id: str
    admission_id: str
    member_id: str
    decision: PromotionDecision
    request: AdmissionRequest
    proposal_ref: str
    placement_plan_ref: str
    actual_candidate_id: str | None = None
    declared_shard_id: str | None = None


@dataclass(frozen=True, slots=True)
class HostRecallBinding:
    query_ref: str
    admitted_workset_ref: str
    invocation: object


@dataclass(frozen=True, slots=True)
class HostDG6VerificationBinding:
    view_ref: str
    verification_only: bool = True


@dataclass(frozen=True, slots=True)
class HostPlanBindings:
    capture_bindings: tuple[HostCaptureBinding, ...] = ()
    admission_bindings: tuple[HostAdmissionBinding, ...] = ()
    recall_binding: HostRecallBinding | None = None
    dg6_binding: HostDG6VerificationBinding | None = None


@dataclass(frozen=True, slots=True)
class HostExecutionContext:
    work_root: Path
    recorded_at: str
    batch_window_id: str = "baw_hx1_window"
    batch_policy_id: str = "policy:hx1:explicit"
    batch_source_ref: str = "source:hx1"
    finite_set_id: str = "hx1_explicit_finite_set"
    enable_dg6_verification: bool = True


@dataclass(frozen=True, slots=True)
class CaptureReceiptView:
    capture_id: str
    status: str
    shard_id: str
    deferred_candidate_id: str
    visibility_scope: str


@dataclass(frozen=True, slots=True)
class HostExecutionReceipt:
    receipt_kind: str
    plan_id: str
    plan_intent: str
    status: str
    completed_stages: tuple[str, ...]
    failed_stage: str | None
    capture_receipt_views: tuple[CaptureReceiptView, ...]
    admission_receipt_ids: tuple[str, ...]
    explicit_assembly_admission_ids: tuple[str, ...]
    snapshot_id: str | None
    snapshot_source_admission_ids: tuple[str, ...]
    dg6_projection_id: str | None
    recall_public_envelope: dict[str, Any] | None
    partial_outcome_message: str | None
    work_root_marker_id: str
    execution_input_fingerprint: str
    output_fingerprint: str


__all__ = [
    "CaptureReceiptView",
    "HostAdmissionBinding",
    "HostCaptureBinding",
    "HostDG6VerificationBinding",
    "HostExecutionContext",
    "HostExecutionReceipt",
    "HostPlanBindings",
    "HostRecallBinding",
]
