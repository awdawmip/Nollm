"""Hex-grid coordinate operations for the DG1 V2 geometry kernel.

Allowed: axial/cube conversion, distance, finite rings/disks, and deterministic
fractional coordinate rounding.
Forbidden: placement, recall, Field, Cortex, Adapter, V1, OpenClaw, runtime,
filesystem, network, subprocess, or memory behavior.
"""

from math import floor, sqrt

from .types import AxialCoord, CubeCoord, LocalChart, Vec2


AXIAL_DIRECTIONS: tuple[AxialCoord, ...] = (
    AxialCoord(1, 0),
    AxialCoord(0, 1),
    AxialCoord(-1, 1),
    AxialCoord(-1, 0),
    AxialCoord(0, -1),
    AxialCoord(1, -1),
)


def axial_to_cube(axial: AxialCoord) -> CubeCoord:
    return CubeCoord(axial.q, -axial.q - axial.r, axial.r)


def cube_to_axial(cube: CubeCoord) -> AxialCoord:
    return AxialCoord(cube.x, cube.z)


def hex_distance(a: AxialCoord, b: AxialCoord) -> int:
    ac = axial_to_cube(a)
    bc = axial_to_cube(b)
    return max(abs(ac.x - bc.x), abs(ac.y - bc.y), abs(ac.z - bc.z))


def neighbors(center: AxialCoord) -> tuple[AxialCoord, ...]:
    return tuple(AxialCoord(center.q + direction.q, center.r + direction.r) for direction in AXIAL_DIRECTIONS)


def ring(center: AxialCoord, radius: int) -> tuple[AxialCoord, ...]:
    _require_non_negative_radius(radius)
    if radius == 0:
        return (center,)
    results: list[AxialCoord] = []
    current = AxialCoord(center.q + AXIAL_DIRECTIONS[4].q * radius, center.r + AXIAL_DIRECTIONS[4].r * radius)
    for direction in AXIAL_DIRECTIONS:
        for _ in range(radius):
            results.append(current)
            current = AxialCoord(current.q + direction.q, current.r + direction.r)
    return tuple(results)


def disk(center: AxialCoord, radius: int) -> tuple[AxialCoord, ...]:
    _require_non_negative_radius(radius)
    cells: list[AxialCoord] = []
    for dq in range(-radius, radius + 1):
        min_dr = max(-radius, -dq - radius)
        max_dr = min(radius, -dq + radius)
        for dr in range(min_dr, max_dr + 1):
            cells.append(AxialCoord(center.q + dq, center.r + dr))
    return tuple(sorted(cells))


def world_to_fractional_axial(chart: LocalChart, point: Vec2) -> tuple[float, float]:
    from .chart import world_to_fractional_axial as chart_world_to_fractional_axial

    return chart_world_to_fractional_axial(chart, point)


def round_fractional_axial(qf: float, rf: float, tie_policy: str = "lexicographic_q_r") -> AxialCoord:
    """Round fractional axial coordinates with a stable tie policy.

    `lexicographic_q_r` evaluates the nearest integer cube candidates and picks
    the lexicographically smallest `(q, r)` among equal-distance candidates.
    This avoids Python bankers-rounding as an implicit policy.
    """

    if tie_policy != "lexicographic_q_r":
        raise ValueError("unsupported tie_policy")
    xf = qf
    zf = rf
    yf = -xf - zf
    q_floor = floor(xf)
    y_floor = floor(yf)
    z_floor = floor(zf)
    candidates: set[CubeCoord] = set()
    for xi in (q_floor - 1, q_floor, q_floor + 1, q_floor + 2):
        for yi in (y_floor - 1, y_floor, y_floor + 1, y_floor + 2):
            zi = -xi - yi
            if z_floor - 1 <= zi <= z_floor + 2:
                candidates.add(CubeCoord(int(xi), int(yi), int(zi)))
    if not candidates:
        raise ValueError("rounding produced no cube candidates")
    best = min(
        candidates,
        key=lambda cube: (
            (cube.x - xf) ** 2 + (cube.y - yf) ** 2 + (cube.z - zf) ** 2,
            cube.x,
            cube.z,
        ),
    )
    return cube_to_axial(best)


def nearest_axial(chart: LocalChart, point: Vec2) -> AxialCoord:
    qf, rf = world_to_fractional_axial(chart, point)
    return round_fractional_axial(qf, rf)


def _require_non_negative_radius(radius: int) -> None:
    if not isinstance(radius, int) or isinstance(radius, bool) or radius < 0:
        raise ValueError("radius must be a non-negative integer")


__all__ = [
    "AXIAL_DIRECTIONS",
    "axial_to_cube",
    "cube_to_axial",
    "disk",
    "hex_distance",
    "nearest_axial",
    "neighbors",
    "ring",
    "round_fractional_axial",
    "world_to_fractional_axial",
]
