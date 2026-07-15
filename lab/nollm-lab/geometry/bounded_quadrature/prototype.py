from __future__ import annotations

from functools import lru_cache
import math


@lru_cache(maxsize=2)
def sample_offsets(subdivision: int) -> tuple[tuple[float, float], ...]:
    if subdivision not in (3, 4):
        raise ValueError("calibration subdivision must be 3 or 4")
    vertices = tuple(
        (math.cos(math.pi / 6 + index * math.pi / 3), math.sin(math.pi / 6 + index * math.pi / 3))
        for index in range(6)
    )
    output = []
    for sector, first in enumerate(vertices):
        second = vertices[(sector + 1) % 6]
        for i in range(subdivision):
            for j in range(subdivision - i):
                output.append(_centroid(first, second, 3 * i + 1, 3 * j + 1, 3 * subdivision))
        for i in range(subdivision - 1):
            for j in range(subdivision - 1 - i):
                output.append(_centroid(first, second, 3 * i + 2, 3 * j + 2, 3 * subdivision))
    expected = 6 * subdivision * subdivision
    if len(output) != expected:
        raise RuntimeError("quadrature sample count mismatch")
    return tuple(output)


def approximate_hits(
    source_layer: int,
    q: int,
    r: int,
    target_layer: int,
    subdivision: int,
) -> dict[tuple[int, int], int]:
    delta = target_layer - source_layer
    if delta not in (-1, 1):
        raise ValueError("quadrature requires adjacent physical layers")
    side = 2 ** (-delta / 4)
    angle = math.pi * delta / 8
    cosine, sine = math.cos(angle), math.sin(angle)
    source_x = math.sqrt(3) * (q + r / 2)
    source_y = 1.5 * r
    output: dict[tuple[int, int], int] = {}
    for offset_x, offset_y in sample_offsets(subdivision):
        x, y = source_x + offset_x, source_y + offset_y
        target_x = (cosine * x + sine * y) / side
        target_y = (-sine * x + cosine * y) / side
        target_r = 2 * target_y / 3
        target_q = target_x / math.sqrt(3) - target_r / 2
        target = _nearest_axial(target_q, target_r)
        output[target] = output.get(target, 0) + 1
    return output


def _centroid(first, second, first_weight: int, second_weight: int, denominator: int):
    return (
        (first_weight * first[0] + second_weight * second[0]) / denominator,
        (first_weight * first[1] + second_weight * second[1]) / denominator,
    )


def _nearest_axial(q: float, r: float) -> tuple[int, int]:
    x_fraction, z_fraction, y_fraction = q, r, -q - r
    x, z, y = round(x_fraction), round(z_fraction), round(y_fraction)
    dx, dz, dy = abs(x - x_fraction), abs(z - z_fraction), abs(y - y_fraction)
    if dx >= dz and dx >= dy:
        x = -y - z
    elif dz >= dy:
        z = -x - y
    return x, z
