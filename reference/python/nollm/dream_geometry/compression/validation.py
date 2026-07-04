"""DG5 fail-closed compression plan and manifest validation."""

from __future__ import annotations

from nollm.dream_geometry.field.types import stable_id

from .errors import CompressionPlanningError
from .fingerprint import compression_plan_fingerprint, planned_payload, plan_id_for
from .types import CompressionPlan, CompressionPolicy


def validate_compression_plan(plan: CompressionPlan) -> CompressionPlan:
    if plan.policy_id != "dg5_exact_transport_view" or plan.policy_version != "1" or plan.mode != "view_only":
        raise CompressionPlanningError("DG5_INVALID_POLICY", "plan carries an unsupported policy")
    policy = CompressionPolicy(plan.policy_id, plan.policy_version, plan.mode, True)
    if tuple(sorted(plan.input_trace_ids)) != plan.input_trace_ids:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "input_trace_ids must be canonical")
    if len(set(plan.input_trace_ids)) != len(plan.input_trace_ids):
        raise CompressionPlanningError("DG5_DUPLICATE_TRACE_ID", "input_trace_ids contain duplicates")
    fingerprint_ids = tuple(trace_id for trace_id, _ in plan.input_trace_fingerprints)
    if fingerprint_ids != plan.input_trace_ids:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "input fingerprints must match input trace ids")
    if tuple(sorted(plan.passthrough_trace_ids)) != plan.passthrough_trace_ids:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "passthrough trace ids must be canonical")
    if tuple(sorted(plan.compactions, key=lambda item: item.compaction_id)) != plan.compactions:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "compactions must be canonical")
    for compaction in plan.compactions:
        _validate_compaction_shape(compaction)
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
    expected_plan_id = plan_id_for(planned_payload(policy, plan.input_trace_ids, plan.input_trace_fingerprints, plan.compactions, plan.passthrough_trace_ids))
    if plan.plan_id != expected_plan_id:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "plan id mismatch")
    if compression_plan_fingerprint(plan) != plan.plan_fingerprint:
        raise CompressionPlanningError("DG5_PLAN_FINGERPRINT_MISMATCH", "plan fingerprint mismatch")
    return plan


def _validate_compaction_shape(compaction) -> None:
    if len(compaction.member_trace_ids) < 2:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "singleton compaction is invalid")
    if compaction.member_trace_ids != compaction.expansion_manifest:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "compaction expansion manifest mismatch")
    if tuple(sorted(compaction.member_trace_ids)) != compaction.member_trace_ids:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "compaction member ids must be canonical")
    if len(set(compaction.member_trace_ids)) != len(compaction.member_trace_ids):
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "compaction member ids contain duplicates")
    expected_id = stable_id(
        "trace_compaction:v2",
        {"canonical_key": compaction.canonical_key, "members": compaction.member_trace_ids},
    )
    if compaction.compaction_id != expected_id:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "compaction id mismatch")
