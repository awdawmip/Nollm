"""DG2 lossless Growth Trace compaction views."""

from .types import GrowthTrace, TraceCompaction, cell_payload, float_token, stable_id, stable_json


def compact_traces(traces: tuple[GrowthTrace, ...]) -> tuple[TraceCompaction, ...]:
    _reject_duplicate_trace_ids(trace.trace_id for trace in traces)
    groups: dict[str, list[GrowthTrace]] = {}
    for trace in traces:
        groups.setdefault(_canonical_key(trace), []).append(trace)
    compacted = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        ordered = tuple(sorted(members, key=lambda trace: trace.trace_id))
        member_ids = tuple(trace.trace_id for trace in ordered)
        payload = {"canonical_key": key, "members": member_ids}
        compacted.append(
            TraceCompaction(
                compaction_id=stable_id("trace_compaction:v2", payload),
                member_trace_ids=member_ids,
                canonical_key=key,
                aggregate_mass=sum(trace.mass for trace in ordered),
                expansion_manifest=member_ids,
            )
        )
    return tuple(sorted(compacted, key=lambda item: item.compaction_id))


def expand_compaction(compaction: TraceCompaction, trace_index: dict[str, GrowthTrace]) -> tuple[GrowthTrace, ...]:
    _reject_duplicate_trace_ids(compaction.expansion_manifest)
    missing = tuple(trace_id for trace_id in compaction.expansion_manifest if trace_id not in trace_index)
    if missing:
        raise ValueError(f"missing trace_id: {missing[0]}")
    return tuple(trace_index[trace_id] for trace_id in compaction.expansion_manifest)


def _canonical_key(trace: GrowthTrace) -> str:
    return stable_json(
        {
            "origin_shard_id": trace.origin_shard_id,
            "proposal_id": trace.proposal_id,
            "parent_trace_id": trace.parent_trace_id,
            "cell": cell_payload(trace.cell),
            "axis": trace.axis,
            "basis": trace.basis.value,
            "basis_refs": trace.basis_refs,
            "state": trace.state.value,
            "support_key": trace.support_key,
            "genericity": float_token(trace.genericity),
            "ambiguity": float_token(trace.ambiguity),
            "conflict": float_token(trace.conflict),
            "stability_epochs": trace.stability_epochs,
            "derivation_kind": trace.derivation_kind,
            "geometry_refs": trace.geometry_refs,
        }
    )


def _reject_duplicate_trace_ids(trace_ids) -> None:
    seen: set[str] = set()
    for trace_id in trace_ids:
        if trace_id in seen:
            raise ValueError("duplicate trace_id")
        seen.add(trace_id)
