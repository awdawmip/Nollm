"""Local chart coordinate maps for the DG1 V2 geometry kernel.

Allowed: chart-local axial/world conversion, hex cell construction, and phase
diagnostics.
Forbidden: global atlas merge, recall, placement, Field, Cortex, Adapter, V1,
OpenClaw, runtime, filesystem, network, subprocess, or memory behavior.
"""

from math import cos, floor, pi, sin, sqrt

from .types import AxialCoord, CellRef, HexCell, LocalChart, PhaseCoord, Vec2, default_metadata


SQRT3 = sqrt(3.0)


def axial_to_world(chart: LocalChart, axial: AxialCoord) -> Vec2:
    reference_x = axial.q + axial.r / 2.0
    reference_y = SQRT3 * axial.r / 2.0
    scale = SQRT3 * chart.side_length
    local = Vec2(reference_x * scale, reference_y * scale)
    rotated = rotate_vec(local, chart.rotation_radians)
    return chart.translation + rotated


def world_to_fractional_axial(chart: LocalChart, point: Vec2) -> tuple[float, float]:
    translated = point - chart.translation
    local = rotate_vec(translated, -chart.rotation_radians).scale(1.0 / (SQRT3 * chart.side_length))
    rf = 2.0 * local.y / SQRT3
    qf = local.x - rf / 2.0
    return (qf, rf)


def make_hex_cell(chart: LocalChart, axial: AxialCoord) -> HexCell:
    center = axial_to_world(chart, axial)
    vertices = hex_polygon_vertices_from_center(center, chart.side_length, chart.rotation_radians)
    return HexCell(
        cell_ref=CellRef(chart.chart_id, axial),
        center=center,
        side_length=chart.side_length,
        rotation_radians=chart.rotation_radians,
        vertices=vertices,
        metadata=default_metadata(comparison_scale=chart.side_length),
    )


def hex_polygon_vertices(cell: HexCell) -> tuple[Vec2, ...]:
    return cell.vertices


def hex_polygon_vertices_from_center(center: Vec2, side_length: float, rotation_radians: float) -> tuple[Vec2, ...]:
    return tuple(
        Vec2(
            center.x + side_length * cos(rotation_radians + pi / 6.0 + index * pi / 3.0),
            center.y + side_length * sin(rotation_radians + pi / 6.0 + index * pi / 3.0),
        )
        for index in range(6)
    )


def normalized_phase(chart: LocalChart) -> PhaseCoord:
    local = rotate_vec(chart.translation, -chart.rotation_radians).scale(1.0 / (SQRT3 * chart.side_length))
    rf = 2.0 * local.y / SQRT3
    qf = local.x - rf / 2.0
    return PhaseCoord(_mod_one(qf), _mod_one(rf))


def phase_distance(a: PhaseCoord, b: PhaseCoord) -> float:
    dq = abs(a.q - b.q)
    dr = abs(a.r - b.r)
    dq = min(dq, 1.0 - dq)
    dr = min(dr, 1.0 - dr)
    return (dq * dq + dr * dr) ** 0.5


def rotate_vec(value: Vec2, angle_radians: float) -> Vec2:
    c = cos(angle_radians)
    s = sin(angle_radians)
    return Vec2(value.x * c - value.y * s, value.x * s + value.y * c)


def _mod_one(value: float) -> float:
    result = value - floor(value)
    if result >= 1.0:
        return 0.0
    if result < 0.0:
        return result + 1.0
    return 0.0 if abs(result - 1.0) <= 1e-12 or abs(result) <= 1e-12 else result


__all__ = [
    "SQRT3",
    "axial_to_world",
    "hex_polygon_vertices",
    "hex_polygon_vertices_from_center",
    "make_hex_cell",
    "normalized_phase",
    "phase_distance",
    "rotate_vec",
    "world_to_fractional_axial",
]
