"""HX1 host binding preflight."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from nollm.dream_geometry.adapters import RecallInvocation
from nollm.dream_geometry.admission import AdmissionPlacementPlan, AdmissionRequest
from nollm.dream_geometry.admission import fingerprint as admission_fingerprint
from nollm.dream_geometry.admission import placement_plan_payload
from nollm.dream_geometry.batch_admission import PromotionDecider, PromotionDecision as BA1PromotionDecision
from nollm.dream_geometry.batch_admission import PromotionDecisionKind, PromotionReason
from nollm.dream_geometry.capture import (
    CandidateTrigger,
    CaptureDiagnostics,
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    CaptureRequest,
    DeferredCandidateRequest,
    PromotionMode,
    RetentionClass,
    VisibilityScope,
)
from nollm.dream_geometry.cortex import CompiledQueryProbe
from nollm.dream_geometry.cortex import canonical_payload as cortex_payload
from nollm.dream_geometry.cortex import payload_fingerprint as cortex_fingerprint
from nollm.dream_geometry.evidence import DreamShard
from nollm.dream_geometry.evidence import canonical_payload as evidence_payload
from nollm.dream_geometry.evidence import payload_key as evidence_payload_key
from nollm.dream_geometry.protocol.contracts import OriginKind
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
from .types import HostAdmissionBinding, HostCaptureBinding, HostDG6VerificationBinding, HostExecutionContext, HostPlanBindings, HostRecallBinding


FORBIDDEN_WORK_DIRS = ("field", "assembly", "recall", "cache", "database", "global-field")


def preflight_host_plan(plan: CortexActionPlan | Mapping[str, Any], bindings: HostPlanBindings, context: HostExecutionContext):
    try:
        summary = validate_cortex_action_plan(plan)
    except Exception as exc:
        raise HX1ExecutionError("HX1_INVALID_PLAN", stable_message(exc)) from exc
    try:
        normalized = plan if isinstance(plan, CortexActionPlan) else _coerced_plan(plan)
    except Exception as exc:
        raise HX1ExecutionError("HX1_INVALID_PLAN", stable_message(exc)) from exc
    try:
        _validate_context(context)
        _validate_binding_shape(bindings)
        _validate_context_semantics(normalized, bindings, context)
        _validate_capture_bindings(normalized, bindings)
        _validate_admission_bindings(normalized, bindings)
        _validate_recall_bindings(normalized, bindings)
        _validate_dg6_bindings(normalized, bindings)
    except HX1ExecutionError:
        raise
    except Exception as exc:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", stable_message(exc)) from exc
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
    for value, label in (
        (context.recorded_at, "recorded_at"),
        (context.batch_window_id, "batch_window_id"),
        (context.batch_policy_id, "batch_policy_id"),
        (context.batch_source_ref, "batch_source_ref"),
        (context.finite_set_id, "finite_set_id"),
    ):
        _require_context_non_empty(value, label)
    if type(context.enable_dg6_verification) is not bool:
        raise HX1ExecutionError("HX1_INVALID_CONTEXT", "enable_dg6_verification must be boolean")
    try:
        work_root = Path(context.work_root)
    except (TypeError, ValueError) as exc:
        raise HX1ExecutionError("HX1_INVALID_CONTEXT", "work root is invalid") from exc
    repo_root = _repository_root(Path.cwd())
    try:
        resolved = work_root.resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise HX1ExecutionError("HX1_INVALID_CONTEXT", "work root is invalid") from exc
    if _is_relative_to(resolved, repo_root):
        raise HX1ExecutionError("HX1_WORK_ROOT_REJECTED", "work root must be an explicit owned directory outside repo root")
    if work_root.exists() and not work_root.is_dir():
        raise HX1ExecutionError("HX1_WORK_ROOT_REJECTED", "work root must be a directory")
    for name in FORBIDDEN_WORK_DIRS:
        if (work_root / name).exists():
            raise HX1ExecutionError("HX1_WORK_ROOT_REJECTED", "work root contains a forbidden HX1 output directory")


def _validate_context_semantics(plan: CortexActionPlan, bindings: HostPlanBindings, context: HostExecutionContext) -> None:
    if plan.derived_views and context.enable_dg6_verification is not True:
        raise HX1ExecutionError("HX1_INVALID_CONTEXT", "DG6 verification must be enabled when a DG6 view is declared")


def _validate_binding_shape(bindings: HostPlanBindings) -> None:
    if not isinstance(bindings, HostPlanBindings):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "host bindings must be HostPlanBindings")
    for collection, cls, label in (
        (bindings.capture_bindings, HostCaptureBinding, "capture bindings"),
        (bindings.admission_bindings, HostAdmissionBinding, "admission bindings"),
    ):
        if not isinstance(collection, tuple):
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", f"{label} must be immutable tuples")
        if any(not isinstance(binding, cls) for binding in collection):
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", f"{label} must contain structured host binding values")
    if bindings.recall_binding is not None and not isinstance(bindings.recall_binding, HostRecallBinding):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "recall binding must be HostRecallBinding")
    if bindings.dg6_binding is not None and not isinstance(bindings.dg6_binding, HostDG6VerificationBinding):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "DG6 binding must be HostDG6VerificationBinding")
    for binding in bindings.capture_bindings:
        _require_non_empty(binding.capture_id, "capture binding id")
        if not isinstance(binding.request, CaptureRequest) or not isinstance(binding.policy, CapturePolicy):
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture binding request/policy type mismatch")
        _validate_capture_request(binding.request)
        _validate_capture_policy(binding.policy)
    for binding in bindings.admission_bindings:
        for value, label in (
            (binding.request_id, "request_id"),
            (binding.decision_id, "decision_id"),
            (binding.candidate_id, "candidate_id"),
            (binding.admission_id, "admission_id"),
            (binding.member_id, "member_id"),
            (binding.proposal_ref, "proposal_ref"),
            (binding.placement_plan_ref, "placement_plan_ref"),
        ):
            _require_non_empty(value, label)
        if binding.actual_candidate_id is not None:
            _require_non_empty(binding.actual_candidate_id, "actual_candidate_id")
        if binding.declared_shard_id is not None:
            _require_non_empty(binding.declared_shard_id, "declared_shard_id")
        if not isinstance(binding.decision, BA1PromotionDecision) or not isinstance(binding.request, AdmissionRequest):
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "admission binding decision/request type mismatch")
        _validate_promotion_decision_value(binding.decision)
        _validate_admission_request_value(binding.request)
    if bindings.recall_binding is not None:
        _require_non_empty(bindings.recall_binding.query_ref, "query_ref")
        _require_non_empty(bindings.recall_binding.admitted_workset_ref, "admitted_workset_ref")
        if not isinstance(bindings.recall_binding.invocation, RecallInvocation):
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "recall binding invocation type mismatch")
        _validate_recall_invocation_value(bindings.recall_binding.invocation)
    if bindings.dg6_binding is not None:
        _require_non_empty(bindings.dg6_binding.view_ref, "view_ref")
        if bindings.dg6_binding.verification_only is not True:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "DG6 binding must be verification-only")
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
        if ref.persistence_state == "ephemeral" and binding.request.requested_visibility_scope is not VisibilityScope.current_turn:
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
        if plan.intent == "mixed_explicit" and bound != declared:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "mixed explicit admission bindings must exactly equal explicit assembly ids")
        if plan.intent != "mixed_explicit" and not _ordered_subsequence(declared, bound):
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
        if bindings.dg6_binding is not None:
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", "DG6 binding is not declared by plan")
        return
    if bindings.dg6_binding is None:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "DG6 view binding is required when declared")
    if len(plan.derived_views) != 1 or plan.derived_views[0].view_ref != bindings.dg6_binding.view_ref or not bindings.dg6_binding.verification_only:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "DG6 binding must be verification-only and exact")


def _reject_duplicate(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", f"{label} must be unique")


def _require_non_empty(value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", f"{label} must be non-empty string")


def _require_context_non_empty(value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise HX1ExecutionError("HX1_INVALID_CONTEXT", f"{label} must be non-empty string")


def _validate_capture_request(request: CaptureRequest) -> None:
    _require_non_empty(request.capture_id, "capture_id")
    if not isinstance(request.content, str):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture content must be string")
    if not isinstance(request.origin, CaptureOrigin) or not isinstance(request.origin.kind, OriginKind):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture origin must be structured")
    for value, label in (
        (request.origin.reference, "origin reference"),
        (request.origin.context_reference, "origin context reference"),
        (request.origin.role_label, "origin role label"),
    ):
        if value is not None and not isinstance(value, str):
            raise HX1ExecutionError("HX1_INVALID_BINDINGS", f"{label} must be string or None")
    _require_non_empty(request.recorded_at, "capture recorded_at")
    _validate_string_tuple(request.context_refs, "capture context_refs", allow_empty=True)
    if not isinstance(request.requested_visibility_scope, VisibilityScope):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture visibility scope must be structured")
    candidate = request.deferred_candidate_request
    if not isinstance(candidate, DeferredCandidateRequest) or type(candidate.requested) is not bool:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "deferred candidate request must be structured")
    if not isinstance(candidate.trigger_refs, tuple) or any(not isinstance(item, CandidateTrigger) for item in candidate.trigger_refs):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "deferred candidate triggers must be structured")
    if request.diagnostic_retention_until is not None:
        _require_non_empty(request.diagnostic_retention_until, "diagnostic_retention_until")


def _validate_capture_policy(policy: CapturePolicy) -> None:
    _require_non_empty(policy.policy_id, "policy_id")
    _require_non_empty(policy.policy_version, "policy_version")
    if not isinstance(policy.persistence, CapturePersistence):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture policy persistence must be structured")
    if not isinstance(policy.lineage, CaptureLineage):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture policy lineage must be structured")
    if not isinstance(policy.diagnostics, CaptureDiagnostics):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture policy diagnostics must be structured")
    if not isinstance(policy.allowed_visibility_scopes, tuple) or any(not isinstance(item, VisibilityScope) for item in policy.allowed_visibility_scopes):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "allowed visibility scopes must be structured")
    if not isinstance(policy.retention_class, RetentionClass):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture policy retention class must be structured")
    if not isinstance(policy.promotion_mode, PromotionMode):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "capture policy promotion mode must be structured")


def _validate_promotion_decision_value(decision: BA1PromotionDecision) -> None:
    for value, label in (
        (decision.decision_id, "decision_id"),
        (decision.candidate_id, "decision candidate_id"),
        (decision.shard_id, "decision shard_id"),
        (decision.recorded_at, "decision recorded_at"),
        (decision.next_action, "decision next_action"),
    ):
        _require_non_empty(value, label)
    if not isinstance(decision.decision, PromotionDecisionKind):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "promotion decision kind must be structured")
    if not isinstance(decision.reasons, tuple) or not decision.reasons or any(not isinstance(item, PromotionReason) for item in decision.reasons):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "promotion decision reasons must be structured")
    if not isinstance(decision.decided_by, PromotionDecider):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "promotion decider must be structured")


def _validate_admission_request_value(request: AdmissionRequest) -> None:
    for value, label in (
        (request.admission_id, "admission_id"),
        (request.recorded_at, "admission recorded_at"),
        (request.contract_version, "admission contract_version"),
    ):
        _require_non_empty(value, label)
    if not isinstance(request.dream_shard, DreamShard):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "admission dream_shard must be structured")
    _require_non_empty(request.dream_shard.shard_id, "dream_shard shard_id")
    _validate_dream_shard_canonical(request.dream_shard)
    if not isinstance(request.growth_submission, Mapping):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "growth_submission must be mapping")
    if not isinstance(request.placement_plan, AdmissionPlacementPlan):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "placement_plan must be structured")
    _require_non_empty(request.placement_plan.plan_id, "placement plan id")
    _validate_placement_plan_canonical(request.placement_plan)


def _validate_recall_invocation_value(invocation: RecallInvocation) -> None:
    _require_non_empty(invocation.request_id, "recall request_id")
    _require_non_empty(invocation.operation, "recall operation")
    if not isinstance(invocation.query_probe, CompiledQueryProbe):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "recall query probe must be structured")
    _require_non_empty(invocation.query_probe.probe_id, "compiled probe id")
    if not isinstance(invocation.query_probe.query_text, str):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "compiled query text must be structured")
    _validate_query_probe_canonical(invocation.query_probe)


def _validate_dream_shard_canonical(shard: DreamShard) -> None:
    try:
        evidence_payload(shard)
        evidence_payload_key(shard)
    except (AttributeError, TypeError, KeyError, ValueError) as exc:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "dream shard cannot be canonically fingerprinted") from exc


def _validate_placement_plan_canonical(plan: AdmissionPlacementPlan) -> None:
    if not isinstance(plan.axis_placements, tuple) or not plan.axis_placements:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "placement plan axis placements must be structured")
    try:
        admission_fingerprint(placement_plan_payload(plan))
    except (AttributeError, TypeError, KeyError, ValueError) as exc:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "placement plan cannot be canonically fingerprinted") from exc


def _validate_query_probe_canonical(probe: CompiledQueryProbe) -> None:
    try:
        cortex_fingerprint(cortex_payload(probe))
    except (AttributeError, TypeError, KeyError, ValueError) as exc:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "compiled query probe cannot be canonically fingerprinted") from exc


def _validate_string_tuple(values: object, label: str, *, allow_empty: bool = False) -> None:
    if not isinstance(values, tuple) or (not allow_empty and not values):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", f"{label} must be tuple")
    if any(not isinstance(value, str) for value in values):
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", f"{label} must contain strings")


def _ordered_subsequence(expected: tuple[str, ...], actual: tuple[str, ...]) -> bool:
    cursor = 0
    for value in actual:
        if cursor < len(expected) and expected[cursor] == value:
            cursor += 1
    return cursor == len(expected)


def _repository_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


__all__ = ["FORBIDDEN_WORK_DIRS", "preflight_host_plan"]
