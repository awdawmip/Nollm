"""DA1 immutable Memory Admission value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Any

from nollm.dream_geometry.cortex import CompilationReceipt, CompiledGrowthProposal, canonical_payload as cortex_payload
from nollm.dream_geometry.evidence import DreamShard, canonical_payload as evidence_payload
from nollm.dream_geometry.field import CoarseCover, GravitySnapshot, GrowthTrace, TraceResidual, VerifiedChartLink
from nollm.dream_geometry.field.types import cell_payload, cell_ref_key, chart_fingerprint_payload, float_token
from nollm.dream_geometry.geometry import HexCell
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2
from nollm.dream_geometry.protocol.contracts import CoverState


CONTRACT_VERSION = "da1.v1"
FIELD_PROFILE_ID = "da1_sealed_default_v1"
RFC3339_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$"
)


class AdmissionOutcome(Enum):
    committed = "committed"
    idempotent = "idempotent"
    rejected = "rejected"
    partial = "partial"


@dataclass(frozen=True)
class AxisPlacement:
    axis_id: str
    step_id: str
    source_cell: HexCell
    fine_to_coarse_targets: tuple[HexCell, ...]
    verified_chart_link: VerifiedChartLink | None = None

    def __post_init__(self) -> None:
        _require_id(self.axis_id, "axis_id")
        _require_id(self.step_id, "step_id")
        _require_cell(self.source_cell, "source_cell")
        if not isinstance(self.fine_to_coarse_targets, tuple) or not self.fine_to_coarse_targets:
            raise ValueError("fine_to_coarse_targets must be a non-empty tuple")
        for cell in self.fine_to_coarse_targets:
            _require_cell(cell, "target_cell")
        targets = tuple(sorted(self.fine_to_coarse_targets, key=cell_ref_key))
        if len({cell_ref_key(cell) for cell in targets}) != len(targets):
            raise ValueError("duplicate target cell")
        object.__setattr__(self, "fine_to_coarse_targets", targets)


@dataclass(frozen=True)
class AdmissionPlacementPlan:
    plan_id: str
    axis_placements: tuple[AxisPlacement, ...]

    def __post_init__(self) -> None:
        _require_prefixed_id(self.plan_id, "apl_", "plan_id")
        if not isinstance(self.axis_placements, tuple) or not self.axis_placements:
            raise ValueError("axis_placements must be a non-empty tuple")
        placements = tuple(sorted(self.axis_placements, key=lambda item: (item.axis_id, item.step_id)))
        seen_axes: set[str] = set()
        seen_steps: set[str] = set()
        for placement in placements:
            if not isinstance(placement, AxisPlacement):
                raise ValueError("axis_placements must contain AxisPlacement values")
            if placement.axis_id in seen_axes or placement.step_id in seen_steps:
                raise ValueError("duplicate axis or step placement")
            seen_axes.add(placement.axis_id)
            seen_steps.add(placement.step_id)
        object.__setattr__(self, "axis_placements", placements)


@dataclass(frozen=True)
class AdmissionRequest:
    admission_id: str
    dream_shard: DreamShard
    growth_submission: dict[str, Any]
    placement_plan: AdmissionPlacementPlan
    recorded_at: str | None = None
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        _require_prefixed_id(self.admission_id, "adm_", "admission_id")
        if not isinstance(self.dream_shard, DreamShard):
            raise ValueError("dream_shard must be DreamShard")
        if not isinstance(self.growth_submission, dict):
            raise ValueError("growth_submission must be a mapping")
        if not isinstance(self.placement_plan, AdmissionPlacementPlan):
            raise ValueError("placement_plan must be AdmissionPlacementPlan")
        if self.recorded_at is not None and not isinstance(self.recorded_at, str):
            raise ValueError("recorded_at must be string or None")
        _require_contract(self.contract_version)


@dataclass(frozen=True)
class AdmissionProjection:
    proposal: CompiledGrowthProposal
    receipt: CompilationReceipt | None
    source_traces: tuple[GrowthTrace, ...]
    derived_traces: tuple[GrowthTrace, ...]
    residuals: tuple[TraceResidual, ...]
    covers: tuple[CoarseCover, ...]
    gravity_snapshot: GravitySnapshot
    projection_fingerprint: str


@dataclass(frozen=True)
class AdmissionRecord:
    admission_id: str
    subject_shard_id: str
    proposal_id: str
    compilation_receipt_id: str
    recorded_at: str | None
    request_fingerprint: str
    placement_plan_payload: dict[str, Any]
    placement_plan_fingerprint: str
    projection_fingerprint: str
    source_trace_ids: tuple[str, ...]
    derived_trace_ids: tuple[str, ...]
    residual_ids: tuple[str, ...]
    cover_ids: tuple[str, ...]
    cover_state_counts: dict[str, int]
    field_profile_id: str = FIELD_PROFILE_ID
    record_type: str = "admission_record"
    contract_version: str = CONTRACT_VERSION
    format_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        _require_prefixed_id(self.admission_id, "adm_", "admission_id")
        for label, value in (
            ("subject_shard_id", self.subject_shard_id),
            ("proposal_id", self.proposal_id),
            ("compilation_receipt_id", self.compilation_receipt_id),
            ("request_fingerprint", self.request_fingerprint),
            ("placement_plan_fingerprint", self.placement_plan_fingerprint),
            ("projection_fingerprint", self.projection_fingerprint),
        ):
            _require_id(value, label)
        if self.field_profile_id != FIELD_PROFILE_ID:
            raise ValueError("unsupported field profile")
        validate_rfc3339_timestamp(self.recorded_at)
        _require_contract(self.contract_version)
        _require_contract(self.format_version)
        if self.placement_plan_fingerprint != fingerprint(self.placement_plan_payload):
            raise ValueError("placement_plan_fingerprint mismatch")
        object.__setattr__(self, "source_trace_ids", tuple(sorted(self.source_trace_ids)))
        object.__setattr__(self, "derived_trace_ids", tuple(sorted(self.derived_trace_ids)))
        object.__setattr__(self, "residual_ids", tuple(sorted(self.residual_ids)))
        object.__setattr__(self, "cover_ids", tuple(sorted(self.cover_ids)))
        expected = {"candidate": 0, "stable": 0, "crystallized": 0}
        expected.update(self.cover_state_counts)
        object.__setattr__(self, "cover_state_counts", {key: int(expected[key]) for key in ("candidate", "stable", "crystallized")})


@dataclass(frozen=True)
class AdmissionReceipt:
    admission_id: str
    outcome: AdmissionOutcome
    subject_shard_id: str
    proposal_id: str
    compilation_receipt_id: str
    projection_fingerprint: str
    source_trace_count: int
    derived_trace_count: int
    residual_count: int
    cover_state_counts: dict[str, int]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "admission_id": self.admission_id,
            "outcome": self.outcome.value,
            "subject_shard_id": self.subject_shard_id,
            "proposal_id": self.proposal_id,
            "compilation_receipt_id": self.compilation_receipt_id,
            "projection_fingerprint": self.projection_fingerprint,
            "source_trace_count": self.source_trace_count,
            "derived_trace_count": self.derived_trace_count,
            "residual_count": self.residual_count,
            "cover_state_counts": self.cover_state_counts,
        }


def request_fingerprint(request: AdmissionRequest) -> str:
    return fingerprint(
        {
            "contract_version": request.contract_version,
            "admission_id": request.admission_id,
            "dream_shard": evidence_payload(request.dream_shard),
            "growth_submission": request.growth_submission,
            "placement_plan": placement_plan_payload(request.placement_plan),
            "recorded_at": request.recorded_at,
        }
    )


def placement_plan_payload(plan: AdmissionPlacementPlan) -> dict[str, Any]:
    return {
        "plan_id": plan.plan_id,
        "axis_placements": tuple(axis_placement_payload(item) for item in plan.axis_placements),
    }


def axis_placement_payload(placement: AxisPlacement) -> dict[str, Any]:
    return {
        "axis_id": placement.axis_id,
        "step_id": placement.step_id,
        "source_cell": replay_cell_payload(placement.source_cell),
        "fine_to_coarse_targets": tuple(replay_cell_payload(cell) for cell in placement.fine_to_coarse_targets),
        "verified_chart_link": _chart_link_payload(placement.verified_chart_link),
    }


def replay_cell_payload(cell: HexCell) -> dict[str, Any]:
    chart = cell.chart_fingerprint
    if chart is None:
        raise ValueError("cell chart fingerprint required")
    return {
        "chart_id": cell.cell_ref.chart_id,
        "q": cell.cell_ref.axial.q,
        "r": cell.cell_ref.axial.r,
        "chart": {
            "chart_id": chart.chart_id,
            "layer_index": chart.layer_index,
            "side_length": float_token(chart.side_length),
            "rotation_radians": float_token(chart.rotation_radians),
            "translation": {"x": float_token(chart.translation.x), "y": float_token(chart.translation.y)},
            "phase_metadata_items": tuple(tuple(item) for item in chart.phase_metadata_items),
        },
    }


def projection_fingerprint_payload(projection: AdmissionProjection) -> dict[str, Any]:
    return {
        "field_profile_id": FIELD_PROFILE_ID,
        "proposal": cortex_payload(projection.proposal),
        "source_trace_ids": tuple(trace.trace_id for trace in projection.source_traces),
        "derived_trace_ids": tuple(trace.trace_id for trace in projection.derived_traces),
        "residual_ids": tuple(residual.residual_id for residual in projection.residuals),
        "cover_ids": tuple(cover.cover_id for cover in projection.covers),
        "cover_state_counts": cover_state_counts(projection.covers),
        "gravity_snapshot_id": projection.gravity_snapshot.snapshot_id,
    }


def make_record(request: AdmissionRequest, projection: AdmissionProjection, receipt: CompilationReceipt) -> AdmissionRecord:
    plan_payload = placement_plan_payload(request.placement_plan)
    return AdmissionRecord(
        admission_id=request.admission_id,
        subject_shard_id=request.dream_shard.shard_id,
        proposal_id=projection.proposal.proposal_id,
        compilation_receipt_id=receipt.receipt_id,
        recorded_at=request.recorded_at,
        request_fingerprint=request_fingerprint(request),
        placement_plan_payload=plan_payload,
        placement_plan_fingerprint=fingerprint(plan_payload),
        projection_fingerprint=projection.projection_fingerprint,
        source_trace_ids=tuple(trace.trace_id for trace in projection.source_traces),
        derived_trace_ids=tuple(trace.trace_id for trace in projection.derived_traces),
        residual_ids=tuple(residual.residual_id for residual in projection.residuals),
        cover_ids=tuple(cover.cover_id for cover in projection.covers),
        cover_state_counts=cover_state_counts(projection.covers),
    )


def receipt_from_record(record: AdmissionRecord, outcome: AdmissionOutcome) -> AdmissionReceipt:
    return AdmissionReceipt(
        record.admission_id,
        outcome,
        record.subject_shard_id,
        record.proposal_id,
        record.compilation_receipt_id,
        record.projection_fingerprint,
        len(record.source_trace_ids),
        len(record.derived_trace_ids),
        len(record.residual_ids),
        record.cover_state_counts,
    )


def canonical_payload(value: object) -> dict[str, Any]:
    if isinstance(value, AdmissionRecord):
        return {
            "record_type": value.record_type,
            "contract_version": value.contract_version,
            "format_version": value.format_version,
            "admission_id": value.admission_id,
            "subject_shard_id": value.subject_shard_id,
            "proposal_id": value.proposal_id,
            "compilation_receipt_id": value.compilation_receipt_id,
            "recorded_at": value.recorded_at,
            "request_fingerprint": value.request_fingerprint,
            "placement_plan_payload": value.placement_plan_payload,
            "placement_plan_fingerprint": value.placement_plan_fingerprint,
            "field_profile_id": value.field_profile_id,
            "projection_fingerprint": value.projection_fingerprint,
            "source_trace_ids": value.source_trace_ids,
            "derived_trace_ids": value.derived_trace_ids,
            "residual_ids": value.residual_ids,
            "cover_ids": value.cover_ids,
            "cover_state_counts": value.cover_state_counts,
        }
    raise TypeError(f"unsupported canonical payload type: {type(value).__name__}")


def canonical_json(value: object) -> str:
    return stable_json(canonical_payload(value))


def stable_json(payload: object) -> str:
    return json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint(payload: object) -> str:
    return "sha256:" + sha256(stable_json(payload).encode("utf-8")).hexdigest()


def cover_state_counts(covers: tuple[CoarseCover, ...]) -> dict[str, int]:
    counts = {"candidate": 0, "stable": 0, "crystallized": 0}
    for cover in covers:
        if cover.state in {CoverState.candidate, CoverState.stable, CoverState.crystallized}:
            counts[cover.state.value] += 1
    return counts


def _chart_link_payload(link: VerifiedChartLink | None) -> dict[str, Any] | None:
    if link is None:
        return None
    return {
        "source_chart_fingerprint": chart_fingerprint_payload(link.source_chart_fingerprint),
        "target_chart_fingerprint": chart_fingerprint_payload(link.target_chart_fingerprint),
        "direction": "source_to_target",
        "verified": True,
    }


def _normalize(payload: object) -> object:
    if hasattr(payload, "value"):
        return getattr(payload, "value")
    if isinstance(payload, float):
        return float_token(payload)
    if isinstance(payload, (str, int, bool)) or payload is None:
        return payload
    if isinstance(payload, tuple | list):
        return [_normalize(item) for item in payload]
    if isinstance(payload, dict):
        return {str(key): _normalize(value) for key, value in payload.items()}
    return str(payload)


def _require_cell(cell: HexCell, label: str) -> None:
    if not isinstance(cell, HexCell):
        raise ValueError(f"{label} must be HexCell")
    cell_payload(cell)


def _require_contract(value: str) -> None:
    if value != CONTRACT_VERSION:
        raise ValueError("unsupported contract_version")


def _require_prefixed_id(value: str, prefix: str, label: str) -> None:
    _require_id(value, label)
    if not value.startswith(prefix):
        raise ValueError(f"{label} must start with {prefix}")


def _require_id(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty string")
    if any(char in value for char in ("/", "\\", "\x00")):
        raise ValueError(f"{label} must be path-safe")


def validate_rfc3339_timestamp(value: str | None) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not RFC3339_TIMESTAMP_PATTERN.fullmatch(value):
        raise ValueError("recorded_at must match DA1 RFC3339 timestamp profile")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("recorded_at must be a valid RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("recorded_at must include timezone")


def chart_from_payload(payload: dict[str, Any]) -> LocalChart:
    return LocalChart(
        payload["chart_id"],
        payload["layer_index"],
        float(payload["side_length"]),
        float(payload["rotation_radians"]),
        Vec2(float(payload["translation"]["x"]), float(payload["translation"]["y"])),
        {key: value for key, value in payload["phase_metadata_items"]},
    )


def axial_from_payload(payload: dict[str, Any]) -> AxialCoord:
    return AxialCoord(payload["q"], payload["r"])


__all__ = [
    "CONTRACT_VERSION",
    "FIELD_PROFILE_ID",
    "AdmissionOutcome",
    "AdmissionPlacementPlan",
    "AdmissionProjection",
    "AdmissionReceipt",
    "AdmissionRecord",
    "AdmissionRequest",
    "AxisPlacement",
    "canonical_json",
    "canonical_payload",
    "fingerprint",
    "make_record",
    "placement_plan_payload",
    "projection_fingerprint_payload",
    "receipt_from_record",
    "request_fingerprint",
    "stable_json",
    "validate_rfc3339_timestamp",
]
