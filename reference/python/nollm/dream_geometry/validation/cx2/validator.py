"""Deterministic CX2 Cortex Action Plan validator."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any

from .types import (
    ADMISSION_FIELDS,
    ASSEMBLY_FIELDS,
    CAPTURE_FIELDS,
    FORBIDDEN_FIELDS,
    PLAN_FIELDS,
    PROMOTION_FIELDS,
    RECALL_FIELDS,
    VIEW_FIELDS,
    AdmissionRequestRef,
    AdmissionState,
    AssemblyDeclarer,
    CaptureRef,
    CortexActionPlan,
    CortexActionPlanSummary,
    CX2PlanValidationError,
    DecisionSource,
    DerivedViewRef,
    ExplicitAssembly,
    MemoryIntent,
    NonInference,
    PersistenceState,
    PlanIntent,
    PromotionDecision,
    PromotionDecisionValue,
    PromotionReason,
    RecallRequest,
    UsageState,
    VisibilityScope,
)


REQUIRED_NON_INFERENCES = tuple(item.value for item in NonInference)
FORBIDDEN_AUTOMATION_VALUES = frozenset(
    {
        "auto_admit",
        "model_important",
        "global_discovery",
        "global_search",
        "vector_query",
        "semantic_embedding",
        "auto_anchor",
        "auto_axis",
        "auto_chart",
        "auto_cell",
        "auto_cover",
        "auto_parent",
        "truth_score",
        "importance_score",
    }
)


def validate_cortex_action_plan(plan: CortexActionPlan | Mapping[str, Any]) -> CortexActionPlanSummary:
    """Validate a declaration-only Cortex plan and return a canonical summary."""

    try:
        _reject_forbidden_payload(plan)
        normalized = _coerce_plan(plan)
        _validate_plan_shape(normalized)
        _validate_identity(normalized)
        _validate_capture_refs(normalized.capture_refs)
        promoted_decisions = _validate_promotion_decisions(normalized.promotion_decisions)
        _validate_admission_requests(normalized.admission_request_refs, promoted_decisions)
        assembly_ids = _validate_explicit_assembly(normalized.explicit_assembly)
        _validate_recall_request(normalized.recall_request)
        _validate_derived_views(normalized.derived_views)
        _validate_non_inferences(normalized.non_inferences)
        _validate_intent_specific(normalized)
        _validate_duplicate_ids(normalized)
    except CX2PlanValidationError:
        raise
    except (TypeError, AttributeError, KeyError, IndexError, ValueError, AssertionError) as exc:
        _fail("CX2_INVALID_PLAN", "plan input shape is invalid")

    return CortexActionPlanSummary(
        plan_id=normalized.plan_id,
        intent=normalized.intent,
        capture_ref_count=len(normalized.capture_refs),
        promotion_decision_count=len(normalized.promotion_decisions),
        admission_request_count=len(normalized.admission_request_refs),
        explicit_assembly_admission_ids=assembly_ids,
        has_recall_request=normalized.recall_request is not None,
        derived_view_count=len(normalized.derived_views),
        non_inferences=normalized.non_inferences,
    )


def _coerce_plan(value: CortexActionPlan | Mapping[str, Any]) -> CortexActionPlan:
    if isinstance(value, CortexActionPlan):
        return value
    if not isinstance(value, Mapping):
        _fail("CX2_INVALID_PLAN", "plan must be a CortexActionPlan value or mapping")
    _reject_unknown_fields(value, PLAN_FIELDS, "CX2_INVALID_PLAN", "plan contains unsupported fields")

    return CortexActionPlan(
        plan_kind=str(value.get("plan_kind", "")),
        plan_version=str(value.get("plan_version", "")),
        plan_id=str(value.get("plan_id", "")),
        intent=str(value.get("intent", "")),
        capture_refs=tuple(
            _coerce_item(item, CaptureRef, CAPTURE_FIELDS, "CX2_INVALID_PLAN")
            for item in _collection(value, "capture_refs", "CX2_INVALID_PLAN", "capture refs must be an immutable tuple of CaptureRef values")
        ),
        promotion_decisions=tuple(
            _coerce_item(item, PromotionDecision, PROMOTION_FIELDS, "CX2_INVALID_PROMOTION")
            for item in _collection(
                value,
                "promotion_decisions",
                "CX2_INVALID_PROMOTION",
                "promotion decisions must be an immutable tuple of PromotionDecision values",
            )
        ),
        admission_request_refs=tuple(
            _coerce_item(item, AdmissionRequestRef, ADMISSION_FIELDS, "CX2_INVALID_ADMISSION_REQUEST")
            for item in _collection(
                value,
                "admission_request_refs",
                "CX2_INVALID_ADMISSION_REQUEST",
                "admission request refs must be an immutable tuple of AdmissionRequestRef values",
            )
        ),
        explicit_assembly=_coerce_optional_item(
            value.get("explicit_assembly"), ExplicitAssembly, ASSEMBLY_FIELDS, "CX2_INVALID_EXPLICIT_ASSEMBLY"
        ),
        recall_request=_coerce_optional_item(value.get("recall_request"), RecallRequest, RECALL_FIELDS, "CX2_INVALID_RECALL_REQUEST"),
        derived_views=tuple(
            _coerce_item(item, DerivedViewRef, VIEW_FIELDS, "CX2_FORBIDDEN_DG6_INFERENCE")
            for item in _collection(value, "derived_views", "CX2_INVALID_PLAN", "derived views must be an immutable tuple of DerivedViewRef values")
        ),
        non_inferences=tuple(
            _string_collection(value, "non_inferences", "CX2_INVALID_PLAN", "non-inferences must be an immutable tuple of strings")
        ),
    )


def _coerce_item(value: object, cls: type, fields: frozenset[str], reason_code: str):
    if isinstance(value, cls):
        return value
    if not isinstance(value, Mapping):
        _fail(reason_code, "plan item must be a mapping or immutable value")
    _reject_unknown_fields(value, fields, reason_code, "plan item contains unsupported fields")
    kwargs = {field: value.get(field) for field in fields}
    if cls in (CaptureRef, PromotionDecision, AdmissionRequestRef, DerivedViewRef):
        kwargs = {key: "" if item is None else item for key, item in kwargs.items()}
    if cls is CaptureRef and value.get("shard_id") is None:
        kwargs["shard_id"] = None
    if cls is PromotionDecision:
        kwargs["reasons"] = tuple(
            _string_collection(value, "reasons", "CX2_INVALID_PROMOTION", "promotion reasons must be an immutable tuple of strings")
        )
    if cls is ExplicitAssembly:
        kwargs["admission_ids"] = tuple(
            _string_collection(value, "admission_ids", "CX2_INVALID_EXPLICIT_ASSEMBLY", "explicit assembly admission ids must be an immutable tuple of strings")
        )
        kwargs["declared_by"] = "" if value.get("declared_by") is None else value.get("declared_by")
        kwargs["purpose"] = "" if value.get("purpose") is None else value.get("purpose")
    if cls is RecallRequest:
        kwargs["max_cards"] = value.get("max_cards", 0)
        kwargs["max_layers"] = value.get("max_layers", 0)
    return cls(**kwargs)


def _coerce_optional_item(value: object, cls: type, fields: frozenset[str], reason_code: str):
    if value is None:
        return None
    return _coerce_item(value, cls, fields, reason_code)


def _collection(value: Mapping[str, Any], field: str, reason_code: str, message: str) -> tuple[object, ...] | list[object]:
    item = value.get(field, ())
    if not isinstance(item, (tuple, list)):
        _fail(reason_code, message)
    return item


def _string_collection(value: Mapping[str, Any], field: str, reason_code: str, message: str) -> tuple[str, ...]:
    item = value.get(field, ())
    if not isinstance(item, (tuple, list)):
        _fail(reason_code, message)
    if any(not isinstance(entry, str) for entry in item):
        _fail(reason_code, message)
    return tuple(item)


def _validate_plan_shape(plan: CortexActionPlan) -> None:
    _validate_typed_tuple(plan.capture_refs, CaptureRef, "CX2_INVALID_PLAN", "capture refs must be an immutable tuple of CaptureRef values")
    _validate_typed_tuple(
        plan.promotion_decisions,
        PromotionDecision,
        "CX2_INVALID_PROMOTION",
        "promotion decisions must be an immutable tuple of PromotionDecision values",
    )
    _validate_typed_tuple(
        plan.admission_request_refs,
        AdmissionRequestRef,
        "CX2_INVALID_ADMISSION_REQUEST",
        "admission request refs must be an immutable tuple of AdmissionRequestRef values",
    )
    _validate_typed_tuple(plan.derived_views, DerivedViewRef, "CX2_INVALID_PLAN", "derived views must be an immutable tuple of DerivedViewRef values")
    _validate_typed_tuple(plan.non_inferences, str, "CX2_INVALID_PLAN", "non-inferences must be an immutable tuple of strings")
    if plan.explicit_assembly is not None and not isinstance(plan.explicit_assembly, ExplicitAssembly):
        _fail("CX2_INVALID_EXPLICIT_ASSEMBLY", "explicit assembly must be ExplicitAssembly or None")
    if plan.recall_request is not None and not isinstance(plan.recall_request, RecallRequest):
        _fail("CX2_INVALID_RECALL_REQUEST", "recall request must be RecallRequest or None")
    for decision in plan.promotion_decisions:
        _validate_typed_tuple(decision.reasons, str, "CX2_INVALID_PROMOTION", "promotion reasons must be an immutable tuple of strings")
    if plan.explicit_assembly is not None:
        _validate_typed_tuple(
            plan.explicit_assembly.admission_ids,
            str,
            "CX2_INVALID_EXPLICIT_ASSEMBLY",
            "explicit assembly admission ids must be an immutable tuple of strings",
        )


def _validate_typed_tuple(value: object, item_type: type, reason_code: str, message: str) -> None:
    if not isinstance(value, tuple) or any(not isinstance(item, item_type) for item in value):
        _fail(reason_code, message)


def _validate_identity(plan: CortexActionPlan) -> None:
    if plan.plan_kind != "nollm_cortex_action_plan" or plan.plan_version != "1":
        _fail("CX2_INVALID_PLAN", "plan kind and version must be nollm_cortex_action_plan v1")
    if not _is_id(plan.plan_id, "cx2_"):
        _fail("CX2_INVALID_PLAN", "plan id must be a non-empty cx2_ identifier")
    if plan.intent not in _enum_values(PlanIntent):
        _fail("CX2_INVALID_PLAN", "plan intent is not supported")


def _validate_capture_refs(captures: tuple[CaptureRef, ...]) -> None:
    for capture in captures:
        if not _is_id(capture.capture_id, "cap_"):
            _fail("CX2_INVALID_REFERENCE", "capture ref must have a cap_ id")
        if capture.shard_id is not None and not _is_id(capture.shard_id, "shard_"):
            _fail("CX2_INVALID_REFERENCE", "capture shard ref must be empty or shard_ id")
        if capture.persistence_state not in _enum_values(PersistenceState):
            _fail("CX2_INVALID_STATE_SEPARATION", "capture persistence state is invalid")
        if capture.admission_state not in _enum_values(AdmissionState):
            _fail("CX2_INVALID_STATE_SEPARATION", "capture admission state is invalid")
        if capture.usage_state not in _enum_values(UsageState):
            _fail("CX2_INVALID_STATE_SEPARATION", "capture usage state is invalid")
        if capture.visibility_scope not in _enum_values(VisibilityScope):
            _fail("CX2_INVALID_STATE_SEPARATION", "capture visibility scope is invalid")
        if capture.persistence_state == PersistenceState.EPHEMERAL.value and (
            capture.shard_id is not None
            or capture.admission_state != AdmissionState.NONE.value
            or capture.usage_state != UsageState.TENTATIVE.value
            or capture.visibility_scope != VisibilityScope.CURRENT_TURN.value
        ):
            _fail("CX2_INVALID_STATE_SEPARATION", "ephemeral capture must be current-turn tentative and unadmitted")


def _validate_promotion_decisions(decisions: tuple[PromotionDecision, ...]) -> dict[str, PromotionDecision]:
    result: dict[str, PromotionDecision] = {}
    for decision in decisions:
        if not _is_id(decision.decision_id, "pmd_") or not _is_id(decision.candidate_id, "dac_") or not _is_id(decision.shard_id, "shard_"):
            _fail("CX2_INVALID_PROMOTION", "promotion decision must bind pmd_, dac_, and shard_ ids")
        if decision.decision not in _enum_values(PromotionDecisionValue):
            _fail("CX2_INVALID_PROMOTION", "promotion decision value is invalid")
        if decision.decided_by not in _enum_values(DecisionSource):
            _fail("CX2_INVALID_PROMOTION", "promotion decided_by is invalid")
        if decision.decision == PromotionDecisionValue.PROMOTE.value and not decision.reasons:
            _fail("CX2_INVALID_PROMOTION", "promote decision must have at least one enumerable reason")
        for reason in decision.reasons:
            if reason not in _enum_values(PromotionReason):
                _fail("CX2_INVALID_PROMOTION", "promotion reason is not an allowed CX2 reason")
        result[decision.decision_id] = decision
    return result


def _validate_admission_requests(requests: tuple[AdmissionRequestRef, ...], decisions: dict[str, PromotionDecision]) -> None:
    referenced_decisions: set[str] = set()
    for request in requests:
        if not _is_id(request.request_id, "admreq_") or not _is_id(request.shard_id, "shard_"):
            _fail("CX2_INVALID_ADMISSION_REQUEST", "admission request must bind admreq_ and shard_ ids")
        decision = decisions.get(request.decision_id)
        if decision is None:
            _fail("CX2_INVALID_ADMISSION_REQUEST", "admission request references an unknown promotion decision")
        if decision.decision != PromotionDecisionValue.PROMOTE.value:
            _fail("CX2_INVALID_ADMISSION_REQUEST", "admission request can reference only promote decisions")
        if request.decision_id in referenced_decisions:
            _fail("CX2_INVALID_ADMISSION_REQUEST", "admission request decision refs must be unique within a plan")
        referenced_decisions.add(request.decision_id)
        if decision.decided_by == DecisionSource.CORTEX_SUGGESTION.value:
            _fail("CX2_INVALID_ADMISSION_REQUEST", "admission request requires a host, user, or human_operator promote decision")
        if request.shard_id != decision.shard_id:
            _fail("CX2_INVALID_ADMISSION_REQUEST", "admission request shard must match its promotion decision")
        if not _non_empty(request.proposal_ref) or not _non_empty(request.placement_plan_ref):
            _fail("CX2_INVALID_ADMISSION_REQUEST", "admission request needs opaque proposal and placement refs")


def _validate_explicit_assembly(assembly: ExplicitAssembly | None) -> tuple[str, ...]:
    if assembly is None:
        return ()
    ids = assembly.admission_ids
    if not ids or any(not _is_id(item, "adm_") for item in ids) or len(ids) != len(set(ids)):
        _fail("CX2_INVALID_EXPLICIT_ASSEMBLY", "explicit assembly admission ids must be non-empty, unique strings")
    if assembly.declared_by not in _enum_values(AssemblyDeclarer):
        _fail("CX2_INVALID_EXPLICIT_ASSEMBLY", "explicit assembly must be declared by host, user, or human_operator")
    if not _non_empty(assembly.purpose) or "inferred" in assembly.purpose.lower():
        _fail("CX2_INVALID_EXPLICIT_ASSEMBLY", "explicit assembly purpose must not claim inferred discovery")
    return ids


def _validate_recall_request(request: RecallRequest | None) -> None:
    if request is None:
        return
    if not _non_empty(request.query_ref) or not _non_empty(request.admitted_workset_ref):
        _fail("CX2_INVALID_RECALL_REQUEST", "recall request needs opaque query and explicit admitted workset refs")
    if "global" in request.admitted_workset_ref.lower() or "captured_pool" in request.admitted_workset_ref.lower():
        _fail("CX2_FORBIDDEN_AUTOMATION", "recall workset must not be global discovery or captured pool")
    if request.memory_intent not in _enum_values(MemoryIntent):
        _fail("CX2_INVALID_RECALL_REQUEST", "recall memory intent is invalid")
    if type(request.max_cards) is not int or type(request.max_layers) is not int or request.max_cards <= 0 or request.max_layers <= 0:
        _fail("CX2_INVALID_RECALL_REQUEST", "recall budgets must be positive non-boolean integers")


def _validate_derived_views(views: tuple[DerivedViewRef, ...]) -> None:
    for view in views:
        if view.view_kind != "dg6_compacted_view":
            _fail("CX2_FORBIDDEN_DG6_INFERENCE", "CX2 v1 allows only dg6_compacted_view derived views")
        if not _non_empty(view.view_ref):
            _fail("CX2_FORBIDDEN_DG6_INFERENCE", "DG6 verification view must have a non-empty opaque reference")
        if view.usage != "verification_only":
            _fail("CX2_FORBIDDEN_DG6_INFERENCE", "DG6 view may be used only for verification-only conformance language")


def _validate_non_inferences(non_inferences: tuple[str, ...]) -> None:
    if tuple(dict.fromkeys(non_inferences)) != non_inferences:
        _fail("CX2_INVALID_PLAN", "non-inferences must be unique and ordered")
    missing = [item for item in REQUIRED_NON_INFERENCES if item not in non_inferences]
    if missing:
        _fail("CX2_FORBIDDEN_AUTOMATION", "plan must explicitly list CX2 non-inference boundaries")
    for item in non_inferences:
        if item not in REQUIRED_NON_INFERENCES:
            _fail("CX2_FORBIDDEN_AUTOMATION", "plan contains unsupported non-inference language")


def _validate_intent_specific(plan: CortexActionPlan) -> None:
    if plan.intent == PlanIntent.CAPTURE_ONLY.value:
        if not plan.capture_refs or plan.admission_request_refs or plan.explicit_assembly or plan.recall_request:
            _fail("CX2_INVALID_PLAN", "capture_only plan may contain capture refs but no admission, assembly, or recall")
        if any(item.decision == PromotionDecisionValue.PROMOTE.value for item in plan.promotion_decisions):
            _fail("CX2_INVALID_PLAN", "capture_only plan must not contain promote decisions")
    if plan.intent == PlanIntent.ADMISSION.value:
        if not plan.promotion_decisions or not plan.admission_request_refs or plan.recall_request:
            _fail("CX2_INVALID_PLAN", "admission plan requires promotion and admission refs without recall")
    if plan.intent == PlanIntent.RECALL.value:
        if plan.explicit_assembly is None or plan.recall_request is None:
            _fail("CX2_INVALID_RECALL_REQUEST", "recall plan requires explicit finite assembly and recall request")
    if plan.intent == PlanIntent.MIXED_EXPLICIT.value:
        if not plan.capture_refs or not plan.promotion_decisions or not plan.admission_request_refs or plan.explicit_assembly is None or plan.recall_request is None:
            _fail("CX2_INVALID_PLAN", "mixed_explicit plan requires capture, promotion, admission, assembly, and recall declarations")


def _validate_duplicate_ids(plan: CortexActionPlan) -> None:
    ids: list[str] = [plan.plan_id]
    ids.extend(item.capture_id for item in plan.capture_refs)
    ids.extend(item.decision_id for item in plan.promotion_decisions)
    ids.extend(item.candidate_id for item in plan.promotion_decisions)
    ids.extend(item.request_id for item in plan.admission_request_refs)
    if len(ids) != len(set(ids)):
        _fail("CX2_INVALID_REFERENCE", "plan IDs must be unique and acyclic within their namespace")


def _reject_forbidden_payload(value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            _reject_forbidden_payload(getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_FIELDS:
                _fail(_forbidden_reason(key_text), f"field is forbidden in CortexActionPlan: {key_text}")
            if isinstance(item, str) and item in FORBIDDEN_AUTOMATION_VALUES:
                _fail(_forbidden_reason(item), f"forbidden automation value in CortexActionPlan: {item}")
            _reject_forbidden_payload(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _reject_forbidden_payload(item)
    elif isinstance(value, str) and value in FORBIDDEN_AUTOMATION_VALUES:
        _fail(_forbidden_reason(value), f"forbidden automation value in CortexActionPlan: {value}")


def _reject_unknown_fields(value: Mapping[str, Any], fields: frozenset[str], reason_code: str, message: str) -> None:
    unknown = set(str(key) for key in value) - fields
    if unknown:
        token = sorted(unknown)[0]
        if token in FORBIDDEN_FIELDS:
            _fail(_forbidden_reason(token), f"field is forbidden in CortexActionPlan: {token}")
        _fail(reason_code, message)


def _forbidden_reason(token: str) -> str:
    if token.startswith("dg6") or token in {"recall_filter", "recall_rank", "recall_source"}:
        return "CX2_FORBIDDEN_DG6_INFERENCE"
    if token in {"field_snapshot_payload", "admission_record_payload", "recall_result_payload"}:
        return "CX2_INVALID_PLAN"
    return "CX2_FORBIDDEN_AUTOMATION"


def _is_id(value: object, prefix: str) -> bool:
    return isinstance(value, str) and value.startswith(prefix) and len(value) > len(prefix)


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _enum_values(enum_type: type) -> frozenset[str]:
    return frozenset(item.value for item in enum_type)


def _fail(reason_code: str, message: str) -> None:
    raise CX2PlanValidationError(reason_code, message)


__all__ = ["REQUIRED_NON_INFERENCES", "validate_cortex_action_plan"]
