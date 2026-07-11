from __future__ import annotations

from dataclasses import dataclass

from .axial import AxialCoord, hex_ring
from .fixed_point import Q16_ONE, normalize_q16_weights
from .geometry import GeometryAddress
from .profiles import get_profile

COVERAGE_UP = "coverage_up"
COVERAGE_DOWN = "coverage_down"
LATERAL = "lateral"
DIRECTIONS = frozenset({COVERAGE_UP, COVERAGE_DOWN, LATERAL})
LAYER_INDEX_DIRECTION = "finer_with_increasing_index"


@dataclass(frozen=True, order=True)
class KernelEntry:
    layer_delta: int
    dq: int
    dr: int
    weight_q16: int


@dataclass(frozen=True)
class CoverageTemplate:
    profile_id: str
    direction: str
    entries: tuple[KernelEntry, ...]


class CoverageTemplateCompiler:
    def compile(self, profile_id: str, direction: str) -> CoverageTemplate:
        get_profile(profile_id)
        if direction not in DIRECTIONS:
            raise ValueError("unknown coverage direction")
        if direction == LATERAL:
            offsets = tuple((coord.q, coord.r) for coord in hex_ring(AxialCoord(0, 0), 1))
        elif profile_id == "aligned_baseline_v1":
            offsets = ((0, 0),)
        elif profile_id == "dream_quasi_v1":
            offsets = ((0, 0), (1, 0), (0, 1))
        elif profile_id == "eisenstein_exact_v1":
            offsets = ((0, 0), (1, 0), (0, 1)) if direction == COVERAGE_UP else ((0, 0), (-1, 0), (0, -1))
        else:
            raise ValueError("unknown profile_id")
        weights = normalize_q16_weights([1] * len(offsets))
        delta = -1 if direction == COVERAGE_UP else 1 if direction == COVERAGE_DOWN else 0
        entries = tuple(sorted((KernelEntry(delta, dq, dr, weight) for (dq, dr), weight in zip(offsets, weights))))
        return CoverageTemplate(profile_id, direction, entries)


def expand_template(cell: GeometryAddress, template: CoverageTemplate) -> tuple[tuple[GeometryAddress, int], ...]:
    if cell.profile_id != template.profile_id:
        raise ValueError("cell profile does not match template")
    return tuple(sorted(((GeometryAddress(cell.profile_id, cell.chart_id, cell.layer + entry.layer_delta, cell.q + entry.dq, cell.r + entry.dr, cell.phase), entry.weight_q16) for entry in template.entries), key=lambda item: (item[0].stable_key(), item[1])))


def expand_lateral(cell: GeometryAddress, ring: int) -> tuple[tuple[GeometryAddress, int], ...]:
    coords = hex_ring(AxialCoord(cell.q, cell.r), ring)
    weights = normalize_q16_weights([1] * len(coords))
    return tuple((GeometryAddress(cell.profile_id, cell.chart_id, cell.layer, coord.q, coord.r, cell.phase), weight) for coord, weight in zip(coords, weights))
