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
    interpretation_record = "interpretation_record"
    revision_thread = "revision_thread"
    usage_state_transition = "usage_state_transition"
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


class OriginKind(Enum):
    """Opaque channel labels for memory substrate inputs."""

    user_utterance = "user_utterance"
    assistant_utterance = "assistant_utterance"
    tool_observation = "tool_observation"
    imported_text = "imported_text"
    internal_reflection = "internal_reflection"
    system_seed = "system_seed"
    unknown = "unknown"


class UsageState(Enum):
    """Current use posture, not truth or authentication."""

    tentative = "tentative"
    active = "active"
    retired = "retired"
    rejected = "rejected"


class InterpretationKind(Enum):
    """Externally supplied interpretation record kinds."""

    summary = "summary"
    classification = "classification"
    relation = "relation"
    growth_hint = "growth_hint"
    constraint = "constraint"
    other = "other"


class InterpretationAuthoringMode(Enum):
    """How an interpretation statement was supplied."""

    user_stated = "user_stated"
    llm_proposed = "llm_proposed"
    deterministic_projection = "deterministic_projection"
    imported_annotation = "imported_annotation"
    unknown = "unknown"


class RevisionRelation(Enum):
    """Explicit revision relation labels."""

    supersedes = "supersedes"
    withdraws = "withdraws"
    clarifies = "clarifies"
    coexists = "coexists"
    conflicts = "conflicts"


class LedgerEventKind(Enum):
    """Memory substrate ledger event kinds."""

    shard_recorded = "shard_recorded"
    interpretation_recorded = "interpretation_recorded"
    revision_thread_recorded = "revision_thread_recorded"
    usage_state_transition_recorded = "usage_state_transition_recorded"


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
    ObjectOwnership(ObjectKind.interpretation_record, ModuleName.evidence, True, True, "Durable externally supplied interpretation."),
    ObjectOwnership(ObjectKind.revision_thread, ModuleName.evidence, True, True, "Durable explicit revision relation thread."),
    ObjectOwnership(ObjectKind.usage_state_transition, ModuleName.evidence, True, True, "Durable usage-state transition."),
    ObjectOwnership(ObjectKind.ledger_event, ModuleName.evidence, True, True, "Durable audit event."),
    ObjectOwnership(ObjectKind.growth_proposal, ModuleName.cortex, True, False, "Cortex compiled proposal, not fact confirmation."),
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


DG2_FIELD_INVARIANTS: tuple[Invariant, ...] = (
    Invariant("I-V2-011", "Field propagates only through supplied, DG1-confirmed directed coverage distributions; it must not create nearest-center parent links.", ModuleName.field),
    Invariant("I-V2-012", "Every propagation conserves parent trace mass after explicit residual accounting.", ModuleName.field),
    Invariant("I-V2-013", "Every derived Trace and Cover preserves origin shard, proposal, basis, support, and geometry provenance.", ModuleName.field),
    Invariant("I-V2-014", "provisional_llm_generalization cannot become accepted, stable, or crystallized by Field alone.", ModuleName.field),
    Invariant("I-V2-015", "Field cannot write, replace, or delete Evidence, Card, Ledger, or original Trace inputs.", ModuleName.field),
    Invariant("I-V2-016", "Stable Cover requires explicit multi-support and anti-black-hole eligibility under a versioned policy.", ModuleName.field),
    Invariant("I-V2-017", "Gravity Snapshot is internal Field state and cannot be accepted as an external anchor, index, or query parameter.", ModuleName.field),
    Invariant("I-V2-018", "Trace compaction is lossless and reversible; it cannot merge across origin, basis, axis, state, geometry, residual, or support boundaries.", ModuleName.field),
)


DE1_MEMORY_SUBSTRATE_INVARIANTS: tuple[Invariant, ...] = (
    Invariant("I-V2-019", "DreamShard preserves original expression, origin, and temporal context; later interpretation, state, or revision cannot replace them.", ModuleName.evidence),
    Invariant("I-V2-020", "Interpretation is a separate epistemic object and must not be silently promoted to DreamShard, confirmed fact, or Field placement.", ModuleName.evidence),
    Invariant("I-V2-021", "UsageState denotes current use posture, not truth, authentication, or permanent human confirmation.", ModuleName.evidence),
    Invariant("I-V2-022", "Revision relations are explicit and do not automatically determine a unique current truth or mutate member content.", ModuleName.evidence),
    Invariant("I-V2-023", "Ledger is an append-only memory-history spine within the DE1 API, not a cryptographic anti-tamper or authorization mechanism.", ModuleName.evidence),
    Invariant("I-V2-024", "Evidence persistence is file-first and must not depend on Geometry, Field, Cortex, Recall, Adapter, V1, OpenClaw, runtime, database, or vector search.", ModuleName.evidence),
    Invariant("I-V2-025", "Relative-time expressions are preserved with optional reference instants; Evidence must not interpret them as absolute event facts.", ModuleName.evidence),
)


DR1_RECALL_RESOLVER_INVARIANTS: tuple[Invariant, ...] = (
    Invariant("I-V2-029", "RecallDigest is ephemeral, read-only, and must not be persisted as Evidence, Cortex, Field, Adapter, runtime, or ledger state.", ModuleName.recall),
    Invariant("I-V2-030", "Recall Resolver may consume only supplied Query Probe, RecallUniverse, and read-only DE1/DC1/DG1/DG2 objects; it must not compile, propagate, place, or mutate upstream objects.", ModuleName.recall),
    Invariant("I-V2-031", "Recall seeding requires exact structural projection from explicit query atoms to stored proposal steps and accepted traces; no NLP, semantic search, embedding, or vector similarity may fill projection gaps.", ModuleName.recall),
    Invariant("I-V2-032", "Directed K_up and K_down traversal preserves coverage direction and residual diagnostics; residual mass is reported, not inferred away.", ModuleName.recall),
    Invariant("I-V2-033", "DreamShard remains the primary evidence fallback; Interpretation, Revision, and UsageState provide context and qualification, not truth override or source replacement.", ModuleName.recall),
    Invariant("I-V2-034", "UsageState is a recall qualification posture only; active and tentative may be primary evidence by policy, while retired and rejected are context-only unless explicitly included as context.", ModuleName.recall),
    Invariant("I-V2-035", "Gravity may be used only as an internal deterministic tie-break over already eligible structural candidates; it is not an external selector, anchor, query parameter, or source of evidence.", ModuleName.recall),
    Invariant("I-V2-036", "Legacy DC1 proposal records are read-only context and cannot seed DR1 recall unless admitted through the current DC1 contract.", ModuleName.recall),
)


__all__ = [
    "ChartTransformState",
    "CoverState",
    "DE1_MEMORY_SUBSTRATE_INVARIANTS",
    "DR1_RECALL_RESOLVER_INVARIANTS",
    "DG2_FIELD_INVARIANTS",
    "DependencyRule",
    "GrowthBasis",
    "INVARIANTS",
    "InterpretationAuthoringMode",
    "InterpretationKind",
    "Invariant",
    "KernelDirection",
    "LedgerEventKind",
    "ModuleName",
    "OBJECT_OWNERSHIP",
    "ObjectKind",
    "ObjectOwnership",
    "OriginKind",
    "RevisionRelation",
    "TraceState",
    "UsageState",
]
