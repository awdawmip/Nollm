"""DG5 exact transport-view compression planning."""

from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.field.compaction import compact_traces
from nollm.dream_geometry.field.types import GrowthTrace

from .errors import CompressionPlanningError
from .fingerprint import compression_plan_fingerprint, plan_id_for, planned_payload, trace_fingerprint
from .types import CompressionPlan, CompressionPolicy
from .validation import validate_compression_plan


def plan_trace_compaction(
    traces: tuple[GrowthTrace, ...],
    policy: CompressionPolicy = CompressionPolicy(),
) -> CompressionPlan:
    if not isinstance(traces, tuple):
        traces = tuple(traces)
    _reject_duplicate_trace_ids(traces)
    policy = _validate_policy(policy)
    try:
        compactions = compact_traces(traces)
    except ValueError as exc:
        if "duplicate trace_id" in str(exc):
            raise CompressionPlanningError("DG5_DUPLICATE_TRACE_ID", str(exc)) from exc
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", str(exc)) from exc
    input_trace_ids = tuple(sorted(trace.trace_id for trace in traces))
    input_trace_fingerprints = tuple(sorted((trace.trace_id, trace_fingerprint(trace)) for trace in traces))
    compacted_ids = {trace_id for compaction in compactions for trace_id in compaction.member_trace_ids}
    passthrough_trace_ids = tuple(trace_id for trace_id in input_trace_ids if trace_id not in compacted_ids)
    payload = planned_payload(policy, input_trace_ids, input_trace_fingerprints, compactions, passthrough_trace_ids)
    plan_id = plan_id_for(payload)
    plan = CompressionPlan(
        plan_id=plan_id,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        mode=policy.mode,
        input_trace_ids=input_trace_ids,
        input_trace_fingerprints=input_trace_fingerprints,
        compactions=compactions,
        passthrough_trace_ids=passthrough_trace_ids,
        input_trace_count=len(input_trace_ids),
        compacted_member_count=sum(len(item.member_trace_ids) for item in compactions),
        output_view_entry_count=len(compactions) + len(passthrough_trace_ids),
        estimated_view_entry_reduction=len(input_trace_ids) - (len(compactions) + len(passthrough_trace_ids)),
        plan_fingerprint="",
    )
    plan = replace(plan, plan_fingerprint=compression_plan_fingerprint(plan))
    validate_compression_plan(plan)
    return plan


def _validate_policy(policy: CompressionPolicy) -> CompressionPolicy:
    if not isinstance(policy, CompressionPolicy):
        raise CompressionPlanningError("DG5_INVALID_POLICY", "policy must be a CompressionPolicy")
    CompressionPolicy(policy.policy_id, policy.policy_version, policy.mode, policy.require_exact_transport_identity)
    return policy


def _reject_duplicate_trace_ids(traces: tuple[GrowthTrace, ...]) -> None:
    seen: set[str] = set()
    for trace in traces:
        if trace.trace_id in seen:
            raise CompressionPlanningError("DG5_DUPLICATE_TRACE_ID", f"duplicate trace_id: {trace.trace_id}")
        seen.add(trace.trace_id)
