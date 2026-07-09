"""Integer axial and cube coordinates for GRF cells."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class AxialCoord:
    q: int
    r: int

    def __post_init__(self) -> None:
        if type(self.q) is not int or type(self.r) is not int:
            raise TypeError("axial coordinates must be integers")


@dataclass(frozen=True, order=True)
class CubeCoord:
    x: int
    y: int
    z: int

    def __post_init__(self) -> None:
        if type(self.x) is not int or type(self.y) is not int or type(self.z) is not int:
            raise TypeError("cube coordinates must be integers")
        if self.x + self.y + self.z != 0:
            raise ValueError("cube coordinates must satisfy x + y + z = 0")


AXIAL_DIRECTIONS: tuple[AxialCoord, ...] = (
    AxialCoord(1, 0),
    AxialCoord(1, -1),
    AxialCoord(0, -1),
    AxialCoord(-1, 0),
    AxialCoord(-1, 1),
    AxialCoord(0, 1),
)


def axial_to_cube(coord: AxialCoord) -> CubeCoord:
    return CubeCoord(coord.q, coord.r, -coord.q - coord.r)


def cube_to_axial(coord: CubeCoord) -> AxialCoord:
    return AxialCoord(coord.x, coord.y)


def hex_distance(a: AxialCoord, b: AxialCoord = AxialCoord(0, 0)) -> int:
    dq = a.q - b.q
    dr = a.r - b.r
    return max(abs(dq), abs(dr), abs(dq + dr))


def hex_neighbors(coord: AxialCoord) -> tuple[AxialCoord, ...]:
    return tuple(AxialCoord(coord.q + delta.q, coord.r + delta.r) for delta in AXIAL_DIRECTIONS)


def hex_ring(center: AxialCoord, radius: int) -> tuple[AxialCoord, ...]:
    if type(radius) is not int or radius < 0:
        raise ValueError("radius must be a non-negative integer")
    if radius == 0:
        return (center,)
    cells = []
    for dq in range(-radius, radius + 1):
        for dr in range(-radius, radius + 1):
            coord = AxialCoord(center.q + dq, center.r + dr)
            if hex_distance(coord, center) == radius:
                cells.append(coord)
    return tuple(sorted(cells, key=lambda item: (item.q, item.r)))
