"""Frozen DG2 Field Dynamics value objects.

Allowed: deterministic field contracts and validation helpers.
Forbidden: Evidence I/O, runtime access, OpenClaw, adapters, filesystem,
network, subprocess, or natural-language interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any

from nollm.dream_geometry.geometry.types import HexCell
from nollm.dream_geometry.protocol.contracts import CoverState, GrowthBasis, TraceState


@dataclass(frozen=True)
class TraceSeed:
    trace_id: str
    shard_id: str
    proposal_id: str
    source_cell: HexCell
    axis: str
    basis: GrowthBasis
    basis_refs: tuple[str, ...]
    mass: float
    support_key: str
    genericity: float
    ambiguity: float
    conflict: float
    stability_epochs: int
    state: TraceState

    def __post_init__(self) -> None:
        _require_id(self.trace_id, "trace_id")
        _require_id(self.shard_id, "shard_id")
        _require_id(self.proposal_id, "proposal_id")
        _require_cell_fingerprint(self.source_cell)
        _require_id(self.axis, "axis")
        _require_basis_refs(self.basis, self.basis_refs)
        _require_positive(self.mass, "mass")
        _require_id(self.support_key, "support_key")
        _require_unit(self.genericity, "genericity")
        _require_unit(self.ambiguity, "ambiguity")
        _require_unit(self.conflict, "conflict")
        _require_non_negative_int(self.stability_epochs, "stability_epochs")
        if self.state is TraceState.accepted and self.basis is GrowthBasis.provisional_llm_generalization:
            raise ValueError("accepted seed cannot use provisional_llm_generalization basis")


@dataclass(frozen=True)
class GrowthTrace:
    trace_id: str
    origin_shard_id: str
    proposal_id: str
    parent_trace_id: str | None
    cell: HexCell
    axis: str
    basis: GrowthBasis
    basis_refs: tuple[str, ...]
    mass: float
    support_key: str
    genericity: float
    ambiguity: float
    conflict: float
    stability_epochs: int
    state: TraceState
    derivation_kind: str
    geometry_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_id(self.trace_id, "trace_id")
        _require_id(self.origin_shard_id, "origin_shard_id")
        _require_id(self.proposal_id, "proposal_id")
        if self.parent_trace_id is not None:
            _require_id(self.parent_trace_id, "parent_trace_id")
        _require_cell_fingerprint(self.cell)
        _require_id(self.axis, "axis")
        _require_basis_refs(self.basis, self.basis_refs)
        _require_positive(self.mass, "mass")
        _require_id(self.support_key, "support_key")
        _require_unit(self.genericity, "genericity")
        _require_unit(self.ambiguity, "ambiguity")
        _require_unit(self.conflict, "conflict")
        _require_non_negative_int(self.stability_epochs, "stability_epochs")
        _require_id(self.derivation_kind, "derivation_kind")


@dataclass(frozen=True)
class TraceResidual:
    residual_id: str
    parent_trace_id: str
    source_cell_ref: str
    mass: float
    reasons: tuple[str, ...]
    geometry_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_id(self.residual_id, "residual_id")
        _require_id(self.parent_trace_id, "parent_trace_id")
        _require_id(self.source_cell_ref, "source_cell_ref")
        _require_non_negative(self.mass, "mass")


@dataclass(frozen=True)
class VerifiedChartLink:
    source_chart_fingerprint: object
    target_chart_fingerprint: object
    transform_validation: object

    def __post_init__(self) -> None:
        if getattr(self.transform_validation, "state_recommendation", None) != "verified":
            raise ValueError("chart link requires verified transform validation")


@dataclass(frozen=True)
class TracePropagationResult:
    derived_traces: tuple[GrowthTrace, ...]
    residual: TraceResidual
    parent_mass: float
    derived_mass: float
    accounting_error: float

    def __post_init__(self) -> None:
        _require_positive(self.parent_mass, "parent_mass")
        _require_non_negative(self.derived_mass, "derived_mass")
        _require_non_negative(self.accounting_error, "accounting_error")


@dataclass(frozen=True)
class CoverPolicy:
    policy_id: str = "dg2_cover_policy"
    version: str = "1"
    min_total_mass: float = 0.25
    min_independent_support: int = 2
    min_axes: int = 2
    max_provisional_mass: float = 0.0
    max_genericity: float = 0.6
    max_ambiguity: float = 0.4
    max_conflict: float = 0.2
    min_stability: int = 1

    def __post_init__(self) -> None:
        _require_id(self.policy_id, "policy_id")
        _require_id(self.version, "version")
        _require_non_negative(self.min_total_mass, "min_total_mass")
        _require_non_negative_int(self.min_independent_support, "min_independent_support")
        _require_non_negative_int(self.min_axes, "min_axes")
        _require_non_negative(self.max_provisional_mass, "max_provisional_mass")
        _require_unit(self.max_genericity, "max_genericity")
        _require_unit(self.max_ambiguity, "max_ambiguity")
        _require_unit(self.max_conflict, "max_conflict")
        _require_non_negative_int(self.min_stability, "min_stability")


@dataclass(frozen=True)
class CoverEligibility:
    approved: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CoarseCover:
    cover_id: str
    chart_fingerprint: object
    support_cell: object
    support_trace_ids: tuple[str, ...]
    support_shard_ids: tuple[str, ...]
    support_keys: tuple[str, ...]
    axes_present: tuple[str, ...]
    mass: float
    provisional_mass: float
    genericity: float
    ambiguity: float
    conflict: float
    stability: int
    state: CoverState
    policy_version: str
    eligibility_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_id(self.cover_id, "cover_id")
        _require_non_negative(self.mass, "mass")
        _require_non_negative(self.provisional_mass, "provisional_mass")
        _require_unit(self.genericity, "genericity")
        _require_unit(self.ambiguity, "ambiguity")
        _require_unit(self.conflict, "conflict")
        _require_non_negative_int(self.stability, "stability")
        _require_id(self.policy_version, "policy_version")


@dataclass(frozen=True)
class CrystallizationDecision:
    decision_id: str
    cover_id: str
    approved: bool
    authorized_by: str
    decision_basis_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_id(self.decision_id, "decision_id")
        _require_id(self.cover_id, "cover_id")
        if self.approved:
            _require_id(self.authorized_by, "authorized_by")
            if not self.decision_basis_refs:
                raise ValueError("approved crystallization requires decision_basis_refs")


@dataclass(frozen=True)
class GravityPolicy:
    policy_id: str = "dg2_gravity_policy"
    version: str = "1"
    mass_weight: float = 1.0
    support_weight: float = 1.0
    axis_weight: float = 1.0
    stability_weight: float = 1.0
    genericity_penalty_weight: float = 1.0
    ambiguity_penalty_weight: float = 1.0
    conflict_penalty_weight: float = 1.0
    congestion_penalty_weight: float = 0.25
    stability_epoch_scale: int = 4

    def __post_init__(self) -> None:
        _require_id(self.policy_id, "policy_id")
        _require_id(self.version, "version")
        weights = (
            self.mass_weight,
            self.support_weight,
            self.axis_weight,
            self.stability_weight,
            self.genericity_penalty_weight,
            self.ambiguity_penalty_weight,
            self.conflict_penalty_weight,
            self.congestion_penalty_weight,
        )
        for value in weights:
            _require_non_negative(value, "gravity weight")
        if sum(weights[:4]) <= 0.0 or sum(weights[4:]) <= 0.0:
            raise ValueError("gravity policy requires positive support and penalty terms")
        _require_positive(self.stability_epoch_scale, "stability_epoch_scale")


@dataclass(frozen=True)
class GravityContribution:
    cover_id: str
    cell_ref: str
    potential: float
    support_term: float
    penalty_terms: tuple[tuple[str, float], ...]
    policy_id: str


@dataclass(frozen=True)
class GravitySnapshot:
    snapshot_id: str
    chart_fingerprint: object
    contributions: tuple[GravityContribution, ...]
    input_cover_ids: tuple[str, ...]
    policy_id: str
    policy_version: str


@dataclass(frozen=True)
class TraceCompaction:
    compaction_id: str
    member_trace_ids: tuple[str, ...]
    canonical_key: str
    aggregate_mass: float
    expansion_manifest: tuple[str, ...]


def stable_id(prefix: str, payload: object) -> str:
    return f"{prefix}:{sha256(stable_json(payload).encode('utf-8')).hexdigest()[:32]}"


def stable_json(payload: object) -> str:
    return json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def cell_ref_key(cell: HexCell) -> str:
    return f"{cell.cell_ref.chart_id}:{cell.cell_ref.axial.q}:{cell.cell_ref.axial.r}"


def chart_fingerprint_payload(fingerprint: object) -> object:
    if fingerprint is None:
        raise ValueError("chart fingerprint is required")
    items = getattr(fingerprint, "phase_metadata_items", ())
    return {
        "chart_id": getattr(fingerprint, "chart_id"),
        "layer_index": getattr(fingerprint, "layer_index"),
        "side_length": float_token(getattr(fingerprint, "side_length")),
        "rotation_radians": float_token(getattr(fingerprint, "rotation_radians")),
        "translation": {
            "x": float_token(getattr(getattr(fingerprint, "translation"), "x")),
            "y": float_token(getattr(getattr(fingerprint, "translation"), "y")),
        },
        "phase_metadata_items": tuple(tuple(item) for item in items),
    }


def cell_payload(cell: HexCell) -> object:
    return {"cell_ref": cell_ref_key(cell), "chart_fingerprint": chart_fingerprint_payload(cell.chart_fingerprint)}


def float_token(value: float) -> str:
    if not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise ValueError("finite float required")
    return format(float(value), ".17g")


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


def _require_cell_fingerprint(cell: HexCell) -> None:
    if cell.chart_fingerprint is None:
        raise ValueError("cell must carry chart geometry fingerprint")


def _require_id(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty")


def _require_positive(value: float, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(float(value)) or float(value) <= 0.0:
        raise ValueError(f"{label} must be positive")


def _require_non_negative(value: float, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(float(value)) or float(value) < 0.0:
        raise ValueError(f"{label} must be non-negative")


def _require_unit(value: float, label: str) -> None:
    _require_non_negative(value, label)
    if float(value) > 1.0:
        raise ValueError(f"{label} must be in [0, 1]")


def _require_non_negative_int(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def _require_basis_refs(basis: GrowthBasis, basis_refs: tuple[str, ...]) -> None:
    if basis is not GrowthBasis.deterministic_projection and not basis_refs:
        raise ValueError("basis_refs must be non-empty")
    for ref in basis_refs:
        _require_id(ref, "basis_ref")
