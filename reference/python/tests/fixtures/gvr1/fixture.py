from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import isfinite
from pathlib import Path
from typing import Any

from nollm.dream_geometry.geometry.chart import make_hex_cell, relative_phase
from nollm.dream_geometry.geometry.coverage import CoverageDirection, CoverageDistribution, compute_distribution
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial
from nollm.dream_geometry.geometry.metrics import distribution_metrics, percentile, phase_recurrence_score, summarize_distributions
from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX, LayerPhasePolicy, ParameterSet, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, DEFAULT_TOLERANCE, GeometryTolerance


BASELINE_COMMIT = "c48ceba98e5d5197d16f91c3bad507b2ceaed242"
PARAMETER_ID = "B"
LAYER_RANGE = tuple(range(0, 17))
LAYER_GAPS = (1, 2, 4, 8, 16)
TRANSLATION_RADIUS = 1
TRANSLATION_OFFSETS = disk(AxialCoord(0, 0), TRANSLATION_RADIUS)
TARGET_RADIUS = 4
THRESHOLD = 1e-9
TOLERANCE = DEFAULT_TOLERANCE


@dataclass(frozen=True, slots=True)
class OffsetEnvelope:
    branching_mean_min: float
    branching_mean_max: float
    branching_mean_span: float
    max_mass_mean_min: float
    max_mass_mean_max: float
    max_mass_mean_span: float
    residual_mean_min: float
    residual_mean_max: float
    residual_mean_span: float


@dataclass(frozen=True, slots=True)
class GVR1MetricRow:
    parameter_id: str
    gap: int
    phase_label: str
    phase_policy: str
    base_layer_count: int
    offset_count: int
    distribution_count: int
    branching_mean: float
    branching_p95: float
    branching_max: int
    effective_count_mean: float
    effective_count_p95: float
    residual_mean: float
    residual_p95: float
    residual_max: float
    max_mass: float
    overlap_entropy: float
    nesting_tendency: float
    phase_recurrence_score: float
    rotation_recurrence_mod60: bool
    envelope: OffsetEnvelope


def baseline_parameter() -> ParameterSet:
    return next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == PARAMETER_ID)


def base_layers_for(gap: int) -> tuple[int, ...]:
    if gap not in LAYER_GAPS:
        raise ValueError("gap must be one of LAYER_GAPS")
    return tuple(range(LAYER_RANGE[0], LAYER_RANGE[-1] + 1 - gap))


def build_metric_rows() -> tuple[GVR1MetricRow, ...]:
    return _build_metric_rows_cached()


@lru_cache(maxsize=1)
def _build_metric_rows_cached() -> tuple[GVR1MetricRow, ...]:
    parameter = baseline_parameter()
    schedule = ScaleRotationSchedule(parameter)
    rows = []
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
                    GVR1MetricRow(
                        parameter_id=parameter.parameter_id,
                        gap=gap,
                        phase_label=phase_label(phase),
                        phase_policy=policy.policy_id,
                        base_layer_count=len(base_layers_for(gap)),
                        offset_count=len(TRANSLATION_OFFSETS),
                        distribution_count=len(distributions),
                        branching_mean=_mean(summary.branching_factors),
                        branching_p95=percentile(summary.branching_factors, 95),
                        branching_max=max(summary.branching_factors) if summary.branching_factors else 0,
                        effective_count_mean=_mean(summary.effective_parent_counts),
                        effective_count_p95=percentile(summary.effective_parent_counts, 95),
                        residual_mean=_mean(summary.residual_masses),
                        residual_p95=percentile(summary.residual_masses, 95),
                        residual_max=max(summary.residual_masses) if summary.residual_masses else 0.0,
                        max_mass=max(summary.max_coverage_masses) if summary.max_coverage_masses else 0.0,
                        overlap_entropy=summary.repeat_overlap_entropy,
                        nesting_tendency=summary.multi_layer_nesting_tendency,
                        phase_recurrence_score=summary.phase_recurrence_score,
                        rotation_recurrence_mod60=((parameter.delta_theta_degrees * gap) % 60.0) <= TOLERANCE.coordinate_abs_tol,
                        envelope=translation_envelope(schedule, gap, phase, policy),
                    )
                )
    return tuple(rows)


def canonical_metric_payload() -> tuple[dict[str, Any], ...]:
    return _canonical_metric_payload_cached()


@lru_cache(maxsize=1)
def _canonical_metric_payload_cached() -> tuple[dict[str, Any], ...]:
    return tuple(row_payload(row) for row in build_metric_rows())


def row_payload(row: GVR1MetricRow) -> dict[str, Any]:
    return {
        "parameter_id": row.parameter_id,
        "gap": row.gap,
        "phase_label": row.phase_label,
        "phase_policy": row.phase_policy,
        "base_layer_count": row.base_layer_count,
        "offset_count": row.offset_count,
        "distribution_count": row.distribution_count,
        "branching_mean": _float(row.branching_mean),
        "branching_p95": _float(row.branching_p95),
        "branching_max": row.branching_max,
        "effective_count_mean": _float(row.effective_count_mean),
        "effective_count_p95": _float(row.effective_count_p95),
        "residual_mean": _float(row.residual_mean),
        "residual_p95": _float(row.residual_p95),
        "residual_max": _float(row.residual_max),
        "max_mass": _float(row.max_mass),
        "overlap_entropy": _float(row.overlap_entropy),
        "nesting_tendency": _float(row.nesting_tendency),
        "phase_recurrence_score": _float(row.phase_recurrence_score),
        "rotation_recurrence_mod60": row.rotation_recurrence_mod60,
        "translation_envelope": envelope_payload(row.envelope),
    }


def envelope_payload(envelope: OffsetEnvelope) -> dict[str, str]:
    return {
        "branching_mean_min": _float(envelope.branching_mean_min),
        "branching_mean_max": _float(envelope.branching_mean_max),
        "branching_mean_span": _float(envelope.branching_mean_span),
        "max_mass_mean_min": _float(envelope.max_mass_mean_min),
        "max_mass_mean_max": _float(envelope.max_mass_mean_max),
        "max_mass_mean_span": _float(envelope.max_mass_mean_span),
        "residual_mean_min": _float(envelope.residual_mean_min),
        "residual_mean_max": _float(envelope.residual_mean_max),
        "residual_mean_span": _float(envelope.residual_mean_span),
    }


def distributions_for(schedule: ScaleRotationSchedule, gap: int, phase: PhaseSchedule, policy: LayerPhasePolicy) -> tuple[CoverageDistribution, ...]:
    distributions = []
    for offset in TRANSLATION_OFFSETS:
        distributions.extend(distributions_for_offset(schedule, gap, phase, policy, offset))
    return tuple(distributions)


@lru_cache(maxsize=None)
def distributions_for_offset(
    schedule: ScaleRotationSchedule,
    gap: int,
    phase: PhaseSchedule,
    policy: LayerPhasePolicy,
    source_offset: AxialCoord,
) -> tuple[CoverageDistribution, ...]:
    return tuple(
        distribution_for_base_layer(schedule, gap, phase, policy, base_layer, source_offset)
        for base_layer in base_layers_for(gap)
    )


def distribution_for_base_layer(
    schedule: ScaleRotationSchedule,
    gap: int,
    phase: PhaseSchedule,
    policy: LayerPhasePolicy,
    base_layer: int,
    source_offset: AxialCoord,
) -> CoverageDistribution:
    source_layer = base_layer + gap
    source_phase = policy.phase_for_layer(phase, source_layer)
    target_phase = policy.phase_for_layer(phase, base_layer)
    source_chart = schedule.chart_for_layer(source_layer, source_phase)
    target_chart = schedule.chart_for_layer(base_layer, target_phase)
    source_cell = make_hex_cell(source_chart, source_offset)
    target_center = nearest_axial(target_chart, source_cell.center)
    targets = tuple(make_hex_cell(target_chart, target) for target in disk(target_center, TARGET_RADIUS))
    return compute_distribution(source_cell, targets, CoverageDirection.fine_to_coarse, THRESHOLD, TOLERANCE)


def independently_reconstruct_center_distributions(gap: int, phase: PhaseSchedule, policy: LayerPhasePolicy) -> tuple[CoverageDistribution, ...]:
    schedule = ScaleRotationSchedule(baseline_parameter())
    distributions = []
    for base_layer in range(0, 17 - gap):
        source_layer = base_layer + gap
        source_phase = policy.phase_for_layer(phase, source_layer)
        target_phase = policy.phase_for_layer(phase, base_layer)
        source_chart = schedule.chart_for_layer(source_layer, source_phase)
        target_chart = schedule.chart_for_layer(base_layer, target_phase)
        source_cell = make_hex_cell(source_chart, AxialCoord(0, 0))
        target_center = nearest_axial(target_chart, source_cell.center)
        targets = tuple(make_hex_cell(target_chart, axial) for axial in disk(target_center, TARGET_RADIUS))
        distributions.append(compute_distribution(source_cell, targets, CoverageDirection.fine_to_coarse, THRESHOLD, TOLERANCE))
    return tuple(distributions)


def translation_envelope(schedule: ScaleRotationSchedule, gap: int, phase: PhaseSchedule, policy: LayerPhasePolicy) -> OffsetEnvelope:
    branching_means = []
    max_mass_means = []
    residual_means = []
    for offset in TRANSLATION_OFFSETS:
        metrics = tuple(distribution_metrics(distribution) for distribution in distributions_for_offset(schedule, gap, phase, policy, offset))
        branching_means.append(_mean(tuple(metric.branching_factor for metric in metrics)))
        max_mass_means.append(_mean(tuple(metric.max_coverage_mass for metric in metrics)))
        residual_means.append(_mean(tuple(metric.residual_mass for metric in metrics)))
    return OffsetEnvelope(
        branching_mean_min=min(branching_means),
        branching_mean_max=max(branching_means),
        branching_mean_span=max(branching_means) - min(branching_means),
        max_mass_mean_min=min(max_mass_means),
        max_mass_mean_max=max(max_mass_means),
        max_mass_mean_span=max(max_mass_means) - min(max_mass_means),
        residual_mean_min=min(residual_means),
        residual_mean_max=max(residual_means),
        residual_mean_span=max(residual_means) - min(residual_means),
    )


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
        "parameter_id": PARAMETER_ID,
        "layer_range": (LAYER_RANGE[0], LAYER_RANGE[-1]),
        "layer_gaps": LAYER_GAPS,
        "base_layer_rule": "base_layers(gap)=range(0, 17-gap)",
        "base_layer_counts": tuple((gap, len(base_layers_for(gap))) for gap in LAYER_GAPS),
        "translation_radius": TRANSLATION_RADIUS,
        "translation_offsets": tuple((offset.q, offset.r) for offset in TRANSLATION_OFFSETS),
        "offset_count": len(TRANSLATION_OFFSETS),
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


def all_finite(row: GVR1MetricRow) -> bool:
    return all(
        isfinite(value)
        for value in (
            row.branching_mean,
            row.branching_p95,
            row.effective_count_mean,
            row.effective_count_p95,
            row.residual_mean,
            row.residual_p95,
            row.residual_max,
            row.max_mass,
            row.overlap_entropy,
            row.nesting_tendency,
            row.phase_recurrence_score,
            row.envelope.branching_mean_min,
            row.envelope.branching_mean_max,
            row.envelope.branching_mean_span,
            row.envelope.max_mass_mean_min,
            row.envelope.max_mass_mean_max,
            row.envelope.max_mass_mean_span,
            row.envelope.residual_mean_min,
            row.envelope.residual_mean_max,
            row.envelope.residual_mean_span,
        )
    )


def _float(value: float) -> str:
    return format(float(value), ".12g")


def _mean(values) -> float:
    return sum(values) / len(values) if values else 0.0
