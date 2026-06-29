"""Pure geometry boundary for Dream Geometry V2.

Allowed: local charts, hex cells, transforms, directed coverage kernels, cycle
residuals, and anti-resonance metrics.
Forbidden: natural language understanding, LLM calls, OpenClaw access, fact
truth decisions, real memory writes, recall resolution, Field/Cortex/Adapter
behavior, or runtime integration.
"""

from .chart import axial_to_world, make_hex_cell, normalized_phase, phase_distance, relative_phase, world_to_fractional_axial
from .coverage import CoverageDirection, CoverageDistribution, CoverageKernel, compute_distribution, compute_kernel
from .hexgrid import axial_to_cube, cube_to_axial, disk, hex_distance, nearest_axial, neighbors, ring
from .types import AxialCoord, CellRef, CubeCoord, GeometryTolerance, HexCell, LocalChart, Vec2

__all__ = [
    "AxialCoord",
    "CellRef",
    "CoverageDirection",
    "CoverageDistribution",
    "CoverageKernel",
    "CubeCoord",
    "GeometryTolerance",
    "HexCell",
    "LocalChart",
    "Vec2",
    "axial_to_cube",
    "axial_to_world",
    "compute_distribution",
    "compute_kernel",
    "cube_to_axial",
    "disk",
    "hex_distance",
    "make_hex_cell",
    "nearest_axial",
    "neighbors",
    "normalized_phase",
    "phase_distance",
    "relative_phase",
    "ring",
    "world_to_fractional_axial",
]
