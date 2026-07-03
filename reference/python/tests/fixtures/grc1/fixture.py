from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from nollm.dream_geometry.geometry.chart import axial_to_world, world_to_fractional_axial
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial
from nollm.dream_geometry.geometry.metrics import DistributionMetrics, distribution_metrics
from nollm.dream_geometry.geometry.schedules import LAYER_PHASE_POLICIES, PARAMETER_MATRIX, LayerPhasePolicy, ParameterSet, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, CellRef, DEFAULT_TOLERANCE, HexCell, LocalChart


BASELINE_COMMIT = "1c9b1f0498051cd62b66cfad2fa05a6071778ab3"
PARAMETER_ID = "B"
MAX_LAYER = 16
PHASE = PhaseSchedule(0.0, 0.0)
LAYER_GAPS = (4, 8, 16)
SOURCE_AXIAL_STENCIL = (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1), AxialCoord(2, -1))
TARGET_DISK_RADIUS = 4
COVERAGE_THRESHOLD = 1e-9
COVERAGE_TOLERANCE = DEFAULT_TOLERANCE
ANGLE_TOLERANCE_DEGREES = 1e-12
SCALE_TOLERANCE = 1e-12
LATTICE_TOLERANCE = 1e-12
OBSERVATION_COUNT = 230
GRC1_REPORTING_NOISE_FLOOR = 1e-12


@dataclass(frozen=True, slots=True)
class ResonanceCoverageObservation:
    parameter_id: str
    base_layer: int
    fine_layer: int
    layer_gap: int
    phase_policy: str
    source_axial: AxialCoord
    source_cell_ref: tuple[str, int, int]
    target_chart_id: str
    target_center_axial: AxialCoord
    side_ratio: float
    rotation_mod_hex_degrees: float
    nearest_integer_scale: int
    scale_integer_error: float
    center_map_residual: float
    alignment_class: str
    coverage_support_count: int
    effective_support_count: float
    max_coverage_mass: float
    coverage_residual_mass: float
    kernel_weights_descending: tuple[float, ...]
    target_refs_in_canonical_order: tuple[tuple[str, int, int], ...]
    center_exact: bool
    coverage_singleton: bool
    coverage_multisupport: bool


def baseline_parameter() -> ParameterSet:
    return next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == PARAMETER_ID)


def build_observations() -> tuple[ResonanceCoverageObservation, ...]:
    return build_observations_from_order(LAYER_GAPS, tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES), SOURCE_AXIAL_STENCIL)


def build_observations_from_order(gaps: tuple[int, ...], policy_ids: tuple[str, ...], source_axials: tuple[AxialCoord, ...]) -> tuple[ResonanceCoverageObservation, ...]:
    schedule = ScaleRotationSchedule(baseline_parameter())
    policies = tuple(next(policy for policy in LAYER_PHASE_POLICIES if policy.policy_id == policy_id) for policy_id in policy_ids)
    observations = []
    for gap in gaps:
        for base_layer in base_layers_for_gap(gap):
            for policy in policies:
                for source_axial in source_axials:
                    observations.append(build_observation(schedule, gap, base_layer, policy, source_axial))
    return tuple(sorted(observations, key=observation_key))


def build_observation(
    schedule: ScaleRotationSchedule,
    gap: int,
    base_layer: int,
    policy: LayerPhasePolicy,
    source_axial: AxialCoord,
) -> ResonanceCoverageObservation:
    fine_layer = base_layer + gap
    coarse_chart = chart_for(schedule, base_layer, policy)
    fine_chart = chart_for(schedule, fine_layer, policy)
    source_cell = make_source_cell(fine_chart, source_axial)
    target_center = nearest_axial(coarse_chart, source_cell.center)
    target_cells = tuple(make_source_cell(coarse_chart, axial) for axial in disk(target_center, TARGET_DISK_RADIUS))
    distribution = compute_distribution(source_cell, target_cells, CoverageDirection.fine_to_coarse, COVERAGE_THRESHOLD, COVERAGE_TOLERANCE)
    metrics = distribution_metrics(distribution, COVERAGE_THRESHOLD)
    side_ratio = coarse_chart.side_length / fine_chart.side_length
    rotation_mod_hex = rotation_mod_hex_degrees(rotation_delta_degrees(coarse_chart, fine_chart))
    nearest_integer_scale = round(side_ratio)
    scale_integer_error = abs(side_ratio - nearest_integer_scale)
    center_residual = center_map_residual(coarse_chart, fine_chart, source_axial)
    alignment_class = classify(rotation_mod_hex, nearest_integer_scale, scale_integer_error, center_residual)
    kernels = tuple(sorted(distribution.kernels, key=lambda kernel: cell_ref_payload(kernel.target_cell.cell_ref)))
    weights = tuple(kernel.weight for kernel in kernels)
    return ResonanceCoverageObservation(
        parameter_id=PARAMETER_ID,
        base_layer=base_layer,
        fine_layer=fine_layer,
        layer_gap=gap,
        phase_policy=policy.policy_id,
        source_axial=source_axial,
        source_cell_ref=cell_ref_payload(source_cell.cell_ref),
        target_chart_id=coarse_chart.chart_id,
        target_center_axial=target_center,
        side_ratio=side_ratio,
        rotation_mod_hex_degrees=rotation_mod_hex,
        nearest_integer_scale=nearest_integer_scale,
        scale_integer_error=scale_integer_error,
        center_map_residual=center_residual,
        alignment_class=alignment_class,
        coverage_support_count=metrics.branching_factor,
        effective_support_count=metrics.effective_parent_count,
        max_coverage_mass=metrics.max_coverage_mass,
        coverage_residual_mass=metrics.residual_mass,
        kernel_weights_descending=tuple(sorted(weights, reverse=True)),
        target_refs_in_canonical_order=tuple(cell_ref_payload(kernel.target_cell.cell_ref) for kernel in kernels),
        center_exact=alignment_class == "exact_center_sublattice",
        coverage_singleton=metrics.branching_factor == 1 and abs(metrics.max_coverage_mass - 1.0) <= LATTICE_TOLERANCE and metrics.residual_mass <= LATTICE_TOLERANCE,
        coverage_multisupport=metrics.branching_factor > 1,
    )


def recompute_alignment_class(observation: ResonanceCoverageObservation) -> str:
    return classify(
        observation.rotation_mod_hex_degrees,
        observation.nearest_integer_scale,
        observation.scale_integer_error,
        observation.center_map_residual,
    )


def recompute_coverage_metrics(observation: ResonanceCoverageObservation) -> DistributionMetrics:
    schedule = ScaleRotationSchedule(baseline_parameter())
    policy = next(policy for policy in LAYER_PHASE_POLICIES if policy.policy_id == observation.phase_policy)
    fine_chart = chart_for(schedule, observation.fine_layer, policy)
    coarse_chart = chart_for(schedule, observation.base_layer, policy)
    source_cell = make_source_cell(fine_chart, observation.source_axial)
    target_center = nearest_axial(coarse_chart, source_cell.center)
    target_cells = tuple(make_source_cell(coarse_chart, axial) for axial in disk(target_center, TARGET_DISK_RADIUS))
    distribution = compute_distribution(source_cell, target_cells, CoverageDirection.fine_to_coarse, COVERAGE_THRESHOLD, COVERAGE_TOLERANCE)
    return distribution_metrics(distribution, COVERAGE_THRESHOLD)


def canonical_payload(observations: tuple[ResonanceCoverageObservation, ...] | None = None) -> tuple[dict[str, Any], ...]:
    selected = build_observations() if observations is None else tuple(sorted(observations, key=observation_key))
    return tuple(observation_payload(observation) for observation in selected)


def observation_payload(observation: ResonanceCoverageObservation) -> dict[str, Any]:
    return {
        "parameter_id": observation.parameter_id,
        "base_layer": observation.base_layer,
        "fine_layer": observation.fine_layer,
        "layer_gap": observation.layer_gap,
        "phase_policy": observation.phase_policy,
        "source_axial": (observation.source_axial.q, observation.source_axial.r),
        "source_cell_ref": observation.source_cell_ref,
        "target_chart_id": observation.target_chart_id,
        "target_center_axial": (observation.target_center_axial.q, observation.target_center_axial.r),
        "side_ratio": _float(observation.side_ratio),
        "rotation_mod_hex_degrees": _float(observation.rotation_mod_hex_degrees),
        "nearest_integer_scale": observation.nearest_integer_scale,
        "scale_integer_error": _float(observation.scale_integer_error),
        "center_map_residual": _float(observation.center_map_residual),
        "alignment_class": observation.alignment_class,
        "coverage_support_count": observation.coverage_support_count,
        "effective_support_count": _float(observation.effective_support_count),
        "max_coverage_mass": _float(observation.max_coverage_mass),
        "coverage_residual_mass": _float(observation.coverage_residual_mass),
        "kernel_weights_descending": tuple(_float(weight) for weight in observation.kernel_weights_descending),
        "target_refs_in_canonical_order": observation.target_refs_in_canonical_order,
        "center_exact": observation.center_exact,
        "coverage_singleton": observation.coverage_singleton,
        "coverage_multisupport": observation.coverage_multisupport,
    }


def classification_counts(observations: tuple[ResonanceCoverageObservation, ...] | None = None) -> dict[tuple[int, str, str], int]:
    selected = build_observations() if observations is None else observations
    counts: dict[tuple[int, str, str], int] = {}
    for observation in selected:
        key = (observation.layer_gap, observation.phase_policy, observation.alignment_class)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def coverage_summary(observations: tuple[ResonanceCoverageObservation, ...] | None = None) -> dict[tuple[int, str, str], int]:
    selected = build_observations() if observations is None else observations
    counts: dict[tuple[int, str, str], int] = {}
    for observation in selected:
        key = (observation.layer_gap, observation.phase_policy, "singleton" if observation.coverage_singleton else "multisupport")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def conditional_counts(observations: tuple[ResonanceCoverageObservation, ...] | None = None) -> dict[tuple[str, str], int]:
    selected = build_observations() if observations is None else observations
    counts: dict[tuple[str, str], int] = {}
    for observation in selected:
        alignment = observation.alignment_class
        coverage = "singleton" if observation.coverage_singleton else "multisupport"
        counts[(alignment, coverage)] = counts.get((alignment, coverage), 0) + 1
    return dict(sorted(counts.items()))


def base_layers_for_gap(gap: int) -> tuple[int, ...]:
    return tuple(range(0, MAX_LAYER - gap + 1))


def chart_for(schedule: ScaleRotationSchedule, layer: int, policy: LayerPhasePolicy) -> LocalChart:
    return schedule.chart_for_layer(layer, policy.phase_for_layer(PHASE, layer))


def make_source_cell(chart: LocalChart, axial: AxialCoord) -> HexCell:
    from nollm.dream_geometry.geometry.chart import make_hex_cell

    return make_hex_cell(chart, axial)


def center_map_residual(coarse_chart: LocalChart, fine_chart: LocalChart, source_axial: AxialCoord) -> float:
    qf, rf = world_to_fractional_axial(fine_chart, axial_to_world(coarse_chart, source_axial))
    return max(abs(qf - round(qf)), abs(rf - round(rf)))


def classify(rotation_mod_hex: float, nearest_integer_scale: int, scale_integer_error: float, center_residual: float) -> str:
    commensurate = (
        rotation_mod_hex <= ANGLE_TOLERANCE_DEGREES
        and nearest_integer_scale >= 2
        and scale_integer_error <= SCALE_TOLERANCE
    )
    if commensurate and center_residual <= LATTICE_TOLERANCE:
        return "exact_center_sublattice"
    if commensurate:
        return "commensurate_phase_separated"
    return "noncommensurate"


def experiment_window_payload() -> dict[str, Any]:
    parameter = baseline_parameter()
    return {
        "baseline_commit": BASELINE_COMMIT,
        "parameter_id": PARAMETER_ID,
        "beta": _float(parameter.beta),
        "delta_theta_degrees": _float(parameter.delta_theta_degrees),
        "max_layer": MAX_LAYER,
        "phase": (PHASE.phase_q, PHASE.phase_r),
        "phase_policies": tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES),
        "layer_gaps": LAYER_GAPS,
        "base_layer_counts": {gap: len(base_layers_for_gap(gap)) for gap in LAYER_GAPS},
        "source_axial_stencil": tuple((axial.q, axial.r) for axial in SOURCE_AXIAL_STENCIL),
        "target_disk_radius": TARGET_DISK_RADIUS,
        "coverage_direction": CoverageDirection.fine_to_coarse.value,
        "coverage_threshold": _float(COVERAGE_THRESHOLD),
        "observation_count": OBSERVATION_COUNT,
        "tolerances": {
            "angle_degrees": _float(ANGLE_TOLERANCE_DEGREES),
            "scale": _float(SCALE_TOLERANCE),
            "lattice": _float(LATTICE_TOLERANCE),
            "coverage_area_abs": _float(COVERAGE_TOLERANCE.area_abs_tol),
        },
    }


def all_finite(observations: tuple[ResonanceCoverageObservation, ...]) -> bool:
    values = []
    for observation in observations:
        values.extend(
            (
                observation.side_ratio,
                observation.rotation_mod_hex_degrees,
                observation.scale_integer_error,
                observation.center_map_residual,
                observation.effective_support_count,
                observation.max_coverage_mass,
                observation.coverage_residual_mass,
            )
        )
        values.extend(observation.kernel_weights_descending)
    return all(isfinite(value) for value in values)


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "cortex", "field", "admission", "assembly", "recall", "atlas", "state")}


def observation_key(observation: ResonanceCoverageObservation) -> tuple[int, int, str, int, int]:
    return (observation.layer_gap, observation.base_layer, observation.phase_policy, observation.source_axial.q, observation.source_axial.r)


def cell_ref_payload(ref: CellRef) -> tuple[str, int, int]:
    return (ref.chart_id, ref.axial.q, ref.axial.r)


def rotation_delta_degrees(coarse_chart: LocalChart, fine_chart: LocalChart) -> float:
    return (fine_chart.rotation_radians - coarse_chart.rotation_radians) * 180.0 / 3.141592653589793


def rotation_mod_hex_degrees(delta_degrees: float) -> float:
    return min(abs(delta_degrees - 60.0 * k) for k in range(-12, 13))


def render_report_metric(value: float) -> str:
    if not isfinite(value):
        raise ValueError("report metric must be finite")
    if abs(value) <= GRC1_REPORTING_NOISE_FLOOR:
        return f"\u2264{GRC1_REPORTING_NOISE_FLOOR:.6e}"
    return format(float(value), ".6e")


def _float(value: float) -> str:
    return format(float(value), ".12g")
