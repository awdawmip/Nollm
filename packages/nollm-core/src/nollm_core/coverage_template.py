from __future__ import annotations

from dataclasses import dataclass

from .axial import AxialCoord, hex_ring
from .fixed_point import Q16_ONE, WEIGHT_FORMAT, normalize_q16_weights
from .geometry import GeometryAddress
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
    kernel_type: str = "coverage_template"
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("layer_delta", "dq", "dr", "weight_q16"):
            if type(getattr(self, name)) is not int:
                raise TypeError(f"{name} must be an integer")
        if self.weight_q16 < 0 or type(self.kernel_type) is not str or not self.kernel_type:
            raise ValueError("invalid KernelEntry")
        if type(self.flags) is not tuple or any(type(flag) is not str or not flag for flag in self.flags):
            raise TypeError("flags must be a tuple of strings")

    def to_mapping(self) -> dict[str, object]:
        return {"layer_delta": self.layer_delta, "dq": self.dq, "dr": self.dr, "weight_q16": self.weight_q16, "kernel_type": self.kernel_type, "flags": list(self.flags)}


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
    compiler: CompilerMetadata

    def __post_init__(self) -> None:
        get_profile(self.profile_id)
        if self.direction not in DIRECTIONS or type(self.from_layer_mod) is not int or type(self.to_layer_mod) is not int:
            raise TypeError("invalid CoverageTemplate identity")
        if self.source_phase is not None and (type(self.source_phase) is not str or not self.source_phase):
            raise TypeError("source_phase must be null or non-empty string")
        if type(self.entries) is not tuple or not self.entries or any(type(entry) is not KernelEntry for entry in self.entries):
            raise TypeError("entries must be a non-empty KernelEntry tuple")
        if any(type(value) is not int for value in (self.sum_weight_q16, self.normalization_residual_q16, self.approximation_residual_q16)):
            raise TypeError("CoverageTemplate residuals must be integers")
        if self.sum_weight_q16 != sum(entry.weight_q16 for entry in self.entries) or self.normalization_residual_q16 != Q16_ONE - self.sum_weight_q16 or self.approximation_residual_q16 < 0:
            raise ValueError("CoverageTemplate weight metadata mismatch")
        if type(self.compiler) is not CompilerMetadata:
            raise TypeError("compiler must be CompilerMetadata")
        delta = -1 if self.direction == COVERAGE_UP else 1 if self.direction == COVERAGE_DOWN else 0
        if self.to_layer_mod != self.from_layer_mod + delta or any(entry.layer_delta != delta for entry in self.entries):
            raise ValueError("coverage layer contract mismatch")
        if len(self.entries) > self.compiler.fanout_limit or tuple(sorted(self.entries)) != self.entries or len(set(self.entries)) != len(self.entries):
            raise ValueError("coverage entries are not canonical or exceed fanout")
        profile = get_profile(self.profile_id)
        expected_flags = tuple(sorted({flag for entry in self.entries for flag in entry.flags}))
        expected_method = "symbolic_research_template_with_residual" if self.profile_id == "dream_quasi_v1" else "integer_template_lookup"
        if self.compiler.flags != expected_flags or self.compiler.method != expected_method or self.compiler.weight_format != profile.weight_format or self.compiler.layer_index_direction != LAYER_INDEX_DIRECTION:
            raise ValueError("coverage compiler metadata mismatch")
        if (self.profile_id == "dream_quasi_v1" and self.approximation_residual_q16 <= 0) or (self.profile_id != "dream_quasi_v1" and self.approximation_residual_q16 != 0):
            raise ValueError("profile approximation residual mismatch")

    def to_mapping(self) -> dict[str, object]:
        return {"profile_id": self.profile_id, "direction": self.direction, "from_layer_mod": self.from_layer_mod, "to_layer_mod": self.to_layer_mod, "source_phase": self.source_phase, "entries": [entry.to_mapping() for entry in self.entries], "sum_weight_q16": self.sum_weight_q16, "normalization_residual_q16": self.normalization_residual_q16, "approximation_residual_q16": self.approximation_residual_q16, "compiler": self.compiler.to_mapping()}


class CoverageTemplateCompiler:
    def __init__(self, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> None:
        if type(fanout_limit) is not int or fanout_limit <= 0:
            raise ValueError("fanout_limit must be positive")
        self.fanout_limit = fanout_limit

    def compile(self, profile_id: str, direction: str, from_layer_mod: int = 0, source_phase: str | None = None) -> CoverageTemplate:
        profile = get_profile(profile_id)
        if direction not in DIRECTIONS or type(from_layer_mod) is not int:
            raise ValueError("invalid coverage request")
        entries = self._entries(profile_id, direction)
        if len(entries) > self.fanout_limit:
            raise ValueError("template fanout exceeds hard bound")
        flags = tuple(sorted({flag for entry in entries for flag in entry.flags}))
        total = sum(entry.weight_q16 for entry in entries)
        metadata = CompilerMetadata("grf1a_coverage_template_compiler", "symbolic_research_template_with_residual" if profile_id == "dream_quasi_v1" else "integer_template_lookup", profile.weight_format, self.fanout_limit, LAYER_INDEX_DIRECTION, flags)
        return CoverageTemplate(profile_id, direction, from_layer_mod, from_layer_mod + _layer_delta(direction), source_phase, entries, total, Q16_ONE - total, Q16_ONE // 16 if profile_id == "dream_quasi_v1" else 0, metadata)

    def _entries(self, profile_id: str, direction: str) -> tuple[KernelEntry, ...]:
        if direction == LATERAL:
            offsets = tuple((coord.q, coord.r, "lateral_neighbor") for coord in hex_ring(AxialCoord(0, 0), 1))
        elif profile_id == "aligned_baseline_v1":
            offsets = ((0, 0, "aligned_center"),)
        elif profile_id == "eisenstein_exact_v1":
            offsets = ((0, 0, "eisenstein_exact"), (1, 0, "eisenstein_exact"), (0, 1, "eisenstein_exact")) if direction == COVERAGE_UP else ((0, 0, "eisenstein_exact"), (-1, 0, "eisenstein_exact"), (0, -1, "eisenstein_exact"))
        else:
            offsets = ((0, 0, "boundary_ambiguous"), (1, 0, "boundary_ambiguous"), (0, 1, "boundary_ambiguous"))
        weights = normalize_q16_weights([1] * len(offsets))
        return tuple(sorted((KernelEntry(_layer_delta(direction), dq, dr, weight, "coverage_template", (flag,)) for (dq, dr, flag), weight in zip(offsets, weights)), key=lambda item: (item.layer_delta, item.dq, item.dr, item.kernel_type, item.flags)))


def expand_template(cell: GeometryAddress, template: CoverageTemplate, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> tuple[tuple[GeometryAddress, int], ...]:
    if cell.profile_id != template.profile_id or len(template.entries) > fanout_limit:
        raise ValueError("template cannot be expanded")
    return tuple(sorted(((GeometryAddress(cell.profile_id, cell.chart_id, cell.layer + entry.layer_delta, cell.q + entry.dq, cell.r + entry.dr, cell.phase), entry.weight_q16) for entry in template.entries), key=lambda item: (item[0].stable_key(), item[1])))


def validate_lateral_ring(ring: int, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> None:
    if type(ring) is not int or ring < 1:
        raise ValueError("lateral ring must be positive")
    if 6 * ring > fanout_limit:
        raise ValueError("lateral fanout exceeds hard bound")


def _layer_delta(direction: str) -> int:
    return -1 if direction == COVERAGE_UP else 1 if direction == COVERAGE_DOWN else 0
@dataclass(frozen=True)
class CompilerMetadata:
    compiler_id: str
    method: str
    weight_format: str
    fanout_limit: int
    layer_index_direction: str
    flags: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(type(getattr(self, name)) is not str or not getattr(self, name) for name in ("compiler_id", "method", "weight_format", "layer_index_direction")):
            raise TypeError("compiler string fields must be non-empty")
        if type(self.fanout_limit) is not int or self.fanout_limit <= 0:
            raise ValueError("compiler fanout_limit must be positive")
        if type(self.flags) is not tuple or tuple(sorted(set(self.flags))) != self.flags:
            raise ValueError("compiler flags must be sorted and unique")

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)

    def to_mapping(self) -> dict[str, object]:
        return {"compiler_id": self.compiler_id, "method": self.method, "weight_format": self.weight_format, "fanout_limit": self.fanout_limit, "layer_index_direction": self.layer_index_direction, "flags": list(self.flags)}
