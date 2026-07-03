from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import isfinite, sqrt
from pathlib import Path
from typing import Any

from nollm.dream_geometry.geometry.chart import make_hex_cell, relative_phase
from nollm.dream_geometry.geometry.coverage import CoverageDirection, CoverageDistribution, compute_distribution
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial
from nollm.dream_geometry.geometry.metrics import percentile, phase_recurrence_score, summarize_distributions
from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX, LayerPhasePolicy, ParameterSet, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, DEFAULT_TOLERANCE, GeometryTolerance


BASELINE_COMMIT = "5e5110a0b1c4f08e9b5cce1b4864f7d403a35cee"
LAYER_RANGE = tuple(range(0, 17))
LAYER_GAPS = (1, 2, 4, 8, 16)
SOURCE_RADIUS = 0
TARGET_RADIUS = 4
THRESHOLD = 1e-9
TOLERANCE = DEFAULT_TOLERANCE


@dataclass(frozen=True, slots=True)
class GPR1MetricRow:
    parameter_id: str
    gap: int
    phase_label: str
    phase_policy: str
    distribution_count: int
    branching_mean: float
    branching_p95: float
    branching_max: int
    effective_count_mean: float
    effective_count_p95: float
    residual_mean: float
    residual_p95: float
    max_mass: float
    overlap_entropy: float
    nesting_tendency: float
    phase_recurrence_score: float
    rotation_recurrence_mod60: bool


def parameter_by_id(parameter_id: str) -> ParameterSet:
    return next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == parameter_id)


def parameter_payload() -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "parameter_id": parameter.parameter_id,
            "beta": _float(parameter.beta),
            "delta_theta_degrees": _float(parameter.delta_theta_degrees),
            "role": parameter.role,
        }
        for parameter in PARAMETER_MATRIX
    )


def baseline_b_formula_payload(max_layer: int = 16) -> dict[str, Any]:
    baseline = parameter_by_id("B")
    schedule = ScaleRotationSchedule(baseline)
    return {
        "parameter_id": baseline.parameter_id,
        "beta": _float(baseline.beta),
        "density_growth_per_layer": _float(baseline.beta**2),
        "expected_density_growth_per_layer": _float(sqrt(2.0)),
        "delta_theta_degrees": _float(baseline.delta_theta_degrees),
        "layers": tuple(
            {
                "layer": layer,
                "side_ratio": _float(schedule.side_length(layer) / schedule.side_length(0)),
                "area_ratio": _float((schedule.side_length(layer) / schedule.side_length(0)) ** 2),
                "density_ratio": _float((schedule.side_length(0) / schedule.side_length(layer)) ** 2),
            }
            for layer in range(max_layer + 1)
        ),
    }


def build_metric_rows() -> tuple[GPR1MetricRow, ...]:
    return _build_metric_rows_cached()


@lru_cache(maxsize=1)
def _build_metric_rows_cached() -> tuple[GPR1MetricRow, ...]:
    rows = []
    for parameter in PARAMETER_MATRIX:
        schedule = ScaleRotationSchedule(parameter)
        for gap in LAYER_GAPS:
            for phase in DEFAULT_PHASE_SAMPLES:
                for policy in LAYER_PHASE_POLICIES:
                    distributions = distributions_for(schedule, gap, phase, policy)
                    summary = summarize_distributions(
                        parameter.parameter_id,
                        gap,
                        phase_label(phase),
                        distributions,
                        phase_score_for(schedule, gap, phase, policy),
                    )
                    rows.append(
                        GPR1MetricRow(
                            parameter_id=parameter.parameter_id,
                            gap=gap,
                            phase_label=phase_label(phase),
                            phase_policy=policy.policy_id,
                            distribution_count=len(distributions),
                            branching_mean=_mean(summary.branching_factors),
                            branching_p95=percentile(summary.branching_factors, 95),
                            branching_max=max(summary.branching_factors) if summary.branching_factors else 0,
                            effective_count_mean=_mean(summary.effective_parent_counts),
                            effective_count_p95=percentile(summary.effective_parent_counts, 95),
                            residual_mean=_mean(summary.residual_masses),
                            residual_p95=percentile(summary.residual_masses, 95),
                            max_mass=max(summary.max_coverage_masses) if summary.max_coverage_masses else 0.0,
                            overlap_entropy=summary.repeat_overlap_entropy,
                            nesting_tendency=summary.multi_layer_nesting_tendency,
                            phase_recurrence_score=summary.phase_recurrence_score,
                            rotation_recurrence_mod60=((parameter.delta_theta_degrees * gap) % 60.0) <= TOLERANCE.coordinate_abs_tol,
                        )
                    )
    return tuple(rows)


def canonical_metric_payload() -> tuple[dict[str, Any], ...]:
    return _canonical_metric_payload_cached()


@lru_cache(maxsize=1)
def _canonical_metric_payload_cached() -> tuple[dict[str, Any], ...]:
    return tuple(row_payload(row) for row in build_metric_rows())


def row_payload(row: GPR1MetricRow) -> dict[str, Any]:
    return {
        "parameter_id": row.parameter_id,
        "gap": row.gap,
        "phase_label": row.phase_label,
        "phase_policy": row.phase_policy,
        "distribution_count": row.distribution_count,
        "branching_mean": _float(row.branching_mean),
        "branching_p95": _float(row.branching_p95),
        "branching_max": row.branching_max,
        "effective_count_mean": _float(row.effective_count_mean),
        "effective_count_p95": _float(row.effective_count_p95),
        "residual_mean": _float(row.residual_mean),
        "residual_p95": _float(row.residual_p95),
        "max_mass": _float(row.max_mass),
        "overlap_entropy": _float(row.overlap_entropy),
        "nesting_tendency": _float(row.nesting_tendency),
        "phase_recurrence_score": _float(row.phase_recurrence_score),
        "rotation_recurrence_mod60": row.rotation_recurrence_mod60,
    }


def distributions_for(schedule: ScaleRotationSchedule, gap: int, phase: PhaseSchedule, policy: LayerPhasePolicy) -> tuple[CoverageDistribution, ...]:
    distributions = []
    for base_layer in base_layers_for(gap):
        distributions.extend(distributions_for_base_layer(schedule, gap, phase, policy, base_layer))
    return tuple(distributions)


def distributions_for_base_layer(
    schedule: ScaleRotationSchedule,
    gap: int,
    phase: PhaseSchedule,
    policy: LayerPhasePolicy,
    base_layer: int,
) -> tuple[CoverageDistribution, ...]:
    source_layer = base_layer + gap
    source_phase = policy.phase_for_layer(phase, source_layer)
    target_phase = policy.phase_for_layer(phase, base_layer)
    source_chart = schedule.chart_for_layer(source_layer, source_phase)
    target_chart = schedule.chart_for_layer(base_layer, target_phase)
    distributions = []
    for axial in disk(AxialCoord(0, 0), SOURCE_RADIUS):
        source_cell = make_hex_cell(source_chart, axial)
        target_center = nearest_axial(target_chart, source_cell.center)
        targets = tuple(make_hex_cell(target_chart, target) for target in disk(target_center, TARGET_RADIUS))
        distributions.append(compute_distribution(source_cell, targets, CoverageDirection.fine_to_coarse, THRESHOLD, TOLERANCE))
    return tuple(distributions)


def base_layers_for(gap: int) -> tuple[int, ...]:
    if gap not in LAYER_GAPS:
        raise ValueError("gap must be one of LAYER_GAPS")
    return tuple(range(LAYER_RANGE[0], LAYER_RANGE[-1] + 1 - gap))


def phase_score_for(schedule: ScaleRotationSchedule, gap: int, phase: PhaseSchedule, policy: LayerPhasePolicy) -> float:
    phases = tuple(
        relative_phase(
            schedule.chart_for_layer(base_layer, policy.phase_for_layer(phase, base_layer)),
            schedule.chart_for_layer(base_layer + gap, policy.phase_for_layer(phase, base_layer + gap)),
        )
        for base_layer in base_layers_for(gap)
    )
    return phase_recurrence_score(phases)


def experiment_window_payload() -> dict[str, Any]:
    return {
        "layer_range": (LAYER_RANGE[0], LAYER_RANGE[-1]),
        "layer_gaps": LAYER_GAPS,
        "base_layer_rule": "base_layers(gap)=range(0, 17-gap)",
        "base_layer_counts": tuple((gap, len(base_layers_for(gap))) for gap in LAYER_GAPS),
        "source_axial_disk_radius": SOURCE_RADIUS,
        "target_neighborhood_radius": TARGET_RADIUS,
        "phase_samples": tuple((phase.phase_q, phase.phase_r) for phase in DEFAULT_PHASE_SAMPLES),
        "layer_phase_policies": tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES),
        "threshold": _float(THRESHOLD),
        "tolerance": tolerance_payload(TOLERANCE),
    }


def tolerance_payload(tolerance: GeometryTolerance) -> dict[str, str]:
    return {
        "coordinate_abs_tol": _float(tolerance.coordinate_abs_tol),
        "coordinate_rel_tol": _float(tolerance.coordinate_rel_tol),
        "area_abs_tol": _float(tolerance.area_abs_tol),
        "area_rel_tol": _float(tolerance.area_rel_tol),
    }


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "cortex", "admission", "field", "assembly", "recall")}


def phase_label(phase: PhaseSchedule) -> str:
    return f"({phase.phase_q:.6g},{phase.phase_r:.6g})"


def all_finite(row: GPR1MetricRow) -> bool:
    return all(
        isfinite(value)
        for value in (
            row.branching_mean,
            row.branching_p95,
            row.effective_count_mean,
            row.effective_count_p95,
            row.residual_mean,
            row.residual_p95,
            row.max_mass,
            row.overlap_entropy,
            row.nesting_tendency,
            row.phase_recurrence_score,
        )
    )


def _float(value: float) -> str:
    return format(float(value), ".12g")


def _mean(values) -> float:
    return sum(values) / len(values) if values else 0.0
