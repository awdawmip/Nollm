"""DG5 fail-closed compression plan and manifest validation."""

from __future__ import annotations

from .errors import CompressionPlanningError
from .fingerprint import compression_plan_fingerprint
from .types import CompressionPlan


def validate_compression_plan(plan: CompressionPlan) -> CompressionPlan:
    if plan.policy_id != "dg5_exact_transport_view" or plan.policy_version != "1" or plan.mode != "view_only":
        raise CompressionPlanningError("DG5_INVALID_POLICY", "plan carries an unsupported policy")
    if tuple(sorted(plan.input_trace_ids)) != plan.input_trace_ids:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "input_trace_ids must be canonical")
    if len(set(plan.input_trace_ids)) != len(plan.input_trace_ids):
        raise CompressionPlanningError("DG5_DUPLICATE_TRACE_ID", "input_trace_ids contain duplicates")
    fingerprint_ids = tuple(trace_id for trace_id, _ in plan.input_trace_fingerprints)
    if fingerprint_ids != plan.input_trace_ids:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "input fingerprints must match input trace ids")
    member_ids = tuple(trace_id for compaction in plan.compactions for trace_id in compaction.member_trace_ids)
    if len(set(member_ids)) != len(member_ids):
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "compaction member overlap")
    if any(trace_id not in plan.input_trace_ids for trace_id in member_ids):
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "compaction member outside input manifest")
    if any(trace_id not in plan.input_trace_ids for trace_id in plan.passthrough_trace_ids):
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "passthrough trace outside input manifest")
    if set(member_ids).intersection(plan.passthrough_trace_ids):
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "compacted member cannot be passthrough")
    if set(member_ids).union(plan.passthrough_trace_ids) != set(plan.input_trace_ids):
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "input manifest is not fully covered")
    if plan.input_trace_count != len(plan.input_trace_ids):
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "input trace count mismatch")
    if plan.compacted_member_count != len(member_ids):
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "compacted member count mismatch")
    if plan.output_view_entry_count != len(plan.compactions) + len(plan.passthrough_trace_ids):
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "output view entry count mismatch")
    if plan.estimated_view_entry_reduction != plan.input_trace_count - plan.output_view_entry_count:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "view entry reduction mismatch")
    if compression_plan_fingerprint(plan) != plan.plan_fingerprint:
        raise CompressionPlanningError("DG5_PLAN_FINGERPRINT_MISMATCH", "plan fingerprint mismatch")
    return plan

