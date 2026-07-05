"""DG6 projection validation helpers."""

from __future__ import annotations

from typing import Protocol

from nollm.dream_geometry.assembly.types import FiniteFieldSnapshot, snapshot_fingerprint_payload, stable_fingerprint
from nollm.dream_geometry.compression import CompressionPlanningError

from .errors import DG6AdapterError
from .types import SnapshotCompactionAdapterPolicy, SnapshotCompactionProjection


class _TraceIdentityView(Protocol):
    trace_id: object


def validate_policy(policy: SnapshotCompactionAdapterPolicy) -> SnapshotCompactionAdapterPolicy:
    if not isinstance(policy, SnapshotCompactionAdapterPolicy):
        raise DG6AdapterError("DG6_INVALID_POLICY", "policy must be SnapshotCompactionAdapterPolicy")
    return SnapshotCompactionAdapterPolicy(
        policy.policy_id,
        policy.policy_version,
        policy.mode,
        policy.require_snapshot_fingerprint_match,
        policy.require_exact_trace_manifest,
        policy.require_dg5_bound_plan,
    )


def validate_snapshot(snapshot: FiniteFieldSnapshot) -> FiniteFieldSnapshot:
    if not isinstance(snapshot, FiniteFieldSnapshot):
        raise DG6AdapterError("DG6_INVALID_SNAPSHOT", "snapshot must be FiniteFieldSnapshot")
    try:
        expected = stable_fingerprint(snapshot_fingerprint_payload(snapshot))
    except (AttributeError, TypeError, ValueError) as exc:
        raise DG6AdapterError("DG6_INVALID_SNAPSHOT", str(exc)) from exc
    if snapshot.snapshot_id != expected:
        raise DG6AdapterError("DG6_SNAPSHOT_FINGERPRINT_MISMATCH", "snapshot_id does not match DF1 fingerprint payload")
    traces = _snapshot_traces(snapshot)
    _canonical_replayed_trace_ids(traces)
    return snapshot


def snapshot_fingerprint(snapshot: FiniteFieldSnapshot) -> str:
    try:
        return stable_fingerprint(snapshot_fingerprint_payload(snapshot))
    except (AttributeError, TypeError, ValueError) as exc:
        raise DG6AdapterError("DG6_INVALID_SNAPSHOT", str(exc)) from exc


def trace_manifest(traces: tuple[_TraceIdentityView, ...], trace_fingerprints: tuple[tuple[str, str], ...]) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
    trace_ids = _canonical_replayed_trace_ids(traces)
    if tuple(trace_id for trace_id, _ in trace_fingerprints) != trace_ids:
        raise DG6AdapterError("DG6_SOURCE_TRACE_MANIFEST_MISMATCH", "source trace fingerprints must match trace ids")
    return trace_ids, trace_fingerprints


def _canonical_replayed_trace_ids(traces: tuple[_TraceIdentityView, ...]) -> tuple[str, ...]:
    trace_ids: list[str] = []
    for trace in traces:
        try:
            trace_id = trace.trace_id
        except (AttributeError, TypeError, ValueError, KeyError) as exc:
            raise DG6AdapterError("DG6_INVALID_SNAPSHOT", str(exc)) from exc
        if not isinstance(trace_id, str) or trace_id == "":
            raise DG6AdapterError("DG6_INVALID_SNAPSHOT", "snapshot replayed trace_id must be non-empty string")
        trace_ids.append(trace_id)
    trace_id_tuple = tuple(trace_ids)
    if tuple(sorted(trace_id_tuple)) != trace_id_tuple:
        raise DG6AdapterError("DG6_INVALID_SNAPSHOT", "snapshot replayed traces must be canonical by trace_id")
    if len(set(trace_id_tuple)) != len(trace_id_tuple):
        raise DG6AdapterError("DG6_DUPLICATE_TRACE_ID", "snapshot replayed traces contain duplicate trace_id")
    return trace_id_tuple


def validate_projection_shape(projection: SnapshotCompactionProjection) -> SnapshotCompactionProjection:
    if not isinstance(projection, SnapshotCompactionProjection):
        raise DG6AdapterError("DG6_PROJECTION_MANIFEST_INVALID", "projection must be SnapshotCompactionProjection")
    try:
        SnapshotCompactionAdapterPolicy(projection.adapter_policy_id, projection.adapter_policy_version, projection.mode)
    except DG6AdapterError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise DG6AdapterError("DG6_PROJECTION_MANIFEST_INVALID", str(exc)) from exc
    source_trace_ids = _string_tuple(projection.source_trace_ids, "source_trace_ids")
    source_trace_fingerprints = _fingerprint_pairs(projection.source_trace_fingerprints)
    if tuple(sorted(source_trace_ids)) != source_trace_ids:
        raise DG6AdapterError("DG6_SOURCE_TRACE_MANIFEST_MISMATCH", "projection source_trace_ids must be canonical")
    if tuple(trace_id for trace_id, _ in source_trace_fingerprints) != source_trace_ids:
        raise DG6AdapterError("DG6_SOURCE_TRACE_MANIFEST_MISMATCH", "projection source fingerprints must match source ids")
    return projection


def wrap_dg5(reason_code: str, exc: CompressionPlanningError) -> DG6AdapterError:
    return DG6AdapterError(reason_code, f"{exc.reason_code}: {exc}")


def _snapshot_traces(snapshot: FiniteFieldSnapshot) -> tuple[_TraceIdentityView, ...]:
    try:
        traces = snapshot.replayed_traces
    except AttributeError as exc:
        raise DG6AdapterError("DG6_INVALID_SNAPSHOT", str(exc)) from exc
    if not isinstance(traces, tuple):
        raise DG6AdapterError("DG6_INVALID_SNAPSHOT", "snapshot.replayed_traces must be tuple")
    return traces


def _string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DG6AdapterError("DG6_PROJECTION_MANIFEST_INVALID", f"{field_name} must be tuple")
    if not all(isinstance(item, str) for item in value):
        raise DG6AdapterError("DG6_PROJECTION_MANIFEST_INVALID", f"{field_name} must contain only strings")
    return value


def _fingerprint_pairs(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, tuple):
        raise DG6AdapterError("DG6_PROJECTION_MANIFEST_INVALID", "source_trace_fingerprints must be tuple")
    pairs = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise DG6AdapterError("DG6_PROJECTION_MANIFEST_INVALID", "source_trace_fingerprints members must be pairs")
        trace_id, fingerprint = item
        if not isinstance(trace_id, str) or not isinstance(fingerprint, str):
            raise DG6AdapterError("DG6_PROJECTION_MANIFEST_INVALID", "source_trace_fingerprints pair values must be strings")
        pairs.append((trace_id, fingerprint))
    return tuple(pairs)
