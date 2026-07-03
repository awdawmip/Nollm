from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from nollm.dream_geometry.field.compaction import compact_traces, expand_compaction
from nollm.dream_geometry.field.types import GrowthTrace, TraceCompaction, cell_ref_key, float_token
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.schedules import LAYER_PHASE_POLICIES, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, HexCell
from nollm.dream_geometry.protocol.contracts import GrowthBasis, TraceState
from tests.fixtures.gsc1.fixture import PARAMETER_ID, PHASES, TARGET_RADIUS, baseline_parameter, build_collision_summaries, chart_for


BASELINE_COMMIT = "f850599995e75b0a5c74fa9267202958a6369bdd"
SCENARIO_IDS = (
    "shared_support_distinct_shards",
    "shared_support_distinct_proposals",
    "shared_support_distinct_revision_proxy",
    "exact_duplicate_transport_view",
    "mixed_group",
)


@dataclass(frozen=True, slots=True)
class GCM1CollisionWitness:
    pattern_id: str
    layer_gap: int
    base_layer: int
    phase_label: str
    phase_policy: str
    target_ref: tuple[str, int, int]
    supporting_marker_ids: tuple[str, ...]
    hex_cell: HexCell


@dataclass(frozen=True, slots=True)
class GCM1TraceScenario:
    scenario_id: str
    input_traces: tuple[GrowthTrace, ...]
    expected_compaction_member_ids: tuple[str, ...]
    expected_uncompacted_trace_ids: tuple[str, ...]

    @property
    def input_trace_ids(self) -> tuple[str, ...]:
        return tuple(trace.trace_id for trace in self.input_traces)


def build_collision_witness() -> GCM1CollisionWitness:
    summary = next(summary for summary in build_collision_summaries() if summary.pattern_id == "local_fork" and summary.collision_target_count > 0)
    target_ref, supporting_marker_ids = next((target_ref, markers) for target_ref, markers in summary.target_marker_ids if len(markers) > 1)
    hex_cell = reconstruct_target_hex_cell(summary.base_layer, summary.phase_label, summary.phase_policy, target_ref)
    if (hex_cell.cell_ref.chart_id, hex_cell.cell_ref.axial.q, hex_cell.cell_ref.axial.r) != target_ref:
        raise ValueError("reconstructed witness HexCell does not match GSC1 target_ref")
    return GCM1CollisionWitness(
        pattern_id=summary.pattern_id,
        layer_gap=summary.layer_gap,
        base_layer=summary.base_layer,
        phase_label=summary.phase_label,
        phase_policy=summary.phase_policy,
        target_ref=target_ref,
        supporting_marker_ids=supporting_marker_ids,
        hex_cell=hex_cell,
    )


def build_trace_scenarios() -> tuple[GCM1TraceScenario, ...]:
    witness = build_collision_witness()
    cell = witness.hex_cell
    shared = {
        "cell": cell,
        "axis": "gcm1-support-axis",
        "support_key": "gcm1-shared-target-support",
        "basis": GrowthBasis.explicit_in_shard,
        "mass": 0.25,
        "genericity": 0.1,
        "ambiguity": 0.1,
        "conflict": 0.0,
        "stability_epochs": 2,
        "state": TraceState.accepted,
        "derivation_kind": "gcm1_synthetic_transport",
        "geometry_refs": (cell_ref_key(cell),),
    }
    scenario_a = (
        trace("a0", origin_shard_id="gcm1-shard-f0", proposal_id="gcm1-proposal-a", parent_trace_id="gcm1-parent-a", basis_refs=("gcm1-basis-a",), **shared),
        trace("a1", origin_shard_id="gcm1-shard-f1", proposal_id="gcm1-proposal-a", parent_trace_id="gcm1-parent-a", basis_refs=("gcm1-basis-a",), **shared),
    )
    scenario_b = (
        trace("b0", origin_shard_id="gcm1-shard-b", proposal_id="gcm1-proposal-b0", parent_trace_id="gcm1-parent-b", basis_refs=("gcm1-basis-b",), **shared),
        trace("b1", origin_shard_id="gcm1-shard-b", proposal_id="gcm1-proposal-b1", parent_trace_id="gcm1-parent-b", basis_refs=("gcm1-basis-b",), **shared),
    )
    scenario_c = (
        trace("c0", origin_shard_id="gcm1-shard-c", proposal_id="gcm1-proposal-c", parent_trace_id="gcm1-parent-c0", basis_refs=("gcm1-basis-c0",), **shared),
        trace("c1", origin_shard_id="gcm1-shard-c", proposal_id="gcm1-proposal-c", parent_trace_id="gcm1-parent-c1", basis_refs=("gcm1-basis-c1",), **shared),
    )
    scenario_d = (
        trace("d0", origin_shard_id="gcm1-shard-d", proposal_id="gcm1-proposal-d", parent_trace_id="gcm1-parent-d", basis_refs=("gcm1-basis-d",), **shared),
        trace("d1", origin_shard_id="gcm1-shard-d", proposal_id="gcm1-proposal-d", parent_trace_id="gcm1-parent-d", basis_refs=("gcm1-basis-d",), **shared),
    )
    mixed = scenario_a + scenario_b + scenario_c + scenario_d
    return (
        GCM1TraceScenario("shared_support_distinct_shards", scenario_a, (), ("a0", "a1")),
        GCM1TraceScenario("shared_support_distinct_proposals", scenario_b, (), ("b0", "b1")),
        GCM1TraceScenario("shared_support_distinct_revision_proxy", scenario_c, (), ("c0", "c1")),
        GCM1TraceScenario("exact_duplicate_transport_view", scenario_d, ("d0", "d1"), ()),
        GCM1TraceScenario("mixed_group", mixed, ("d0", "d1"), ("a0", "a1", "b0", "b1", "c0", "c1")),
    )


def evaluate_scenario(scenario: GCM1TraceScenario) -> tuple[TraceCompaction, ...]:
    return compact_traces(scenario.input_traces)


def expand_scenario_compaction(scenario: GCM1TraceScenario, compaction: TraceCompaction) -> tuple[GrowthTrace, ...]:
    return expand_compaction(compaction, {trace.trace_id: trace for trace in scenario.input_traces})


def canonical_compaction_payload(compactions: tuple[TraceCompaction, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "compaction_id": compaction.compaction_id,
            "member_trace_ids": compaction.member_trace_ids,
            "canonical_key": compaction.canonical_key,
            "aggregate_mass": float_token(compaction.aggregate_mass),
            "expansion_manifest": compaction.expansion_manifest,
        }
        for compaction in sorted(compactions, key=lambda item: item.compaction_id)
    )


def scenario_payload(scenario: GCM1TraceScenario) -> dict[str, Any]:
    compactions = evaluate_scenario(scenario)
    compacted_ids = tuple(trace_id for compaction in compactions for trace_id in compaction.member_trace_ids)
    return {
        "scenario_id": scenario.scenario_id,
        "input_trace_ids": scenario.input_trace_ids,
        "expected_compaction_member_ids": scenario.expected_compaction_member_ids,
        "expected_uncompacted_trace_ids": scenario.expected_uncompacted_trace_ids,
        "actual_compactions": canonical_compaction_payload(compactions),
        "actual_uncompacted_trace_ids": tuple(trace_id for trace_id in sorted(scenario.input_trace_ids) if trace_id not in set(compacted_ids)),
    }


def witness_payload(witness: GCM1CollisionWitness | None = None) -> dict[str, Any]:
    selected = build_collision_witness() if witness is None else witness
    return {
        "pattern_id": selected.pattern_id,
        "parameter_id": PARAMETER_ID,
        "layer_gap": selected.layer_gap,
        "base_layer": selected.base_layer,
        "phase_label": selected.phase_label,
        "phase_policy": selected.phase_policy,
        "target_ref": selected.target_ref,
        "supporting_marker_ids": selected.supporting_marker_ids,
        "target_radius": TARGET_RADIUS,
        "hex_cell_ref": cell_ref_key(selected.hex_cell),
        "chart_fingerprint_chart_id": selected.hex_cell.chart_fingerprint.chart_id,
    }


def experiment_window_payload() -> dict[str, Any]:
    return {
        "baseline_commit": BASELINE_COMMIT,
        "source_phase": "GSC1 sealed fixture",
        "parameter_id": PARAMETER_ID,
        "pattern_id": "local_fork",
        "scenario_ids": SCENARIO_IDS,
    }


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "cortex", "admission", "assembly", "recall", "atlas", "state")}


def trace(trace_id: str, **kwargs: Any) -> GrowthTrace:
    return GrowthTrace(trace_id=trace_id, **kwargs)


def reconstruct_target_hex_cell(base_layer: int, phase_label: str, phase_policy: str, target_ref: tuple[str, int, int]) -> HexCell:
    schedule = ScaleRotationSchedule(baseline_parameter())
    phase = phase_from_label(phase_label)
    policy = next(policy for policy in LAYER_PHASE_POLICIES if policy.policy_id == phase_policy)
    chart = chart_for(schedule, base_layer, phase, policy)
    cell = make_hex_cell(chart, AxialCoord(target_ref[1], target_ref[2]))
    if cell.cell_ref.chart_id != target_ref[0]:
        raise ValueError("target_ref chart does not match reconstructed chart")
    return cell


def phase_from_label(label: str) -> PhaseSchedule:
    for phase in PHASES:
        if f"({phase.phase_q:.6g},{phase.phase_r:.6g})" == label:
            return phase
    raise ValueError(f"unknown phase label: {label}")


def traces_equal(left: GrowthTrace, right: GrowthTrace) -> bool:
    return left == right


def all_finite_scenarios(scenarios: tuple[GCM1TraceScenario, ...]) -> bool:
    values = []
    for scenario in scenarios:
        for trace_item in scenario.input_traces:
            values.extend((trace_item.mass, trace_item.genericity, trace_item.ambiguity, trace_item.conflict))
        for compaction in evaluate_scenario(scenario):
            values.append(compaction.aggregate_mass)
    return all(isfinite(value) for value in values)
