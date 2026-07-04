"""Canonical DG5 fingerprints for immutable trace compression views."""

from __future__ import annotations

from hashlib import sha256

from nollm.dream_geometry.field.types import GrowthTrace, TraceCompaction, cell_payload, float_token, stable_id, stable_json

from .types import CompactedTraceEntry, CompressionPlan, CompressionPolicy


def trace_payload(trace: GrowthTrace) -> object:
    return {
        "trace_id": trace.trace_id,
        "origin_shard_id": trace.origin_shard_id,
        "proposal_id": trace.proposal_id,
        "parent_trace_id": trace.parent_trace_id,
        "cell": cell_payload(trace.cell),
        "axis": trace.axis,
        "basis": trace.basis.value,
        "basis_refs": trace.basis_refs,
        "mass": float_token(trace.mass),
        "support_key": trace.support_key,
        "genericity": float_token(trace.genericity),
        "ambiguity": float_token(trace.ambiguity),
        "conflict": float_token(trace.conflict),
        "stability_epochs": trace.stability_epochs,
        "state": trace.state.value,
        "derivation_kind": trace.derivation_kind,
        "geometry_refs": trace.geometry_refs,
    }


def trace_fingerprint(trace: GrowthTrace) -> str:
    return _sha256_payload(trace_payload(trace))


def compaction_payload(compaction: TraceCompaction) -> object:
    return {
        "compaction_id": compaction.compaction_id,
        "member_trace_ids": compaction.member_trace_ids,
        "canonical_key": compaction.canonical_key,
        "aggregate_mass": float_token(compaction.aggregate_mass),
        "expansion_manifest": compaction.expansion_manifest,
    }


def compression_plan_payload_without_fingerprint(plan: CompressionPlan) -> object:
    return {
        "plan_id": plan.plan_id,
        "policy_id": plan.policy_id,
        "policy_version": plan.policy_version,
        "mode": plan.mode,
        "input_trace_ids": plan.input_trace_ids,
        "input_trace_fingerprints": plan.input_trace_fingerprints,
        "compactions": tuple(compaction_payload(item) for item in plan.compactions),
        "passthrough_trace_ids": plan.passthrough_trace_ids,
        "input_trace_count": plan.input_trace_count,
        "compacted_member_count": plan.compacted_member_count,
        "output_view_entry_count": plan.output_view_entry_count,
        "estimated_view_entry_reduction": plan.estimated_view_entry_reduction,
    }


def compression_plan_fingerprint(plan: CompressionPlan) -> str:
    return _sha256_payload(compression_plan_payload_without_fingerprint(plan))


def planned_payload(
    policy: CompressionPolicy,
    input_trace_ids: tuple[str, ...],
    input_trace_fingerprints: tuple[tuple[str, str], ...],
    compactions: tuple[TraceCompaction, ...],
    passthrough_trace_ids: tuple[str, ...],
) -> object:
    compacted_member_count = sum(len(item.member_trace_ids) for item in compactions)
    output_view_entry_count = len(compactions) + len(passthrough_trace_ids)
    return {
        "policy_id": policy.policy_id,
        "policy_version": policy.policy_version,
        "mode": policy.mode,
        "input_trace_ids": input_trace_ids,
        "input_trace_fingerprints": input_trace_fingerprints,
        "compactions": tuple(compaction_payload(item) for item in compactions),
        "passthrough_trace_ids": passthrough_trace_ids,
        "input_trace_count": len(input_trace_ids),
        "compacted_member_count": compacted_member_count,
        "output_view_entry_count": output_view_entry_count,
        "estimated_view_entry_reduction": len(input_trace_ids) - output_view_entry_count,
    }


def plan_id_for(payload: object) -> str:
    return stable_id("compression_plan:dg5", payload)


def entry_payload(entry: CompactedTraceEntry) -> object:
    return {
        "entry_id": entry.entry_id,
        "entry_kind": entry.entry_kind,
        "trace_id": entry.trace_id,
        "trace_fingerprint": entry.trace_fingerprint,
        "compaction": None if entry.compaction is None else compaction_payload(entry.compaction),
        "member_trace_ids": entry.member_trace_ids,
        "aggregate_mass": float_token(entry.aggregate_mass),
    }


def view_fingerprint_payload(plan: CompressionPlan, entries: tuple[CompactedTraceEntry, ...]) -> object:
    return {
        "plan_fingerprint": plan.plan_fingerprint,
        "entries": tuple(entry_payload(entry) for entry in entries),
    }


def view_fingerprint(plan: CompressionPlan, entries: tuple[CompactedTraceEntry, ...]) -> str:
    return _sha256_payload(view_fingerprint_payload(plan, entries))


def _sha256_payload(payload: object) -> str:
    return sha256(stable_json(payload).encode("utf-8")).hexdigest()
