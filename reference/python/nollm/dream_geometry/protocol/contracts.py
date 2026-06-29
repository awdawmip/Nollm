"""Stable DG0 protocol contracts for Dream Geometry V2.

Allowed: immutable names, states, object ownership, and invariant anchors.
Forbidden: V1 model imports, runtime behavior, real memory access, OpenClaw
access, natural language interpretation, or geometry algorithms.
"""

from dataclasses import dataclass
from enum import Enum


class GrowthBasis(Enum):
    """Permitted basis labels for a proposed growth step."""

    explicit_in_shard = "explicit_in_shard"
    deterministic_projection = "deterministic_projection"
    backed_by_other_shard = "backed_by_other_shard"
    source_backed_rule = "source_backed_rule"
    provisional_llm_generalization = "provisional_llm_generalization"
    rejected = "rejected"


class ChartTransformState(Enum):
    """Lifecycle states for chart transform candidates."""

    proposed = "proposed"
    verified = "verified"
    requires_review = "requires_review"
    rejected = "rejected"
    conflict = "conflict"
    deferred = "deferred"


class TraceState(Enum):
    """Lifecycle states for field growth traces."""

    proposed = "proposed"
    accepted = "accepted"
    suppressed = "suppressed"
    superseded = "superseded"
    archived = "archived"


class CoverState(Enum):
    """Lifecycle states for coarse covers."""

    candidate = "candidate"
    stable = "stable"
    crystallized = "crystallized"
    deprecated = "deprecated"
    conflicted = "conflicted"


class KernelDirection(Enum):
    """Directed coverage-kernel directions."""

    fine_to_coarse = "fine_to_coarse"
    coarse_to_fine = "coarse_to_fine"


class ModuleName(Enum):
    """Dream Geometry V2 module names."""

    protocol = "protocol"
    evidence = "evidence"
    geometry = "geometry"
    field = "field"
    cortex = "cortex"
    recall = "recall"
    adapters = "adapters"
    validation = "validation"


class ObjectKind(Enum):
    """Stable V2 object kinds."""

    dream_shard = "dream_shard"
    growth_proposal = "growth_proposal"
    query_probe = "query_probe"
    local_chart = "local_chart"
    chart_transform = "chart_transform"
    coverage_kernel = "coverage_kernel"
    growth_trace = "growth_trace"
    coarse_cover = "coarse_cover"
    gravity_snapshot = "gravity_snapshot"
    recall_digest = "recall_digest"
    ledger_event = "ledger_event"


@dataclass(frozen=True)
class ObjectOwnership:
    """Sovereign module ownership for one V2 object kind."""

    object_kind: ObjectKind
    owner: ModuleName
    durable: bool
    externally_visible: bool
    notes: str


@dataclass(frozen=True)
class DependencyRule:
    """One executable dependency rule between V2 modules."""

    importer: ModuleName
    imported: ModuleName
    allowed: bool
    rationale: str


@dataclass(frozen=True)
class Invariant:
    """Stable invariant anchor for future enforcement."""

    identifier: str
    statement: str
    enforcement_layer: ModuleName


OBJECT_OWNERSHIP: tuple[ObjectOwnership, ...] = (
    ObjectOwnership(ObjectKind.dream_shard, ModuleName.evidence, True, True, "Durable original evidence."),
    ObjectOwnership(ObjectKind.ledger_event, ModuleName.evidence, True, True, "Durable audit event."),
    ObjectOwnership(ObjectKind.growth_proposal, ModuleName.cortex, False, False, "Cortex candidate, not fact confirmation."),
    ObjectOwnership(ObjectKind.query_probe, ModuleName.cortex, False, False, "Temporary read-side object."),
    ObjectOwnership(ObjectKind.local_chart, ModuleName.geometry, False, False, "Geometry-owned local chart."),
    ObjectOwnership(ObjectKind.chart_transform, ModuleName.geometry, False, False, "Verified transform candidate state belongs to geometry."),
    ObjectOwnership(ObjectKind.coverage_kernel, ModuleName.geometry, False, False, "Directed kernel, not externally visible in DG0."),
    ObjectOwnership(ObjectKind.growth_trace, ModuleName.field, False, False, "Field trace derived from evidence-backed proposal."),
    ObjectOwnership(ObjectKind.coarse_cover, ModuleName.field, False, False, "Field cover, not evidence ownership."),
    ObjectOwnership(ObjectKind.gravity_snapshot, ModuleName.field, False, False, "Internal Field/Core potential only."),
    ObjectOwnership(ObjectKind.recall_digest, ModuleName.recall, False, True, "Read result with evidence fallback."),
)


INVARIANTS: tuple[Invariant, ...] = (
    Invariant("I-V2-001", "Original Evidence must not be replaced or silently overwritten by Cover, Trace, or Gravity.", ModuleName.evidence),
    Invariant("I-V2-002", "Cortex may propose semantics but must not confirm facts, place cells, or mutate Field directly.", ModuleName.cortex),
    Invariant("I-V2-003", "Geometry must not depend on natural language, LLMs, OpenClaw, runtime, or legacy recall.", ModuleName.geometry),
    Invariant("I-V2-004", "Coverage must use directed K_up and K_down; it must not collapse into undirected parent-child edges.", ModuleName.geometry),
    Invariant("I-V2-005", "Gravity is Field/Core internal and must not be an external query parameter or named index.", ModuleName.field),
    Invariant("I-V2-006", "Query Probe is temporary by default and must not be silently persisted as Evidence.", ModuleName.cortex),
    Invariant("I-V2-007", "Unverified Chart Transform must not support atlas merge or recall identity inference.", ModuleName.geometry),
    Invariant("I-V2-008", "Validation must not enter production paths or write production state.", ModuleName.validation),
    Invariant("I-V2-009", "Adapter must not define, recompute, or bypass Geometry or Field rules.", ModuleName.adapters),
    Invariant("I-V2-010", "V1 legacy and V2 must remain import-isolated during DG0.", ModuleName.protocol),
)


__all__ = [
    "ChartTransformState",
    "CoverState",
    "DependencyRule",
    "GrowthBasis",
    "INVARIANTS",
    "Invariant",
    "KernelDirection",
    "ModuleName",
    "OBJECT_OWNERSHIP",
    "ObjectKind",
    "ObjectOwnership",
    "TraceState",
]
