"""DR1 Recall Resolver foundation."""

from __future__ import annotations

from hashlib import sha256

from nollm.dream_geometry.cortex.types import CompiledQueryProbe
from nollm.dream_geometry.evidence import MemorySubstrateStore
from nollm.dream_geometry.field.types import CoarseCover, GrowthTrace, cell_ref_key
from nollm.dream_geometry.protocol.contracts import CoverState, TraceState

from .projection import projection_for_trace, query_atoms, relative_time_required
from .qualification import qualify_shard
from .time_projection import validate_runtime_time_resolution
from .types import (
    ProbeAtom,
    ProposalAdmission,
    RecallDigest,
    RecallDigestStatus,
    RecallPolicy,
    RecallResultItem,
    RecallValidationError,
    RecallUniverse,
    RuntimeTimeResolution,
    TraceSemanticProjection,
    TraversalRecord,
)
from .universe import validate_recall_universe


GRAVITY_TIE_EPSILON = 1e-12


def resolve_recall(
    probe,
    universe: RecallUniverse,
    evidence_store: MemorySubstrateStore,
    *,
    runtime_time: RuntimeTimeResolution | None = None,
    policy: RecallPolicy = RecallPolicy(),
) -> RecallDigest:
    if not isinstance(probe, CompiledQueryProbe):
        return _digest(str(getattr(probe, "probe_id", "invalid_probe")), RecallDigestStatus.rejected, (), (), (), ("DR1_INVALID_QUERY_PROBE",), ("DR1_INVALID_QUERY_PROBE",), 0.0, False)
    try:
        _validate_policy_for_probe(policy, probe)
        time_warnings = validate_runtime_time_resolution(probe, runtime_time)
        validated = validate_recall_universe(universe, evidence_store)
    except RecallValidationError as exc:
        return _digest(probe.probe_id, RecallDigestStatus.rejected, (), (), (), (exc.reason_code,), (str(exc),), 0.0, False)
    except ValueError as exc:
        return _digest(probe.probe_id, RecallDigestStatus.rejected, (), (), (), ("DR1_POLICY_INVALID",), (str(exc),), 0.0, False)

    warnings = list(time_warnings)
    discarded: list[str] = []

    if "DEFERRED_TIME_RESOLUTION_REQUIRED" in warnings:
        return _digest(probe.probe_id, RecallDigestStatus.deferred, (), (), (), tuple(warnings), (), 0.0, False)

    atoms = query_atoms(probe, runtime_time)
    if not atoms:
        warnings.append("DR1_NO_EXACT_QUERY_ATOMS")

    current_records = validated.current_records
    if policy.include_legacy_context:
        warnings.append("DR1_LEGACY_PROPOSALS_CONTEXT_ONLY")
    projections: dict[str, TraceSemanticProjection] = {}
    for trace in sorted(universe.traces, key=lambda item: item.trace_id):
        if trace.state is not TraceState.accepted:
            discarded.append(f"{trace.trace_id}:DR1_TRACE_NOT_ACCEPTED")
            continue
        projection = projection_for_trace(trace, current_records)
        if projection is None:
            discarded.append(f"{trace.trace_id}:DR1_TRACE_STEP_BINDING_MISSING")
            continue
        projections[trace.trace_id] = projection

    if not universe.coverage_down:
        discarded.append("DR1_K_DOWN_REQUIRED")
        return _digest(probe.probe_id, RecallDigestStatus.insufficient_evidence, (), (), (), tuple(warnings), tuple(discarded), 0.0, False)

    result_items: list[RecallResultItem] = []
    traversal: list[TraversalRecord] = []
    eligible_covers = _eligible_covers(universe.covers, discarded)
    if len(eligible_covers) > policy.max_seed_covers:
        eligible_covers = eligible_covers[: policy.max_seed_covers]
        discarded.append("DR1_BUDGET_MAX_SEED_COVERS")
    budget_exhausted = False
    for cover in eligible_covers:
        support_traces = tuple(trace for trace in universe.traces if trace.trace_id in cover.support_trace_ids)
        matched = _matched_support(atoms, support_traces, projections)
        matched_axes = tuple(sorted({projection.axis_id for _, projection in matched}))
        required_axes = len({atom.axis_id for atom in atoms if atom.required})
        minimum_axes = max(2, min(policy.min_required_axis_matches, required_axes))
        if len(matched_axes) < max(1, minimum_axes):
            discarded.append(f"{cover.cover_id}:DR1_INSUFFICIENT_EXACT_AXIS_MATCH")
            continue
        executed, records, budget_reason = _execute_traversal(cover, matched, universe, probe)
        if budget_reason is not None:
            discarded.append(budget_reason)
            budget_exhausted = True
            continue
        if not executed:
            discarded.append(f"{cover.cover_id}:DR1_K_UP_DOWN_PATH_MISSING")
            continue
        traversal.extend(records)
        for shard_id in sorted({trace.origin_shard_id for trace, _ in matched}):
            try:
                qualification = qualify_shard(evidence_store, shard_id, policy)
            except Exception:
                discarded.append(f"{shard_id}:DR1_TRACE_ORIGIN_SHARD_MISSING")
                continue
            context_ids = _context_ids(shard_id, universe)
            if not qualification.included_as_evidence and not _include_context(qualification.usage_state, policy):
                discarded.append(f"{shard_id}:DR1_USAGE_STATE_EXCLUDED")
                continue
            trace_ids = tuple(sorted(trace.trace_id for trace, _ in matched if trace.origin_shard_id == shard_id))
            projection_refs = tuple(sorted(projection.step_id for trace, projection in matched if trace.origin_shard_id == shard_id))
            score = _core_score(cover, matched_axes)
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

    sorted_items, gravity_applied, gravity_warning = _sort_with_gravity(result_items, universe)
    if gravity_warning:
        warnings.append(gravity_warning)
    limited_items = sorted_items[: policy.max_result_items]
    if len(sorted_items) > len(limited_items):
        discarded.append("DR1_BUDGET_MAX_RESULT_ITEMS")
        budget_exhausted = True
    primary = tuple(item for item in limited_items if item.qualification.included_as_evidence)
    contextual = tuple(item for item in limited_items if not item.qualification.included_as_evidence)
    residual = sum(record.residual_mass for record in traversal)
    if budget_exhausted:
        status = RecallDigestStatus.budget_exhausted
    elif primary:
        status = RecallDigestStatus.resolved
    elif contextual:
        status = RecallDigestStatus.insufficient_evidence
    else:
        status = RecallDigestStatus.insufficient_evidence
    return _digest(probe.probe_id, status, primary, contextual, tuple(traversal), tuple(dict.fromkeys(warnings)), tuple(discarded), residual, gravity_applied)


def _eligible_covers(covers: tuple[CoarseCover, ...], discarded: list[str]) -> tuple[CoarseCover, ...]:
    eligible: list[CoarseCover] = []
    for cover in sorted(covers, key=lambda item: item.cover_id):
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


def _gravity_potential(cover: CoarseCover, universe: RecallUniverse) -> float:
    snapshot = universe.gravity_snapshot
    if snapshot is None:
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


def _core_score(cover: CoarseCover, matched_axes: tuple[str, ...]) -> float:
    return float(len(matched_axes)) + float(cover.mass) - float(cover.genericity) - float(cover.ambiguity) - float(cover.conflict)


def _sort_with_gravity(items: list[RecallResultItem], universe: RecallUniverse) -> tuple[tuple[RecallResultItem, ...], bool, str | None]:
    if universe.gravity_snapshot is not None:
        cover_by_id = {cover.cover_id: cover for cover in universe.covers}
        if any(universe.gravity_snapshot.chart_fingerprint != cover_by_id[item.cover_id].chart_fingerprint for item in items if item.cover_id in cover_by_id):
            return tuple(sorted(items, key=_result_sort_key)), False, "DR1_GRAVITY_SNAPSHOT_IGNORED_IDENTITY_MISMATCH"
    ordered: list[RecallResultItem] = []
    gravity_applied = False
    for _, group in _score_groups(tuple(sorted(items, key=_result_sort_key))):
        if len(group) == 1:
            ordered.extend(group)
            continue
        group_with_gravity = sorted(group, key=lambda item: (-_gravity_potential(next(cover for cover in universe.covers if cover.cover_id == item.cover_id), universe), _result_sort_key(item)))
        if tuple(group_with_gravity) != group:
            gravity_applied = True
        ordered.extend(group_with_gravity)
    return tuple(ordered), gravity_applied, None


def _score_groups(items: tuple[RecallResultItem, ...]) -> tuple[tuple[float, list[RecallResultItem]], ...]:
    groups: list[tuple[float, list[RecallResultItem]]] = []
    for item in items:
        for score, group in groups:
            if abs(item.structural_score - score) <= GRAVITY_TIE_EPSILON:
                group.append(item)
                break
        else:
            groups.append((item.structural_score, [item]))
    return tuple(groups)


def _execute_traversal(cover: CoarseCover, matched, universe: RecallUniverse, probe: CompiledQueryProbe) -> tuple[bool, tuple[TraversalRecord, ...], str | None]:
    distinct_charts: set[str] = set()
    records: list[TraversalRecord] = []
    cover_ref = cell_ref_key(cover.support_cell)
    up_records = []
    for trace, _ in matched:
        trace_ref = cell_ref_key(trace.cell)
        up = [
            distribution
            for distribution in universe.coverage_up
            if cell_ref_key(distribution.source_cell) == trace_ref and any(cell_ref_key(kernel.target_cell) == cover_ref for kernel in distribution.kernels)
        ]
        if not up:
            return False, (), None
        distribution = up[0]
        mass_out = sum(kernel.weight * trace.mass for kernel in distribution.kernels)
        residual = distribution.residual.mass * trace.mass
        if abs((mass_out + residual) - trace.mass) > 1e-9:
            return False, (), "DR1_K_UP_MASS_ACCOUNTING_FAILED"
        up_records.append(
            TraversalRecord(
                "up",
                cover.cover_id,
                trace_ref,
                distribution.direction.value,
                tuple(cell_ref_key(kernel.target_cell) for kernel in distribution.kernels),
                residual,
                tuple(reason.value for reason in distribution.residual.reasons),
                trace.mass,
                mass_out,
                "DR1_K_UP_EXECUTED",
            )
        )
        distinct_charts.add(getattr(trace.cell.cell_ref, "chart_id"))
    down = [distribution for distribution in universe.coverage_down if cell_ref_key(distribution.source_cell) == cover_ref]
    if not down:
        return False, (), None
    down_distribution = down[0]
    if len(down_distribution.kernels) > probe.budget.max_cells_per_layer:
        return False, (), "DR1_BUDGET_MAX_CELLS_PER_LAYER"
    distinct_charts.add(getattr(down_distribution.source_cell.cell_ref, "chart_id"))
    distinct_charts.update(getattr(kernel.target_cell.cell_ref, "chart_id") for kernel in down_distribution.kernels)
    if len(distinct_charts) > probe.budget.max_charts:
        return False, (), "DR1_BUDGET_MAX_CHARTS"
    layers = {getattr(down_distribution.source_cell.chart_fingerprint, "layer_index", 0)}
    layers.update(getattr(kernel.target_cell.chart_fingerprint, "layer_index", 0) for kernel in down_distribution.kernels)
    if len(layers) > probe.budget.max_layers:
        return False, (), "DR1_BUDGET_MAX_LAYERS"
    down_mass_out = sum(kernel.weight for kernel in down_distribution.kernels)
    records.extend(up_records)
    records.append(
        TraversalRecord(
            "down",
            cover.cover_id,
            cover_ref,
            down_distribution.direction.value,
            tuple(cell_ref_key(kernel.target_cell) for kernel in down_distribution.kernels),
            down_distribution.residual.mass,
            tuple(reason.value for reason in down_distribution.residual.reasons),
            1.0,
            down_mass_out,
            "DR1_K_DOWN_EXECUTED",
        )
    )
    return True, tuple(records), None


def _validate_policy_for_probe(policy: RecallPolicy, probe: CompiledQueryProbe) -> None:
    if policy.max_seed_covers > probe.budget.max_cells_per_layer:
        raise RecallValidationError("DR1_POLICY_MAX_SEED_EXCEEDS_QUERY_BUDGET", policy.policy_id)


def _digest(
    probe_id: str,
    status: RecallDigestStatus,
    primary: tuple[RecallResultItem, ...],
    contextual: tuple[RecallResultItem, ...],
    traversal,
    warnings: tuple[str, ...],
    discarded: tuple[str, ...],
    residual: float,
    gravity_applied: bool,
) -> RecallDigest:
    items = primary + contextual
    payload = f"{probe_id}|{status.value}|{tuple(item.shard_id for item in items)}|{warnings}|{discarded}|{residual:.17g}|{gravity_applied}"
    return RecallDigest(
        "recall_digest:" + sha256(payload.encode("utf-8")).hexdigest()[:32],
        probe_id,
        status,
        True,
        items,
        primary,
        contextual,
        tuple(traversal),
        warnings,
        discarded,
        residual,
        gravity_applied,
        {"contract_version": "dr1.v1", "storage": "ephemeral"},
    )


__all__ = ["resolve_recall"]
