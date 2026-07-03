from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import isfinite
from pathlib import Path
from typing import Any

from nollm.dream_geometry.geometry.chart import axial_to_world, normalized_phase, relative_phase, world_to_fractional_axial
from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX, LayerPhasePolicy, ParameterSet, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, PhaseCoord


BASELINE_COMMIT = "2ce5c13f48c2478010acb73c4a612678e7830b10"
PARAMETER_ID = "B"
MAX_LAYER = 16
LAYER_GAPS = (1, 2, 4, 8, 16)
AXIAL_CENTER_STENCIL = (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1), AxialCoord(2, -1))
ANGLE_TOLERANCE_DEGREES = 1e-12
SCALE_TOLERANCE = 1e-12
LATTICE_TOLERANCE = 1e-12
OBSERVATION_COUNT = 432


@dataclass(frozen=True, slots=True)
class CenterMapRow:
    coarse_axial: AxialCoord
    fine_fractional_axial: tuple[float, float]
    nearest_fine_axial: AxialCoord
    residual_linf: float


@dataclass(frozen=True, slots=True)
class ResonanceObservation:
    parameter_id: str
    base_layer: int
    fine_layer: int
    layer_gap: int
    phase_label: str
    phase_policy: str
    coarse_chart_id: str
    fine_chart_id: str
    side_ratio: float
    rotation_delta_degrees: float
    rotation_mod_hex_degrees: float
    nearest_integer_scale: int
    scale_integer_error: float
    coarse_phase: PhaseCoord
    fine_phase: PhaseCoord
    relative_phase: PhaseCoord
    center_map_rows: tuple[CenterMapRow, ...]
    max_center_map_residual: float
    classification: str


def baseline_parameter() -> ParameterSet:
    return next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == PARAMETER_ID)


def build_observations() -> tuple[ResonanceObservation, ...]:
    return _build_observations_cached()


@lru_cache(maxsize=1)
def _build_observations_cached() -> tuple[ResonanceObservation, ...]:
    schedule = ScaleRotationSchedule(baseline_parameter())
    observations = []
    for gap in LAYER_GAPS:
        for base_layer in base_layers_for_gap(gap):
            for phase in DEFAULT_PHASE_SAMPLES:
                for policy in LAYER_PHASE_POLICIES:
                    observations.append(build_observation(schedule, gap, base_layer, phase, policy))
    return tuple(sorted(observations, key=observation_key))


def build_observations_from_order(gaps: tuple[int, ...]) -> tuple[ResonanceObservation, ...]:
    schedule = ScaleRotationSchedule(baseline_parameter())
    observations = []
    for gap in gaps:
        for base_layer in base_layers_for_gap(gap):
            for phase in DEFAULT_PHASE_SAMPLES:
                for policy in LAYER_PHASE_POLICIES:
                    observations.append(build_observation(schedule, gap, base_layer, phase, policy))
    return tuple(sorted(observations, key=observation_key))


def build_observation(schedule: ScaleRotationSchedule, gap: int, base_layer: int, phase: PhaseSchedule, policy: LayerPhasePolicy) -> ResonanceObservation:
    fine_layer = base_layer + gap
    coarse_chart = chart_for(schedule, base_layer, phase, policy)
    fine_chart = chart_for(schedule, fine_layer, phase, policy)
    side_ratio = coarse_chart.side_length / fine_chart.side_length
    rotation_delta = rotation_delta_degrees(coarse_chart, fine_chart)
    rotation_mod_hex = rotation_mod_hex_degrees(rotation_delta)
    nearest_integer_scale = round(side_ratio)
    scale_integer_error = abs(side_ratio - nearest_integer_scale)
    rows = tuple(center_map_row(coarse_chart, fine_chart, axial) for axial in AXIAL_CENTER_STENCIL)
    max_residual = max(row.residual_linf for row in rows)
    return ResonanceObservation(
        parameter_id=PARAMETER_ID,
        base_layer=base_layer,
        fine_layer=fine_layer,
        layer_gap=gap,
        phase_label=phase_label(phase),
        phase_policy=policy.policy_id,
        coarse_chart_id=coarse_chart.chart_id,
        fine_chart_id=fine_chart.chart_id,
        side_ratio=side_ratio,
        rotation_delta_degrees=rotation_delta,
        rotation_mod_hex_degrees=rotation_mod_hex,
        nearest_integer_scale=nearest_integer_scale,
        scale_integer_error=scale_integer_error,
        coarse_phase=normalized_phase(coarse_chart),
        fine_phase=normalized_phase(fine_chart),
        relative_phase=relative_phase(fine_chart, coarse_chart),
        center_map_rows=rows,
        max_center_map_residual=max_residual,
        classification=classify(rotation_mod_hex, nearest_integer_scale, scale_integer_error, max_residual),
    )


def chart_for(schedule: ScaleRotationSchedule, layer: int, phase: PhaseSchedule, policy: LayerPhasePolicy) -> LocalChart:
    return schedule.chart_for_layer(layer, policy.phase_for_layer(phase, layer))


def center_map_row(coarse_chart: LocalChart, fine_chart: LocalChart, axial: AxialCoord) -> CenterMapRow:
    qf, rf = world_to_fractional_axial(fine_chart, axial_to_world(coarse_chart, axial))
    nearest_q = round(qf)
    nearest_r = round(rf)
    return CenterMapRow(
        coarse_axial=axial,
        fine_fractional_axial=(qf, rf),
        nearest_fine_axial=AxialCoord(nearest_q, nearest_r),
        residual_linf=max(abs(qf - nearest_q), abs(rf - nearest_r)),
    )


def classify(rotation_mod_hex: float, nearest_integer_scale: int, scale_integer_error: float, max_center_map_residual: float) -> str:
    commensurate = (
        rotation_mod_hex <= ANGLE_TOLERANCE_DEGREES
        and nearest_integer_scale >= 2
        and scale_integer_error <= SCALE_TOLERANCE
    )
    if commensurate and max_center_map_residual <= LATTICE_TOLERANCE:
        return "exact_center_sublattice"
    if commensurate:
        return "commensurate_phase_separated"
    return "noncommensurate"


def recompute_classification(observation: ResonanceObservation) -> str:
    return classify(
        observation.rotation_mod_hex_degrees,
        observation.nearest_integer_scale,
        observation.scale_integer_error,
        observation.max_center_map_residual,
    )


def canonical_payload(observations: tuple[ResonanceObservation, ...] | None = None) -> tuple[dict[str, Any], ...]:
    selected = build_observations() if observations is None else tuple(sorted(observations, key=observation_key))
    return tuple(observation_payload(observation) for observation in selected)


def observation_payload(observation: ResonanceObservation) -> dict[str, Any]:
    return {
        "parameter_id": observation.parameter_id,
        "base_layer": observation.base_layer,
        "fine_layer": observation.fine_layer,
        "layer_gap": observation.layer_gap,
        "phase_label": observation.phase_label,
        "phase_policy": observation.phase_policy,
        "coarse_chart_id": observation.coarse_chart_id,
        "fine_chart_id": observation.fine_chart_id,
        "side_ratio": _float(observation.side_ratio),
        "rotation_delta_degrees": _float(observation.rotation_delta_degrees),
        "rotation_mod_hex_degrees": _float(observation.rotation_mod_hex_degrees),
        "nearest_integer_scale": observation.nearest_integer_scale,
        "scale_integer_error": _float(observation.scale_integer_error),
        "coarse_phase": phase_payload(observation.coarse_phase),
        "fine_phase": phase_payload(observation.fine_phase),
        "relative_phase": phase_payload(observation.relative_phase),
        "center_map_rows": tuple(row_payload(row) for row in observation.center_map_rows),
        "max_center_map_residual": _float(observation.max_center_map_residual),
        "classification": observation.classification,
    }


def row_payload(row: CenterMapRow) -> dict[str, Any]:
    return {
        "coarse_axial": (row.coarse_axial.q, row.coarse_axial.r),
        "fine_fractional_axial": (_float(row.fine_fractional_axial[0]), _float(row.fine_fractional_axial[1])),
        "nearest_fine_axial": (row.nearest_fine_axial.q, row.nearest_fine_axial.r),
        "residual_linf": _float(row.residual_linf),
    }


def phase_payload(phase: PhaseCoord) -> tuple[str, str]:
    return (_float(phase.q), _float(phase.r))


def summary_counts(observations: tuple[ResonanceObservation, ...] | None = None) -> dict[tuple[int, str, str], int]:
    selected = build_observations() if observations is None else observations
    counts: dict[tuple[int, str, str], int] = {}
    for observation in selected:
        key = (observation.layer_gap, observation.phase_policy, observation.classification)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def classification_totals(observations: tuple[ResonanceObservation, ...] | None = None) -> dict[str, int]:
    selected = build_observations() if observations is None else observations
    totals = {"exact_center_sublattice": 0, "commensurate_phase_separated": 0, "noncommensurate": 0}
    for observation in selected:
        totals[observation.classification] += 1
    return totals


def recurrence_candidates(observations: tuple[ResonanceObservation, ...] | None = None) -> tuple[ResonanceObservation, ...]:
    selected = build_observations() if observations is None else observations
    return tuple(observation for observation in selected if observation.layer_gap in (8, 16))


def base_layers_for_gap(gap: int) -> tuple[int, ...]:
    return tuple(range(0, MAX_LAYER - gap + 1))


def experiment_window_payload() -> dict[str, Any]:
    parameter = baseline_parameter()
    return {
        "baseline_commit": BASELINE_COMMIT,
        "parameter_id": PARAMETER_ID,
        "beta": _float(parameter.beta),
        "delta_theta_degrees": _float(parameter.delta_theta_degrees),
        "max_layer": MAX_LAYER,
        "layer_gaps": LAYER_GAPS,
        "base_layer_counts": {gap: len(base_layers_for_gap(gap)) for gap in LAYER_GAPS},
        "phase_samples": tuple((phase.phase_q, phase.phase_r) for phase in DEFAULT_PHASE_SAMPLES),
        "phase_policies": tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES),
        "axial_center_stencil": tuple((axial.q, axial.r) for axial in AXIAL_CENTER_STENCIL),
        "observation_count": OBSERVATION_COUNT,
        "tolerances": {
            "angle_degrees": _float(ANGLE_TOLERANCE_DEGREES),
            "scale": _float(SCALE_TOLERANCE),
            "lattice": _float(LATTICE_TOLERANCE),
        },
    }


def all_finite(observations: tuple[ResonanceObservation, ...]) -> bool:
    values = []
    for observation in observations:
        values.extend(
            (
                observation.side_ratio,
                observation.rotation_delta_degrees,
                observation.rotation_mod_hex_degrees,
                observation.scale_integer_error,
                observation.coarse_phase.q,
                observation.coarse_phase.r,
                observation.fine_phase.q,
                observation.fine_phase.r,
                observation.relative_phase.q,
                observation.relative_phase.r,
                observation.max_center_map_residual,
            )
        )
        for row in observation.center_map_rows:
            values.extend((row.fine_fractional_axial[0], row.fine_fractional_axial[1], row.residual_linf))
    return all(isfinite(value) for value in values)


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "cortex", "field", "admission", "assembly", "recall", "atlas", "state")}


def observation_key(observation: ResonanceObservation) -> tuple[int, int, str, str]:
    return (observation.layer_gap, observation.base_layer, observation.phase_label, observation.phase_policy)


def phase_label(phase: PhaseSchedule) -> str:
    return f"({phase.phase_q:.6g},{phase.phase_r:.6g})"


def rotation_delta_degrees(coarse_chart: LocalChart, fine_chart: LocalChart) -> float:
    return (fine_chart.rotation_radians - coarse_chart.rotation_radians) * 180.0 / 3.141592653589793


def rotation_mod_hex_degrees(delta_degrees: float) -> float:
    return min(abs(delta_degrees - 60.0 * k) for k in range(-12, 13))


def _float(value: float) -> str:
    return format(float(value), ".12g")
