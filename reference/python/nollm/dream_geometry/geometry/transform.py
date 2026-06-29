"""Similarity transforms for the DG1 V2 geometry kernel.

Allowed: orientation-preserving similarity fit, residual validation, inverse,
composition, and cycle residual reporting.
Forbidden: atlas merge, recall identity inference, Field, Cortex, Adapter, V1,
OpenClaw, runtime, filesystem, network, subprocess, or memory behavior.
"""

from dataclasses import dataclass
from math import hypot, isfinite

from .types import DEFAULT_TOLERANCE, GeometryTolerance, Vec2, default_metadata


@dataclass(frozen=True)
class SimilarityTransform:
    """Orientation-preserving similarity g(z) = a*z + b."""

    a_real: float
    a_imag: float
    b: Vec2
    orientation: str = "orientation_preserving"

    def __post_init__(self) -> None:
        if not isfinite(self.a_real) or not isfinite(self.a_imag):
            raise ValueError("transform scale components must be finite")
        if self.orientation not in {"orientation_preserving", "orientation_reversing"}:
            raise ValueError("unsupported transform orientation")

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
    linear_identity_error: float = 0.0
    translation_identity_error: float = 0.0
    witness_geometry_status: str = "unchecked"


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
    linear_identity_error: float
    translation_identity_error: float
    witness_geometry_status: str
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
    floor = _nondegenerate_floor(1.0, tolerance)
    if src_len2 <= floor * floor:
        raise ValueError("source witness pair must be non-degenerate")
    if dst_delta.norm() <= floor:
        raise ValueError("target witness pair must be non-degenerate")
    # Complex division (dst_delta / src_delta).
    a_real = (dst_delta.x * src_delta.x + dst_delta.y * src_delta.y) / src_len2
    a_imag = (dst_delta.y * src_delta.x - dst_delta.x * src_delta.y) / src_len2
    mapped = _apply_complex(a_real, a_imag, source_a)
    transform = SimilarityTransform(a_real, a_imag, target_a - mapped)
    if transform.scale <= floor:
        raise ValueError("fitted transform scale must be non-degenerate")
    return transform


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
    residual = _residual_for(transform, witnesses, reference_scale, tolerance)
    if transform.orientation != "orientation_preserving" or transform.scale <= _nondegenerate_floor(reference_scale, tolerance):
        return TransformValidation(transform, residual, "rejected")
    if residual.witness_geometry_status == "duplicate" or residual.witness_geometry_status == "collinear":
        return TransformValidation(transform, residual, "requires_review")
    if residual.orientation != "orientation_preserving":
        return TransformValidation(transform, residual, "rejected")
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
    linear_identity_error = hypot(composed.a_real - 1.0, composed.a_imag)
    translation_identity_error = composed.b.norm() / reference_scale
    witness_geometry_status = _witness_geometry_status(witness_points, reference_scale, tolerance)
    nondegenerate = all(transform.scale > _nondegenerate_floor(reference_scale, tolerance) for transform in cycle)
    identity_ok = linear_identity_error <= limit and translation_identity_error <= limit
    if composed.orientation != "orientation_preserving" or not nondegenerate:
        state = "rejected"
    elif max_error <= limit and identity_ok and witness_geometry_status == "nondegenerate":
        state = "verified"
    elif max_error <= 100.0 * limit and identity_ok:
        state = "requires_review"
    else:
        state = "rejected"
    return CycleResidual(rms, max_error, len(witness_points), reference_scale, linear_identity_error, translation_identity_error, witness_geometry_status, state)


def _residual_for(
    transform: SimilarityTransform,
    witnesses: tuple[TransformWitness, ...],
    reference_scale: float,
    tolerance: GeometryTolerance,
) -> TransformResidual:
    if not witnesses:
        raise ValueError("witnesses must be non-empty")
    errors = [(apply_transform(transform, witness.source) - witness.target).norm() for witness in witnesses]
    rms = (sum(error * error for error in errors) / len(errors)) ** 0.5
    source_status = _witness_geometry_status(tuple(witness.source for witness in witnesses), reference_scale, tolerance)
    target_status = _witness_geometry_status(tuple(witness.target for witness in witnesses), reference_scale, tolerance)
    status = source_status if source_status != "nondegenerate" else target_status
    return TransformResidual(rms, max(errors), len(witnesses), reference_scale, transform.orientation, witness_geometry_status=status)


def _apply_complex(a_real: float, a_imag: float, point: Vec2) -> Vec2:
    return Vec2(a_real * point.x - a_imag * point.y, a_imag * point.x + a_real * point.y)


def _nondegenerate_floor(reference_scale: float, tolerance: GeometryTolerance) -> float:
    return tolerance.coordinate_abs_tol + tolerance.coordinate_rel_tol * max(reference_scale, 1.0)


def _witness_geometry_status(points: tuple[Vec2, ...], reference_scale: float, tolerance: GeometryTolerance) -> str:
    if len(points) < 3:
        return "insufficient"
    if len(_distinct_points(points, reference_scale, tolerance)) < 3:
        return "duplicate"
    return "nondegenerate" if _has_noncollinear_triple(points, reference_scale, tolerance) else "collinear"


def _distinct_points(points: tuple[Vec2, ...], reference_scale: float, tolerance: GeometryTolerance) -> tuple[Vec2, ...]:
    limit = _nondegenerate_floor(reference_scale, tolerance)
    distinct: list[Vec2] = []
    for point in points:
        if all((point - existing).norm() > limit for existing in distinct):
            distinct.append(point)
    return tuple(distinct)


def _has_noncollinear_triple(points: tuple[Vec2, ...], reference_scale: float, tolerance: GeometryTolerance) -> bool:
    scale = max(reference_scale, 1.0)
    limit = max(tolerance.coordinate_rel_tol, tolerance.coordinate_abs_tol / scale)
    distinct = _distinct_points(points, reference_scale, tolerance)
    for index, first in enumerate(distinct):
        for jndex, second in enumerate(distinct[index + 1 :], start=index + 1):
            for third in distinct[jndex + 1 :]:
                normalized_area = abs((second - first).cross(third - first)) / (scale * scale)
                if normalized_area > limit:
                    return True
    return False


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
