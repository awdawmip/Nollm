"""DR1 Recall Resolver immutable value objects.

Allowed: read-only contracts for deterministic recall digests.
Forbidden: persistence, runtime access, OpenClaw, adapters, NLP, semantic search,
filesystem, network, subprocess, or upstream mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from nollm.dream_geometry.cortex.types import CompiledGrowthProposal
from nollm.dream_geometry.evidence import InterpretationRecord, RevisionThread
from nollm.dream_geometry.field.types import CoarseCover, GravitySnapshot, GrowthTrace, TraceCompaction, VerifiedChartLink
from nollm.dream_geometry.geometry.coverage import CoverageDistribution


class ProposalAdmission(Enum):
    current_accepted = "current_accepted"
    legacy_dc1_read_only = "legacy_dc1_read_only"


class RecallDigestStatus(Enum):
    resolved = "resolved"
    deferred = "deferred"


@dataclass(frozen=True)
class ProposalReadRecord:
    proposal: CompiledGrowthProposal
    admission: ProposalAdmission
    source_ref: str


@dataclass(frozen=True)
class ResolvedRelativeSpan:
    query_axis_id: str
    query_expression: str
    resolved_axis_id: str
    resolved_expression: str
    reference_instant: str
    resolver_basis: str


@dataclass(frozen=True)
class RuntimeTimeResolution:
    spans: tuple[ResolvedRelativeSpan, ...]
    complete: bool


@dataclass(frozen=True)
class RecallPolicy:
    min_required_axis_matches: int = 2
    include_tentative: bool = True
    include_retired_context: bool = False
    include_rejected_context: bool = False
    include_legacy_context: bool = False
    apply_gravity_tie_break: bool = True


@dataclass(frozen=True)
class RecallUniverse:
    proposal_records: tuple[ProposalReadRecord, ...]
    traces: tuple[GrowthTrace, ...]
    covers: tuple[CoarseCover, ...]
    coverage_up: tuple[CoverageDistribution, ...] = ()
    coverage_down: tuple[CoverageDistribution, ...] = ()
    verified_chart_links: tuple[VerifiedChartLink, ...] = ()
    gravity_snapshot: GravitySnapshot | None = None
    trace_compactions: tuple[TraceCompaction, ...] = ()
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
    cover_id: str
    source_cell_ref: str
    direction: str
    target_cell_refs: tuple[str, ...]
    residual_mass: float
    residual_reasons: tuple[str, ...]


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


@dataclass(frozen=True)
class RecallDigest:
    digest_id: str
    query_probe_id: str
    status: RecallDigestStatus
    ephemeral: bool
    items: tuple[RecallResultItem, ...]
    traversal_records: tuple[TraversalRecord, ...]
    warnings: tuple[str, ...]
    discarded: tuple[str, ...]
    unresolved_residual_mass: float
    gravity_guidance_applied: bool
    metadata: dict[str, Any]


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
    "ResolvedRelativeSpan",
    "RuntimeTimeResolution",
    "TraceSemanticProjection",
    "TraversalRecord",
]
