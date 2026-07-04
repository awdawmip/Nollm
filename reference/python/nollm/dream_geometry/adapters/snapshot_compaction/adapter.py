"""DG6 isolated DF1 snapshot to DG5 compaction projection adapter."""

from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.assembly.types import FiniteFieldSnapshot
from nollm.dream_geometry.compression import CompressionPlanningError, expand_compression_plan, plan_trace_compaction
from nollm.dream_geometry.compression.view import build_compacted_trace_view
from nollm.dream_geometry.field.types import GrowthTrace

from .errors import DG6AdapterError
from .fingerprint import projection_fingerprint_for, projection_id_for, projection_identity_payload, projection_payload
from .types import SnapshotCompactionAdapterPolicy, SnapshotCompactionProjection
from .validation import (
    _canonical_replayed_trace_ids,
    snapshot_fingerprint,
    trace_manifest,
    validate_policy,
    validate_projection_shape,
    validate_snapshot,
    wrap_dg5,
)


def project_snapshot_compaction(
    snapshot: FiniteFieldSnapshot,
    policy: SnapshotCompactionAdapterPolicy = SnapshotCompactionAdapterPolicy(),
) -> SnapshotCompactionProjection:
    policy = validate_policy(policy)
    validate_snapshot(snapshot)
    projection = _build_projection(snapshot, policy)
    return validate_snapshot_compaction_projection(snapshot, projection)


def validate_snapshot_compaction_projection(
    snapshot: FiniteFieldSnapshot,
    projection: SnapshotCompactionProjection,
) -> SnapshotCompactionProjection:
    validate_snapshot(snapshot)
    validate_projection_shape(projection)
    policy = SnapshotCompactionAdapterPolicy(projection.adapter_policy_id, projection.adapter_policy_version, projection.mode)
    expected = _build_projection(snapshot, policy)
    if projection.source_snapshot_id != expected.source_snapshot_id:
        raise DG6AdapterError("DG6_PROJECTION_MANIFEST_INVALID", "projection source snapshot id mismatch")
    if projection.source_snapshot_fingerprint != expected.source_snapshot_fingerprint:
        raise DG6AdapterError("DG6_SNAPSHOT_FINGERPRINT_MISMATCH", "projection source snapshot fingerprint mismatch")
    if projection.source_trace_ids != expected.source_trace_ids:
        raise DG6AdapterError("DG6_SOURCE_TRACE_MANIFEST_MISMATCH", "projection source trace ids mismatch")
    if projection.source_trace_fingerprints != expected.source_trace_fingerprints:
        raise DG6AdapterError("DG6_SOURCE_TRACE_MANIFEST_MISMATCH", "projection source trace fingerprints mismatch")
    if projection.compression_plan != expected.compression_plan:
        raise DG6AdapterError("DG6_DG5_PLAN_INVALID", "projection DG5 plan is not bound to snapshot")
    if projection.compacted_trace_view != expected.compacted_trace_view:
        raise DG6AdapterError("DG6_DG5_VIEW_INVALID", "projection DG5 view is not bound to snapshot")
    expected_projection_id = projection_id_for(_identity_payload(expected, policy))
    if projection.projection_id != expected_projection_id:
        raise DG6AdapterError("DG6_PROJECTION_MANIFEST_INVALID", "projection id mismatch")
    expected_fingerprint = projection_fingerprint_for(projection_payload(replace(projection, projection_fingerprint="")))
    if projection.projection_fingerprint != expected_fingerprint:
        raise DG6AdapterError("DG6_PROJECTION_FINGERPRINT_MISMATCH", "projection fingerprint mismatch")
    return projection


def expand_snapshot_compaction_projection(
    snapshot: FiniteFieldSnapshot,
    projection: SnapshotCompactionProjection,
) -> tuple[GrowthTrace, ...]:
    projection = validate_snapshot_compaction_projection(snapshot, projection)
    traces = snapshot.replayed_traces
    _canonical_replayed_trace_ids(traces)
    trace_index = {trace.trace_id: trace for trace in traces}
    try:
        expanded = expand_compression_plan(projection.compression_plan, trace_index)
    except CompressionPlanningError as exc:
        raise wrap_dg5("DG6_EXPANSION_MISMATCH", exc) from exc
    if tuple(trace.trace_id for trace in expanded) != projection.source_trace_ids:
        raise DG6AdapterError("DG6_EXPANSION_MISMATCH", "expanded trace ids do not match snapshot manifest")
    if expanded != traces:
        raise DG6AdapterError("DG6_EXPANSION_MISMATCH", "expanded traces do not match snapshot replayed traces")
    return expanded


def _build_projection(snapshot: FiniteFieldSnapshot, policy: SnapshotCompactionAdapterPolicy) -> SnapshotCompactionProjection:
    traces = snapshot.replayed_traces
    _canonical_replayed_trace_ids(traces)
    try:
        plan = plan_trace_compaction(traces)
    except CompressionPlanningError as exc:
        raise wrap_dg5("DG6_DG5_PLAN_INVALID", exc) from exc
    except (AttributeError, TypeError, ValueError, KeyError) as exc:
        raise DG6AdapterError("DG6_INVALID_SNAPSHOT", str(exc)) from exc
    trace_index = {trace.trace_id: trace for trace in traces}
    try:
        view = build_compacted_trace_view(plan, trace_index)
    except CompressionPlanningError as exc:
        raise wrap_dg5("DG6_DG5_VIEW_INVALID", exc) from exc
    except (AttributeError, TypeError, ValueError, KeyError) as exc:
        raise DG6AdapterError("DG6_INVALID_SNAPSHOT", str(exc)) from exc
    source_trace_ids, source_trace_fingerprints = trace_manifest(traces, plan.input_trace_fingerprints)
    source_snapshot_fingerprint = snapshot_fingerprint(snapshot)
    partial = SnapshotCompactionProjection(
        projection_id="",
        adapter_policy_id=policy.policy_id,
        adapter_policy_version=policy.policy_version,
        mode=policy.mode,
        source_snapshot_id=snapshot.snapshot_id,
        source_snapshot_fingerprint=source_snapshot_fingerprint,
        source_trace_ids=source_trace_ids,
        source_trace_fingerprints=source_trace_fingerprints,
        compression_plan=plan,
        compacted_trace_view=view,
        projection_fingerprint="",
    )
    identity_payload = _identity_payload(partial, policy)
    with_id = replace(partial, projection_id=projection_id_for(identity_payload))
    return replace(with_id, projection_fingerprint=projection_fingerprint_for(projection_payload(with_id)))


def _identity_payload(projection: SnapshotCompactionProjection, policy: SnapshotCompactionAdapterPolicy) -> object:
    return projection_identity_payload(
        policy,
        projection.source_snapshot_id,
        projection.source_snapshot_fingerprint,
        projection.source_trace_ids,
        projection.source_trace_fingerprints,
        projection.compression_plan.plan_id,
        projection.compression_plan.plan_fingerprint,
        projection.compacted_trace_view.view_fingerprint,
    )
