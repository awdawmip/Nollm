"""Finite anti-resonance metrics for the DG1 V2 geometry kernel.

Allowed: pure statistics over finite coverage distributions, phase samples, and
synthetic transform residuals.
Forbidden: final parameter selection, semantic interpretation, Field, Cortex,
Recall, Adapter, V1, OpenClaw, runtime, filesystem, network, subprocess, or
memory behavior.
"""

from dataclasses import dataclass
from math import log

from .coverage import CoverageDistribution
from .types import PhaseCoord


@dataclass(frozen=True)
class DistributionMetrics:
    branching_factor: int
    effective_parent_count: float
    max_coverage_mass: float
    coverage_ambiguity: float
    residual_mass: float


@dataclass(frozen=True)
class AntiResonanceSummary:
    parameter_id: str
    gap: int
    phase_label: str
    branching_factors: tuple[int, ...]
    effective_parent_counts: tuple[float, ...]
    max_coverage_masses: tuple[float, ...]
    residual_masses: tuple[float, ...]
    repeat_overlap_entropy: float
    multi_layer_nesting_tendency: float
    coverage_ambiguity: float
    phase_recurrence_score: float


def branching_factor(weights: tuple[float, ...], threshold: float = 0.0) -> int:
    return len([weight for weight in weights if weight > threshold])


def effective_parent_count(weights: tuple[float, ...]) -> float:
    total = sum(weight for weight in weights if weight > 0.0)
    if total <= 0.0:
        return 0.0
    entropy = 0.0
    for weight in weights:
        if weight <= 0.0:
            continue
        probability = weight / total
        entropy -= probability * log(probability)
    return 2.718281828459045 ** entropy


def max_coverage_mass(weights: tuple[float, ...]) -> float:
    return max(weights) if weights else 0.0


def coverage_ambiguity(weights: tuple[float, ...]) -> float:
    return effective_parent_count(weights)


def distribution_metrics(distribution: CoverageDistribution, threshold: float = 0.0) -> DistributionMetrics:
    weights = tuple(kernel.weight for kernel in distribution.kernels)
    return DistributionMetrics(
        branching_factor=branching_factor(weights, threshold),
        effective_parent_count=effective_parent_count(weights),
        max_coverage_mass=max_coverage_mass(weights),
        coverage_ambiguity=coverage_ambiguity(weights),
        residual_mass=distribution.residual.mass,
    )


def repeat_overlap_entropy(signatures: tuple[tuple[int, ...], ...]) -> float:
    if not signatures:
        return 0.0
    counts: dict[tuple[int, ...], int] = {}
    for signature in signatures:
        counts[signature] = counts.get(signature, 0) + 1
    total = float(len(signatures))
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * log(p, 2.0)
    return entropy


def quantized_signature(weights: tuple[float, ...], quantum: float = 0.05) -> tuple[int, ...]:
    if quantum <= 0.0:
        raise ValueError("quantum must be positive")
    positive = sorted((weight for weight in weights if weight > 0.0), reverse=True)
    return tuple(int(round(weight / quantum)) for weight in positive)


def multi_layer_nesting_tendency(max_masses: tuple[float, ...], epsilon: float = 1e-6) -> float:
    if not max_masses:
        return 0.0
    nested = len([mass for mass in max_masses if mass >= 1.0 - epsilon])
    return nested / len(max_masses)


def phase_recurrence_score(phases: tuple[PhaseCoord, ...], max_distance: float = 1e-9) -> float:
    if len(phases) < 2:
        return 0.0
    from .chart import phase_distance

    pairs = 0
    recurrent = 0
    for index, first in enumerate(phases):
        for second in phases[index + 1 :]:
            pairs += 1
            if phase_distance(first, second) <= max_distance:
                recurrent += 1
    return recurrent / pairs if pairs else 0.0


def summarize_distributions(
    parameter_id: str,
    gap: int,
    phase_label: str,
    distributions: tuple[CoverageDistribution, ...],
    phase_score: float,
) -> AntiResonanceSummary:
    metric_rows = tuple(distribution_metrics(distribution) for distribution in distributions)
    signatures = tuple(quantized_signature(tuple(kernel.weight for kernel in distribution.kernels)) for distribution in distributions)
    max_masses = tuple(row.max_coverage_mass for row in metric_rows)
    return AntiResonanceSummary(
        parameter_id=parameter_id,
        gap=gap,
        phase_label=phase_label,
        branching_factors=tuple(row.branching_factor for row in metric_rows),
        effective_parent_counts=tuple(row.effective_parent_count for row in metric_rows),
        max_coverage_masses=max_masses,
        residual_masses=tuple(row.residual_mass for row in metric_rows),
        repeat_overlap_entropy=repeat_overlap_entropy(signatures),
        multi_layer_nesting_tendency=multi_layer_nesting_tendency(max_masses),
        coverage_ambiguity=_mean(tuple(row.coverage_ambiguity for row in metric_rows)),
        phase_recurrence_score=phase_score,
    )


def percentile(values: tuple[float, ...] | tuple[int, ...], percentile_value: float) -> float:
    if not values:
        return 0.0
    if not 0.0 <= percentile_value <= 100.0:
        raise ValueError("percentile_value must be in [0, 100]")
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    rank = percentile_value / 100.0 * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _mean(values: tuple[float, ...] | tuple[int, ...]) -> float:
    return sum(values) / len(values) if values else 0.0


__all__ = [
    "AntiResonanceSummary",
    "DistributionMetrics",
    "branching_factor",
    "coverage_ambiguity",
    "distribution_metrics",
    "effective_parent_count",
    "max_coverage_mass",
    "multi_layer_nesting_tendency",
    "percentile",
    "phase_recurrence_score",
    "quantized_signature",
    "repeat_overlap_entropy",
    "summarize_distributions",
]
