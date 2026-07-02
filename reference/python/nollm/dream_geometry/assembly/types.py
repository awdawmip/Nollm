"""DF1 finite in-memory FieldSnapshot value objects."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Callable

from nollm.dream_geometry.admission import AdmissionProjection, AdmissionRecord
from nollm.dream_geometry.admission.types import canonical_payload as admission_payload
from nollm.dream_geometry.cortex import CompilationReceipt, CortexStore
from nollm.dream_geometry.evidence import MemorySubstrateStore
from nollm.dream_geometry.field import CoarseCover, CoverPolicy, GravityPolicy, GravitySnapshot, GrowthTrace, TraceResidual, VerifiedChartLink
from nollm.dream_geometry.geometry.coverage import CoverageDistribution
from nollm.dream_geometry.recall import RecallUniverse


DEFAULT_ASSEMBLY_POLICY_ID = "df1_finite_field_assembly"
DEFAULT_ASSEMBLY_POLICY_VERSION = "1"
DEFAULT_GEOMETRY_PROFILE_ID = "da1_sealed_default_v1"
DEFAULT_FIELD_POLICY_IDENTITY = "da1_sealed_default_v1|dg2_cover_policy:cover_policy:v2:a2d647c2e140e8629ddf4fa1352e8bda|dg2_gravity_policy:1"


@dataclass(frozen=True)
class AdmissionReplaySource:
    admission_record: AdmissionRecord
    evidence_reader: MemorySubstrateStore
    cortex_reader: CortexStore
    replay_validator: Callable[[AdmissionRecord], AdmissionProjection]
    compilation_receipt: CompilationReceipt | None = None
    replayed_projection: AdmissionProjection | None = None


@dataclass(frozen=True)
class FiniteAdmissionSet:
    assembly_id: str
    admissions: tuple[AdmissionReplaySource, ...]
    geometry_profile_id: str = DEFAULT_GEOMETRY_PROFILE_ID
    field_policy_identity: str = DEFAULT_FIELD_POLICY_IDENTITY


@dataclass(frozen=True)
class FieldAssemblyPolicy:
    policy_id: str = DEFAULT_ASSEMBLY_POLICY_ID
    version: str = DEFAULT_ASSEMBLY_POLICY_VERSION
    require_replay_validation: bool = True
    require_verified_chart_links: bool = True
    reject_duplicate_admission_id: bool = True
    reject_incompatible_geometry_profile: bool = True
    reject_incompatible_field_policy: bool = True
    output_mode: str = "in_memory_only"


@dataclass(frozen=True)
class AdmissionManifestEntry:
    admission_id: str
    admission_record_fingerprint: str
    shard_id: str
    proposal_id: str
    compilation_receipt_id: str
    placement_plan_fingerprint: str
    projection_fingerprint: str


@dataclass(frozen=True)
class AssemblyAuditSummary:
    assembly_id: str
    snapshot_id: str
    source_admission_ids: tuple[str, ...]
    trace_count: int
    cover_count: int
    verified_link_count: int
    universe_id: str
    validation_status: str


@dataclass(frozen=True)
class FiniteFieldSnapshot:
    snapshot_id: str
    assembly_id: str
    policy_identity: str
    geometry_profile_id: str
    field_policy_identity: str
    admission_manifest: tuple[AdmissionManifestEntry, ...]
    replayed_traces: tuple[GrowthTrace, ...]
    trace_residuals: tuple[TraceResidual, ...]
    coarse_covers: tuple[CoarseCover, ...]
    coverage_up: tuple[CoverageDistribution, ...]
    coverage_down: tuple[CoverageDistribution, ...]
    verified_chart_links: tuple[VerifiedChartLink, ...]
    gravity_snapshot: GravitySnapshot
    source_admission_ids: tuple[str, ...]


@dataclass(frozen=True)
class FieldAssemblyResult:
    snapshot: FiniteFieldSnapshot
    universe: RecallUniverse
    audit_summary: AssemblyAuditSummary


def record_fingerprint(record: AdmissionRecord) -> str:
    return stable_fingerprint(admission_payload(record))


def policy_identity(policy: FieldAssemblyPolicy) -> str:
    return stable_fingerprint(
        {
            "policy_id": policy.policy_id,
            "version": policy.version,
            "require_replay_validation": policy.require_replay_validation,
            "require_verified_chart_links": policy.require_verified_chart_links,
            "reject_duplicate_admission_id": policy.reject_duplicate_admission_id,
            "reject_incompatible_geometry_profile": policy.reject_incompatible_geometry_profile,
            "reject_incompatible_field_policy": policy.reject_incompatible_field_policy,
            "output_mode": policy.output_mode,
        }
    )


def snapshot_fingerprint_payload(snapshot: FiniteFieldSnapshot) -> dict[str, object]:
    return {
        "assembly_id": snapshot.assembly_id,
        "policy_identity": snapshot.policy_identity,
        "geometry_profile_id": snapshot.geometry_profile_id,
        "field_policy_identity": snapshot.field_policy_identity,
        "admission_manifest": tuple(entry.__dict__ for entry in snapshot.admission_manifest),
        "trace_ids": tuple(trace.trace_id for trace in snapshot.replayed_traces),
        "residual_ids": tuple(residual.residual_id for residual in snapshot.trace_residuals),
        "cover_ids": tuple(cover.cover_id for cover in snapshot.coarse_covers),
        "coverage_up": tuple(_distribution_key(item) for item in snapshot.coverage_up),
        "coverage_down": tuple(_distribution_key(item) for item in snapshot.coverage_down),
        "verified_chart_links": tuple(str(link) for link in snapshot.verified_chart_links),
        "gravity_snapshot_id": snapshot.gravity_snapshot.snapshot_id,
        "source_admission_ids": snapshot.source_admission_ids,
    }


def stable_fingerprint(payload: object) -> str:
    return "sha256:" + sha256(stable_json(payload).encode("utf-8")).hexdigest()


def stable_json(payload: object) -> str:
    return json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _distribution_key(distribution: CoverageDistribution) -> object:
    return {
        "direction": distribution.direction.value,
        "source": _cell_ref(distribution.source_cell),
        "source_chart": _chart_ref(distribution.source_cell),
        "targets": tuple(_cell_ref(kernel.target_cell) for kernel in distribution.kernels),
        "target_charts": tuple(_chart_ref(kernel.target_cell) for kernel in distribution.kernels),
        "weights": tuple(format(float(kernel.weight), ".17g") for kernel in distribution.kernels),
        "overlaps": tuple(format(float(kernel.overlap_area), ".17g") for kernel in distribution.kernels),
        "residual": format(float(distribution.residual.mass), ".17g"),
        "residual_reasons": tuple(reason.value for reason in distribution.residual.reasons),
    }


def _cell_ref(cell) -> str:
    return f"{cell.cell_ref.chart_id}:{cell.cell_ref.axial.q}:{cell.cell_ref.axial.r}"


def _chart_ref(cell) -> object:
    chart = cell.chart_fingerprint
    return {
        "chart_id": getattr(chart, "chart_id"),
        "layer_index": getattr(chart, "layer_index"),
        "side_length": format(float(getattr(chart, "side_length")), ".17g"),
        "rotation_radians": format(float(getattr(chart, "rotation_radians")), ".17g"),
        "translation": {
            "x": format(float(getattr(getattr(chart, "translation"), "x")), ".17g"),
            "y": format(float(getattr(getattr(chart, "translation"), "y")), ".17g"),
        },
        "phase_metadata_items": tuple(tuple(item) for item in getattr(chart, "phase_metadata_items", ())),
    }


def _normalize(payload: object) -> object:
    if hasattr(payload, "value"):
        return getattr(payload, "value")
    if isinstance(payload, float):
        return format(float(payload), ".17g")
    if isinstance(payload, (str, int, bool)) or payload is None:
        return payload
    if isinstance(payload, tuple | list):
        return [_normalize(item) for item in payload]
    if isinstance(payload, dict):
        return {str(key): _normalize(value) for key, value in payload.items()}
    return str(payload)


__all__ = [
    "AdmissionManifestEntry",
    "AdmissionReplaySource",
    "AssemblyAuditSummary",
    "DEFAULT_ASSEMBLY_POLICY_ID",
    "DEFAULT_ASSEMBLY_POLICY_VERSION",
    "DEFAULT_FIELD_POLICY_IDENTITY",
    "DEFAULT_GEOMETRY_PROFILE_ID",
    "FieldAssemblyPolicy",
    "FieldAssemblyResult",
    "FiniteAdmissionSet",
    "FiniteFieldSnapshot",
    "policy_identity",
    "record_fingerprint",
    "snapshot_fingerprint_payload",
    "stable_fingerprint",
]
