"""Immutable HAG1 gateway values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GatewayWindow:
    window_id: str
    member_shard_ids: tuple[str, ...]
    source_window_refs: tuple[str, ...]
    opened_at: str
    closed_at: str | None
    shared_policy_ref: str
    shared_geometry_profile_ref: str
    status: str


@dataclass(frozen=True, slots=True)
class GatewayPromotionDecision:
    decision_id: str
    candidate_id: str
    shard_id: str
    decision: str
    reasons: tuple[str, ...]
    decided_by: str
    recorded_at: str
    next_action: str


@dataclass(frozen=True, slots=True)
class GatewayAdmission:
    admission_id: str
    shard_id: str
    growth_submission: dict[str, Any]
    placement_plan: dict[str, Any]
    recorded_at: str


@dataclass(frozen=True, slots=True)
class GatewayMember:
    member_id: str
    candidate_id: str
    promotion_decision: GatewayPromotionDecision
    admission: GatewayAdmission


@dataclass(frozen=True, slots=True)
class GatewayAdmissionRequest:
    request_id: str
    submitted_at: str
    window: GatewayWindow
    members: tuple[GatewayMember, ...]
    raw_payload: dict[str, Any]


__all__ = [
    "GatewayAdmission",
    "GatewayAdmissionRequest",
    "GatewayMember",
    "GatewayPromotionDecision",
    "GatewayWindow",
]
