from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import isfinite
from pathlib import Path
from typing import Any

from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial
from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX, LayerPhasePolicy, ParameterSet, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, CellRef, DEFAULT_TOLERANCE, GeometryTolerance, HexCell, LocalChart


BASELINE_COMMIT = "7c3ef9d3a83f87a0dccfa7e9018692be9cdc69af"
PARAMETER_ID = "B"
LAYER_GAPS = (1, 4, 8)
BASE_LAYERS = (0, 8)
PHASES = (PhaseSchedule(0.0, 0.0), PhaseSchedule(0.5, 0.0))
TARGET_RADIUS = 4
THRESHOLD = 1e-9
TOLERANCE = DEFAULT_TOLERANCE
SOURCE_DISTRIBUTION_CALL_COUNT = 144
GSC1_REPORTING_NOISE_FLOOR = 1e-12


@dataclass(frozen=True, slots=True, order=True)
class SyntheticOccupancyMarker:
    marker_id: str
    axial: AxialCoord


@dataclass(frozen=True, slots=True)
class SourceCoverageObservation:
    pattern_id: str
    marker_id: str
    source_axial: AxialCoord
    source_layer: int
    base_layer: int
    layer_gap: int
    phase_label: str
    phase_policy: str
    source_chart_id: str
    target_chart_id: str
    target_refs: tuple[tuple[str, int, int], ...]
    kernel_weights: tuple[str, ...]
    residual_mass: float
    residual_reasons: tuple[str, ...]
    total_mass: float
    partition_size: int


@dataclass(frozen=True, slots=True)
class SupportCollisionSummary:
    pattern_id: str
    base_layer: int
    layer_gap: int
    phase_label: str
    phase_policy: str
    source_count: int
    incidence_count: int
    unique_target_count: int
    collision_target_count: int
    max_marker_support_per_target: int
    max_residual_mass: float
    target_marker_ids: tuple[tuple[tuple[str, int, int], tuple[str, ...]], ...]


OCCUPANCY_PATTERNS: tuple[tuple[str, tuple[SyntheticOccupancyMarker, ...]], ...] = (
    ("singleton", (SyntheticOccupancyMarker("s0", AxialCoord(0, 0)),)),
    (
        "local_fork",
        (
            SyntheticOccupancyMarker("f0", AxialCoord(0, 0)),
            SyntheticOccupancyMarker("f1", AxialCoord(1, 0)),
            SyntheticOccupancyMarker("f2", AxialCoord(0, 1)),
        ),
    ),
    (
        "separated_pair",
        (
            SyntheticOccupancyMarker("p0", AxialCoord(-1, 0)),
            SyntheticOccupancyMarker("p1", AxialCoord(1, 0)),
        ),
    ),
)


def baseline_parameter() -> ParameterSet:
    return next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == PARAMETER_ID)


def phase_samples() -> tuple[PhaseSchedule, ...]:
    return tuple(phase for phase in DEFAULT_PHASE_SAMPLES if (phase.phase_q, phase.phase_r) in {(0.0, 0.0), (0.5, 0.0)})


def build_observations() -> tuple[SourceCoverageObservation, ...]:
    return _build_observations_cached()


@lru_cache(maxsize=1)
def _build_observations_cached() -> tuple[SourceCoverageObservation, ...]:
    observations: list[SourceCoverageObservation] = []
    for pattern_id, markers in OCCUPANCY_PATTERNS:
        observations.extend(observations_for_pattern(pattern_id, markers))
    return tuple(sorted(observations, key=observation_key))


def observations_for_pattern(pattern_id: str, markers: tuple[SyntheticOccupancyMarker, ...]) -> tuple[SourceCoverageObservation, ...]:
    schedule = ScaleRotationSchedule(baseline_parameter())
    observations = []
    for marker in sorted(markers):
        for layer_gap in LAYER_GAPS:
            for base_layer in BASE_LAYERS:
                for phase in PHASES:
                    for policy in LAYER_PHASE_POLICIES:
                        observations.append(distribution_for_marker(schedule, pattern_id, marker, layer_gap, base_layer, phase, policy))
    return tuple(sorted(observations, key=observation_key))


def distribution_for_marker(
    schedule: ScaleRotationSchedule,
    pattern_id: str,
    marker: SyntheticOccupancyMarker,
    layer_gap: int,
    base_layer: int,
    phase: PhaseSchedule,
    policy: LayerPhasePolicy,
) -> SourceCoverageObservation:
    source_layer = base_layer + layer_gap
    source_chart = chart_for(schedule, source_layer, phase, policy)
    target_chart = chart_for(schedule, base_layer, phase, policy)
    source_cell = make_hex_cell(source_chart, marker.axial)
    target_cells = target_partition(source_cell, target_chart)
    distribution = compute_distribution(source_cell, target_cells, CoverageDirection.fine_to_coarse, THRESHOLD, TOLERANCE)
    kernels = tuple(sorted(distribution.kernels, key=lambda kernel: cell_ref_payload(kernel.target_cell.cell_ref)))
    return SourceCoverageObservation(
        pattern_id=pattern_id,
        marker_id=marker.marker_id,
        source_axial=marker.axial,
        source_layer=source_layer,
        base_layer=base_layer,
        layer_gap=layer_gap,
        phase_label=phase_label(phase),
        phase_policy=policy.policy_id,
        source_chart_id=source_chart.chart_id,
        target_chart_id=target_chart.chart_id,
        target_refs=tuple(cell_ref_payload(kernel.target_cell.cell_ref) for kernel in kernels),
        kernel_weights=tuple(_float(kernel.weight) for kernel in kernels),
        residual_mass=distribution.residual.mass,
        residual_reasons=tuple(reason.value for reason in distribution.residual.reasons),
        total_mass=distribution.total_mass,
        partition_size=distribution.partition_size,
    )


def build_collision_summaries() -> tuple[SupportCollisionSummary, ...]:
    return summaries_for_observations(build_observations())


def summaries_for_observations(observations: tuple[SourceCoverageObservation, ...]) -> tuple[SupportCollisionSummary, ...]:
    groups: dict[tuple[str, int, int, str, str], list[SourceCoverageObservation]] = {}
    for observation in observations:
        groups.setdefault(summary_group_key(observation), []).append(observation)
    summaries = []
    for key, items in groups.items():
        target_to_markers: dict[tuple[str, int, int], set[str]] = {}
        for observation in items:
            for target_ref in observation.target_refs:
                target_to_markers.setdefault(target_ref, set()).add(observation.marker_id)
        support = tuple((target_ref, tuple(sorted(marker_ids))) for target_ref, marker_ids in sorted(target_to_markers.items()))
        summaries.append(
            SupportCollisionSummary(
                pattern_id=key[0],
                base_layer=key[1],
                layer_gap=key[2],
                phase_label=key[3],
                phase_policy=key[4],
                source_count=len({item.marker_id for item in items}),
                incidence_count=sum(len(item.target_refs) for item in items),
                unique_target_count=len(target_to_markers),
                collision_target_count=sum(1 for marker_ids in target_to_markers.values() if len(marker_ids) > 1),
                max_marker_support_per_target=max((len(marker_ids) for marker_ids in target_to_markers.values()), default=0),
                max_residual_mass=max(item.residual_mass for item in items),
                target_marker_ids=support,
            )
        )
    return tuple(sorted(summaries, key=summary_key))


def canonical_observation_payload(observations: tuple[SourceCoverageObservation, ...] | None = None) -> tuple[dict[str, Any], ...]:
    selected = build_observations() if observations is None else tuple(sorted(observations, key=observation_key))
    return tuple(observation_payload(observation) for observation in selected)


def canonical_summary_payload(summaries: tuple[SupportCollisionSummary, ...] | None = None) -> tuple[dict[str, Any], ...]:
    selected = build_collision_summaries() if summaries is None else tuple(sorted(summaries, key=summary_key))
    return tuple(summary_payload(summary) for summary in selected)


def observation_payload(observation: SourceCoverageObservation) -> dict[str, Any]:
    return {
        "pattern_id": observation.pattern_id,
        "marker_id": observation.marker_id,
        "source_axial": (observation.source_axial.q, observation.source_axial.r),
        "source_layer": observation.source_layer,
        "base_layer": observation.base_layer,
        "layer_gap": observation.layer_gap,
        "phase_label": observation.phase_label,
        "phase_policy": observation.phase_policy,
        "source_chart_id": observation.source_chart_id,
        "target_chart_id": observation.target_chart_id,
        "target_refs": observation.target_refs,
        "kernel_weights": observation.kernel_weights,
        "residual_mass": _float(observation.residual_mass),
        "residual_reasons": observation.residual_reasons,
        "total_mass": _float(observation.total_mass),
        "partition_size": observation.partition_size,
    }


def summary_payload(summary: SupportCollisionSummary) -> dict[str, Any]:
    return {
        "pattern_id": summary.pattern_id,
        "base_layer": summary.base_layer,
        "layer_gap": summary.layer_gap,
        "phase_label": summary.phase_label,
        "phase_policy": summary.phase_policy,
        "source_count": summary.source_count,
        "incidence_count": summary.incidence_count,
        "unique_target_count": summary.unique_target_count,
        "collision_target_count": summary.collision_target_count,
        "max_marker_support_per_target": summary.max_marker_support_per_target,
        "max_residual_mass": _float(summary.max_residual_mass),
        "target_marker_ids": summary.target_marker_ids,
    }


def experiment_window_payload() -> dict[str, Any]:
    return {
        "parameter_id": PARAMETER_ID,
        "layer_gaps": LAYER_GAPS,
        "base_layers": BASE_LAYERS,
        "phases": tuple((phase.phase_q, phase.phase_r) for phase in PHASES),
        "layer_phase_policies": tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES),
        "target_radius": TARGET_RADIUS,
        "threshold": _float(THRESHOLD),
        "tolerance": tolerance_payload(TOLERANCE),
        "source_distribution_call_count": SOURCE_DISTRIBUTION_CALL_COUNT,
        "patterns": {
            pattern_id: tuple((marker.marker_id, (marker.axial.q, marker.axial.r)) for marker in markers)
            for pattern_id, markers in OCCUPANCY_PATTERNS
        },
    }


def tolerance_payload(tolerance: GeometryTolerance) -> dict[str, str]:
    return {
        "coordinate_abs_tol": _float(tolerance.coordinate_abs_tol),
        "coordinate_rel_tol": _float(tolerance.coordinate_rel_tol),
        "area_abs_tol": _float(tolerance.area_abs_tol),
        "area_rel_tol": _float(tolerance.area_rel_tol),
    }


def max_residual_mass(observations: tuple[SourceCoverageObservation, ...]) -> float:
    return max(observation.residual_mass for observation in observations)


def max_support_per_target(summaries: tuple[SupportCollisionSummary, ...]) -> int:
    return max(summary.max_marker_support_per_target for summary in summaries)


def total_collision_targets(summaries: tuple[SupportCollisionSummary, ...]) -> int:
    return sum(summary.collision_target_count for summary in summaries)


def render_report_metric(value: float) -> str:
    if not isfinite(value):
        raise ValueError("report metric must be finite")
    if abs(value) <= GSC1_REPORTING_NOISE_FLOOR:
        return f"\u2264{GSC1_REPORTING_NOISE_FLOOR:.6e}"
    return format(float(value), ".6e")


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "cortex", "admission", "field", "assembly", "recall", "atlas")}


def pattern_markers(pattern_id: str) -> tuple[SyntheticOccupancyMarker, ...]:
    return next(markers for current_id, markers in OCCUPANCY_PATTERNS if current_id == pattern_id)


def chart_for(schedule: ScaleRotationSchedule, layer: int, phase: PhaseSchedule, policy: LayerPhasePolicy) -> LocalChart:
    return schedule.chart_for_layer(layer, policy.phase_for_layer(phase, layer))


def target_partition(source_cell: HexCell, target_chart: LocalChart) -> tuple[HexCell, ...]:
    center = nearest_axial(target_chart, source_cell.center)
    return tuple(make_hex_cell(target_chart, axial) for axial in disk(center, TARGET_RADIUS))


def phase_label(phase: PhaseSchedule) -> str:
    return f"({phase.phase_q:.6g},{phase.phase_r:.6g})"


def cell_ref_payload(ref: CellRef) -> tuple[str, int, int]:
    return (ref.chart_id, ref.axial.q, ref.axial.r)


def observation_key(observation: SourceCoverageObservation) -> tuple[str, str, int, int, str, str]:
    return (observation.pattern_id, observation.marker_id, observation.layer_gap, observation.base_layer, observation.phase_label, observation.phase_policy)


def summary_group_key(observation: SourceCoverageObservation) -> tuple[str, int, int, str, str]:
    return (observation.pattern_id, observation.base_layer, observation.layer_gap, observation.phase_label, observation.phase_policy)


def summary_key(summary: SupportCollisionSummary) -> tuple[str, int, int, str, str]:
    return (summary.pattern_id, summary.layer_gap, summary.base_layer, summary.phase_label, summary.phase_policy)


def all_finite(observations: tuple[SourceCoverageObservation, ...]) -> bool:
    values = []
    for observation in observations:
        values.extend((observation.residual_mass, observation.total_mass))
        values.extend(float(weight) for weight in observation.kernel_weights)
    return all(isfinite(value) for value in values)


def _float(value: float) -> str:
    return format(float(value), ".12g")
