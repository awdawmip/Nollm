"""DR1 Recall Resolver foundation."""

from __future__ import annotations

from hashlib import sha256

from nollm.dream_geometry.evidence import MemorySubstrateStore
from nollm.dream_geometry.field.types import CoarseCover, GrowthTrace
from nollm.dream_geometry.protocol.contracts import CoverState, TraceState

from .projection import projection_for_trace, query_atoms, relative_time_required
from .qualification import qualify_shard
from .traversal import direction_warnings, traversal_records
from .types import (
    ProbeAtom,
    ProposalAdmission,
    RecallDigest,
    RecallDigestStatus,
    RecallPolicy,
    RecallResultItem,
    RecallUniverse,
    RuntimeTimeResolution,
    TraceSemanticProjection,
)


def resolve_recall(
    probe,
    universe: RecallUniverse,
    evidence_store: MemorySubstrateStore,
    *,
    runtime_time: RuntimeTimeResolution | None = None,
    policy: RecallPolicy = RecallPolicy(),
) -> RecallDigest:
    warnings = list(direction_warnings(universe.coverage_up, universe.coverage_down))
    discarded: list[str] = []

    if relative_time_required(probe):
        if runtime_time is None or not runtime_time.complete:
            return _digest(
                probe.probe_id,
                RecallDigestStatus.deferred,
                (),
                (),
                tuple(warnings + ["DEFERRED_TIME_RESOLUTION_REQUIRED"]),
                (),
                0.0,
                False,
            )
    elif runtime_time is not None:
        warnings.append("DR1_RUNTIME_TIME_SUPPLIED_WITHOUT_RELATIVE_QUERY")

    atoms = query_atoms(probe, runtime_time)
    if not atoms:
        warnings.append("DR1_NO_EXACT_QUERY_ATOMS")

    current_records = tuple(record for record in universe.proposal_records if record.admission is ProposalAdmission.current_accepted)
    if policy.include_legacy_context:
        warnings.append("DR1_LEGACY_PROPOSALS_CONTEXT_ONLY")
    projections: dict[str, TraceSemanticProjection] = {}
    for trace in universe.traces:
        if trace.state is not TraceState.accepted:
            discarded.append(f"{trace.trace_id}:DR1_TRACE_NOT_ACCEPTED")
            continue
        projection = projection_for_trace(trace, current_records)
        if projection is None:
            discarded.append(f"{trace.trace_id}:DR1_TRACE_STEP_BINDING_MISSING")
            continue
        projections[trace.trace_id] = projection

    traversal = traversal_records(universe.covers, universe.coverage_down)
    result_items: list[RecallResultItem] = []
    gravity_applied = False
    for cover in _eligible_covers(universe.covers, discarded):
        support_traces = tuple(trace for trace in universe.traces if trace.trace_id in cover.support_trace_ids)
        matched = _matched_support(atoms, support_traces, projections)
        matched_axes = tuple(sorted({projection.axis_id for _, projection in matched}))
        if len(matched_axes) < max(1, policy.min_required_axis_matches):
            discarded.append(f"{cover.cover_id}:DR1_INSUFFICIENT_EXACT_AXIS_MATCH")
            continue
        gravity_bonus = _gravity_bonus(cover, universe, policy)
        if gravity_bonus > 0.0:
            gravity_applied = True
        for shard_id in sorted({trace.origin_shard_id for trace, _ in matched}):
            qualification = qualify_shard(evidence_store, shard_id, policy)
            context_ids = _context_ids(shard_id, universe)
            if not qualification.included_as_evidence and not _include_context(qualification.usage_state, policy):
                discarded.append(f"{shard_id}:DR1_USAGE_STATE_EXCLUDED")
                continue
            trace_ids = tuple(sorted(trace.trace_id for trace, _ in matched if trace.origin_shard_id == shard_id))
            projection_refs = tuple(sorted(projection.step_id for trace, projection in matched if trace.origin_shard_id == shard_id))
            score = float(len(matched_axes)) + float(cover.mass) - float(cover.genericity) - float(cover.ambiguity) - float(cover.conflict) + gravity_bonus
            result_items.append(
                RecallResultItem(
                    shard_id,
                    cover.cover_id,
                    trace_ids,
                    matched_axes,
                    score,
                    qualification,
                    projection_refs,
                    context_ids,
                )
            )

    items = tuple(sorted(result_items, key=_result_sort_key))
    residual = sum(record.residual_mass for record in traversal)
    return _digest(probe.probe_id, RecallDigestStatus.resolved, items, traversal, tuple(dict.fromkeys(warnings)), tuple(discarded), residual, gravity_applied)


def _eligible_covers(covers: tuple[CoarseCover, ...], discarded: list[str]) -> tuple[CoarseCover, ...]:
    eligible: list[CoarseCover] = []
    for cover in covers:
        if cover.state not in {CoverState.stable, CoverState.crystallized}:
            discarded.append(f"{cover.cover_id}:DR1_COVER_NOT_STABLE")
            continue
        if cover.provisional_mass != 0.0 or len(cover.support_keys) < 2 or len(cover.axes_present) < 2:
            discarded.append(f"{cover.cover_id}:DR1_COVER_STRUCTURAL_RULE_FAILED")
            continue
        eligible.append(cover)
    return tuple(eligible)


def _matched_support(
    atoms: tuple[ProbeAtom, ...],
    traces: tuple[GrowthTrace, ...],
    projections: dict[str, TraceSemanticProjection],
) -> tuple[tuple[GrowthTrace, TraceSemanticProjection], ...]:
    atom_keys = {(atom.axis_id, atom.expression) for atom in atoms if atom.required}
    matches = []
    for trace in traces:
        projection = projections.get(trace.trace_id)
        if projection is None:
            continue
        if (projection.axis_id, projection.expression) in atom_keys:
            matches.append((trace, projection))
    return tuple(matches)


def _gravity_bonus(cover: CoarseCover, universe: RecallUniverse, policy: RecallPolicy) -> float:
    snapshot = universe.gravity_snapshot
    if snapshot is None or not policy.apply_gravity_tie_break:
        return 0.0
    if snapshot.chart_fingerprint != cover.chart_fingerprint:
        return 0.0
    for contribution in snapshot.contributions:
        if contribution.cover_id == cover.cover_id:
            return min(0.25, max(0.0, contribution.potential) / 1000.0)
    return 0.0


def _include_context(usage_state: str, policy: RecallPolicy) -> bool:
    if usage_state == "retired":
        return policy.include_retired_context
    if usage_state == "rejected":
        return policy.include_rejected_context
    return False


def _context_ids(shard_id: str, universe: RecallUniverse) -> tuple[str, ...]:
    ids: list[str] = []
    for interpretation in universe.interpretation_records:
        if interpretation.subject_shard_id == shard_id:
            ids.append(interpretation.interpretation_id)
    for thread in universe.revision_threads:
        if shard_id in thread.member_record_ids:
            ids.append(thread.thread_id)
    return tuple(sorted(ids))


def _result_sort_key(item: RecallResultItem) -> tuple[int, float, int, str]:
    tier_rank = {"primary_active": 0, "primary_tentative": 1, "context_retired": 2, "context_rejected": 3}.get(item.qualification.tier, 9)
    return (tier_rank, -item.structural_score, -len(item.matched_axes), item.shard_id)


def _digest(
    probe_id: str,
    status: RecallDigestStatus,
    items: tuple[RecallResultItem, ...],
    traversal,
    warnings: tuple[str, ...],
    discarded: tuple[str, ...],
    residual: float,
    gravity_applied: bool,
) -> RecallDigest:
    payload = f"{probe_id}|{status.value}|{tuple(item.shard_id for item in items)}|{warnings}|{discarded}|{residual:.17g}|{gravity_applied}"
    return RecallDigest(
        "recall_digest:" + sha256(payload.encode("utf-8")).hexdigest()[:32],
        probe_id,
        status,
        True,
        items,
        tuple(traversal),
        warnings,
        discarded,
        residual,
        gravity_applied,
        {"contract_version": "dr1.v1", "storage": "ephemeral"},
    )


__all__ = ["resolve_recall"]
