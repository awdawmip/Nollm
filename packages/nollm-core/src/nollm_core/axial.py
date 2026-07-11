from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class AxialCoord:
    q: int
    r: int

    def __post_init__(self) -> None:
        if type(self.q) is not int or type(self.r) is not int:
            raise TypeError("axial coordinates must be integers")


def hex_distance(a: AxialCoord, b: AxialCoord = AxialCoord(0, 0)) -> int:
    dq, dr = a.q - b.q, a.r - b.r
    return max(abs(dq), abs(dr), abs(dq + dr))


def hex_ring(center: AxialCoord, radius: int) -> tuple[AxialCoord, ...]:
    if type(radius) is not int or radius < 0:
        raise ValueError("radius must be a non-negative integer")
    cells = [AxialCoord(center.q + dq, center.r + dr) for dq in range(-radius, radius + 1) for dr in range(-radius, radius + 1) if hex_distance(AxialCoord(center.q + dq, center.r + dr), center) == radius]
    return tuple(sorted(cells))
