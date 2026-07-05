"""HX1 host binding preflight."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from nollm.dream_geometry.batch_admission import PromotionDecider, PromotionDecisionKind
from nollm.dream_geometry.capture import VisibilityScope
from nollm.dream_geometry.validation.cx2 import validate_cortex_action_plan
from nollm.dream_geometry.validation.cx2.types import (
    AdmissionRequestRef,
    CaptureRef,
    CortexActionPlan,
    DerivedViewRef,
    ExplicitAssembly,
    PromotionDecision,
    RecallRequest,
)

from .errors import HX1ExecutionError, stable_message
from .types import HostAdmissionBinding, HostExecutionContext, HostPlanBindings


FORBIDDEN_WORK_DIRS = ("field", "assembly", "recall", "cache", "database", "global-field")


def preflight_host_plan(plan: CortexActionPlan | Mapping[str, Any], bindings: HostPlanBindings, context: HostExecutionContext):
    try:
        summary = validate_cortex_action_plan(plan)
    except Exception as exc:
        raise HX1ExecutionError("HX1_INVALID_PLAN", stable_message(exc)) from exc
    normalized = plan if isinstance(plan, CortexActionPlan) else _coerced_plan(plan)
    _validate_context(context)
    _validate_binding_shape(bindings)
    _validate_capture_bindings(normalized, bindings)
    _validate_admission_bindings(normalized, bindings)
    _validate_recall_bindings(normalized, bindings)
    _validate_dg6_bindings(normalized, bindings)
    return summary, normalized


def _coerced_plan(plan: Mapping[str, Any]) -> CortexActionPlan:
    assembly = plan.get("explicit_assembly")
    recall = plan.get("recall_request")
    return CortexActionPlan(
        str(plan.get("plan_kind", "")),
        str(plan.get("plan_version", "")),
        str(plan.get("plan_id", "")),
        str(plan.get("intent", "")),
        capture_refs=tuple(CaptureRef(**item) for item in plan.get("capture_refs", ())),
        promotion_decisions=tuple(PromotionDecision(**{**item, "reasons": tuple(item.get("reasons", ()))}) for item in plan.get("promotion_decisions", ())),
        admission_request_refs=tuple(AdmissionRequestRef(**item) for item in plan.get("admission_request_refs", ())),
        explicit_assembly=None if assembly is None else ExplicitAssembly(tuple(assembly.get("admission_ids", ())), assembly.get("declared_by", ""), assembly.get("purpose", "")),
        recall_request=None if recall is None else RecallRequest(**recall),
        derived_views=tuple(DerivedViewRef(**item) for item in plan.get("derived_views", ())),
        non_inferences=tuple(plan.get("non_inferences", ())),
    )


def _validate_context(context: HostExecutionContext) -> None:
    if not isinstance(context, HostExecutionContext):
        raise HX1ExecutionError("HX1_INVALID_CONTEXT", "host execution context is invalid")
    work_root = Path(context.work_root)
    cwd = Path.cwd().resolve()
    try:
        resolved = work_root.resolve()
    except Exception as exc:
        raise HX1ExecutionError("HX1_INVALID_CONTEXT", "work root is invalid") from exc
    if resolved == cwd or (resolved / ".git").exists():
        raise HX1ExecutionError("HX1_WORK_ROOT_REJECTED", "work root must be an explicit owned directory outside repo root")
    if work_root.exists() and not work_root.is_dir():
        raise HX1ExecutionError("HX1_WORK_ROOT_REJECTED", "work root must be a directory")
    for name in FORBIDDEN_WORK_DIRS:
        if (work_root / name).exists():
            raise HX1ExecutionError("HX1_WORK_ROOT_REJECTED", "work root contains a forbidden HX1 output directory")


def _validate_binding_shape(bindings: HostPlanBindings) -> None:
    if not isinstance(bindings, HostPlanBindings):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "host bindings must be HostPlanBindings")
    for collection, cls, label in (
        (bindings.capture_bindings, object, "capture bindings"),
        (bindings.admission_bindings, HostAdmissionBinding, "admission bindings"),
    ):
        if not isinstance(collection, tuple):
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", f"{label} must be immutable tuples")
    _reject_duplicate([binding.capture_id for binding in bindings.capture_bindings], "capture binding keys")
    _reject_duplicate([binding.request_id for binding in bindings.admission_bindings], "admission binding keys")
    _reject_duplicate([binding.admission_id for binding in bindings.admission_bindings], "bound admission ids")


def _validate_capture_bindings(plan: CortexActionPlan, bindings: HostPlanBindings) -> None:
    plan_ids = tuple(ref.capture_id for ref in plan.capture_refs)
    binding_ids = tuple(binding.capture_id for binding in bindings.capture_bindings)
    if tuple(sorted(plan_ids)) != tuple(sorted(binding_ids)):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture binding keys must exactly match plan capture refs")
    by_id = {binding.capture_id: binding for binding in bindings.capture_bindings}
    for ref in plan.capture_refs:
        binding = by_id[ref.capture_id]
        if binding.request.capture_id != ref.capture_id:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture request id must match plan capture id")
        if ref.visibility_scope != binding.request.requested_visibility_scope.value:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture visibility scope must match host request")
        if ref.persistence_state == "ephemeral" and binding.request.visibility_scope is not VisibilityScope.current_turn:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "ephemeral capture must use current_turn visibility")


def _validate_admission_bindings(plan: CortexActionPlan, bindings: HostPlanBindings) -> None:
    plan_ids = tuple(ref.request_id for ref in plan.admission_request_refs)
    binding_ids = tuple(binding.request_id for binding in bindings.admission_bindings)
    if tuple(sorted(plan_ids)) != tuple(sorted(binding_ids)):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "admission binding keys must exactly match plan admission refs")
    decisions = {decision.decision_id: decision for decision in plan.promotion_decisions}
    by_request = {binding.request_id: binding for binding in bindings.admission_bindings}
    for ref in plan.admission_request_refs:
        binding = by_request[ref.request_id]
        decision = decisions.get(ref.decision_id)
        if decision is None:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "admission ref points at missing promotion decision")
        _validate_decision(binding, decision)
        if binding.request.admission_id != binding.admission_id:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "bound admission id must match actual AdmissionRequest")
        declared_shard_id = binding.declared_shard_id or binding.request.dream_shard.shard_id
        if declared_shard_id != ref.shard_id or declared_shard_id != decision.shard_id:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "admission shard binding mismatch")
        proposal_id = str(binding.request.growth_submission.get("proposal_id", ""))
        if ref.proposal_ref != binding.proposal_ref or proposal_id != binding.proposal_ref:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "admission proposal ref binding mismatch")
        if ref.placement_plan_ref != binding.placement_plan_ref or binding.request.placement_plan.plan_id != binding.placement_plan_ref:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "admission placement ref binding mismatch")
    if plan.explicit_assembly is not None and bindings.admission_bindings:
        bound = tuple(binding.admission_id for binding in bindings.admission_bindings)
        declared = plan.explicit_assembly.admission_ids
        if not declared or len(set(declared)) != len(declared):
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "explicit assembly ids must be unique")
        if not _ordered_subsequence(declared, bound):
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "explicit assembly ids must be an ordered subset of bound admission ids")


def _validate_decision(binding: HostAdmissionBinding, decision) -> None:
    actual = binding.decision
    actual_candidate_id = binding.actual_candidate_id or binding.candidate_id
    actual_shard_id = binding.request.dream_shard.shard_id
    expected_reasons = tuple(reason.value for reason in actual.reasons)
    if (
        actual.decision_id != decision.decision_id
        or binding.decision_id != decision.decision_id
        or binding.candidate_id != decision.candidate_id
        or actual.candidate_id != actual_candidate_id
        or actual.shard_id != actual_shard_id
        or actual.decision.value != decision.decision
        or expected_reasons != decision.reasons
        or actual.decided_by.value != decision.decided_by
    ):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "promotion decision binding mismatch")
    if actual.decision is not PromotionDecisionKind.promote:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "admission binding requires promote decision")
    if actual.decided_by is PromotionDecider.cortex_suggestion:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "cortex_suggestion cannot bind admission execution")


def _validate_recall_bindings(plan: CortexActionPlan, bindings: HostPlanBindings) -> None:
    if plan.recall_request is None:
        if bindings.recall_binding is not None:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "recall binding is not declared by plan")
        return
    if bindings.recall_binding is None:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "recall binding is required")
    if (
        bindings.recall_binding.query_ref != plan.recall_request.query_ref
        or bindings.recall_binding.admitted_workset_ref != plan.recall_request.admitted_workset_ref
    ):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "recall query/workset binding mismatch")


def _validate_dg6_bindings(plan: CortexActionPlan, bindings: HostPlanBindings) -> None:
    if not plan.derived_views:
        return
    if bindings.dg6_binding is None:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "DG6 view binding is required when declared")
    if len(plan.derived_views) != 1 or plan.derived_views[0].view_ref != bindings.dg6_binding.view_ref or not bindings.dg6_binding.verification_only:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "DG6 binding must be verification-only and exact")


def _reject_duplicate(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", f"{label} must be unique")


def _ordered_subsequence(expected: tuple[str, ...], actual: tuple[str, ...]) -> bool:
    cursor = 0
    for value in actual:
        if cursor < len(expected) and expected[cursor] == value:
            cursor += 1
    return cursor == len(expected)


__all__ = ["FORBIDDEN_WORK_DIRS", "preflight_host_plan"]
