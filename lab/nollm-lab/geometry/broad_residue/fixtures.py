from __future__ import annotations

from dataclasses import dataclass


DEFAULT_EXACT_PER_PHASE_DIRECTION = 128
DEFAULT_DIAGNOSTIC_COUNT = 20_000
STORAGE_RADIUS = (1 << 31) - 1
WRITABLE_RADIUS = (1 << 30) - 1


@dataclass(frozen=True)
class BroadFixture:
    layer: int
    q: int
    r: int
    direction: str
    phase: int
    coordinate_bucket: str
    ordinal: int


class _Lcg:
    def __init__(self, seed: int) -> None:
        self._state = seed & ((1 << 64) - 1)

    def next(self) -> int:
        self._state = (6364136223846793005 * self._state + 1442695040888963407) & ((1 << 64) - 1)
        return self._state

    def integer(self, low: int, high: int) -> int:
        return low + self.next() % (high - low + 1)


def broad_exact_fixtures(
    per_phase_direction: int = DEFAULT_EXACT_PER_PHASE_DIRECTION,
    *,
    seed: int = 0xCA01D39,
) -> tuple[BroadFixture, ...]:
    if type(per_phase_direction) is not int or per_phase_direction < 1:
        raise ValueError("per_phase_direction must be a positive integer")
    output = []
    for phase in range(8):
        layer = phase - 4
        for direction_index, direction in enumerate(("coverage_up", "coverage_down")):
            rng = _Lcg(seed ^ (phase << 20) ^ (direction_index << 16))
            for ordinal in range(per_phase_direction):
                bucket = _bucket(ordinal, per_phase_direction)
                q, r = _coordinate(rng, bucket, ordinal, phase, direction_index)
                output.append(BroadFixture(layer, q, r, direction, phase, bucket, ordinal))
    return tuple(output)


def fast_diagnostic_fixtures(
    count: int = DEFAULT_DIAGNOSTIC_COUNT,
    *,
    seed: int = 0xCA01D20,
) -> tuple[BroadFixture, ...]:
    if type(count) is not int or count < 1:
        raise ValueError("count must be a positive integer")
    rng = _Lcg(seed)
    output = []
    for ordinal in range(count):
        q, r = _uniform_hex(rng, STORAGE_RADIUS)
        phase = ordinal % 8
        output.append(BroadFixture(
            layer=phase - 4,
            q=q,
            r=r,
            direction="coverage_up" if (ordinal // 8) % 2 == 0 else "coverage_down",
            phase=phase,
            coordinate_bucket="storage_domain",
            ordinal=ordinal,
        ))
    return tuple(output)


def _bucket(ordinal: int, count: int) -> str:
    fraction = ordinal / count
    if fraction < 0.125:
        return "origin_small"
    if fraction < 0.5:
        return "uniform_residue"
    if fraction < 0.75:
        return "large_safe"
    if fraction < 0.875:
        return "hex_boundary_direction"
    return "cube_rounding_probe"


def _coordinate(
    rng: _Lcg,
    bucket: str,
    ordinal: int,
    phase: int,
    direction_index: int,
) -> tuple[int, int]:
    if bucket == "origin_small":
        points = ((0, 0), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1), (7, -3))
        q, r = points[(ordinal + phase + direction_index) % len(points)]
        scale = 1 + ordinal // len(points)
        return q * scale, r * scale
    if bucket == "uniform_residue":
        return _uniform_hex(rng, 1_000_003)
    if bucket == "large_safe":
        q, r = _uniform_hex(rng, WRITABLE_RADIUS - 4096)
        if _hex_radius(q, r) < WRITABLE_RADIUS // 4:
            q += WRITABLE_RADIUS // 3
        return q, r
    if bucket == "hex_boundary_direction":
        radius = WRITABLE_RADIUS - 8192 - ordinal
        corners = ((radius, 0), (0, radius), (-radius, radius), (-radius, 0), (0, -radius), (radius, -radius))
        return corners[(ordinal + phase + direction_index) % 6]
    # A wide odd-coordinate sweep exercises cube-rounding residues without
    # coupling the fixture generator to either implementation under test.
    base = rng.integer(-(1 << 25), 1 << 25)
    return base * 2 + 1, rng.integer(-(1 << 25), 1 << 25) * 2 - 1


def _uniform_hex(rng: _Lcg, radius: int) -> tuple[int, int]:
    while True:
        q = rng.integer(-radius, radius)
        r = rng.integer(-radius, radius)
        if _hex_radius(q, r) <= radius:
            return q, r


def _hex_radius(q: int, r: int) -> int:
    return max(abs(q), abs(r), abs(q + r))
