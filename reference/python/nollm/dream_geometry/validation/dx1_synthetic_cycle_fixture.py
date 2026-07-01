"""DX1 synthetic end-to-end memory cycle fixture."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from math import pi
from pathlib import Path
from typing import Any

from nollm.dream_geometry.adapters import IntegrationReadContext, RecallInvocation
from nollm.dream_geometry.cortex import compile_query
from nollm.dream_geometry.cortex.store import ADMISSION_CURRENT_DC1_1, CortexStore, open_store as open_cortex_store
from nollm.dream_geometry.evidence import (
    DreamShard,
    InterpretationRecord,
    MemorySubstrateStore,
    OriginDescriptor,
    RevisionEdge,
    RevisionThread,
    TemporalContext,
    UsageStateTransition,
    open_store as open_evidence_store,
)
from nollm.dream_geometry.field import (
    CoverPolicy,
    GravitySnapshot,
    TraceSeed,
    VerifiedChartLink,
    build_local_covers,
    calculate_gravity_snapshot,
    propagate_trace,
    seed_to_trace,
)
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.transform import SimilarityTransform, TransformWitness, validate_transform
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2
from nollm.dream_geometry.protocol.contracts import (
    GrowthBasis,
    InterpretationAuthoringMode,
    InterpretationKind,
    OriginKind,
    RevisionRelation,
    TraceState,
    UsageState,
)
from nollm.dream_geometry.recall import RecallPolicy, RecallUniverse, RuntimeTimeResolution
from nollm.dream_geometry.recall.projection import basis_ref_key
from nollm.dream_geometry.recall.types import ProposalAdmission, ProposalReadRecord, ResolvedRelativeSpan


REFERENCE_INSTANT = "2026-06-30T08:00:00+08:00"
TARGET_SHARD_ID = "shard:dx1:kunming-rain-2026-06-29"
DISTRACTOR_IDS = ("shard:dx1:kunming-clear-2026-06-29", "shard:dx1:beijing-rain-2026-06-29")


@dataclass(frozen=True)
class DX1CycleFixture:
    root: Path
    evidence_store: MemorySubstrateStore
    cortex_store: CortexStore
    target_shard_id: str
    distractor_shard_ids: tuple[str, ...]
    target_proposal: object
    target_receipt: object
    compiled_query_probe: object
    exact_mismatch_probe: object
    runtime_time_resolution: RuntimeTimeResolution
    recall_universe: RecallUniverse
    integration_context: IntegrationReadContext
    invocation: RecallInvocation
    mismatch_invocation: RecallInvocation
    policy: RecallPolicy
    before_recall_manifests: dict[str, tuple[tuple[str, str], ...]]
    gravity_snapshot: GravitySnapshot


def build_dx1_cycle(root: Path, *, permuted: bool = False, retired_target: bool = False) -> DX1CycleFixture:
    root = Path(root)
    evidence_root = root / "evidence"
    cortex_root = root / "cortex"
    evidence = open_evidence_store(evidence_root)
    _write_evidence(evidence, retired_target=retired_target, permuted=permuted)
    evidence = open_evidence_store(evidence_root)
    cortex = open_cortex_store(cortex_root, evidence)
    growth_results = _compile_growth(cortex, permuted=permuted)
    cortex = open_cortex_store(cortex_root, evidence)
    query = compile_query(_query_payload("Kunming rain yesterday?", "rain", "probe_dx1_kunming_rain_yesterday"))
    mismatch = compile_query(_query_payload("Kunming snow yesterday?", "snow", "probe_dx1_kunming_snow_yesterday"))
    universe, gravity = _build_universe(evidence, cortex, growth_results, permuted=permuted)
    runtime_time = _runtime_time()
    policy = RecallPolicy(min_required_axis_matches=3, max_lateral_hops=2, include_retired_context=retired_target)
    context = IntegrationReadContext(evidence, universe, runtime_time, policy)
    target = next(result for result in growth_results if result.proposal.subject_shard_id == TARGET_SHARD_ID)
    return DX1CycleFixture(
        root,
        evidence,
        cortex,
        TARGET_SHARD_ID,
        DISTRACTOR_IDS,
        target.proposal,
        target.receipt,
        query,
        mismatch,
        runtime_time,
        universe,
        context,
        RecallInvocation("req_dx1_s01", "recall", query),
        RecallInvocation("req_dx1_s03", "recall", mismatch),
        policy,
        {"evidence": tree_manifest(evidence_root), "cortex": tree_manifest(cortex_root)},
        gravity,
    )


def build_dx1_deferred_cycle(root: Path) -> DX1CycleFixture:
    fixture = build_dx1_cycle(root)
    return replace(fixture, integration_context=replace(fixture.integration_context, runtime_time=None))


def build_dx1_retired_cycle(root: Path) -> DX1CycleFixture:
    return build_dx1_cycle(root, retired_target=True)


def canonical_mapping(mapping: dict[str, Any]) -> str:
    return json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def tree_manifest(root: Path) -> tuple[tuple[str, str], ...]:
    root = Path(root)
    if not root.exists():
        return ()
    return tuple(
        sorted(
            (path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest())
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def _write_evidence(store: MemorySubstrateStore, *, retired_target: bool, permuted: bool) -> None:
    records = _shard_specs()
    if permuted:
        records = tuple(reversed(records))
    for shard_id, content, _values in records:
        target = shard_id == TARGET_SHARD_ID
        store.put_dream_shard(
            DreamShard(
                shard_id,
                content,
                OriginDescriptor(
                    OriginKind.user_utterance,
                    r"C:\dx1-private\MEMORY.md" if target else "synthetic:dx1",
                    "/dx1-private/conversation.json" if target else None,
                    "synthetic-private-role" if target else None,
                ),
                TemporalContext(REFERENCE_INSTANT, "2026-06-29", REFERENCE_INSTANT, "en-US"),
                (),
                UsageState.tentative,
            )
        )
        to_state = UsageState.retired if target and retired_target else UsageState.active
        store.record_usage_transition(
            UsageStateTransition(
                "state:" + _id_suffix(shard_id),
                shard_id,
                UsageState.tentative,
                to_state,
                ("reason:dx1",),
                "2026-06-30T08:01:00+08:00",
            )
        )
    interpretation = InterpretationRecord(
        "interpretation:dx1:weather-note",
        TARGET_SHARD_ID,
        InterpretationKind.classification,
        "Synthetic weather-observation classification.",
        InterpretationAuthoringMode.llm_proposed,
        ("basis:dx1",),
        (),
        UsageState.tentative,
    )
    store.put_interpretation(interpretation)
    store.put_revision_thread(
        RevisionThread(
            "revision:dx1:weather-note",
            (TARGET_SHARD_ID, interpretation.interpretation_id),
            (RevisionEdge(interpretation.interpretation_id, TARGET_SHARD_ID, RevisionRelation.clarifies, ()),),
            (),
        )
    )


def _compile_growth(cortex: CortexStore, *, permuted: bool):
    payloads = tuple(_growth_payload(shard_id, content, values) for shard_id, content, values in _shard_specs())
    if permuted:
        payloads = tuple(reversed(payloads))
    return tuple(cortex.compile_growth(payload) for payload in payloads)


def _build_universe(evidence: MemorySubstrateStore, cortex: CortexStore, growth_results, *, permuted: bool) -> tuple[RecallUniverse, GravitySnapshot]:
    fine_chart = LocalChart("dx1:fine", 1, 2 ** (-0.25), pi / 8, Vec2(0, 0))
    coarse_chart = LocalChart("dx1:coarse", 0, 1.0, 0.0, Vec2(0, 0))
    validation = validate_transform(
        SimilarityTransform(1.0, 0.0, Vec2(0, 0)),
        (TransformWitness(Vec2(0, 0), Vec2(0, 0)), TransformWitness(Vec2(1, 0), Vec2(1, 0)), TransformWitness(Vec2(0, 1), Vec2(0, 1))),
        1.0,
    )
    coords = {
        TARGET_SHARD_ID: AxialCoord(0, 0),
        "shard:dx1:kunming-clear-2026-06-29": AxialCoord(4, 0),
        "shard:dx1:beijing-rain-2026-06-29": AxialCoord(0, 4),
    }
    traces = []
    propagated_traces = []
    coverage_up = []
    coverage_down = []
    links = []
    coarse_cells_by_shard = {}
    for result in growth_results:
        proposal = result.proposal
        fine_cell = make_hex_cell(fine_chart, coords[proposal.subject_shard_id])
        coarse_cell = make_hex_cell(coarse_chart, coords[proposal.subject_shard_id])
        up = compute_distribution(fine_cell, (coarse_cell,), CoverageDirection.fine_to_coarse)
        down = compute_distribution(coarse_cell, (fine_cell,), CoverageDirection.coarse_to_fine)
        coarse_cells_by_shard[proposal.subject_shard_id] = coarse_cell
        coverage_up.append(up)
        coverage_down.append(down)
        links.append(VerifiedChartLink(fine_cell.chart_fingerprint, coarse_cell.chart_fingerprint, validation))
        links.append(VerifiedChartLink(coarse_cell.chart_fingerprint, fine_cell.chart_fingerprint, validation))
        for axis in proposal.axes:
            step = axis.ray[0]
            seed = TraceSeed(
                "trace_dx1_" + _id_suffix(proposal.proposal_id) + "_" + axis.axis_id,
                proposal.subject_shard_id,
                proposal.proposal_id,
                fine_cell,
                axis.axis_id,
                step.basis,
                tuple(basis_ref_key(ref) for ref in step.basis_refs),
                1.0,
                "support_" + proposal.proposal_id + "_" + axis.axis_id,
                0.1,
                0.0,
                0.0,
                2,
                TraceState.accepted,
            )
            trace = seed_to_trace(seed)
            traces.append(trace)
            propagated_traces.extend(propagate_trace(trace, up, links[-2]).derived_traces)
    seed_trace_ids_by_key = {(trace.origin_shard_id, trace.axis, trace.support_key): trace.trace_id for trace in traces}
    dg2_covers = build_local_covers(tuple(propagated_traces), CoverPolicy())
    gravity = calculate_gravity_snapshot(dg2_covers)
    covers = tuple(_bind_cover_hex_cell(cover, coarse_cells_by_shard, seed_trace_ids_by_key) for cover in dg2_covers)
    receipts = {result.receipt.proposal_id: result.receipt for result in growth_results}
    records = []
    for result in growth_results:
        view = cortex.stored_growth_proposal(result.proposal.proposal_id)
        if view.admission != ADMISSION_CURRENT_DC1_1:
            raise AssertionError("DX1 requires current DC1.1 proposal admission")
        records.append(ProposalReadRecord(view.proposal, ProposalAdmission.current_accepted, "dx1:" + view.proposal.proposal_id, receipts[view.proposal.proposal_id]))
    if permuted:
        records = list(reversed(records))
        traces = list(reversed(traces))
        covers = tuple(reversed(covers))
        coverage_up = list(reversed(coverage_up))
        coverage_down = list(reversed(coverage_down))
    universe = RecallUniverse(
        tuple(records),
        tuple(traces),
        tuple(covers),
        coverage_up=tuple(coverage_up),
        coverage_down=tuple(coverage_down),
        verified_chart_links=tuple(links),
        gravity_snapshot=gravity,
        cover_policy_records=(CoverPolicy(),),
        interpretation_records=(evidence.get_interpretation("interpretation:dx1:weather-note"),),
        revision_threads=(evidence.get_revision_thread("revision:dx1:weather-note"),),
    )
    return universe, gravity


def _bind_cover_hex_cell(cover, cells_by_shard: dict[str, object], seed_trace_ids_by_key: dict[tuple[str, str, str], str]):
    if len(cover.support_shard_ids) != 1:
        return cover
    shard_id = cover.support_shard_ids[0]
    cell = cells_by_shard[shard_id]
    support_trace_ids = tuple(
        seed_trace_ids_by_key[(shard_id, axis, support_key)]
        for axis, support_key in zip(cover.axes_present, cover.support_keys)
    )
    return replace(cover, chart_fingerprint=cell.chart_fingerprint, support_cell=cell, support_trace_ids=support_trace_ids)


def _runtime_time() -> RuntimeTimeResolution:
    return RuntimeTimeResolution(
        (
            ResolvedRelativeSpan(
                "relative_time",
                "yesterday",
                "absolute_time",
                "2026-06-29",
                REFERENCE_INSTANT,
                "dx1_synthetic_runtime",
                "step_q_relative_time",
                13,
                22,
                "yesterday",
                "dx1_synthetic_runtime",
                "1",
            ),
        ),
        True,
        "dx1_synthetic_runtime",
        "1",
        REFERENCE_INSTANT,
    )


def _growth_payload(shard_id: str, content: str, values: tuple[tuple[str, str], ...]) -> dict[str, Any]:
    axes = []
    for axis_id, expression in values:
        start, end = _span(content, expression)
        axes.append(
            {
                "axis_id": axis_id,
                "ray": [
                    {
                        "step_id": "step_" + _id_suffix(shard_id) + "_" + axis_id,
                        "expression": expression,
                        "basis": "explicit_in_shard",
                        "basis_refs": [{"ref_type": "text_span", "record_id": shard_id, "start_char": start, "end_char": end, "quoted_text": expression}],
                        "rationale": None,
                    }
                ],
            }
        )
    return {
        "contract_version": "dc1.v1",
        "proposal_id": "gp_" + _id_suffix(shard_id),
        "subject_shard_id": shard_id,
        "submitted_at": REFERENCE_INSTANT,
        "budget": {"max_axes": 4, "max_total_steps": 8, "max_ray_steps": 4},
        "do_not_infer": ["dx1 synthetic fixture only"],
        "forbidden_inferences": ["no semantic fallback"],
        "possible_conflict_refs": [],
        "axes": axes,
    }


def _query_payload(query_text: str, phenomenon: str, probe_id: str) -> dict[str, Any]:
    axes = []
    for axis_id, expression in (("location", "Kunming"), ("phenomenon", phenomenon), ("relative_time", "yesterday")):
        start, end = _span(query_text, expression)
        axes.append(
            {
                "axis_id": axis_id,
                "ray": [
                    {
                        "step_id": "step_q_" + axis_id,
                        "expression": expression,
                        "basis": "explicit_in_query",
                        "basis_refs": [{"ref_type": "text_span", "record_id": probe_id, "start_char": start, "end_char": end, "quoted_text": expression}],
                        "rationale": None,
                    }
                ],
            }
        )
    return {
        "contract_version": "dc1.v1",
        "probe_id": probe_id,
        "query_text": query_text,
        "reference_instant": REFERENCE_INSTANT,
        "requires_runtime_resolution": True,
        "ephemeral": True,
        "budget": {"max_axes": 4, "max_charts": 8, "max_layers": 4, "max_cells_per_layer": 32},
        "do_not_infer": ["dx1 synthetic fixture only"],
        "forbidden_inferences": ["no semantic fallback"],
        "axes": axes,
    }


def _shard_specs() -> tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...]:
    return (
        (TARGET_SHARD_ID, "Kunming had rain on 2026-06-29.", (("location", "Kunming"), ("phenomenon", "rain"), ("absolute_time", "2026-06-29"))),
        ("shard:dx1:kunming-clear-2026-06-29", "Kunming was clear on 2026-06-29.", (("location", "Kunming"), ("phenomenon", "clear"), ("absolute_time", "2026-06-29"))),
        ("shard:dx1:beijing-rain-2026-06-29", "Beijing had rain on 2026-06-29.", (("location", "Beijing"), ("phenomenon", "rain"), ("absolute_time", "2026-06-29"))),
    )


def _span(text: str, expression: str) -> tuple[int, int]:
    start = text.index(expression)
    return start, start + len(expression)


def _id_suffix(value: str) -> str:
    return value.split(":")[-1].replace("-", "_")


__all__ = [
    "DISTRACTOR_IDS",
    "DX1CycleFixture",
    "REFERENCE_INSTANT",
    "TARGET_SHARD_ID",
    "build_dx1_cycle",
    "build_dx1_deferred_cycle",
    "build_dx1_retired_cycle",
    "canonical_mapping",
    "tree_manifest",
]
