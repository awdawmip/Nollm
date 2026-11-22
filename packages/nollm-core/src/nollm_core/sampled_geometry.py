"""Public arithmetic inputs for experiments using the current sample kernel.

The stencil is an immutable value derived from the admitted fixed transform.
These primitives expose its existing samples, nearest-cell tie rule and Q16
normalization without changing the physical coverage contract or persisted
state. Transformed sample coordinates still require the caller's applicable
geometry and storage-domain interpretation.
"""
from __future__ import annotations

from dataclasses import dataclass

from .approximate_coverage import (
    _TRANSFORMS,
    _compiled_sample_offsets_q40,
    _nearest_axial_q40 as nearest_axial_q40,
    _sample_offsets_q40 as coverage_sample_offsets_q40,
    _validate,
)
from .fixed_point import normalize_q16_weights
from .geometry import GeometryAddress


@dataclass(frozen=True)
class CoverageStencil:
    """Q40 mapped source center and all 96 relative target-chart offsets."""

    direction: str
    center_q40: tuple[int, int]
    offsets_q40: tuple[tuple[int, int], ...]


def coverage_stencil_q40(source: GeometryAddress, direction: str) -> CoverageStencil:
    """Expose the existing integer stencil for one admitted source/direction."""
    _validate(source, direction)
    a, b, c, d = _TRANSFORMS[direction][:4]
    center = a * source.q + b * source.r, c * source.q + d * source.r
    return CoverageStencil(direction, center, _compiled_sample_offsets_q40(direction))
