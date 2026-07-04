"""Canonical DG6 projection fingerprints."""

from __future__ import annotations

from hashlib import sha256

from nollm.dream_geometry.field.types import stable_id, stable_json

from .types import SnapshotCompactionAdapterPolicy, SnapshotCompactionProjection


def adapter_policy_payload(policy: SnapshotCompactionAdapterPolicy) -> object:
    return {
        "policy_id": policy.policy_id,
        "policy_version": policy.policy_version,
        "mode": policy.mode,
        "require_snapshot_fingerprint_match": policy.require_snapshot_fingerprint_match,
        "require_exact_trace_manifest": policy.require_exact_trace_manifest,
        "require_dg5_bound_plan": policy.require_dg5_bound_plan,
    }


def projection_identity_payload(
    policy: SnapshotCompactionAdapterPolicy,
    source_snapshot_id: str,
    source_snapshot_fingerprint: str,
    source_trace_ids: tuple[str, ...],
    source_trace_fingerprints: tuple[tuple[str, str], ...],
    compression_plan_id: str,
    compression_plan_fingerprint: str,
    compacted_view_fingerprint: str,
) -> object:
    return {
        "adapter_policy": adapter_policy_payload(policy),
        "source_snapshot_id": source_snapshot_id,
        "source_snapshot_fingerprint": source_snapshot_fingerprint,
        "source_trace_ids": source_trace_ids,
        "source_trace_fingerprints": source_trace_fingerprints,
        "compression_plan_id": compression_plan_id,
        "compression_plan_fingerprint": compression_plan_fingerprint,
        "compacted_trace_view_fingerprint": compacted_view_fingerprint,
    }


def projection_payload(projection: SnapshotCompactionProjection) -> object:
    return {
        "projection_id": projection.projection_id,
        "adapter_policy_id": projection.adapter_policy_id,
        "adapter_policy_version": projection.adapter_policy_version,
        "mode": projection.mode,
        "source_snapshot_id": projection.source_snapshot_id,
        "source_snapshot_fingerprint": projection.source_snapshot_fingerprint,
        "source_trace_ids": projection.source_trace_ids,
        "source_trace_fingerprints": projection.source_trace_fingerprints,
        "compression_plan_id": projection.compression_plan.plan_id,
        "compression_plan_fingerprint": projection.compression_plan.plan_fingerprint,
        "compacted_trace_view_fingerprint": projection.compacted_trace_view.view_fingerprint,
    }


def projection_id_for(payload: object) -> str:
    return stable_id("snapshot_compaction_projection:dg6", payload)


def projection_fingerprint_for(payload: object) -> str:
    return sha256(stable_json(payload).encode("utf-8")).hexdigest()
