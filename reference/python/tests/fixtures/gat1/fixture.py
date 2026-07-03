from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import atan2, isfinite, pi
from pathlib import Path
from typing import Any

from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX, LayerPhasePolicy, ParameterSet, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.transform import (
    CycleResidual,
    SimilarityTransform,
    TransformValidation,
    TransformWitness,
    apply_transform,
    compose_transforms,
    cycle_residual,
    fit_orientation_preserving_similarity_from_two_pairs,
    invert_transform,
    validate_transform,
)
from nollm.dream_geometry.geometry.types import AxialCoord, DEFAULT_TOLERANCE, GeometryTolerance, LocalChart, Vec2


BASELINE_COMMIT = "ffe76e4ed574209e05ef3f8e35440aa50c0cd234"
PARAMETER_ID = "B"
LAYER_RANGE = tuple(range(0, 17))
CHART_LAYER_TRIPLES = ((0, 1, 2), (0, 4, 8), (1, 5, 13), (0, 8, 16))
WITNESS_AXIALS = (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1))
TOLERANCE = DEFAULT_TOLERANCE
GAT1_REPORTING_NOISE_FLOOR = 1e-12


@dataclass(frozen=True, slots=True)
class PairCheck:
    source_layer: int
    target_layer: int
    transform: SimilarityTransform
    validation: TransformValidation
    expected_scale: float
    scale_error: float
    rotation_error: float
    inverse_point_error: float
    composition_point_error: float


@dataclass(frozen=True, slots=True)
class CycleCheck:
    triple: tuple[int, int, int]
    phase_label: str
    phase_policy: str
    pair_checks: tuple[PairCheck, PairCheck, PairCheck]
    cycle: CycleResidual


def baseline_parameter() -> ParameterSet:
    return next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == PARAMETER_ID)


def build_cycle_checks() -> tuple[CycleCheck, ...]:
    return _build_cycle_checks_cached()


@lru_cache(maxsize=1)
def _build_cycle_checks_cached() -> tuple[CycleCheck, ...]:
    schedule = ScaleRotationSchedule(baseline_parameter())
    checks = []
    for triple in CHART_LAYER_TRIPLES:
        for phase in DEFAULT_PHASE_SAMPLES:
            for policy in LAYER_PHASE_POLICIES:
                charts = tuple(chart_for(schedule, layer, phase, policy) for layer in triple)
                ab = fit_pair(charts[0], charts[1])
                bc = fit_pair(charts[1], charts[2])
                ca = fit_pair(charts[2], charts[0])
                direct_ac = fit_pair(charts[0], charts[2])
                direct_ba = fit_pair(charts[1], charts[0])
                direct_cb = fit_pair(charts[2], charts[1])
                pair_checks = (
                    pair_check(charts[0], charts[1], charts[2], ab, direct_ba, bc, direct_ac),
                    pair_check(charts[1], charts[2], charts[0], bc, direct_cb, ca, direct_ba),
                    pair_check(charts[2], charts[0], charts[1], ca, direct_ac, ab, direct_cb),
                )
                cycle = cycle_residual(
                    (ab.transform, bc.transform, ca.transform),
                    witness_points(charts[0]),
                    charts[0].side_length,
                    TOLERANCE,
                )
                checks.append(CycleCheck(triple, phase_label(phase), policy.policy_id, pair_checks, cycle))
    return tuple(checks)


def fit_pair(source_chart: LocalChart, target_chart: LocalChart) -> TransformValidation:
    witnesses = witnesses_for(source_chart, target_chart)
    transform = fit_orientation_preserving_similarity_from_two_pairs(
        witnesses[0].source,
        witnesses[1].source,
        witnesses[0].target,
        witnesses[1].target,
        TOLERANCE,
    )
    return validate_transform(transform, witnesses, source_chart.side_length, TOLERANCE)


def pair_check(
    source_chart: LocalChart,
    target_chart: LocalChart,
    third_chart: LocalChart,
    validation: TransformValidation,
    reverse_validation: TransformValidation,
    target_to_third_validation: TransformValidation,
    source_to_third_validation: TransformValidation,
) -> PairCheck:
    inverse = invert_transform(validation.transform, TOLERANCE)
    composed = compose_transforms(target_to_third_validation.transform, validation.transform)
    direct_composed = source_to_third_validation.transform
    return PairCheck(
        source_layer=source_chart.layer_index,
        target_layer=target_chart.layer_index,
        transform=validation.transform,
        validation=validation,
        expected_scale=target_chart.side_length / source_chart.side_length,
        scale_error=abs(validation.transform.scale - (target_chart.side_length / source_chart.side_length)),
        rotation_error=rotation_distance(transform_angle(validation.transform), target_chart.rotation_radians - source_chart.rotation_radians),
        inverse_point_error=max_point_error(inverse, reverse_validation.transform, witness_points(target_chart)),
        composition_point_error=max_point_error(composed, direct_composed, witness_points(source_chart)),
    )


def chart_for(schedule: ScaleRotationSchedule, layer: int, phase: PhaseSchedule, policy: LayerPhasePolicy) -> LocalChart:
    return schedule.chart_for_layer(layer, policy.phase_for_layer(phase, layer))


def witnesses_for(source_chart: LocalChart, target_chart: LocalChart) -> tuple[TransformWitness, ...]:
    return tuple(
        TransformWitness(
            make_hex_cell(source_chart, axial).center,
            make_hex_cell(target_chart, axial).center,
        )
        for axial in WITNESS_AXIALS
    )


def witness_points(chart: LocalChart) -> tuple[Vec2, ...]:
    return tuple(make_hex_cell(chart, axial).center for axial in WITNESS_AXIALS)


def negative_control_payload() -> dict[str, str]:
    schedule = ScaleRotationSchedule(baseline_parameter())
    phase = DEFAULT_PHASE_SAMPLES[0]
    policy = LAYER_PHASE_POLICIES[0]
    source = chart_for(schedule, 0, phase, policy)
    target = chart_for(schedule, 1, phase, policy)
    validation = fit_pair(source, target)
    witnesses = witnesses_for(source, target)
    shifted = witnesses[:-1] + (TransformWitness(witnesses[-1].source, witnesses[-1].target + Vec2(source.side_length * 0.01, 0.0)),)
    duplicate_witnesses = (
        TransformWitness(witnesses[0].source, witnesses[0].target),
        TransformWitness(witnesses[0].source, witnesses[0].target),
        TransformWitness(witnesses[1].source, witnesses[1].target),
    )
    tampered_cycle = (
        validation.transform,
        SimilarityTransform(1.0, 0.0, Vec2(source.side_length * 0.01, 0.0)),
        invert_transform(validation.transform, TOLERANCE),
    )
    reversing = SimilarityTransform(validation.transform.a_real, validation.transform.a_imag, validation.transform.b, "orientation_reversing")
    return {
        "shifted_target": validate_transform(validation.transform, shifted, source.side_length, TOLERANCE).state_recommendation,
        "duplicate_witness": validate_transform(validation.transform, duplicate_witnesses, source.side_length, TOLERANCE).state_recommendation,
        "tampered_cycle": cycle_residual(tampered_cycle, witness_points(source), source.side_length, TOLERANCE).state_recommendation,
        "orientation_reversing": validate_transform(reversing, witnesses, source.side_length, TOLERANCE).state_recommendation,
    }


def canonical_payload() -> tuple[dict[str, Any], ...]:
    return _canonical_payload_cached()


@lru_cache(maxsize=1)
def _canonical_payload_cached() -> tuple[dict[str, Any], ...]:
    return tuple(cycle_payload(check) for check in build_cycle_checks())


def cycle_payload(check: CycleCheck) -> dict[str, Any]:
    return {
        "triple": check.triple,
        "phase_label": check.phase_label,
        "phase_policy": check.phase_policy,
        "cycle_state": check.cycle.state_recommendation,
        "cycle_max_residual": _float(check.cycle.max_residual),
        "cycle_rms_residual": _float(check.cycle.rms_residual),
        "cycle_linear_identity_error": _float(check.cycle.linear_identity_error),
        "cycle_translation_identity_error": _float(check.cycle.translation_identity_error),
        "witness_geometry_status": check.cycle.witness_geometry_status,
        "pairs": tuple(pair_payload(pair) for pair in check.pair_checks),
    }


def pair_payload(pair: PairCheck) -> dict[str, Any]:
    return {
        "source_layer": pair.source_layer,
        "target_layer": pair.target_layer,
        "state": pair.validation.state_recommendation,
        "orientation": pair.transform.orientation,
        "scale": _float(pair.transform.scale),
        "expected_scale": _float(pair.expected_scale),
        "scale_error": _float(pair.scale_error),
        "rotation_error": _float(pair.rotation_error),
        "max_residual": _float(pair.validation.residual.max_residual),
        "rms_residual": _float(pair.validation.residual.rms_residual),
        "inverse_point_error": _float(pair.inverse_point_error),
        "composition_point_error": _float(pair.composition_point_error),
    }


def experiment_window_payload() -> dict[str, Any]:
    return {
        "parameter_id": PARAMETER_ID,
        "layer_range": (LAYER_RANGE[0], LAYER_RANGE[-1]),
        "chart_layer_triples": CHART_LAYER_TRIPLES,
        "witness_axials": tuple((axial.q, axial.r) for axial in WITNESS_AXIALS),
        "phase_samples": tuple((phase.phase_q, phase.phase_r) for phase in DEFAULT_PHASE_SAMPLES),
        "layer_phase_policies": tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES),
        "cycle_count": len(CHART_LAYER_TRIPLES) * len(DEFAULT_PHASE_SAMPLES) * len(LAYER_PHASE_POLICIES),
        "reference_scale_rule": "source chart side_length",
        "tolerance": tolerance_payload(TOLERANCE),
    }


def tolerance_payload(tolerance: GeometryTolerance) -> dict[str, str]:
    return {
        "coordinate_abs_tol": _float(tolerance.coordinate_abs_tol),
        "coordinate_rel_tol": _float(tolerance.coordinate_rel_tol),
        "area_abs_tol": _float(tolerance.area_abs_tol),
        "area_rel_tol": _float(tolerance.area_rel_tol),
    }


def max_pair_residual(checks: tuple[CycleCheck, ...]) -> float:
    return max(pair.validation.residual.max_residual for check in checks for pair in check.pair_checks)


def max_cycle_residual(checks: tuple[CycleCheck, ...]) -> float:
    return max(check.cycle.max_residual for check in checks)


def max_scale_error(checks: tuple[CycleCheck, ...]) -> float:
    return max(pair.scale_error for check in checks for pair in check.pair_checks)


def max_rotation_error(checks: tuple[CycleCheck, ...]) -> float:
    return max(pair.rotation_error for check in checks for pair in check.pair_checks)


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "cortex", "admission", "field", "assembly", "recall", "atlas")}


def phase_label(phase: PhaseSchedule) -> str:
    return f"({phase.phase_q:.6g},{phase.phase_r:.6g})"


def transform_angle(transform: SimilarityTransform) -> float:
    return atan2(transform.a_imag, transform.a_real)


def rotation_distance(first: float, second: float) -> float:
    delta = (first - second + pi) % (2.0 * pi) - pi
    return abs(delta)


def max_point_error(left: SimilarityTransform, right: SimilarityTransform, points: tuple[Vec2, ...]) -> float:
    return max((apply_transform(left, point) - apply_transform(right, point)).norm() for point in points)


def all_finite(check: CycleCheck) -> bool:
    values = [
        check.cycle.rms_residual,
        check.cycle.max_residual,
        check.cycle.linear_identity_error,
        check.cycle.translation_identity_error,
    ]
    for pair in check.pair_checks:
        values.extend(
            (
                pair.validation.residual.rms_residual,
                pair.validation.residual.max_residual,
                pair.scale_error,
                pair.rotation_error,
                pair.inverse_point_error,
                pair.composition_point_error,
            )
        )
    return all(isfinite(value) for value in values)


def render_report_metric(value: float) -> str:
    if not isfinite(value):
        raise ValueError("report metric must be finite")
    if abs(value) <= GAT1_REPORTING_NOISE_FLOOR:
        return f"\u2264{GAT1_REPORTING_NOISE_FLOOR:.6e}"
    return format(float(value), ".6e")


def _float(value: float) -> str:
    return format(float(value), ".12g")
