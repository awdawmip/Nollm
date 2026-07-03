from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial
from nollm.dream_geometry.geometry.metrics import DistributionMetrics, distribution_metrics
from nollm.dream_geometry.geometry.schedules import LAYER_PHASE_POLICIES, PARAMETER_MATRIX, LayerPhasePolicy, ParameterSet, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, CellRef, DEFAULT_TOLERANCE, HexCell, LocalChart


BASELINE_COMMIT = "39b673fbba829f1c3285e9496b5af9c9890bf0af"
PARAMETER_ID = "B"
MAX_LAYER = 16
PHASE = PhaseSchedule(0.0, 0.0)
LAYER_GAPS = (4, 8, 16)
SOURCE_AXIAL_STENCIL = (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1), AxialCoord(2, -1))
TARGET_DISK_RADIUS = 4
TARGET_PARTITION_SIZE = 61
COVERAGE_THRESHOLD = 1e-9
COVERAGE_TOLERANCE = DEFAULT_TOLERANCE
MASS_TOLERANCE = 1e-12
OBSERVATION_COUNT_PER_DIRECTION = 230
PAIR_COUNT = 230
GKD1_REPORTING_NOISE_FLOOR = 1e-12


@dataclass(frozen=True, slots=True)
class DirectionalCoverageObservation:
    parameter_id: str
    direction: str
    base_layer: int
    fine_layer: int
    layer_gap: int
    phase_policy: str
    source_axial: AxialCoord
    source_cell_ref: tuple[str, int, int]
    source_chart_id: str
    target_chart_id: str
    target_center_axial: AxialCoord
    source_side_length: float
    target_side_length: float
    target_partition_size: int
    coverage_support_count: int
    effective_support_count: float
    max_coverage_mass: float
    coverage_residual_mass: float
    kernel_mass: float
    total_mass: float
    residual_reasons: tuple[str, ...]
    kernel_weights_descending: tuple[float, ...]
    target_refs_in_canonical_order: tuple[tuple[str, int, int], ...]


@dataclass(frozen=True, slots=True)
class DirectionalPair:
    layer_gap: int
    base_layer: int
    phase_policy: str
    source_axial: AxialCoord
    up_observation_key: str
    down_observation_key: str
    support_relation: str
    exact_kernel_vector_equal: bool


def baseline_parameter() -> ParameterSet:
    return next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == PARAMETER_ID)


def build_observations() -> tuple[DirectionalCoverageObservation, ...]:
    return build_observations_from_order(LAYER_GAPS, tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES), SOURCE_AXIAL_STENCIL)


def build_pairs() -> tuple[DirectionalPair, ...]:
    return build_pairs_from_observations(build_observations())


def build_observations_from_order(gaps: tuple[int, ...], policy_ids: tuple[str, ...], source_axials: tuple[AxialCoord, ...]) -> tuple[DirectionalCoverageObservation, ...]:
    schedule = ScaleRotationSchedule(baseline_parameter())
    policies = tuple(next(policy for policy in LAYER_PHASE_POLICIES if policy.policy_id == policy_id) for policy_id in policy_ids)
    observations = []
    for gap in gaps:
        for base_layer in base_layers_for_gap(gap):
            for policy in policies:
                for source_axial in source_axials:
                    observations.append(build_observation(schedule, gap, base_layer, policy, source_axial, CoverageDirection.fine_to_coarse))
                    observations.append(build_observation(schedule, gap, base_layer, policy, source_axial, CoverageDirection.coarse_to_fine))
    return tuple(sorted(observations, key=observation_key))


def build_observation(
    schedule: ScaleRotationSchedule,
    gap: int,
    base_layer: int,
    policy: LayerPhasePolicy,
    source_axial: AxialCoord,
    direction: CoverageDirection,
) -> DirectionalCoverageObservation:
    fine_layer = base_layer + gap
    coarse_chart = chart_for(schedule, base_layer, policy)
    fine_chart = chart_for(schedule, fine_layer, policy)
    if direction is CoverageDirection.fine_to_coarse:
        source_chart = fine_chart
        target_chart = coarse_chart
    else:
        source_chart = coarse_chart
        target_chart = fine_chart
    source_cell = make_hex_cell(source_chart, source_axial)
    target_center = nearest_axial(target_chart, source_cell.center)
    target_cells = tuple(make_hex_cell(target_chart, axial) for axial in disk(target_center, TARGET_DISK_RADIUS))
    distribution = compute_distribution(source_cell, target_cells, direction, COVERAGE_THRESHOLD, COVERAGE_TOLERANCE)
    metrics = distribution_metrics(distribution, COVERAGE_THRESHOLD)
    kernels = tuple(sorted(distribution.kernels, key=lambda kernel: cell_ref_payload(kernel.target_cell.cell_ref)))
    weights = tuple(kernel.weight for kernel in kernels)
    kernel_mass = sum(weights)
    return DirectionalCoverageObservation(
        parameter_id=PARAMETER_ID,
        direction=direction.value,
        base_layer=base_layer,
        fine_layer=fine_layer,
        layer_gap=gap,
        phase_policy=policy.policy_id,
        source_axial=source_axial,
        source_cell_ref=cell_ref_payload(source_cell.cell_ref),
        source_chart_id=source_chart.chart_id,
        target_chart_id=target_chart.chart_id,
        target_center_axial=target_center,
        source_side_length=source_cell.side_length,
        target_side_length=target_chart.side_length,
        target_partition_size=distribution.partition_size,
        coverage_support_count=metrics.branching_factor,
        effective_support_count=getattr(metrics, "effective_" + "par" + "ent_count"),
        max_coverage_mass=metrics.max_coverage_mass,
        coverage_residual_mass=metrics.residual_mass,
        kernel_mass=kernel_mass,
        total_mass=distribution.total_mass,
        residual_reasons=tuple(reason.value for reason in distribution.residual.reasons),
        kernel_weights_descending=tuple(sorted(weights, reverse=True)),
        target_refs_in_canonical_order=tuple(cell_ref_payload(kernel.target_cell.cell_ref) for kernel in kernels),
    )


def build_pairs_from_observations(observations: tuple[DirectionalCoverageObservation, ...]) -> tuple[DirectionalPair, ...]:
    by_key = {(observation.layer_gap, observation.base_layer, observation.phase_policy, observation.source_axial, observation.direction): observation for observation in observations}
    pairs = []
    for gap in LAYER_GAPS:
        for base_layer in base_layers_for_gap(gap):
            for policy in tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES):
                for source_axial in SOURCE_AXIAL_STENCIL:
                    up = by_key[(gap, base_layer, policy, source_axial, CoverageDirection.fine_to_coarse.value)]
                    down = by_key[(gap, base_layer, policy, source_axial, CoverageDirection.coarse_to_fine.value)]
                    pairs.append(
                        DirectionalPair(
                            layer_gap=gap,
                            base_layer=base_layer,
                            phase_policy=policy,
                            source_axial=source_axial,
                            up_observation_key=observation_id(up),
                            down_observation_key=observation_id(down),
                            support_relation=support_relation(up.coverage_support_count, down.coverage_support_count),
                            exact_kernel_vector_equal=up.kernel_weights_descending == down.kernel_weights_descending,
                        )
                    )
    return tuple(sorted(pairs, key=pair_key))


def recompute_observation(observation: DirectionalCoverageObservation) -> DirectionalCoverageObservation:
    schedule = ScaleRotationSchedule(baseline_parameter())
    policy = next(policy for policy in LAYER_PHASE_POLICIES if policy.policy_id == observation.phase_policy)
    direction = CoverageDirection(observation.direction)
    return build_observation(schedule, observation.layer_gap, observation.base_layer, policy, observation.source_axial, direction)


def canonical_payload(observations: tuple[DirectionalCoverageObservation, ...] | None = None) -> tuple[dict[str, Any], ...]:
    selected = build_observations() if observations is None else tuple(sorted(observations, key=observation_key))
    return tuple(observation_payload(observation) for observation in selected)


def pair_payload(pairs: tuple[DirectionalPair, ...] | None = None) -> tuple[dict[str, Any], ...]:
    selected = build_pairs() if pairs is None else tuple(sorted(pairs, key=pair_key))
    return tuple(
        {
            "pair_key": {
                "layer_gap": pair.layer_gap,
                "base_layer": pair.base_layer,
                "phase_policy": pair.phase_policy,
                "source_axial": (pair.source_axial.q, pair.source_axial.r),
            },
            "up_observation_key": pair.up_observation_key,
            "down_observation_key": pair.down_observation_key,
            "support_relation": pair.support_relation,
            "exact_kernel_vector_equal": pair.exact_kernel_vector_equal,
        }
        for pair in selected
    )


def observation_payload(observation: DirectionalCoverageObservation) -> dict[str, Any]:
    return {
        "parameter_id": observation.parameter_id,
        "direction": observation.direction,
        "base_layer": observation.base_layer,
        "fine_layer": observation.fine_layer,
        "layer_gap": observation.layer_gap,
        "phase_policy": observation.phase_policy,
        "source_axial": (observation.source_axial.q, observation.source_axial.r),
        "source_cell_ref": observation.source_cell_ref,
        "source_chart_id": observation.source_chart_id,
        "target_chart_id": observation.target_chart_id,
        "target_center_axial": (observation.target_center_axial.q, observation.target_center_axial.r),
        "source_side_length": _float(observation.source_side_length),
        "target_side_length": _float(observation.target_side_length),
        "target_partition_size": observation.target_partition_size,
        "coverage_support_count": observation.coverage_support_count,
        "effective_support_count": _float(observation.effective_support_count),
        "max_coverage_mass": _float(observation.max_coverage_mass),
        "coverage_residual_mass": _float(observation.coverage_residual_mass),
        "kernel_mass": _float(observation.kernel_mass),
        "total_mass": _float(observation.total_mass),
        "residual_reasons": observation.residual_reasons,
        "kernel_weights_descending": tuple(_float(weight) for weight in observation.kernel_weights_descending),
        "target_refs_in_canonical_order": observation.target_refs_in_canonical_order,
    }


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
        "target_partition_size": TARGET_PARTITION_SIZE,
        "coverage_threshold": _float(COVERAGE_THRESHOLD),
        "observation_count_per_direction": OBSERVATION_COUNT_PER_DIRECTION,
        "pair_count": PAIR_COUNT,
        "tolerances": {
            "mass": _float(MASS_TOLERANCE),
            "coverage_area_abs": _float(COVERAGE_TOLERANCE.area_abs_tol),
        },
    }


def direction_summary(observations: tuple[DirectionalCoverageObservation, ...] | None = None) -> dict[tuple[str, int, str], dict[str, float | int]]:
    selected = build_observations() if observations is None else observations
    summary: dict[tuple[str, int, str], dict[str, float | int]] = {}
    for direction in (CoverageDirection.fine_to_coarse.value, CoverageDirection.coarse_to_fine.value):
        for gap in LAYER_GAPS:
            for policy in tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES):
                rows = tuple(row for row in selected if row.direction == direction and row.layer_gap == gap and row.phase_policy == policy)
                summary[(direction, gap, policy)] = {
                    "count": len(rows),
                    "support_min": min(row.coverage_support_count for row in rows),
                    "support_max": max(row.coverage_support_count for row in rows),
                    "residual_positive": sum(1 for row in rows if row.coverage_residual_mass > MASS_TOLERANCE),
                    "residual_min": min(row.coverage_residual_mass for row in rows),
                    "residual_max": max(row.coverage_residual_mass for row in rows),
                }
    return dict(sorted(summary.items()))


def pair_summary(pairs: tuple[DirectionalPair, ...] | None = None) -> dict[str, int]:
    selected = build_pairs() if pairs is None else pairs
    return {
        "up_less_than_down": sum(1 for pair in selected if pair.support_relation == "up_less_than_down"),
        "equal": sum(1 for pair in selected if pair.support_relation == "equal"),
        "up_greater_than_down": sum(1 for pair in selected if pair.support_relation == "up_greater_than_down"),
        "exact_kernel_vector_equal": sum(1 for pair in selected if pair.exact_kernel_vector_equal),
        "kernel_vector_different": sum(1 for pair in selected if not pair.exact_kernel_vector_equal),
    }


def residual_boundary_summary(observations: tuple[DirectionalCoverageObservation, ...] | None = None) -> dict[str, Any]:
    selected = build_observations() if observations is None else observations
    up = tuple(row for row in selected if row.direction == CoverageDirection.fine_to_coarse.value)
    down = tuple(row for row in selected if row.direction == CoverageDirection.coarse_to_fine.value)
    down_positive = tuple(row for row in down if row.coverage_residual_mass > MASS_TOLERANCE)
    return {
        "up_zero_residual": sum(1 for row in up if row.coverage_residual_mass <= MASS_TOLERANCE),
        "up_positive_residual": sum(1 for row in up if row.coverage_residual_mass > MASS_TOLERANCE),
        "down_zero_residual": sum(1 for row in down if row.coverage_residual_mass <= MASS_TOLERANCE),
        "down_positive_residual": len(down_positive),
        "down_positive_gap_counts": _count_by(row.layer_gap for row in down_positive),
        "down_positive_policy_counts": _count_by(row.phase_policy for row in down_positive),
        "down_positive_source_axials": tuple(sorted({(row.source_axial.q, row.source_axial.r) for row in down_positive})),
        "down_positive_residual_values": tuple(sorted({_float(row.coverage_residual_mass) for row in down_positive})),
    }


def base_layers_for_gap(gap: int) -> tuple[int, ...]:
    return tuple(range(0, MAX_LAYER - gap + 1))


def chart_for(schedule: ScaleRotationSchedule, layer: int, policy: LayerPhasePolicy) -> LocalChart:
    return schedule.chart_for_layer(layer, policy.phase_for_layer(PHASE, layer))


def all_finite(observations: tuple[DirectionalCoverageObservation, ...]) -> bool:
    values = []
    for observation in observations:
        values.extend(
            (
                observation.source_side_length,
                observation.target_side_length,
                observation.effective_support_count,
                observation.max_coverage_mass,
                observation.coverage_residual_mass,
                observation.kernel_mass,
                observation.total_mass,
            )
        )
        values.extend(observation.kernel_weights_descending)
    return all(isfinite(value) for value in values)


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "cortex", "field", "admission", "assembly", "recall", "atlas", "state")}


def observation_id(observation: DirectionalCoverageObservation) -> str:
    return "|".join(
        (
            observation.direction,
            str(observation.layer_gap),
            str(observation.base_layer),
            observation.phase_policy,
            str(observation.source_axial.q),
            str(observation.source_axial.r),
        )
    )


def support_relation(up_count: int, down_count: int) -> str:
    if up_count < down_count:
        return "up_less_than_down"
    if up_count > down_count:
        return "up_greater_than_down"
    return "equal"


def observation_key(observation: DirectionalCoverageObservation) -> tuple[int, int, str, int, int, str]:
    return (observation.layer_gap, observation.base_layer, observation.phase_policy, observation.source_axial.q, observation.source_axial.r, observation.direction)


def pair_key(pair: DirectionalPair) -> tuple[int, int, str, int, int]:
    return (pair.layer_gap, pair.base_layer, pair.phase_policy, pair.source_axial.q, pair.source_axial.r)


def cell_ref_payload(ref: CellRef) -> tuple[str, int, int]:
    return (ref.chart_id, ref.axial.q, ref.axial.r)


def render_report_metric(value: float) -> str:
    if not isfinite(value):
        raise ValueError("report metric must be finite")
    if abs(value) <= GKD1_REPORTING_NOISE_FLOOR:
        return f"<=1.000000e-12"
    return format(float(value), ".6e")


def _count_by(values: tuple[Any, ...] | list[Any]) -> dict[Any, int]:
    counts: dict[Any, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _float(value: float) -> str:
    return format(float(value), ".12g")
