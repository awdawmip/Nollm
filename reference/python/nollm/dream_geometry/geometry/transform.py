"""Similarity transforms for the DG1 V2 geometry kernel.

Allowed: orientation-preserving similarity fit, residual validation, inverse,
composition, and cycle residual reporting.
Forbidden: atlas merge, recall identity inference, Field, Cortex, Adapter, V1,
OpenClaw, runtime, filesystem, network, subprocess, or memory behavior.
"""

from dataclasses import dataclass
from math import atan2, hypot

from .types import DEFAULT_TOLERANCE, GeometryTolerance, Vec2, default_metadata


@dataclass(frozen=True)
class SimilarityTransform:
    """Orientation-preserving similarity g(z) = a*z + b."""

    a_real: float
    a_imag: float
    b: Vec2
    orientation: str = "orientation_preserving"

    @property
    def scale(self) -> float:
        return hypot(self.a_real, self.a_imag)


@dataclass(frozen=True)
class TransformWitness:
    source: Vec2
    target: Vec2


@dataclass(frozen=True)
class TransformResidual:
    rms_residual: float
    max_residual: float
    witness_count: int
    reference_scale: float
    orientation: str


@dataclass(frozen=True)
class TransformValidation:
    transform: SimilarityTransform
    residual: TransformResidual
    state_recommendation: str


@dataclass(frozen=True)
class CycleResidual:
    rms_residual: float
    max_residual: float
    witness_count: int
    reference_scale: float
    state_recommendation: str


def fit_orientation_preserving_similarity_from_two_pairs(
    source_a: Vec2,
    source_b: Vec2,
    target_a: Vec2,
    target_b: Vec2,
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> SimilarityTransform:
    src_delta = source_b - source_a
    dst_delta = target_b - target_a
    src_len2 = src_delta.x * src_delta.x + src_delta.y * src_delta.y
    if src_len2 <= tolerance.coordinate_abs_tol * tolerance.coordinate_abs_tol:
        raise ValueError("source witness pair must be non-degenerate")
    # Complex division (dst_delta / src_delta).
    a_real = (dst_delta.x * src_delta.x + dst_delta.y * src_delta.y) / src_len2
    a_imag = (dst_delta.y * src_delta.x - dst_delta.x * src_delta.y) / src_len2
    mapped = _apply_complex(a_real, a_imag, source_a)
    return SimilarityTransform(a_real, a_imag, target_a - mapped)


def apply_transform(transform: SimilarityTransform, point: Vec2) -> Vec2:
    return _apply_complex(transform.a_real, transform.a_imag, point) + transform.b


def invert_transform(transform: SimilarityTransform, tolerance: GeometryTolerance = DEFAULT_TOLERANCE) -> SimilarityTransform:
    denom = transform.a_real * transform.a_real + transform.a_imag * transform.a_imag
    if denom <= tolerance.coordinate_abs_tol * tolerance.coordinate_abs_tol:
        raise ValueError("cannot invert a zero-scale transform")
    inv_a_real = transform.a_real / denom
    inv_a_imag = -transform.a_imag / denom
    inv_b = _apply_complex(inv_a_real, inv_a_imag, transform.b.scale(-1.0))
    return SimilarityTransform(inv_a_real, inv_a_imag, inv_b, transform.orientation)


def compose_transforms(after: SimilarityTransform, before: SimilarityTransform) -> SimilarityTransform:
    """Return after o before."""

    a_real = after.a_real * before.a_real - after.a_imag * before.a_imag
    a_imag = after.a_real * before.a_imag + after.a_imag * before.a_real
    b = apply_transform(after, before.b)
    orientation = "orientation_preserving" if after.orientation == before.orientation == "orientation_preserving" else "orientation_reversing"
    return SimilarityTransform(a_real, a_imag, b, orientation)


def validate_transform(
    transform: SimilarityTransform,
    witnesses: tuple[TransformWitness, ...],
    reference_scale: float,
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> TransformValidation:
    if reference_scale <= 0:
        raise ValueError("reference_scale must be positive")
    if transform.orientation != "orientation_preserving":
        residual = _residual_for(transform, witnesses, reference_scale)
        return TransformValidation(transform, residual, "rejected")
    residual = _residual_for(transform, witnesses, reference_scale)
    limit = tolerance.coordinate_abs_tol + tolerance.coordinate_rel_tol * reference_scale
    if residual.witness_count >= 3 and residual.max_residual <= limit:
        state = "verified"
    elif residual.max_residual <= 100.0 * limit:
        state = "requires_review"
    else:
        state = "rejected"
    return TransformValidation(transform, residual, state)


def cycle_residual(
    cycle: tuple[SimilarityTransform, ...],
    witness_points: tuple[Vec2, ...],
    reference_scale: float,
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> CycleResidual:
    if not cycle:
        raise ValueError("cycle must contain at least one transform")
    composed = cycle[0]
    for transform in cycle[1:]:
        composed = compose_transforms(transform, composed)
    if not witness_points:
        raise ValueError("witness_points must be non-empty")
    errors = [(apply_transform(composed, point) - point).norm() for point in witness_points]
    rms = (sum(error * error for error in errors) / len(errors)) ** 0.5
    max_error = max(errors)
    limit = tolerance.coordinate_abs_tol + tolerance.coordinate_rel_tol * reference_scale
    if max_error <= limit:
        state = "verified"
    elif max_error <= 100.0 * limit:
        state = "requires_review"
    else:
        state = "rejected"
    return CycleResidual(rms, max_error, len(witness_points), reference_scale, state)


def _residual_for(transform: SimilarityTransform, witnesses: tuple[TransformWitness, ...], reference_scale: float) -> TransformResidual:
    if not witnesses:
        raise ValueError("witnesses must be non-empty")
    errors = [(apply_transform(transform, witness.source) - witness.target).norm() for witness in witnesses]
    rms = (sum(error * error for error in errors) / len(errors)) ** 0.5
    return TransformResidual(rms, max(errors), len(witnesses), reference_scale, transform.orientation)


def _apply_complex(a_real: float, a_imag: float, point: Vec2) -> Vec2:
    return Vec2(a_real * point.x - a_imag * point.y, a_imag * point.x + a_real * point.y)


__all__ = [
    "CycleResidual",
    "SimilarityTransform",
    "TransformResidual",
    "TransformValidation",
    "TransformWitness",
    "apply_transform",
    "compose_transforms",
    "cycle_residual",
    "fit_orientation_preserving_similarity_from_two_pairs",
    "invert_transform",
    "validate_transform",
]
