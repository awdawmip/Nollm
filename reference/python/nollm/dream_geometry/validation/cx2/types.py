"""Immutable CX2 Cortex Action Plan values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CX2PlanValidationError(ValueError):
    """Structured validation failure without traceback-shaped output."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class PlanIntent(str, Enum):
    CAPTURE_ONLY = "capture_only"
    ADMISSION = "admission"
    RECALL = "recall"
    MIXED_EXPLICIT = "mixed_explicit"


class PersistenceState(str, Enum):
    EPHEMERAL = "ephemeral"
    CAPTURED = "captured"
    PERSISTENT = "persistent"


class AdmissionState(str, Enum):
    NONE = "none"
    DEFERRED = "deferred"
    CANDIDATE = "candidate"
    PROMOTION_REQUESTED = "promotion_requested"
    ADMITTED = "admitted"
    DO_NOT_ADMIT = "do_not_admit"


class UsageState(str, Enum):
    TENTATIVE = "tentative"
    ACTIVE = "active"
    RETIRED = "retired"
    REJECTED = "rejected"


class VisibilityScope(str, Enum):
    CURRENT_TURN = "current_turn"
    SESSION_WINDOW = "session_window"
    SOURCE_WINDOW = "source_window"
    PERSISTENT_EXPLICIT = "persistent_explicit"


class PromotionDecisionValue(str, Enum):
    PROMOTE = "promote"
    DEFER = "defer"
    DO_NOT_ADMIT = "do_not_admit"


class PromotionReason(str, Enum):
    EXPLICIT_PIN = "explicit_pin"
    TASK_DEPENDENCY = "task_dependency"
    SOURCE_BACKED_FACT = "source_backed_fact"
    REVISION_EVENT = "revision_event"
    REUSE_OBSERVED = "reuse_observed"
    SESSION_CLOSURE = "session_closure"
    RECALL_MISS_RECEIPT = "recall_miss_receipt"
    MANUAL_BATCH_SELECTION = "manual_batch_selection"


class DecisionSource(str, Enum):
    HOST_RULE = "host_rule"
    USER = "user"
    HUMAN_OPERATOR = "human_operator"
    CORTEX_SUGGESTION = "cortex_suggestion"


class AssemblyDeclarer(str, Enum):
    HOST = "host"
    USER = "user"
    HUMAN_OPERATOR = "human_operator"


class MemoryIntent(str, Enum):
    RECALL_FOCUS = "recall_focus"
    ORIENTATION = "orientation"
    VERIFICATION = "verification"


class NonInference(str, Enum):
    NO_AUTOMATIC_ADMISSION = "no_automatic_admission"
    NO_GLOBAL_DISCOVERY = "no_global_discovery"
    NO_ANCHOR_CREATION = "no_anchor_creation"
    NO_TRUTH_CONFIRMATION = "no_truth_confirmation"
    NO_DG6_RECALL_INFLUENCE = "no_dg6_recall_influence"


@dataclass(frozen=True, slots=True)
class CaptureRef:
    capture_id: str
    shard_id: str | None
    persistence_state: str
    admission_state: str
    usage_state: str
    visibility_scope: str


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    decision_id: str
    candidate_id: str
    shard_id: str
    decision: str
    reasons: tuple[str, ...]
    decided_by: str


@dataclass(frozen=True, slots=True)
class AdmissionRequestRef:
    request_id: str
    decision_id: str
    shard_id: str
    proposal_ref: str
    placement_plan_ref: str


@dataclass(frozen=True, slots=True)
class ExplicitAssembly:
    admission_ids: tuple[str, ...]
    declared_by: str
    purpose: str


@dataclass(frozen=True, slots=True)
class RecallRequest:
    query_ref: str
    memory_intent: str
    admitted_workset_ref: str
    max_cards: int
    max_layers: int


@dataclass(frozen=True, slots=True)
class DerivedViewRef:
    view_kind: str
    view_ref: str
    usage: str


@dataclass(frozen=True, slots=True)
class CortexActionPlan:
    plan_kind: str
    plan_version: str
    plan_id: str
    intent: str
    capture_refs: tuple[CaptureRef, ...] = ()
    promotion_decisions: tuple[PromotionDecision, ...] = ()
    admission_request_refs: tuple[AdmissionRequestRef, ...] = ()
    explicit_assembly: ExplicitAssembly | None = None
    recall_request: RecallRequest | None = None
    derived_views: tuple[DerivedViewRef, ...] = ()
    non_inferences: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CortexActionPlanSummary:
    plan_id: str
    intent: str
    capture_ref_count: int
    promotion_decision_count: int
    admission_request_count: int
    explicit_assembly_admission_ids: tuple[str, ...]
    has_recall_request: bool
    derived_view_count: int
    non_inferences: tuple[str, ...]


FORBIDDEN_FIELDS = frozenset(
    {
        "semantic_embedding",
        "vector_query",
        "similarity_threshold",
        "global_search",
        "auto_anchor",
        "auto_axis",
        "auto_chart",
        "auto_cell",
        "auto_cover",
        "auto_parent",
        "truth_score",
        "importance_score",
        "auto_admit",
        "runtime_command",
        "network_endpoint",
        "cache_key",
        "database_query",
        "field_snapshot_payload",
        "admission_record_payload",
        "recall_result_payload",
    }
)

PLAN_FIELDS = frozenset(CortexActionPlan.__dataclass_fields__)
CAPTURE_FIELDS = frozenset(CaptureRef.__dataclass_fields__)
PROMOTION_FIELDS = frozenset(PromotionDecision.__dataclass_fields__)
ADMISSION_FIELDS = frozenset(AdmissionRequestRef.__dataclass_fields__)
ASSEMBLY_FIELDS = frozenset(ExplicitAssembly.__dataclass_fields__)
RECALL_FIELDS = frozenset(RecallRequest.__dataclass_fields__)
VIEW_FIELDS = frozenset(DerivedViewRef.__dataclass_fields__)

JsonLike = dict[str, Any]

__all__ = [
    "AdmissionRequestRef",
    "AdmissionState",
    "AssemblyDeclarer",
    "CaptureRef",
    "CortexActionPlan",
    "CortexActionPlanSummary",
    "CX2PlanValidationError",
    "DecisionSource",
    "DerivedViewRef",
    "ExplicitAssembly",
    "FORBIDDEN_FIELDS",
    "MemoryIntent",
    "NonInference",
    "PersistenceState",
    "PlanIntent",
    "PromotionDecision",
    "PromotionDecisionValue",
    "PromotionReason",
    "RecallRequest",
    "UsageState",
    "VisibilityScope",
]
