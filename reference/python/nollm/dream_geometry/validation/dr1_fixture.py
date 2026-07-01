"""Synthetic DR1 validation fixture shared by report and tests."""

from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.cortex.types import AxisRay, CompilationBudget, CompilationDecision, CompilationReceipt, CompiledGrowthProposal, CompiledQueryProbe, GrowthStep, QueryBudget, TextSpanRef, payload_fingerprint
from nollm.dream_geometry.evidence import DreamShard, InterpretationRecord, OriginDescriptor, RevisionEdge, RevisionThread, TemporalContext, UsageStateTransition, open_store
from nollm.dream_geometry.field.types import CoarseCover, CoverPolicy, GravityContribution, GravitySnapshot, GrowthTrace, cell_ref_key
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2
from nollm.dream_geometry.protocol.contracts import (
    CoverState,
    GrowthBasis,
    InterpretationAuthoringMode,
    InterpretationKind,
    OriginKind,
    RevisionRelation,
    TraceState,
    UsageState,
)
from nollm.dream_geometry.recall.projection import basis_ref_key
from nollm.dream_geometry.recall.types import ProposalAdmission, ProposalReadRecord, RecallUniverse, ResolvedRelativeSpan, RuntimeTimeResolution


def build_fixture(tmp_path, *, usage_state: UsageState = UsageState.active):
    store = open_store(tmp_path / "evidence")
    shard = DreamShard(
        "shard:rain",
        "Kunming had rain on 2026-06-29.",
        OriginDescriptor(OriginKind.user_utterance, "synthetic:dr1", "turn:1", "user"),
        TemporalContext("2026-06-30T08:00:00+08:00", "2026-06-29", "2026-06-30T08:00:00+08:00", "en-US"),
        (),
        UsageState.tentative,
    )
    store.put_dream_shard(shard)
    if usage_state is not UsageState.tentative:
        store.record_usage_transition(UsageStateTransition("state:rain:" + usage_state.value, shard.shard_id, UsageState.tentative, usage_state, ("reason:fixture",), "2026-06-30T08:01:00+08:00"))

    interpretation = InterpretationRecord(
        "interpretation:rain-context",
        shard.shard_id,
        InterpretationKind.classification,
        "Weather note classification.",
        InterpretationAuthoringMode.llm_proposed,
        ("basis:fixture",),
        (),
        UsageState.tentative,
    )
    store.put_interpretation(interpretation)
    revision = RevisionThread("revision:rain", (shard.shard_id, interpretation.interpretation_id), (RevisionEdge(interpretation.interpretation_id, shard.shard_id, RevisionRelation.clarifies, ()),), ())
    store.put_revision_thread(revision)

    proposal = _proposal()
    receipt = _receipt(proposal)
    traces = _traces(proposal)
    cover = _cover(traces)
    policy = CoverPolicy()
    coverage_down = (compute_distribution(cover.support_cell, (traces[0].cell,), CoverageDirection.coarse_to_fine),)
    coverage_up = (compute_distribution(traces[0].cell, (cover.support_cell,), CoverageDirection.fine_to_coarse),)
    gravity = GravitySnapshot(
        "gravity:dr1",
        cover.chart_fingerprint,
        (GravityContribution(cover.cover_id, cell_ref_key(cover.support_cell), 10.0, 1.0, (), "dg2_gravity_policy"),),
        (cover.cover_id,),
        "dg2_gravity_policy",
        "1",
    )
    universe = RecallUniverse(
        (ProposalReadRecord(proposal, ProposalAdmission.current_accepted, "fixture:proposal", receipt),),
        traces,
        (cover,),
        coverage_up=coverage_up,
        coverage_down=coverage_down,
        gravity_snapshot=gravity,
        cover_policy_records=(policy,),
        interpretation_records=(interpretation,),
        revision_threads=(revision,),
    )
    return store, proposal, universe


def relative_time_resolution() -> RuntimeTimeResolution:
    return RuntimeTimeResolution(
        (
            ResolvedRelativeSpan(
                "relative_time",
                "yesterday",
                "absolute_time",
                "2026-06-29",
                "2026-06-30T08:00:00+08:00",
                "caller_runtime",
                "q:time",
                20,
                29,
                "yesterday",
                "caller_runtime",
                "1",
            ),
        ),
        True,
        "caller_runtime",
        "1",
        "2026-06-30T08:00:00+08:00",
    )


def query_probe(*, relative_time: bool = True, one_axis: bool = False) -> CompiledQueryProbe:
    axes = [
        AxisRay("location", (GrowthStep("q:location", "Kunming", "explicit_in_query", (TextSpanRef("probe:rain", 0, 7, "Kunming"),), None, False),)),
    ]
    if not one_axis:
        axes.append(AxisRay("phenomenon", (GrowthStep("q:phenomenon", "rain", "explicit_in_query", (TextSpanRef("probe:rain", 12, 16, "rain"),), None, False),)))
        if relative_time:
            axes.append(AxisRay("relative_time", (GrowthStep("q:time", "yesterday", "explicit_in_query", (TextSpanRef("probe:rain", 20, 29, "yesterday"),), None, False),)))
        else:
            axes.append(AxisRay("absolute_time", (GrowthStep("q:time", "2026-06-29", "explicit_in_query", (TextSpanRef("probe:rain", 20, 30, "2026-06-29"),), None, False),)))
    return CompiledQueryProbe("probe:rain", "Kunming rain yesterday?", tuple(axes), QueryBudget(4, 8, 4, 16), (), (), "2026-06-30T08:00:00+08:00", relative_time and not one_axis, True)


def with_legacy_proposal_only(universe: RecallUniverse) -> RecallUniverse:
    records = tuple(ProposalReadRecord(record.proposal, ProposalAdmission.legacy_dc1_read_only, record.source_ref, record.receipt) for record in universe.proposal_records)
    return replace(universe, proposal_records=records)


def with_wrong_down_direction(universe: RecallUniverse) -> RecallUniverse:
    source = universe.coverage_down[0].source_cell
    target = universe.coverage_down[0].source_cell
    wrong = compute_distribution(source, (target,), CoverageDirection.fine_to_coarse)
    return replace(universe, coverage_down=(wrong,))


def add_synthetic_cover(
    store,
    proposal: CompiledGrowthProposal,
    universe: RecallUniverse,
    *,
    cover_id: str,
    shard_id: str,
    proposal_id: str,
    trace_prefix: str,
    expressions: dict[str, str] | None = None,
    cell=None,
    usage_state: UsageState = UsageState.active,
) -> RecallUniverse:
    base_shard = store.get_dream_shard("shard:rain")
    shard = replace(base_shard, shard_id=shard_id, content=f"Synthetic DR1 shard {shard_id}.")
    store.put_dream_shard(shard)
    if usage_state is not UsageState.tentative:
        store.record_usage_transition(UsageStateTransition("state:" + shard_id + ":" + usage_state.value, shard_id, UsageState.tentative, usage_state, ("reason:fixture",), "2026-06-30T08:03:00+08:00"))
    expressions = expressions or {axis.axis_id: axis.ray[0].expression for axis in proposal.axes}
    axes = []
    for axis in proposal.axes:
        expression = expressions.get(axis.axis_id, axis.ray[0].expression)
        ref = TextSpanRef(shard_id, 0, len(expression), expression)
        step = replace(axis.ray[0], expression=expression, basis_refs=(ref,))
        axes.append(AxisRay(axis.axis_id, (step,)))
    synthetic_proposal = replace(proposal, proposal_id=proposal_id, subject_shard_id=shard_id, axes=tuple(axes))
    receipt = _receipt(synthetic_proposal)
    synthetic_cell = cell if cell is not None else universe.traces[0].cell
    traces = tuple(replace(trace, trace_id=f"{trace_prefix}:{trace.axis}", origin_shard_id=shard_id, proposal_id=proposal_id, cell=synthetic_cell) for trace in _traces(synthetic_proposal))
    cover = replace(
        _cover(traces),
        cover_id=cover_id,
        chart_fingerprint=synthetic_cell.chart_fingerprint,
        support_cell=synthetic_cell,
        support_trace_ids=tuple(trace.trace_id for trace in traces),
        support_shard_ids=(shard_id,),
        support_keys=tuple(trace.support_key for trace in traces),
        axes_present=tuple(trace.axis for trace in traces),
    )
    up = universe.coverage_up
    down = universe.coverage_down
    source_ref = cell_ref_key(synthetic_cell)
    if not any(cell_ref_key(distribution.source_cell) == source_ref for distribution in up):
        up = up + (compute_distribution(synthetic_cell, (synthetic_cell,), CoverageDirection.fine_to_coarse),)
    if not any(cell_ref_key(distribution.source_cell) == source_ref for distribution in down):
        down = down + (compute_distribution(synthetic_cell, (synthetic_cell,), CoverageDirection.coarse_to_fine),)
    return replace(
        universe,
        proposal_records=universe.proposal_records + (ProposalReadRecord(synthetic_proposal, ProposalAdmission.current_accepted, "fixture:" + proposal_id, receipt),),
        traces=universe.traces + traces,
        covers=universe.covers + (cover,),
        coverage_up=up,
        coverage_down=down,
    )


def _proposal() -> CompiledGrowthProposal:
    refs = {
        "location": TextSpanRef("shard:rain", 0, 7, "Kunming"),
        "phenomenon": TextSpanRef("shard:rain", 12, 16, "rain"),
        "absolute_time": TextSpanRef("shard:rain", 20, 30, "2026-06-29"),
    }
    axes = tuple(
        AxisRay(axis, (GrowthStep(f"step:{axis}", expression, GrowthBasis.explicit_in_shard, (refs[axis],), None, False),))
        for axis, expression in (("location", "Kunming"), ("phenomenon", "rain"), ("absolute_time", "2026-06-29"))
    )
    return CompiledGrowthProposal("proposal:rain", "shard:rain", axes, CompilationBudget(4, 8, 4), (), (), (), "2026-06-30T08:00:00+08:00")


def _receipt(proposal: CompiledGrowthProposal) -> CompilationReceipt:
    fingerprint = payload_fingerprint(proposal)
    return CompilationReceipt(
        "receipt:proposal:rain",
        "growth",
        proposal.proposal_id,
        CompilationDecision.accepted,
        (),
        fingerprint,
        fingerprint,
        proposal.submitted_at,
        {"fixture": "dr1"},
    )


def _traces(proposal: CompiledGrowthProposal) -> tuple[GrowthTrace, ...]:
    chart = LocalChart("dr1:coarse", 0, 1.0, 0.0, Vec2(0, 0))
    cell = make_hex_cell(chart, AxialCoord(0, 0))
    traces = []
    for axis in proposal.axes:
        step = axis.ray[0]
        traces.append(
            GrowthTrace(
                "trace:" + axis.axis_id,
                proposal.subject_shard_id,
                proposal.proposal_id,
                None,
                cell,
                axis.axis_id,
                GrowthBasis.explicit_in_shard,
                tuple(basis_ref_key(ref) for ref in step.basis_refs),
                1.0,
                "support:" + axis.axis_id,
                0.1,
                0.0,
                0.0,
                2,
                TraceState.accepted,
                "fixture",
                ("coverage:fixture",),
            )
        )
    return tuple(traces)


def _cover(traces: tuple[GrowthTrace, ...]) -> CoarseCover:
    policy = CoverPolicy()
    cell = traces[0].cell
    return CoarseCover(
        "cover:rain",
        cell.chart_fingerprint,
        cell,
        tuple(trace.trace_id for trace in traces),
        ("shard:rain",),
        tuple(trace.support_key for trace in traces),
        tuple(trace.axis for trace in traces),
        1.0,
        0.0,
        0.1,
        0.0,
        0.0,
        2,
        CoverState.stable,
        policy.policy_id,
        policy.version,
        policy.policy_fingerprint,
        ("approved",),
    )


__all__ = ["add_synthetic_cover", "build_fixture", "query_probe", "relative_time_resolution", "with_legacy_proposal_only", "with_wrong_down_direction"]
