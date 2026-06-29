"""Directed coverage kernels for the DG1 V2 geometry kernel.

Allowed: polygon-confirmed K_up/K_down kernels, residual mass accounting, and
finite non-overlapping partition validation.
Forbidden: nearest-center confirmation, parent-child structures, cross-chart
multi-hypothesis aggregation, Field, Cortex, Recall, Adapter, V1, OpenClaw,
runtime, filesystem, network, subprocess, or memory behavior.
"""

from dataclasses import dataclass
from enum import Enum

from nollm.dream_geometry.protocol.contracts import KernelDirection

from .polygon import circumcircle_candidate_may_overlap, convex_polygon_intersection_area
from .types import DEFAULT_TOLERANCE, ComputationMetadata, GeometryTolerance, HexCell, default_metadata


class CoverageDirection(Enum):
    fine_to_coarse = "fine_to_coarse"
    coarse_to_fine = "coarse_to_fine"


class ResidualReason(Enum):
    outside_supplied_partition = "outside_supplied_partition"
    threshold_truncation = "threshold_truncation"
    numeric_tolerance = "numeric_tolerance"
    invalid_or_unverified_partition = "invalid_or_unverified_partition"


class PartitionValidationError(ValueError):
    pass


class MassConservationError(ValueError):
    pass


@dataclass(frozen=True)
class CoverageCandidate:
    source_cell: HexCell
    target_cell: HexCell
    may_overlap: bool


@dataclass(frozen=True)
class CoverageKernel:
    source_cell: HexCell
    target_cell: HexCell
    direction: CoverageDirection
    overlap_area: float
    source_area: float
    target_area: float
    weight: float
    metadata: ComputationMetadata


@dataclass(frozen=True)
class CoverageResidual:
    mass: float
    reasons: tuple[ResidualReason, ...]


@dataclass(frozen=True)
class CoverageDistribution:
    source_cell: HexCell
    direction: CoverageDirection
    kernels: tuple[CoverageKernel, ...]
    residual: CoverageResidual
    total_mass: float
    partition_size: int


def coverage_candidates(
    source_cell: HexCell,
    finite_target_cells: tuple[HexCell, ...],
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> tuple[CoverageCandidate, ...]:
    return tuple(
        CoverageCandidate(source_cell, target, circumcircle_candidate_may_overlap(source_cell, target, tolerance))
        for target in finite_target_cells
    )


def compute_kernel(
    source_cell: HexCell,
    target_cell: HexCell,
    direction: CoverageDirection | KernelDirection,
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> CoverageKernel:
    direction = _coerce_direction(direction)
    _validate_direction_scale(source_cell, target_cell, direction, tolerance)
    overlap = convex_polygon_intersection_area(source_cell.vertices, target_cell.vertices, tolerance)
    if overlap <= tolerance.area_abs_tol:
        overlap = 0.0
    denominator = source_cell.area
    weight = overlap / denominator if denominator > tolerance.area_abs_tol else 0.0
    return CoverageKernel(
        source_cell=source_cell,
        target_cell=target_cell,
        direction=direction,
        overlap_area=overlap,
        source_area=source_cell.area,
        target_area=target_cell.area,
        weight=weight,
        metadata=default_metadata(tolerance=tolerance, comparison_scale=max(source_cell.area, target_cell.area), area=True),
    )


def compute_distribution(
    source_cell: HexCell,
    finite_target_partition: tuple[HexCell, ...],
    direction: CoverageDirection | KernelDirection,
    threshold: float = 0.0,
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> CoverageDistribution:
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    direction = _coerce_direction(direction)
    validate_nonoverlapping_partition(finite_target_partition, tolerance)
    kernels: list[CoverageKernel] = []
    truncated_mass = 0.0
    for target in finite_target_partition:
        kernel = compute_kernel(source_cell, target, direction, tolerance)
        if kernel.weight <= tolerance.area_abs_tol:
            continue
        if kernel.weight < threshold:
            truncated_mass += kernel.weight
        else:
            kernels.append(kernel)
    kernel_mass = sum(kernel.weight for kernel in kernels)
    total_before_residual = kernel_mass + truncated_mass
    limit = 1.0 + tolerance.area_abs_tol + tolerance.area_rel_tol
    if total_before_residual > limit:
        raise MassConservationError("coverage mass exceeds one for supplied partition")
    residual_mass = max(0.0, 1.0 - kernel_mass)
    reasons: list[ResidualReason] = []
    if truncated_mass > tolerance.area_abs_tol:
        reasons.append(ResidualReason.threshold_truncation)
    if 1.0 - total_before_residual > tolerance.area_abs_tol:
        reasons.append(ResidualReason.outside_supplied_partition)
    if residual_mass <= tolerance.area_abs_tol:
        residual_mass = 0.0
        if not reasons:
            reasons.append(ResidualReason.numeric_tolerance)
    return CoverageDistribution(
        source_cell=source_cell,
        direction=direction,
        kernels=tuple(kernels),
        residual=CoverageResidual(residual_mass, tuple(dict.fromkeys(reasons))),
        total_mass=kernel_mass + residual_mass,
        partition_size=len(finite_target_partition),
    )


def validate_nonoverlapping_partition(cells: tuple[HexCell, ...], tolerance: GeometryTolerance = DEFAULT_TOLERANCE) -> None:
    seen_refs: set[object] = set()
    expected_fingerprint = None
    for cell in cells:
        if cell.cell_ref in seen_refs:
            raise PartitionValidationError("duplicate target cell in partition")
        seen_refs.add(cell.cell_ref)
        if cell.chart_fingerprint is None:
            raise PartitionValidationError("partition cells must carry chart geometry fingerprint")
        if expected_fingerprint is None:
            expected_fingerprint = cell.chart_fingerprint
        elif cell.chart_fingerprint != expected_fingerprint:
            raise PartitionValidationError("partition must belong to one chart geometry")
    for index, first in enumerate(cells):
        for second in cells[index + 1 :]:
            if first.cell_ref.chart_id != second.cell_ref.chart_id:
                raise PartitionValidationError("partition must belong to one chart")
            if not circumcircle_candidate_may_overlap(first, second, tolerance):
                continue
            area = convex_polygon_intersection_area(first.vertices, second.vertices, tolerance)
            if area > tolerance.area_abs_tol:
                raise PartitionValidationError("target partition cells overlap with positive area")


def _coerce_direction(direction: CoverageDirection | KernelDirection) -> CoverageDirection:
    if isinstance(direction, CoverageDirection):
        return direction
    if direction is KernelDirection.fine_to_coarse:
        return CoverageDirection.fine_to_coarse
    if direction is KernelDirection.coarse_to_fine:
        return CoverageDirection.coarse_to_fine
    raise ValueError("unsupported coverage direction")


def _validate_direction_scale(source_cell: HexCell, target_cell: HexCell, direction: CoverageDirection, tolerance: GeometryTolerance) -> None:
    if direction is CoverageDirection.fine_to_coarse and source_cell.side_length > target_cell.side_length + tolerance.coordinate_abs_tol:
        raise ValueError("fine_to_coarse requires source side_length <= target side_length")
    if direction is CoverageDirection.coarse_to_fine and source_cell.side_length + tolerance.coordinate_abs_tol < target_cell.side_length:
        raise ValueError("coarse_to_fine requires source side_length >= target side_length")


__all__ = [
    "CoverageCandidate",
    "CoverageDirection",
    "CoverageDistribution",
    "CoverageKernel",
    "CoverageResidual",
    "MassConservationError",
    "PartitionValidationError",
    "ResidualReason",
    "compute_distribution",
    "compute_kernel",
    "coverage_candidates",
    "validate_nonoverlapping_partition",
]
