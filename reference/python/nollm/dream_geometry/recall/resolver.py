"""DR1 Recall Resolver foundation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from nollm.dream_geometry.cortex.types import CompiledQueryProbe
from nollm.dream_geometry.evidence import MemorySubstrateStore
from nollm.dream_geometry.field.types import CoarseCover, GrowthTrace, cell_ref_key
from nollm.dream_geometry.geometry.coverage import CoverageDistribution
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
PATH_MASS_TIE_EPSILON = 1e-12


@dataclass(frozen=True)
class _SeedCandidate:
    cover: CoarseCover
    matched: tuple[tuple[GrowthTrace, TraceSemanticProjection], ...]
    matched_axes: tuple[str, ...]


@dataclass(frozen=True)
class _Route:
    trace: GrowthTrace
    projection: TraceSemanticProjection
    cover: CoarseCover
    m_up: float
    m_down: float
    path_mass: float
    up_distribution: CoverageDistribution
    down_distribution: CoverageDistribution
    target_cell_ref: str


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

    if not universe.coverage_up or not universe.coverage_down:
        discarded.append("DR1_K_UP_DOWN_REQUIRED")
        if not universe.coverage_down:
            discarded.append("DR1_K_DOWN_REQUIRED")
        return _digest(probe.probe_id, RecallDigestStatus.insufficient_evidence, (), (), (), tuple(warnings), tuple(discarded), 0.0, False)

    eligible_covers = _eligible_covers(universe.covers, discarded)
    seed_candidates: list[_SeedCandidate] = []
    required_axes = len({atom.axis_id for atom in atoms if atom.required})
    minimum_axes = max(2, min(policy.min_required_axis_matches, required_axes))
    for cover in eligible_covers:
        support_traces = tuple(trace for trace in universe.traces if trace.trace_id in cover.support_trace_ids)
        matched = _matched_support(atoms, support_traces, projections)
        matched_axes = tuple(sorted({projection.axis_id for _, projection in matched}))
        if len(matched_axes) < max(1, minimum_axes):
            discarded.append(f"{cover.cover_id}:DR1_INSUFFICIENT_EXACT_AXIS_MATCH")
            continue
        seed_candidates.append(_SeedCandidate(cover, matched, matched_axes))

    selected_seeds = tuple(seed_candidates)
    budget_exhausted = False
    if len(seed_candidates) > policy.max_seed_covers:
        selected_seeds = tuple(seed_candidates[: policy.max_seed_covers])
        discarded.append("DR1_BUDGET_MAX_SEED_COVERS")
        budget_exhausted = True

    route_candidates: list[_Route] = []
    for candidate in selected_seeds:
        routes = _route_candidates_for_cover(candidate.cover, candidate.matched, universe)
        if not routes:
            discarded.append(f"{candidate.cover.cover_id}:DR1_K_UP_DOWN_PATH_MISSING")
            continue
        route_axes = tuple(sorted({route.projection.axis_id for route in routes}))
        if len(route_axes) < max(1, minimum_axes):
            discarded.append(f"{candidate.cover.cover_id}:DR1_INSUFFICIENT_EXECUTABLE_AXIS_MATCH")
            continue
        route_candidates.extend(routes)

    deduped_routes, dedup_discarded = _dedupe_routes(tuple(route_candidates))
    discarded.extend(dedup_discarded)
    traversal = list(_traversal_records_for_routes(deduped_routes))
    global_budget_reason = _check_global_route_budget(deduped_routes, probe, policy) if deduped_routes else None
    if global_budget_reason is not None:
        discarded.append(global_budget_reason)
        budget_exhausted = True

    result_items: list[RecallResultItem] = []
    if global_budget_reason is None:
        routes_by_cover = {route.cover.cover_id: tuple(item for item in deduped_routes if item.cover.cover_id == route.cover.cover_id) for route in deduped_routes}
        for cover_id in sorted(routes_by_cover):
            cover_routes = routes_by_cover[cover_id]
            routes_by_shard = {route.trace.origin_shard_id: tuple(item for item in cover_routes if item.trace.origin_shard_id == route.trace.origin_shard_id) for route in cover_routes}
            for shard_id in sorted(routes_by_shard):
                try:
                    qualification = qualify_shard(evidence_store, shard_id, policy)
                except Exception:
                    discarded.append(f"{shard_id}:DR1_TRACE_ORIGIN_SHARD_MISSING")
                    continue
                context_ids = _context_ids(shard_id, universe, evidence_store, policy)
                if not qualification.included_as_evidence and not _include_context(qualification.usage_state, policy):
                    discarded.append(f"{shard_id}:DR1_USAGE_STATE_EXCLUDED")
                    continue
                shard_routes = routes_by_shard[shard_id]
                trace_ids = tuple(sorted({route.trace.trace_id for route in shard_routes}))
                projection_refs = tuple(sorted({route.projection.step_id for route in shard_routes}))
                shard_axes = tuple(sorted({route.projection.axis_id for route in shard_routes}))
                cover = shard_routes[0].cover
                score = _core_score(cover, shard_axes)
                result_items.append(
                    RecallResultItem(
                        shard_id,
                        cover.cover_id,
                        trace_ids,
                        shard_axes,
                        score,
                        qualification,
                        projection_refs,
                        context_ids,
                        sum(route.path_mass for route in shard_routes),
                        tuple(sorted(f"{route.trace.trace_id}->{cover.cover_id}->{route.target_cell_ref}" for route in shard_routes)),
                    )
                )

    sorted_items, gravity_applied, gravity_warning = _sort_with_gravity(result_items, universe)
    if gravity_warning:
        warnings.append(gravity_warning)
    primary_all = tuple(item for item in sorted_items if item.qualification.included_as_evidence)
    contextual_all = tuple(item for item in sorted_items if not item.qualification.included_as_evidence)
    result_limit = policy.max_result_items
    limited_primary = primary_all[:result_limit]
    remaining_slots = max(0, result_limit - len(limited_primary))
    limited_contextual = contextual_all[:remaining_slots]
    limited_items = limited_primary + limited_contextual
    if len(sorted_items) > len(limited_items):
        discarded.append("DR1_BUDGET_MAX_RESULT_ITEMS")
        budget_exhausted = True
    primary = limited_primary
    contextual = limited_contextual
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
    if cover.cover_id not in snapshot.input_cover_ids:
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


def _context_ids(shard_id: str, universe: RecallUniverse, evidence_store: MemorySubstrateStore, policy: RecallPolicy) -> tuple[str, ...]:
    ids: list[str] = []
    for interpretation in universe.interpretation_records:
        if interpretation.subject_shard_id == shard_id:
            usage = evidence_store.get_usage_state(interpretation.interpretation_id).value
            if usage in {"active", "tentative"} or _include_context(usage, policy):
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
        snapshot = universe.gravity_snapshot
        if snapshot.policy_id != "dg2_gravity_policy" or snapshot.policy_version != "1":
            return tuple(sorted(items, key=_result_sort_key)), False, "DR1_GRAVITY_SNAPSHOT_IGNORED_IDENTITY_MISMATCH"
        if any(snapshot.chart_fingerprint != cover_by_id[item.cover_id].chart_fingerprint for item in items if item.cover_id in cover_by_id):
            return tuple(sorted(items, key=_result_sort_key)), False, "DR1_GRAVITY_SNAPSHOT_IGNORED_IDENTITY_MISMATCH"
        if any(item.cover_id not in snapshot.input_cover_ids for item in items):
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


def _score_groups(items: tuple[RecallResultItem, ...]) -> tuple[tuple[tuple[str, float], list[RecallResultItem]], ...]:
    groups: list[tuple[tuple[str, float], list[RecallResultItem]]] = []
    for item in items:
        for key, group in groups:
            tier, score = key
            if item.qualification.tier == tier and abs(item.structural_score - score) <= GRAVITY_TIE_EPSILON:
                group.append(item)
                break
        else:
            groups.append(((item.qualification.tier, item.structural_score), [item]))
    return tuple(groups)


def _route_candidates_for_cover(
    cover: CoarseCover,
    matched: tuple[tuple[GrowthTrace, TraceSemanticProjection], ...],
    universe: RecallUniverse,
) -> tuple[_Route, ...]:
    routes: list[_Route] = []
    cover_ref = cell_ref_key(cover.support_cell)
    up_by_source = {cell_ref_key(distribution.source_cell): distribution for distribution in universe.coverage_up}
    down_by_source = {cell_ref_key(distribution.source_cell): distribution for distribution in universe.coverage_down}
    down_distribution = down_by_source.get(cover_ref)
    if down_distribution is None:
        return ()
    for trace, projection in sorted(matched, key=lambda item: item[0].trace_id):
        trace_ref = cell_ref_key(trace.cell)
        up_distribution = up_by_source.get(trace_ref)
        if up_distribution is None:
            continue
        up_weight = sum(kernel.weight for kernel in up_distribution.kernels if cell_ref_key(kernel.target_cell) == cover_ref)
        down_weight = sum(kernel.weight for kernel in down_distribution.kernels if cell_ref_key(kernel.target_cell) == trace_ref)
        if up_weight <= 0.0 or down_weight <= 0.0:
            continue
        m_up = float(trace.mass) * float(up_weight)
        m_down = float(down_weight)
        path_mass = m_up * m_down
        routes.append(_Route(trace, projection, cover, m_up, m_down, path_mass, up_distribution, down_distribution, trace_ref))
    return tuple(sorted(routes, key=_route_sort_key))


def _dedupe_routes(routes: tuple[_Route, ...]) -> tuple[tuple[_Route, ...], tuple[str, ...]]:
    winners: dict[tuple[str, str, str], _Route] = {}
    discarded: list[str] = []
    for route in sorted(routes, key=_route_sort_key):
        key = _route_identity_key(route)
        current = winners.get(key)
        if current is None:
            winners[key] = route
            continue
        if route.path_mass > current.path_mass + PATH_MASS_TIE_EPSILON:
            discarded.append(f"{current.trace.trace_id}->{current.cover.cover_id}:DR1_ROUTE_DEDUPED_GLOBAL")
            winners[key] = route
            continue
        if abs(route.path_mass - current.path_mass) <= PATH_MASS_TIE_EPSILON and _route_sort_key(route) < _route_sort_key(current):
            discarded.append(f"{current.trace.trace_id}->{current.cover.cover_id}:DR1_ROUTE_DEDUPED_GLOBAL")
            winners[key] = route
            continue
        discarded.append(f"{route.trace.trace_id}->{route.cover.cover_id}:DR1_ROUTE_DEDUPED_GLOBAL")
    return tuple(sorted(winners.values(), key=_route_sort_key)), tuple(discarded)


def _traversal_records_for_routes(routes: tuple[_Route, ...]) -> tuple[TraversalRecord, ...]:
    records: list[TraversalRecord] = []
    for route in routes:
        cover_ref = cell_ref_key(route.cover.support_cell)
        up_mass_out = sum(kernel.weight * route.trace.mass for kernel in route.up_distribution.kernels)
        up_residual = route.up_distribution.residual.mass * route.trace.mass
        records.append(
            TraversalRecord(
                "up",
                route.cover.cover_id,
                cell_ref_key(route.trace.cell),
                route.up_distribution.direction.value,
                tuple(sorted(cell_ref_key(kernel.target_cell) for kernel in route.up_distribution.kernels)),
                up_residual,
                tuple(reason.value for reason in route.up_distribution.residual.reasons),
                route.trace.mass,
                up_mass_out,
                route.trace.trace_id,
                cover_ref,
                route.m_up,
                route.m_down,
                route.path_mass,
                "DR1_K_UP_EXECUTED",
            )
        )
        down_target_refs = tuple(sorted(cell_ref_key(kernel.target_cell) for kernel in route.down_distribution.kernels))
        records.append(
            TraversalRecord(
                "down",
                route.cover.cover_id,
                cover_ref,
                route.down_distribution.direction.value,
                down_target_refs,
                route.down_distribution.residual.mass,
                tuple(reason.value for reason in route.down_distribution.residual.reasons),
                1.0,
                sum(kernel.weight for kernel in route.down_distribution.kernels),
                route.trace.trace_id,
                route.target_cell_ref,
                route.m_up,
                route.m_down,
                route.path_mass,
                "DR1_K_DOWN_EXECUTED",
            )
        )
    return tuple(records)


def _check_global_route_budget(routes: tuple[_Route, ...], probe: CompiledQueryProbe, policy: RecallPolicy) -> str | None:
    cells_by_layer: dict[int, set[str]] = {}
    chart_fingerprints: set[object] = set()
    lateral_edges: set[tuple[str, object, object]] = set()
    for route in routes:
        route_cells = (route.trace.cell, route.cover.support_cell) + tuple(kernel.target_cell for kernel in route.down_distribution.kernels if cell_ref_key(kernel.target_cell) == route.target_cell_ref)
        for cell in route_cells:
            layer = getattr(cell.chart_fingerprint, "layer_index", 0)
            cells_by_layer.setdefault(layer, set()).add(cell_ref_key(cell))
            chart_fingerprints.add(cell.chart_fingerprint)
        if route.trace.cell.chart_fingerprint != route.cover.support_cell.chart_fingerprint:
            lateral_edges.add((route.up_distribution.direction.value, route.trace.cell.chart_fingerprint, route.cover.support_cell.chart_fingerprint))
        if route.cover.support_cell.chart_fingerprint != route.trace.cell.chart_fingerprint:
            lateral_edges.add((route.down_distribution.direction.value, route.cover.support_cell.chart_fingerprint, route.trace.cell.chart_fingerprint))
    if any(len(cells) > probe.budget.max_cells_per_layer for cells in cells_by_layer.values()):
        return "DR1_BUDGET_MAX_CELLS_PER_LAYER"
    if len(cells_by_layer) > probe.budget.max_layers:
        return "DR1_BUDGET_MAX_LAYERS"
    if len(chart_fingerprints) > probe.budget.max_charts:
        return "DR1_BUDGET_MAX_CHARTS"
    if lateral_edges and not policy.allow_verified_chart_hops:
        return "DR1_BUDGET_MAX_LATERAL_HOPS"
    if len(lateral_edges) > policy.max_lateral_hops:
        return "DR1_BUDGET_MAX_LATERAL_HOPS"
    return None


def _route_identity_key(route: _Route) -> tuple[str, str, str]:
    return (route.trace.origin_shard_id, route.trace.axis, cell_ref_key(route.trace.cell))


def _route_sort_key(route: _Route) -> tuple[str, str, str, str, str]:
    return (route.cover.cover_id, route.trace.trace_id, route.trace.origin_shard_id, route.trace.axis, route.target_cell_ref)


def _validate_policy_for_probe(policy: RecallPolicy, probe: CompiledQueryProbe) -> None:
    if probe.budget.max_charts < 1 or probe.budget.max_layers < 1 or probe.budget.max_cells_per_layer < 0:
        raise RecallValidationError("DR1_QUERY_BUDGET_INVALID", policy.policy_id)


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
