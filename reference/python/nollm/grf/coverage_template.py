"""Offline coverage template compiler and runtime lookup."""

from __future__ import annotations

from dataclasses import dataclass

from .axial import AxialCoord, hex_ring
from .cell_address import CellAddress
from .fixed_point import Q16_ONE, normalize_q16_weights, residual_q16
from .profiles import get_profile

COVERAGE_UP = "coverage_up"
COVERAGE_DOWN = "coverage_down"
LATERAL = "lateral"
DIRECTIONS = frozenset({COVERAGE_UP, COVERAGE_DOWN, LATERAL})
DEFAULT_FANOUT_LIMIT = 7
LAYER_INDEX_DIRECTION = "finer_with_increasing_index"


@dataclass(frozen=True, order=True)
class KernelEntry:
    layer_delta: int
    dq: int
    dr: int
    weight_q16: int
    kernel_type: str
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value in (self.layer_delta, self.dq, self.dr, self.weight_q16):
            if type(value) is not int:
                raise TypeError("kernel numeric fields must be integers")
        if self.weight_q16 < 0:
            raise ValueError("weight_q16 cannot be negative")


@dataclass(frozen=True)
class CoverageTemplate:
    profile_id: str
    direction: str
    from_layer_mod: int
    to_layer_mod: int
    source_phase: str | None
    entries: tuple[KernelEntry, ...]
    sum_weight_q16: int
    normalization_residual_q16: int
    approximation_residual_q16: int
    compiler: dict[str, object]

    def __post_init__(self) -> None:
        get_profile(self.profile_id)
        if self.direction not in DIRECTIONS:
            raise ValueError("unknown coverage direction")
        if type(self.from_layer_mod) is not int or type(self.to_layer_mod) is not int:
            raise TypeError("layer mods must be integers")
        if not self.entries:
            raise ValueError("template entries cannot be empty")
        if self.sum_weight_q16 != sum(entry.weight_q16 for entry in self.entries):
            raise ValueError("sum_weight_q16 mismatch")
        if self.normalization_residual_q16 != residual_q16([entry.weight_q16 for entry in self.entries]):
            raise ValueError("normalization_residual_q16 mismatch")
        if type(self.approximation_residual_q16) is not int or self.approximation_residual_q16 < 0:
            raise ValueError("approximation_residual_q16 must be a non-negative integer")


class CoverageTemplateCompiler:
    def __init__(self, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> None:
        if type(fanout_limit) is not int or fanout_limit <= 0:
            raise ValueError("fanout_limit must be positive")
        self.fanout_limit = fanout_limit

    def compile(self, profile_id: str, direction: str, from_layer_mod: int = 0, source_phase: str | None = None) -> CoverageTemplate:
        profile = get_profile(profile_id)
        if direction not in DIRECTIONS:
            raise ValueError("unknown coverage direction")
        entries = self._entries(profile.profile_id, direction)
        if len(entries) > self.fanout_limit:
            raise ValueError("template fanout exceeds hard bound")
        to_layer_mod = from_layer_mod + _layer_delta(direction)
        flags = sorted({flag for entry in entries for flag in entry.flags})
        return CoverageTemplate(
            profile.profile_id,
            direction,
            from_layer_mod,
            to_layer_mod,
            source_phase,
            entries,
            sum(entry.weight_q16 for entry in entries),
            residual_q16([entry.weight_q16 for entry in entries]),
            _approximation_residual(profile.profile_id),
            {
                "compiler_id": "grf1a_coverage_template_compiler",
                "method": _method(profile.profile_id),
                "weight_format": profile.weight_format,
                "fanout_limit": self.fanout_limit,
                "layer_index_direction": LAYER_INDEX_DIRECTION,
                "flags": tuple(flags),
            },
        )

    def _entries(self, profile_id: str, direction: str) -> tuple[KernelEntry, ...]:
        if direction == LATERAL:
            return _weighted_entries(0, tuple((coord.q, coord.r, "lateral_neighbor") for coord in hex_ring(AxialCoord(0, 0), 1)))
        if profile_id == "aligned_baseline_v1":
            offsets = ((0, 0, "aligned_center"),)
        elif profile_id == "eisenstein_exact_v1":
            offsets = _eisenstein_offsets(direction)
        elif profile_id == "dream_quasi_v1":
            offsets = ((0, 0, "boundary_ambiguous"), (1, 0, "boundary_ambiguous"), (0, 1, "boundary_ambiguous"))
        else:
            raise ValueError("unknown profile_id")
        return _weighted_entries(_layer_delta(direction), offsets)


def expand_template(cell: CellAddress, template: CoverageTemplate, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> tuple[tuple[CellAddress, int], ...]:
    if cell.profile_id != template.profile_id:
        raise ValueError("cell profile does not match template")
    if len(template.entries) > fanout_limit:
        raise ValueError("template fanout exceeds hard bound")
    expanded = tuple(
        (
            CellAddress(cell.profile_id, cell.chart_id, cell.layer + entry.layer_delta, cell.q + entry.dq, cell.r + entry.dr, cell.phase),
            entry.weight_q16,
        )
        for entry in template.entries
    )
    return tuple(sorted(expanded, key=lambda item: (item[0].stable_key(), item[1])))


def expand_lateral(cell: CellAddress, ring: int = 1, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> tuple[tuple[CellAddress, int], ...]:
    if type(ring) is not int or ring < 0:
        raise ValueError("ring must be a non-negative integer")
    coords = hex_ring(AxialCoord(cell.q, cell.r), ring)
    if len(coords) > fanout_limit:
        raise ValueError("lateral fanout exceeds hard bound")
    weights = normalize_q16_weights([1 for _ in coords])
    return tuple((CellAddress(cell.profile_id, cell.chart_id, cell.layer, coord.q, coord.r, cell.phase), weight) for coord, weight in zip(coords, weights))


def _weighted_entries(layer_delta: int, offsets: tuple[tuple[int, int, str], ...]) -> tuple[KernelEntry, ...]:
    weights = normalize_q16_weights([1 for _ in offsets])
    entries = tuple(KernelEntry(layer_delta, dq, dr, weight, "coverage_template", (flag,)) for (dq, dr, flag), weight in zip(offsets, weights))
    return tuple(sorted(entries, key=lambda item: (item.layer_delta, item.dq, item.dr, item.kernel_type, item.flags)))


def _eisenstein_offsets(direction: str) -> tuple[tuple[int, int, str], ...]:
    if direction == COVERAGE_UP:
        return ((0, 0, "eisenstein_exact"), (1, 0, "eisenstein_exact"), (0, 1, "eisenstein_exact"))
    if direction == COVERAGE_DOWN:
        return ((0, 0, "eisenstein_exact"), (-1, 0, "eisenstein_exact"), (0, -1, "eisenstein_exact"))
    raise ValueError("unsupported exact coverage direction")


def _layer_delta(direction: str) -> int:
    if direction == COVERAGE_UP:
        return -1
    if direction == COVERAGE_DOWN:
        return 1
    if direction == LATERAL:
        return 0
    raise ValueError("unknown coverage direction")


def _method(profile_id: str) -> str:
    if profile_id == "dream_quasi_v1":
        return "symbolic_research_template_with_residual"
    return "integer_template_lookup"


def _approximation_residual(profile_id: str) -> int:
    if profile_id == "dream_quasi_v1":
        return Q16_ONE // 16
    return 0
