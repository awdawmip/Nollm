from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial
from nollm.dream_geometry.geometry.schedules import LAYER_PHASE_POLICIES, PARAMETER_MATRIX, LayerPhasePolicy, ParameterSet, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, CellRef, DEFAULT_TOLERANCE, HexCell, LocalChart


BASELINE_COMMIT = "f2629ba08aeec0a7179e640536a35dd720ab28a1"
PARAMETER_ID = "B"
BASE_LAYER = 0
PHASE = PhaseSchedule(0.0, 0.0)
LAYER_GAPS = (4, 8, 16)
SOURCE_AXIAL_STENCIL = (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1), AxialCoord(2, -1))
TARGET_DISK_RADIUS = 4
TARGET_PARTITION_SIZE = 61
COVERAGE_THRESHOLD = 1e-9
COVERAGE_TOLERANCE = DEFAULT_TOLERANCE
MASS_TOLERANCE = 1e-12
SETTING_COUNT = 30
OBSERVATION_COUNT = 60
GKC1_REPORTING_NOISE_FLOOR = 1e-12


@dataclass(frozen=True, slots=True)
class CompositionObservation:
    parameter_id: str
    composition_direction: str
    base_layer: int
    fine_layer: int
    layer_gap: int
    phase_policy: str
    source_axial: AxialCoord
    source_cell_ref: tuple[str, int, int]
    source_chart_id: str
    return_chart_id: str
    intermediate_chart_id: str
    first_leg_direction: str
    second_leg_direction: str
    first_leg_support_count: int
    second_leg_distribution_count: int
    composed_support_count: int
    composed_kernel_mass: float
    composition_residual_mass: float
    composition_total_mass: float
    self_return_mass: float
    nonself_return_mass: float
    identity_distance: float
    composed_target_refs_in_canonical_order: tuple[tuple[str, int, int], ...]
    composed_weights_in_canonical_order: tuple[float, ...]
    first_leg_residual_mass: float
    second_leg_weighted_residual_mass: float


def baseline_parameter() -> ParameterSet:
    return next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == PARAMETER_ID)


def build_observations() -> tuple[CompositionObservation, ...]:
    return build_observations_from_order(LAYER_GAPS, tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES), SOURCE_AXIAL_STENCIL)


def build_observations_from_order(gaps: tuple[int, ...], policy_ids: tuple[str, ...], source_axials: tuple[AxialCoord, ...]) -> tuple[CompositionObservation, ...]:
    schedule = ScaleRotationSchedule(baseline_parameter())
    policies = tuple(next(policy for policy in LAYER_PHASE_POLICIES if policy.policy_id == policy_id) for policy_id in policy_ids)
    rows = []
    for gap in gaps:
        for policy in policies:
            for source_axial in source_axials:
                rows.append(build_observation(schedule, gap, policy, source_axial, "fine_coarse_fine"))
                rows.append(build_observation(schedule, gap, policy, source_axial, "coarse_fine_coarse"))
    return tuple(sorted(rows, key=observation_key))


def build_observation(
    schedule: ScaleRotationSchedule,
    gap: int,
    policy: LayerPhasePolicy,
    source_axial: AxialCoord,
    composition_direction: str,
) -> CompositionObservation:
    fine_layer = BASE_LAYER + gap
    coarse_chart = chart_for(schedule, BASE_LAYER, policy)
    fine_chart = chart_for(schedule, fine_layer, policy)
    if composition_direction == "fine_coarse_fine":
        source_chart = fine_chart
        intermediate_chart = coarse_chart
        first_direction = CoverageDirection.fine_to_coarse
        second_direction = CoverageDirection.coarse_to_fine
    elif composition_direction == "coarse_fine_coarse":
        source_chart = coarse_chart
        intermediate_chart = fine_chart
        first_direction = CoverageDirection.coarse_to_fine
        second_direction = CoverageDirection.fine_to_coarse
    else:
        raise ValueError("unsupported composition direction")
    source_cell = make_hex_cell(source_chart, source_axial)
    first_targets = target_disk(intermediate_chart, source_cell)
    first = compute_distribution(source_cell, first_targets, first_direction, COVERAGE_THRESHOLD, COVERAGE_TOLERANCE)
    composed: dict[tuple[str, int, int], float] = {}
    second_weighted_residual = 0.0
    for kernel in first.kernels:
        second_targets = target_disk(source_chart, kernel.target_cell)
        second = compute_distribution(kernel.target_cell, second_targets, second_direction, COVERAGE_THRESHOLD, COVERAGE_TOLERANCE)
        second_weighted_residual += kernel.weight * second.residual.mass
        for second_kernel in second.kernels:
            ref = cell_ref_payload(second_kernel.target_cell.cell_ref)
            composed[ref] = composed.get(ref, 0.0) + kernel.weight * second_kernel.weight
    ordered_refs = tuple(sorted(ref for ref, weight in composed.items() if weight > COVERAGE_TOLERANCE.area_abs_tol))
    ordered_weights = tuple(composed[ref] for ref in ordered_refs)
    kernel_mass = sum(ordered_weights)
    residual_mass = first.residual.mass + second_weighted_residual
    total_mass = kernel_mass + residual_mass
    source_ref = cell_ref_payload(source_cell.cell_ref)
    self_mass = composed.get(source_ref, 0.0)
    nonself_mass = kernel_mass - self_mass
    identity_distance = nonself_mass + residual_mass + abs(1.0 - self_mass - nonself_mass - residual_mass)
    return CompositionObservation(
        parameter_id=PARAMETER_ID,
        composition_direction=composition_direction,
        base_layer=BASE_LAYER,
        fine_layer=fine_layer,
        layer_gap=gap,
        phase_policy=policy.policy_id,
        source_axial=source_axial,
        source_cell_ref=source_ref,
        source_chart_id=source_chart.chart_id,
        return_chart_id=source_chart.chart_id,
        intermediate_chart_id=intermediate_chart.chart_id,
        first_leg_direction=first_direction.value,
        second_leg_direction=second_direction.value,
        first_leg_support_count=len(first.kernels),
        second_leg_distribution_count=len(first.kernels),
        composed_support_count=len(ordered_refs),
        composed_kernel_mass=kernel_mass,
        composition_residual_mass=residual_mass,
        composition_total_mass=total_mass,
        self_return_mass=self_mass,
        nonself_return_mass=nonself_mass,
        identity_distance=identity_distance,
        composed_target_refs_in_canonical_order=ordered_refs,
        composed_weights_in_canonical_order=ordered_weights,
        first_leg_residual_mass=first.residual.mass,
        second_leg_weighted_residual_mass=second_weighted_residual,
    )


def recompute_observation(observation: CompositionObservation) -> CompositionObservation:
    schedule = ScaleRotationSchedule(baseline_parameter())
    policy = next(policy for policy in LAYER_PHASE_POLICIES if policy.policy_id == observation.phase_policy)
    return build_observation(schedule, observation.layer_gap, policy, observation.source_axial, observation.composition_direction)


def canonical_payload(observations: tuple[CompositionObservation, ...] | None = None) -> tuple[dict[str, Any], ...]:
    selected = build_observations() if observations is None else tuple(sorted(observations, key=observation_key))
    return tuple(observation_payload(row) for row in selected)


def observation_payload(row: CompositionObservation) -> dict[str, Any]:
    return {
        "parameter_id": row.parameter_id,
        "composition_direction": row.composition_direction,
        "base_layer": row.base_layer,
        "fine_layer": row.fine_layer,
        "layer_gap": row.layer_gap,
        "phase_policy": row.phase_policy,
        "source_axial": (row.source_axial.q, row.source_axial.r),
        "source_cell_ref": row.source_cell_ref,
        "source_chart_id": row.source_chart_id,
        "return_chart_id": row.return_chart_id,
        "intermediate_chart_id": row.intermediate_chart_id,
        "first_leg_direction": row.first_leg_direction,
        "second_leg_direction": row.second_leg_direction,
        "first_leg_support_count": row.first_leg_support_count,
        "second_leg_distribution_count": row.second_leg_distribution_count,
        "composed_support_count": row.composed_support_count,
        "composed_kernel_mass": _float(row.composed_kernel_mass),
        "composition_residual_mass": _float(row.composition_residual_mass),
        "composition_total_mass": _float(row.composition_total_mass),
        "self_return_mass": _float(row.self_return_mass),
        "nonself_return_mass": _float(row.nonself_return_mass),
        "identity_distance": _float(row.identity_distance),
        "composed_target_refs_in_canonical_order": row.composed_target_refs_in_canonical_order,
        "composed_weights_in_canonical_order": tuple(_float(weight) for weight in row.composed_weights_in_canonical_order),
        "first_leg_residual_mass": _float(row.first_leg_residual_mass),
        "second_leg_weighted_residual_mass": _float(row.second_leg_weighted_residual_mass),
    }


def experiment_window_payload() -> dict[str, Any]:
    parameter = baseline_parameter()
    return {
        "baseline_commit": BASELINE_COMMIT,
        "parameter_id": PARAMETER_ID,
        "beta": _float(parameter.beta),
        "delta_theta_degrees": _float(parameter.delta_theta_degrees),
        "base_layer": BASE_LAYER,
        "phase": (PHASE.phase_q, PHASE.phase_r),
        "phase_policies": tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES),
        "layer_gaps": LAYER_GAPS,
        "source_axial_stencil": tuple((axial.q, axial.r) for axial in SOURCE_AXIAL_STENCIL),
        "target_disk_radius": TARGET_DISK_RADIUS,
        "target_partition_size": TARGET_PARTITION_SIZE,
        "coverage_threshold": _float(COVERAGE_THRESHOLD),
        "setting_count": SETTING_COUNT,
        "observation_count": OBSERVATION_COUNT,
        "tolerances": {"mass": _float(MASS_TOLERANCE), "coverage_area_abs": _float(COVERAGE_TOLERANCE.area_abs_tol)},
    }


def composition_summary(observations: tuple[CompositionObservation, ...] | None = None) -> dict[tuple[str, int, str], dict[str, float | int]]:
    selected = build_observations() if observations is None else observations
    summary: dict[tuple[str, int, str], dict[str, float | int]] = {}
    for direction in ("fine_coarse_fine", "coarse_fine_coarse"):
        for gap in LAYER_GAPS:
            for policy in tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES):
                rows = tuple(row for row in selected if row.composition_direction == direction and row.layer_gap == gap and row.phase_policy == policy)
                summary[(direction, gap, policy)] = {
                    "count": len(rows),
                    "support_min": min(row.composed_support_count for row in rows),
                    "support_max": max(row.composed_support_count for row in rows),
                    "self_min": min(row.self_return_mass for row in rows),
                    "self_max": max(row.self_return_mass for row in rows),
                    "residual_positive": sum(1 for row in rows if row.composition_residual_mass > MASS_TOLERANCE),
                    "residual_min": min(row.composition_residual_mass for row in rows),
                    "residual_max": max(row.composition_residual_mass for row in rows),
                }
    return dict(sorted(summary.items()))


def residual_summary(observations: tuple[CompositionObservation, ...] | None = None) -> dict[str, Any]:
    selected = build_observations() if observations is None else observations
    return {
        "positive_by_direction_gap": _count_by((row.composition_direction, row.layer_gap) for row in selected if row.composition_residual_mass > MASS_TOLERANCE),
        "positive_first_leg": sum(1 for row in selected if row.first_leg_residual_mass > MASS_TOLERANCE),
        "positive_second_leg_weighted": sum(1 for row in selected if row.second_leg_weighted_residual_mass > MASS_TOLERANCE),
    }


def central_regression_anchors(observations: tuple[CompositionObservation, ...] | None = None) -> dict[tuple[str, int], float]:
    selected = build_observations() if observations is None else observations
    rows = {}
    for row in selected:
        if row.phase_policy == "constant_local" and row.source_axial == AxialCoord(0, 0):
            rows[(row.composition_direction, row.layer_gap)] = row.self_return_mass
    return dict(sorted(rows.items()))


def target_disk(chart: LocalChart, source_cell: HexCell) -> tuple[HexCell, ...]:
    center = nearest_axial(chart, source_cell.center)
    return tuple(make_hex_cell(chart, axial) for axial in disk(center, TARGET_DISK_RADIUS))


def chart_for(schedule: ScaleRotationSchedule, layer: int, policy: LayerPhasePolicy) -> LocalChart:
    return schedule.chart_for_layer(layer, policy.phase_for_layer(PHASE, layer))


def all_finite(observations: tuple[CompositionObservation, ...]) -> bool:
    values = []
    for row in observations:
        values.extend(
            (
                row.composed_kernel_mass,
                row.composition_residual_mass,
                row.composition_total_mass,
                row.self_return_mass,
                row.nonself_return_mass,
                row.identity_distance,
                row.first_leg_residual_mass,
                row.second_leg_weighted_residual_mass,
            )
        )
        values.extend(row.composed_weights_in_canonical_order)
    return all(isfinite(value) for value in values)


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "cortex", "field", "admission", "assembly", "recall", "atlas", "state")}


def observation_key(row: CompositionObservation) -> tuple[int, str, int, int, str]:
    return (row.layer_gap, row.phase_policy, row.source_axial.q, row.source_axial.r, row.composition_direction)


def cell_ref_payload(ref: CellRef) -> tuple[str, int, int]:
    return (ref.chart_id, ref.axial.q, ref.axial.r)


def render_report_metric(value: float) -> str:
    if not isfinite(value):
        raise ValueError("report metric must be finite")
    if abs(value) <= GKC1_REPORTING_NOISE_FLOOR:
        return "<=1.000000e-12"
    return format(float(value), ".6e")


def _count_by(values) -> dict[Any, int]:
    counts: dict[Any, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _float(value: float) -> str:
    return format(float(value), ".12g")
