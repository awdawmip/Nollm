"""DC1 strict structured compiler for Growth Proposals and Query Probes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from nollm.dream_geometry.evidence import DreamShard
from nollm.dream_geometry.protocol.contracts import GrowthBasis

from .errors import (
    DC1_BACKING_SHARD_SELF_REFERENCE,
    DC1_BACKING_SUBJECT_NOT_DREAM_SHARD,
    DC1_BUDGET_EXCEEDED,
    DC1_DUPLICATE_AXIS,
    DC1_DUPLICATE_RAY_EXPRESSION,
    DC1_DUPLICATE_STEP_ID,
    DC1_EMPTY_DO_NOT_INFER,
    DC1_EMPTY_FORBIDDEN_INFERENCE,
    DC1_EXPLICIT_EXPRESSION_MISMATCH,
    DC1_GROWTH_RELATIVE_TIME_FORBIDDEN,
    DC1_INVALID_AXIS,
    DC1_INVALID_ENUM,
    DC1_INVALID_ID,
    DC1_INVALID_PREDECESSOR,
    DC1_INVALID_TEXT_SPAN,
    DC1_INVALID_TIME_FORMAT,
    DC1_LEGACY_ANCHOR_FIELD_FORBIDDEN,
    DC1_MISSING_BASIS_REFERENCE,
    DC1_MISSING_REQUIRED_FIELD,
    DC1_PROVISIONAL_FIRST_STEP_FORBIDDEN,
    DC1_PROVISIONAL_RATIONALE_REQUIRED,
    DC1_QUERY_MEMORY_BASIS_FORBIDDEN,
    DC1_QUERY_NOT_EPHEMERAL,
    DC1_QUERY_RESOLVED_TIME_FORBIDDEN,
    DC1_RULE_IDENTITY_INCOMPLETE,
    DC1_SUBJECT_NOT_DREAM_SHARD,
    DC1_UNKNOWN_FIELD,
    reject,
)
from .types import (
    CONTRACT_VERSION,
    AxisRay,
    CompilationBudget,
    CompiledGrowthProposal,
    CompiledQueryProbe,
    GrowthStep,
    RuleReference,
    StepReference,
    TextSpanRef,
)

RESERVED_AXES = frozenset({"location", "phenomenon", "absolute_time", "relative_time", "source", "constraint", "revision", "relation"})
LEGACY_FIELDS = frozenset({"anchor", "anchor_name", "active_anchor_fields", "semantic_search_query", "parent_id", "child_id", "chart", "cell", "trace", "cover", "gravity"})
GROWTH_TOP_KEYS = frozenset({"contract_version", "proposal_id", "subject_shard_id", "axes", "budget", "do_not_infer", "forbidden_inferences", "submitted_at"})
QUERY_TOP_KEYS = frozenset({"contract_version", "probe_id", "query_text", "axes", "budget", "do_not_infer", "forbidden_inferences", "reference_instant", "requires_runtime_resolution", "ephemeral"})
AXIS_KEYS = frozenset({"axis_id", "ray"})
STEP_KEYS = frozenset({"step_id", "expression", "basis", "basis_refs", "rationale"})
BUDGET_KEYS = frozenset({"max_axes", "max_total_steps", "max_ray_steps"})
TEXT_REF_KEYS = frozenset({"ref_type", "record_id", "start_char", "end_char", "quoted_text"})
RULE_REF_KEYS = frozenset({"ref_type", "rule_id", "rule_version", "rule_label", "source_ref"})
STEP_REF_KEYS = frozenset({"ref_type", "input_step_id"})
GROWTH_BASIS = frozenset(
    {
        GrowthBasis.explicit_in_shard,
        GrowthBasis.deterministic_projection,
        GrowthBasis.backed_by_other_shard,
        GrowthBasis.source_backed_rule,
        GrowthBasis.provisional_llm_generalization,
    }
)
QUERY_BASIS = frozenset(
    {
        GrowthBasis.deterministic_projection,
        GrowthBasis.source_backed_rule,
        GrowthBasis.provisional_llm_generalization,
    }
)


def compile_growth(submission: dict[str, Any], evidence_reader: object) -> CompiledGrowthProposal:
    _require_mapping(submission, "submission")
    _reject_legacy_fields(submission)
    _require_keys(submission, GROWTH_TOP_KEYS, {"contract_version", "proposal_id", "subject_shard_id", "axes", "budget", "do_not_infer", "forbidden_inferences"})
    _require_contract(submission["contract_version"])
    proposal_id = _require_prefixed_id(submission["proposal_id"], "gp_", "proposal_id")
    subject_shard_id = _require_text(submission["subject_shard_id"], "subject_shard_id")
    submitted_at = _optional_rfc3339(submission.get("submitted_at"), "submitted_at")
    subject = _resolve_subject(evidence_reader, subject_shard_id)
    budget = _parse_budget(submission["budget"])
    do_not_infer = _require_non_empty_text_tuple(submission["do_not_infer"], DC1_EMPTY_DO_NOT_INFER, "do_not_infer")
    forbidden = _require_non_empty_text_tuple(submission["forbidden_inferences"], DC1_EMPTY_FORBIDDEN_INFERENCE, "forbidden_inferences")
    axes = _parse_axes(submission["axes"], budget, "growth", subject, subject_shard_id, None, None, evidence_reader)
    if any(axis.axis_id == "relative_time" for axis in axes):
        reject(DC1_GROWTH_RELATIVE_TIME_FORBIDDEN, "growth proposals cannot contain relative_time")
    return CompiledGrowthProposal(proposal_id, subject_shard_id, axes, budget, do_not_infer, forbidden, submitted_at)


def compile_query(submission: dict[str, Any]) -> CompiledQueryProbe:
    _require_mapping(submission, "submission")
    if any(key in submission for key in ("resolved_absolute_time", "resolved_at_runtime")):
        reject(DC1_QUERY_RESOLVED_TIME_FORBIDDEN, "query cannot contain resolved time fields")
    _reject_legacy_fields(submission)
    _require_keys(submission, QUERY_TOP_KEYS, {"contract_version", "probe_id", "query_text", "axes", "budget", "do_not_infer", "forbidden_inferences", "requires_runtime_resolution", "ephemeral"})
    _require_contract(submission["contract_version"])
    probe_id = _require_prefixed_id(submission["probe_id"], "probe_", "probe_id")
    query_text = _require_text(submission["query_text"], "query_text")
    reference_instant = _optional_rfc3339(submission.get("reference_instant"), "reference_instant")
    requires_runtime_resolution = _require_bool(submission["requires_runtime_resolution"], "requires_runtime_resolution")
    if submission["ephemeral"] is not True:
        reject(DC1_QUERY_NOT_EPHEMERAL, "query probes must be ephemeral")
    budget = _parse_budget(submission["budget"])
    do_not_infer = _require_non_empty_text_tuple(submission["do_not_infer"], DC1_EMPTY_DO_NOT_INFER, "do_not_infer")
    forbidden = _require_non_empty_text_tuple(submission["forbidden_inferences"], DC1_EMPTY_FORBIDDEN_INFERENCE, "forbidden_inferences")
    axes = _parse_axes(submission["axes"], budget, "query", None, None, query_text, probe_id, None)
    has_relative = any(axis.axis_id == "relative_time" for axis in axes)
    if has_relative and not requires_runtime_resolution:
        reject(DC1_QUERY_RESOLVED_TIME_FORBIDDEN, "relative_time query requires runtime resolution")
    if not has_relative and requires_runtime_resolution:
        reject(DC1_QUERY_RESOLVED_TIME_FORBIDDEN, "runtime resolution marker requires relative_time")
    return CompiledQueryProbe(probe_id, query_text, axes, budget, do_not_infer, forbidden, reference_instant, requires_runtime_resolution, True)


def _parse_axes(
    raw_axes: object,
    budget: CompilationBudget,
    mode: str,
    subject: DreamShard | None,
    subject_shard_id: str | None,
    query_text: str | None,
    probe_id: str | None,
    evidence_reader: object | None,
) -> tuple[AxisRay, ...]:
    if not isinstance(raw_axes, list) or not raw_axes:
        reject(DC1_MISSING_REQUIRED_FIELD, "axes must be a non-empty list")
    if len(raw_axes) > budget.max_axes:
        reject(DC1_BUDGET_EXCEEDED, "axis budget exceeded")
    axes: list[AxisRay] = []
    seen_axes: set[str] = set()
    seen_steps: set[str] = set()
    total_steps = 0
    for raw_axis in raw_axes:
        _require_mapping(raw_axis, "axis")
        _reject_legacy_fields(raw_axis)
        _require_keys(raw_axis, AXIS_KEYS, AXIS_KEYS)
        axis_id = _require_axis(raw_axis["axis_id"])
        if axis_id in seen_axes:
            reject(DC1_DUPLICATE_AXIS, "duplicate axis")
        seen_axes.add(axis_id)
        raw_ray = raw_axis["ray"]
        if not isinstance(raw_ray, list) or not raw_ray:
            reject(DC1_MISSING_REQUIRED_FIELD, "ray must be a non-empty list")
        if len(raw_ray) > budget.max_ray_steps:
            reject(DC1_BUDGET_EXCEEDED, "ray step budget exceeded")
        expressions: set[str] = set()
        steps: list[GrowthStep] = []
        for index, raw_step in enumerate(raw_ray):
            step = _parse_step(raw_step, mode, subject, subject_shard_id, query_text, probe_id, evidence_reader, steps[-1] if steps else None)
            if step.step_id in seen_steps:
                reject(DC1_DUPLICATE_STEP_ID, "duplicate step id")
            if step.expression in expressions:
                reject(DC1_DUPLICATE_RAY_EXPRESSION, "duplicate expression in ray")
            seen_steps.add(step.step_id)
            expressions.add(step.expression)
            if step.basis is GrowthBasis.provisional_llm_generalization and index == 0:
                reject(DC1_PROVISIONAL_FIRST_STEP_FORBIDDEN, "provisional step cannot be first")
            steps.append(step)
        axes.append(AxisRay(axis_id, tuple(steps)))
        total_steps += len(steps)
    if total_steps > budget.max_total_steps:
        reject(DC1_BUDGET_EXCEEDED, "total step budget exceeded")
    return tuple(axes)


def _parse_step(
    raw_step: object,
    mode: str,
    subject: DreamShard | None,
    subject_shard_id: str | None,
    query_text: str | None,
    probe_id: str | None,
    evidence_reader: object | None,
    predecessor: GrowthStep | None,
) -> GrowthStep:
    _require_mapping(raw_step, "step")
    _reject_legacy_fields(raw_step)
    _require_keys(raw_step, STEP_KEYS, {"step_id", "expression", "basis", "basis_refs"})
    step_id = _require_prefixed_id(raw_step["step_id"], "step_", "step_id")
    expression = _require_text(raw_step["expression"], "expression")
    basis = _parse_basis(raw_step["basis"], mode)
    rationale = raw_step.get("rationale")
    if rationale is not None:
        rationale = _require_text(rationale, "rationale")
    refs = _parse_refs(raw_step["basis_refs"])
    if not refs:
        reject(DC1_MISSING_BASIS_REFERENCE, "basis_refs cannot be empty")
    text_refs = tuple(ref for ref in refs if isinstance(ref, TextSpanRef))
    rule_refs = tuple(ref for ref in refs if isinstance(ref, RuleReference))
    step_refs = tuple(ref for ref in refs if isinstance(ref, StepReference))
    is_query_explicit = mode == "query" and raw_step["basis"] == "explicit_in_query"
    if is_query_explicit:
        if len(text_refs) != 1 or rule_refs or step_refs:
            reject(DC1_MISSING_BASIS_REFERENCE, "explicit_in_query requires one query text span")
        ref = text_refs[0]
        if ref.record_id != probe_id:
            reject(DC1_INVALID_TEXT_SPAN, "query text span must reference probe_id")
        _validate_span(query_text or "", ref)
        if expression != ref.quoted_text:
            reject(DC1_EXPLICIT_EXPRESSION_MISMATCH, "query expression must equal quoted_text")
    elif basis is GrowthBasis.explicit_in_shard:
        if len(text_refs) != 1 or rule_refs or step_refs:
            reject(DC1_MISSING_BASIS_REFERENCE, "explicit_in_shard requires one text span")
        ref = text_refs[0]
        if ref.record_id != subject_shard_id:
            reject(DC1_SUBJECT_NOT_DREAM_SHARD, "explicit span must reference subject shard")
        _validate_span(subject.content if subject is not None else "", ref)
        if expression != ref.quoted_text:
            reject(DC1_EXPLICIT_EXPRESSION_MISMATCH, "explicit expression must equal quoted_text")
    elif basis is GrowthBasis.backed_by_other_shard:
        if len(text_refs) != 1 or rule_refs or step_refs:
            reject(DC1_MISSING_BASIS_REFERENCE, "backed_by_other_shard requires one text span")
        ref = text_refs[0]
        if ref.record_id == subject_shard_id:
            reject(DC1_BACKING_SHARD_SELF_REFERENCE, "backing shard cannot equal subject")
        try:
            backing = evidence_reader.get_dream_shard(ref.record_id) if evidence_reader is not None else None
        except Exception:
            reject(DC1_BACKING_SUBJECT_NOT_DREAM_SHARD, "backing ref must resolve to DreamShard")
        if not isinstance(backing, DreamShard):
            reject(DC1_BACKING_SUBJECT_NOT_DREAM_SHARD, "backing ref must resolve to DreamShard")
        _validate_span(backing.content, ref)
    elif basis is GrowthBasis.deterministic_projection:
        _require_rule_and_predecessor(rule_refs, step_refs, predecessor)
    elif basis is GrowthBasis.source_backed_rule:
        if len(rule_refs) != 1 or text_refs or step_refs:
            reject(DC1_RULE_IDENTITY_INCOMPLETE, "source_backed_rule requires one rule ref")
    elif basis is GrowthBasis.provisional_llm_generalization:
        _require_rule_or_predecessor(rule_refs, step_refs, predecessor)
        if rationale is None:
            reject(DC1_PROVISIONAL_RATIONALE_REQUIRED, "provisional step requires rationale")
    return GrowthStep(step_id, expression, basis, refs, rationale, basis is GrowthBasis.provisional_llm_generalization)


def _parse_refs(raw_refs: object) -> tuple[TextSpanRef | RuleReference | StepReference, ...]:
    if not isinstance(raw_refs, list):
        reject(DC1_MISSING_BASIS_REFERENCE, "basis_refs must be a list")
    refs: list[TextSpanRef | RuleReference | StepReference] = []
    for raw_ref in raw_refs:
        _require_mapping(raw_ref, "basis_ref")
        ref_type = raw_ref.get("ref_type")
        if ref_type == "text_span":
            _require_keys(raw_ref, TEXT_REF_KEYS, TEXT_REF_KEYS)
            refs.append(TextSpanRef(_require_text(raw_ref["record_id"], "record_id"), _require_non_negative_int(raw_ref["start_char"], "start_char"), _require_positive_int(raw_ref["end_char"], "end_char"), _require_text(raw_ref["quoted_text"], "quoted_text")))
        elif ref_type == "rule":
            _require_keys(raw_ref, RULE_REF_KEYS, RULE_REF_KEYS)
            refs.append(RuleReference(_require_prefixed_id(raw_ref["rule_id"], "rule_", "rule_id"), _require_text(raw_ref["rule_version"], "rule_version"), _require_text(raw_ref["rule_label"], "rule_label"), _optional_text(raw_ref["source_ref"], "source_ref")))
        elif ref_type == "step":
            _require_keys(raw_ref, STEP_REF_KEYS, STEP_REF_KEYS)
            refs.append(StepReference(_require_prefixed_id(raw_ref["input_step_id"], "step_", "input_step_id")))
        else:
            reject(DC1_INVALID_ENUM, "invalid basis ref type")
    return tuple(refs)


def _parse_basis(value: object, mode: str) -> GrowthBasis | str:
    if not isinstance(value, str):
        reject(DC1_INVALID_ENUM, "basis must be a string")
    if mode == "query" and value == "explicit_in_query":
        return "explicit_in_query"
    try:
        basis = GrowthBasis(value)
    except ValueError:
        reject(DC1_INVALID_ENUM, "invalid basis")
    if basis is GrowthBasis.rejected:
        reject(DC1_INVALID_ENUM, "rejected is not an active basis")
    if mode == "growth" and basis not in GROWTH_BASIS:
        reject(DC1_INVALID_ENUM, "basis not allowed for growth")
    if mode == "query":
        if basis in {GrowthBasis.explicit_in_shard, GrowthBasis.backed_by_other_shard}:
            reject(DC1_QUERY_MEMORY_BASIS_FORBIDDEN, "query cannot use memory basis")
        if basis not in QUERY_BASIS:
            reject(DC1_INVALID_ENUM, "basis not allowed for query")
    return basis


def _require_rule_and_predecessor(rule_refs: tuple[RuleReference, ...], step_refs: tuple[StepReference, ...], predecessor: GrowthStep | None) -> None:
    if len(rule_refs) != 1:
        reject(DC1_RULE_IDENTITY_INCOMPLETE, "deterministic projection requires one rule")
    if predecessor is None or len(step_refs) != 1 or step_refs[0].input_step_id != predecessor.step_id:
        reject(DC1_INVALID_PREDECESSOR, "deterministic projection requires adjacent predecessor")


def _require_rule_or_predecessor(rule_refs: tuple[RuleReference, ...], step_refs: tuple[StepReference, ...], predecessor: GrowthStep | None) -> None:
    if predecessor is None:
        reject(DC1_PROVISIONAL_FIRST_STEP_FORBIDDEN, "provisional step cannot be first")
    if len(step_refs) != 1 or step_refs[0].input_step_id != predecessor.step_id:
        reject(DC1_INVALID_PREDECESSOR, "provisional generalization requires adjacent predecessor")
    if len(rule_refs) > 1:
        reject(DC1_RULE_IDENTITY_INCOMPLETE, "too many rule references")


def _validate_span(source_text: str, ref: TextSpanRef) -> None:
    if ref.end_char <= ref.start_char:
        reject(DC1_INVALID_TEXT_SPAN, "end_char must be greater than start_char")
    if source_text[ref.start_char : ref.end_char] != ref.quoted_text:
        reject(DC1_INVALID_TEXT_SPAN, "quoted text does not match source span")


def _resolve_subject(evidence_reader: object, shard_id: str) -> DreamShard:
    try:
        shard = evidence_reader.get_dream_shard(shard_id)
    except Exception:
        reject(DC1_SUBJECT_NOT_DREAM_SHARD, "subject must resolve to DreamShard")
    if not isinstance(shard, DreamShard):
        reject(DC1_SUBJECT_NOT_DREAM_SHARD, "subject must resolve to DreamShard")
    return shard


def _parse_budget(value: object) -> CompilationBudget:
    _require_mapping(value, "budget")
    _require_keys(value, BUDGET_KEYS, BUDGET_KEYS)
    budget = CompilationBudget(_require_positive_int(value["max_axes"], "max_axes"), _require_positive_int(value["max_total_steps"], "max_total_steps"), _require_positive_int(value["max_ray_steps"], "max_ray_steps"))
    if budget.max_axes > 8 or budget.max_total_steps > 256 or budget.max_ray_steps > 64:
        reject(DC1_BUDGET_EXCEEDED, "compiler budget exceeds DC1 maximum")
    return budget


def _require_keys(value: dict[str, Any], allowed: frozenset[str], required: set[str] | frozenset[str]) -> None:
    unknown = set(value) - allowed
    if unknown:
        reject(DC1_LEGACY_ANCHOR_FIELD_FORBIDDEN if unknown & LEGACY_FIELDS else DC1_UNKNOWN_FIELD, f"unknown field: {sorted(unknown)[0]}")
    missing = set(required) - set(value)
    if missing:
        reject(DC1_MISSING_REQUIRED_FIELD, f"missing field: {sorted(missing)[0]}")


def _reject_legacy_fields(value: dict[str, Any]) -> None:
    if set(value) & LEGACY_FIELDS:
        reject(DC1_LEGACY_ANCHOR_FIELD_FORBIDDEN, "legacy anchor/tree/geometry field forbidden")


def _require_contract(value: object) -> None:
    if value != CONTRACT_VERSION:
        reject(DC1_INVALID_ENUM, "unsupported contract_version")


def _require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        reject(DC1_MISSING_REQUIRED_FIELD, f"{label} must be a mapping")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        reject(DC1_MISSING_REQUIRED_FIELD, f"{label} must be non-empty string")
    return value


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, label)


def _require_prefixed_id(value: object, prefix: str, label: str) -> str:
    text = _require_text(value, label)
    if not text.startswith(prefix) or text.strip() != text or any(ord(char) < 32 for char in text) or any(char in text for char in ("/", "\\", "\x7f")):
        reject(DC1_INVALID_ID, f"{label} must be stable path-safe id with prefix {prefix}")
    return text


def _require_axis(value: object) -> str:
    axis = _require_text(value, "axis_id")
    if axis in LEGACY_FIELDS or axis.startswith("anchor"):
        reject(DC1_LEGACY_ANCHOR_FIELD_FORBIDDEN, "legacy anchor axis forbidden")
    if axis in RESERVED_AXES:
        return axis
    if not axis.startswith("custom/"):
        reject(DC1_INVALID_AXIS, "custom axis must start with custom/")
    suffix = axis.removeprefix("custom/")
    if not suffix or any(not (char.islower() or char.isdigit() or char in "-_") for char in suffix):
        reject(DC1_INVALID_AXIS, "invalid custom axis")
    return axis


def _require_non_empty_text_tuple(value: object, empty_code: str, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        reject(empty_code, f"{label} must be non-empty list")
    return tuple(_require_text(item, label) for item in value)


def _require_positive_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        reject(DC1_BUDGET_EXCEEDED if label.startswith("max_") else DC1_INVALID_TEXT_SPAN, f"{label} must be positive integer")
    return value


def _require_non_negative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        reject(DC1_INVALID_TEXT_SPAN, f"{label} must be non-negative integer")
    return value


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        reject(DC1_MISSING_REQUIRED_FIELD, f"{label} must be bool")
    return value


def _optional_rfc3339(value: object, label: str) -> str | None:
    if value is None:
        return None
    text = _require_text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        reject(DC1_INVALID_TIME_FORMAT, f"{label} must be RFC3339")
    if parsed.tzinfo is None:
        reject(DC1_INVALID_TIME_FORMAT, f"{label} must include timezone")
    return text


__all__ = ["compile_growth", "compile_query"]
