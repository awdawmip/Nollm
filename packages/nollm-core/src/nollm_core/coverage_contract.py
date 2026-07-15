from __future__ import annotations

from dataclasses import dataclass

from .fixed_point import Q16_ONE
from .geometry import GeometryAddress


APPROXIMATE_COVERAGE_METHOD_ID = "equal_area_hex_microtriangle_q40_m4_v1"
APPROXIMATE_COVERAGE_CONTRACT_ID = "nollm_bounded_approximate_hex_coverage_v1"
ACTIVE_COORDINATE_CONTRACT_ID = "nollm_hex_radius_2p31_default_chart_null_phase_v1"
SAMPLE_SUBDIVISION = 4
SAMPLE_COUNT = 6 * SAMPLE_SUBDIVISION * SAMPLE_SUBDIVISION
RELATION_THRESHOLD_Q16 = 1311
MAX_ACTIVE_HEX_RADIUS = (1 << 31) - 1
MIN_PHYSICAL_LAYER = -64
MAX_PHYSICAL_LAYER = 64


class UnsupportedPhysicalCoverage(ValueError):
    """The requested address is outside the active product contract."""


class AmbiguousPhysicalCoverage(ValueError):
    """Compatibility error for callers that handled the former exact kernel."""


@dataclass(frozen=True, order=True)
class PhysicalCoverageMember:
    target: GeometryAddress
    weight_q16: int
    hit_count: int
    classification: str
    q16_rounding_residual: int

    @property
    def quantization_residual_q16(self) -> int:
        return self.q16_rounding_residual


@dataclass(frozen=True)
class PhysicalCoverageExpansion:
    source: GeometryAddress
    direction: str
    members: tuple[PhysicalCoverageMember, ...]
    method_id: str
    sample_count: int
    threshold_residual_q16: int
    q16_rounding_residual: int
    fanout: int
    relation_threshold_q16: int
    q16_sum: int
    coordinate_contract_id: str
    approximation_contract_id: str
    ambiguous: bool = False

    @property
    def sum_weight_q16(self) -> int:
        return self.q16_sum

    @property
    def normalization_residual_q16(self) -> int:
        return Q16_ONE - self.q16_sum

    @property
    def max_quantization_residual_q16(self) -> int:
        return self.q16_rounding_residual

    def targets(self) -> tuple[tuple[GeometryAddress, int], ...]:
        if self.ambiguous:
            raise AmbiguousPhysicalCoverage("ambiguous physical coverage cannot propagate")
        return tuple((member.target, member.weight_q16) for member in self.members)
