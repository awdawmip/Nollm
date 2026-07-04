"""DG5 immutable compacted trace views and lossless expansion."""

from __future__ import annotations

from collections.abc import Mapping

from nollm.dream_geometry.field.compaction import compact_traces, expand_compaction
from nollm.dream_geometry.field.types import GrowthTrace, stable_id

from .errors import CompressionPlanningError
from .fingerprint import trace_fingerprint, view_fingerprint
from .types import CompactedTraceEntry, CompactedTraceView, CompressionPlan
from .validation import validate_compression_plan


def build_compacted_trace_view(plan: CompressionPlan, trace_index: Mapping[str, GrowthTrace]) -> CompactedTraceView:
    validate_compression_plan(plan)
    _validate_trace_index_exact(plan, trace_index)
    _validate_plan_bound_to_trace_index(plan, trace_index)
    entries = []
    trace_fingerprints = dict(plan.input_trace_fingerprints)
    for compaction in plan.compactions:
        _expand_verified(compaction, trace_index)
        entries.append(
            CompactedTraceEntry(
                entry_id=stable_id("compacted_entry:dg5", (plan.plan_fingerprint, compaction.compaction_id)),
                entry_kind="compacted_transport_view",
                trace_id=None,
                trace_fingerprint=None,
                compaction=compaction,
                member_trace_ids=compaction.member_trace_ids,
                aggregate_mass=compaction.aggregate_mass,
            )
        )
    for trace_id in plan.passthrough_trace_ids:
        trace = trace_index[trace_id]
        entries.append(
            CompactedTraceEntry(
                entry_id=stable_id("passthrough_entry:dg5", (plan.plan_fingerprint, trace_id, trace_fingerprints[trace_id])),
                entry_kind="passthrough_trace_view",
                trace_id=trace_id,
                trace_fingerprint=trace_fingerprint(trace),
                compaction=None,
                member_trace_ids=(trace_id,),
                aggregate_mass=trace.mass,
            )
        )
    ordered_entries = tuple(sorted(entries, key=lambda entry: (entry.entry_kind, entry.member_trace_ids, entry.entry_id)))
    return CompactedTraceView(
        plan=plan,
        entries=ordered_entries,
        entry_count=len(ordered_entries),
        source_trace_count=plan.input_trace_count,
        view_fingerprint=view_fingerprint(plan, ordered_entries),
    )


def expand_compression_plan(
    plan: CompressionPlan,
    trace_index: Mapping[str, GrowthTrace],
) -> tuple[GrowthTrace, ...]:
    validate_compression_plan(plan)
    _validate_trace_index_exact(plan, trace_index)
    _validate_plan_bound_to_trace_index(plan, trace_index)
    expanded: dict[str, GrowthTrace] = {}
    for compaction in plan.compactions:
        for trace in _expand_verified(compaction, trace_index):
            if trace.trace_id in expanded:
                raise CompressionPlanningError("DG5_EXPANSION_MANIFEST_MISMATCH", "trace expanded more than once")
            expanded[trace.trace_id] = trace
    for trace_id in plan.passthrough_trace_ids:
        if trace_id in expanded:
            raise CompressionPlanningError("DG5_EXPANSION_MANIFEST_MISMATCH", "passthrough overlaps compaction")
        expanded[trace_id] = trace_index[trace_id]
    if set(expanded) != set(plan.input_trace_ids):
        raise CompressionPlanningError("DG5_EXPANSION_MANIFEST_MISMATCH", "expanded trace set does not match input manifest")
    return tuple(expanded[trace_id] for trace_id in plan.input_trace_ids)


def _validate_trace_index_exact(plan: CompressionPlan, trace_index: Mapping[str, GrowthTrace]) -> None:
    expected = set(plan.input_trace_ids)
    actual = set(trace_index)
    missing = sorted(expected - actual)
    if missing:
        raise CompressionPlanningError("DG5_EXPANSION_TRACE_MISSING", f"missing trace_id: {missing[0]}")
    extra = sorted(actual - expected)
    if extra:
        raise CompressionPlanningError("DG5_UNEXPECTED_TRACE_INDEX_ENTRY", f"unexpected trace_id: {extra[0]}")
    expected_fingerprints = dict(plan.input_trace_fingerprints)
    for trace_id in plan.input_trace_ids:
        if trace_fingerprint(trace_index[trace_id]) != expected_fingerprints[trace_id]:
            raise CompressionPlanningError("DG5_EXPANSION_TRACE_FINGERPRINT_MISMATCH", f"fingerprint mismatch: {trace_id}")


def _validate_plan_bound_to_trace_index(plan: CompressionPlan, trace_index: Mapping[str, GrowthTrace]) -> None:
    ordered_traces = tuple(trace_index[trace_id] for trace_id in plan.input_trace_ids)
    try:
        expected_compactions = compact_traces(ordered_traces)
    except ValueError as exc:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", str(exc)) from exc
    expected_compacted_ids = {trace_id for compaction in expected_compactions for trace_id in compaction.member_trace_ids}
    expected_passthrough = tuple(trace_id for trace_id in plan.input_trace_ids if trace_id not in expected_compacted_ids)
    if plan.compactions != expected_compactions:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "plan compactions do not match sealed DG2 output")
    if plan.passthrough_trace_ids != expected_passthrough:
        raise CompressionPlanningError("DG5_PLAN_MANIFEST_INVALID", "plan passthrough ids do not match sealed DG2 output")


def _expand_verified(compaction, trace_index: Mapping[str, GrowthTrace]) -> tuple[GrowthTrace, ...]:
    try:
        expanded = expand_compaction(compaction, dict(trace_index))
    except ValueError as exc:
        if "missing trace_id" in str(exc):
            raise CompressionPlanningError("DG5_EXPANSION_TRACE_MISSING", str(exc)) from exc
        raise CompressionPlanningError("DG5_EXPANSION_MANIFEST_MISMATCH", str(exc)) from exc
    if tuple(trace.trace_id for trace in expanded) != compaction.expansion_manifest:
        raise CompressionPlanningError("DG5_EXPANSION_MANIFEST_MISMATCH", "DG2 expansion order mismatch")
    return expanded
