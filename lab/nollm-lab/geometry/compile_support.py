from __future__ import annotations

from dataclasses import dataclass


Q16_ONE = 1 << 16
WEIGHT_FORMAT = "q16_65536"
DEFAULT_FANOUT_LIMIT = 7
LAYER_INDEX_DIRECTION = "finer_with_increasing_index"
DIRECTIONS = frozenset({"coverage_up", "coverage_down", "lateral"})


def hex_ring_one() -> tuple[tuple[int, int], ...]:
    return ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0))


def normalize_q16_weights(count: int) -> tuple[int, ...]:
    if type(count) is not int or count <= 0:
        raise ValueError("weight count must be positive")
    quotient, remainder = divmod(Q16_ONE, count)
    return tuple(quotient + (1 if index < remainder else 0) for index in range(count))


@dataclass(frozen=True, order=True)
class CompileKernelEntry:
    layer_delta: int
    dq: int
    dr: int
    weight_q16: int
    kernel_type: str
    flags: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "layer_delta": self.layer_delta,
            "dq": self.dq,
            "dr": self.dr,
            "weight_q16": self.weight_q16,
            "kernel_type": self.kernel_type,
            "flags": list(self.flags),
        }


@dataclass(frozen=True)
class CompileMetadata:
    compiler_id: str
    method: str
    weight_format: str
    fanout_limit: int
    layer_index_direction: str
    flags: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "compiler_id": self.compiler_id,
            "method": self.method,
            "weight_format": self.weight_format,
            "fanout_limit": self.fanout_limit,
            "layer_index_direction": self.layer_index_direction,
            "flags": list(self.flags),
        }


@dataclass(frozen=True)
class CompileTemplate:
    profile_id: str
    direction: str
    from_layer_mod: int
    to_layer_mod: int
    source_phase: str | None
    entries: tuple[CompileKernelEntry, ...]
    sum_weight_q16: int
    normalization_residual_q16: int
    approximation_residual_q16: int
    compiler: CompileMetadata

    def to_mapping(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "direction": self.direction,
            "from_layer_mod": self.from_layer_mod,
            "to_layer_mod": self.to_layer_mod,
            "source_phase": self.source_phase,
            "entries": [entry.to_mapping() for entry in self.entries],
            "sum_weight_q16": self.sum_weight_q16,
            "normalization_residual_q16": self.normalization_residual_q16,
            "approximation_residual_q16": self.approximation_residual_q16,
            "compiler": self.compiler.to_mapping(),
        }
