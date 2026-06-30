"""DR1 Recall Resolver immutable value objects.

Allowed: read-only contracts for deterministic recall digests.
Forbidden: persistence, runtime access, OpenClaw, adapters, NLP, semantic search,
filesystem, network, subprocess, or upstream mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any

from nollm.dream_geometry.cortex.types import CompilationReceipt, CompiledGrowthProposal
from nollm.dream_geometry.evidence import InterpretationRecord, RevisionThread
from nollm.dream_geometry.field.types import CoarseCover, CoverPolicy, GravitySnapshot, GrowthTrace, TraceCompaction, VerifiedChartLink
from nollm.dream_geometry.geometry.coverage import CoverageDistribution


class ProposalAdmission(Enum):
    current_accepted = "current_accepted"
    legacy_dc1_read_only = "legacy_dc1_read_only"


class RecallDigestStatus(Enum):
    resolved = "resolved"
    deferred = "deferred"
    insufficient_evidence = "insufficient_evidence"
    budget_exhausted = "budget_exhausted"
    rejected = "rejected"


@dataclass(frozen=True)
class ProposalReadRecord:
    proposal: CompiledGrowthProposal
    admission: ProposalAdmission
    source_ref: str
    receipt: CompilationReceipt | None = None


@dataclass(frozen=True)
class ResolvedRelativeSpan:
    query_axis_id: str
    query_expression: str
    resolved_axis_id: str
    resolved_expression: str
    reference_instant: str
    resolver_basis: str
    source_step_id: str = ""
    start_char: int = -1
    end_char: int = -1
    quoted_text: str = ""
    resolver_id: str = ""
    resolver_version: str = ""


@dataclass(frozen=True)
class RuntimeTimeResolution:
    spans: tuple[ResolvedRelativeSpan, ...]
    complete: bool
    resolver_id: str = "caller_runtime"
    resolver_version: str = "1"
    reference_instant: str = ""


@dataclass(frozen=True)
class RecallPolicy:
    policy_id: str = "dr1_recall_policy"
    version: str = "1"
    min_required_axis_matches: int = 2
    max_seed_covers: int = 8
    max_lateral_hops: int = 0
    max_result_items: int = 16
    include_tentative_primary: bool = True
    include_retired_context: bool = False
    include_rejected_context: bool = False
    include_legacy_context: bool = False
    allow_verified_chart_hops: bool = True

    @property
    def include_tentative(self) -> bool:
        return self.include_tentative_primary

    def __post_init__(self) -> None:
        _require_text(self.policy_id, "policy_id")
        _require_text(self.version, "version")
        if not 1 <= self.min_required_axis_matches <= 8:
            raise ValueError("min_required_axis_matches must be in [1, 8]")
        if self.max_seed_covers < 1:
            raise ValueError("max_seed_covers must be positive")
        if not 0 <= self.max_lateral_hops <= 2:
            raise ValueError("max_lateral_hops must be in [0, 2]")
        if not 1 <= self.max_result_items <= 64:
            raise ValueError("max_result_items must be in [1, 64]")


@dataclass(frozen=True)
class RecallUniverse:
    proposal_records: tuple[ProposalReadRecord, ...]
    traces: tuple[GrowthTrace, ...]
    covers: tuple[CoarseCover, ...]
    universe_id: str = "dr1:universe"
    coverage_up: tuple[CoverageDistribution, ...] = ()
    coverage_down: tuple[CoverageDistribution, ...] = ()
    verified_chart_links: tuple[VerifiedChartLink, ...] = ()
    gravity_snapshot: GravitySnapshot | None = None
    trace_compactions: tuple[TraceCompaction, ...] = ()
    cover_policy_records: tuple[CoverPolicy, ...] = ()
    interpretation_records: tuple[InterpretationRecord, ...] = ()
    revision_threads: tuple[RevisionThread, ...] = ()


@dataclass(frozen=True)
class ProbeAtom:
    axis_id: str
    expression: str
    source_kind: str
    required: bool
    source_step_id: str


@dataclass(frozen=True)
class TraceSemanticProjection:
    trace_id: str
    proposal_id: str
    shard_id: str
    axis_id: str
    expression: str
    step_id: str
    basis: str
    basis_refs: tuple[str, ...]


@dataclass(frozen=True)
class TraversalRecord:
    phase: str
    cover_id: str
    source_cell_ref: str | None
    direction: str
    target_cell_refs: tuple[str, ...]
    residual_mass: float
    residual_reasons: tuple[str, ...]
    mass_in: float = 0.0
    mass_out: float = 0.0
    trace_id: str | None = None
    target_cell_ref: str | None = None
    m_up: float = 0.0
    m_down: float = 0.0
    path_mass: float = 0.0
    reason_code: str = "DR1_TRAVERSAL_EXECUTED"


@dataclass(frozen=True)
class EvidenceQualification:
    shard_id: str
    usage_state: str
    tier: str
    included_as_evidence: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class RecallResultItem:
    shard_id: str
    cover_id: str
    trace_ids: tuple[str, ...]
    matched_axes: tuple[str, ...]
    structural_score: float
    qualification: EvidenceQualification
    projection_refs: tuple[str, ...]
    context_record_ids: tuple[str, ...]
    path_mass: float = 0.0
    route_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecallDigest:
    digest_id: str
    query_probe_id: str
    status: RecallDigestStatus
    ephemeral: bool
    items: tuple[RecallResultItem, ...]
    primary_evidence: tuple[RecallResultItem, ...]
    contextual_evidence: tuple[RecallResultItem, ...]
    traversal_records: tuple[TraversalRecord, ...]
    warnings: tuple[str, ...]
    discarded: tuple[str, ...]
    unresolved_residual_mass: float
    gravity_guidance_applied: bool
    metadata: dict[str, Any]

    @property
    def outcome(self) -> RecallDigestStatus:
        return self.status


@dataclass(frozen=True)
class ValidatedRecallUniverse:
    universe: RecallUniverse
    current_records: tuple[ProposalReadRecord, ...]
    legacy_records: tuple[ProposalReadRecord, ...]
    projections: tuple[TraceSemanticProjection, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class RecallValidationError(ValueError):
    reason_code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.reason_code}: {self.detail}"


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty")


def require_finite_non_negative(value: float, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(float(value)) or float(value) < 0:
        raise ValueError(f"{label} must be finite and non-negative")


__all__ = [
    "EvidenceQualification",
    "ProbeAtom",
    "ProposalAdmission",
    "ProposalReadRecord",
    "RecallDigest",
    "RecallDigestStatus",
    "RecallPolicy",
    "RecallResultItem",
    "RecallUniverse",
    "RecallValidationError",
    "ResolvedRelativeSpan",
    "RuntimeTimeResolution",
    "TraceSemanticProjection",
    "TraversalRecord",
    "ValidatedRecallUniverse",
    "require_finite_non_negative",
]
