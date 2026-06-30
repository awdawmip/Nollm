"""Read-only DR1 traversal diagnostics over supplied coverage distributions."""

from __future__ import annotations

from nollm.dream_geometry.field.types import CoarseCover, cell_ref_key
from nollm.dream_geometry.geometry.coverage import CoverageDirection, CoverageDistribution

from .types import TraversalRecord


def traversal_records(covers: tuple[CoarseCover, ...], coverage_down: tuple[CoverageDistribution, ...]) -> tuple[TraversalRecord, ...]:
    records: list[TraversalRecord] = []
    cover_by_cell = {cell_ref_key(cover.support_cell): cover for cover in covers}
    for distribution in coverage_down:
        source_ref = cell_ref_key(distribution.source_cell)
        cover = cover_by_cell.get(source_ref)
        if cover is None:
            continue
        records.append(
            TraversalRecord(
                phase="down",
                cover_id=cover.cover_id,
                source_cell_ref=source_ref,
                direction=distribution.direction.value,
                target_cell_refs=tuple(cell_ref_key(kernel.target_cell) for kernel in distribution.kernels),
                residual_mass=distribution.residual.mass,
                residual_reasons=tuple(reason.value for reason in distribution.residual.reasons),
                mass_in=1.0,
                mass_out=sum(kernel.weight for kernel in distribution.kernels),
                reason_code="DR1_K_DOWN_EXECUTED",
            )
        )
    return tuple(records)


def direction_warnings(
    coverage_up: tuple[CoverageDistribution, ...],
    coverage_down: tuple[CoverageDistribution, ...],
) -> tuple[str, ...]:
    warnings: list[str] = []
    for distribution in coverage_up:
        if distribution.direction is not CoverageDirection.fine_to_coarse:
            warnings.append("DR1_COVERAGE_UP_DIRECTION_MISMATCH")
    for distribution in coverage_down:
        if distribution.direction is not CoverageDirection.coarse_to_fine:
            warnings.append("DR1_COVERAGE_DOWN_DIRECTION_MISMATCH")
    return tuple(dict.fromkeys(warnings))


__all__ = ["direction_warnings", "traversal_records"]
