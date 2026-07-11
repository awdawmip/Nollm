from __future__ import annotations

from nollm_core.axial import AxialCoord, hex_ring
from nollm_core.coverage_template import (
    COVERAGE_DOWN,
    COVERAGE_UP,
    DEFAULT_FANOUT_LIMIT,
    DIRECTIONS,
    LATERAL,
    CompilerMetadata,
    CoverageTemplate,
    KernelEntry,
    LAYER_INDEX_DIRECTION,
)
from nollm_core.fixed_point import Q16_ONE, normalize_q16_weights
from nollm_core.profiles import get_profile


class CoverageTemplateCompiler:
    """Lab-only compiler for the canonical Core runtime template artifact."""

    def __init__(self, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> None:
        if type(fanout_limit) is not int or fanout_limit <= 0:
            raise ValueError("fanout_limit must be positive")
        self.fanout_limit = fanout_limit

    def compile(
        self,
        profile_id: str,
        direction: str,
        from_layer_mod: int = 0,
        source_phase: str | None = None,
    ) -> CoverageTemplate:
        profile = get_profile(profile_id)
        if direction not in DIRECTIONS or type(from_layer_mod) is not int:
            raise ValueError("invalid coverage request")
        entries = self._entries(profile_id, direction)
        if len(entries) > self.fanout_limit:
            raise ValueError("template fanout exceeds hard bound")
        flags = tuple(sorted({flag for entry in entries for flag in entry.flags}))
        total = sum(entry.weight_q16 for entry in entries)
        metadata = CompilerMetadata(
            "grf1a_coverage_template_compiler",
            "symbolic_research_template_with_residual" if profile_id == "dream_quasi_v1" else "integer_template_lookup",
            profile.weight_format,
            self.fanout_limit,
            LAYER_INDEX_DIRECTION,
            flags,
        )
        delta = -1 if direction == COVERAGE_UP else 1 if direction == COVERAGE_DOWN else 0
        return CoverageTemplate(
            profile_id,
            direction,
            from_layer_mod,
            from_layer_mod + delta,
            source_phase,
            entries,
            total,
            Q16_ONE - total,
            Q16_ONE // 16 if profile_id == "dream_quasi_v1" else 0,
            metadata,
        )

    def _entries(self, profile_id: str, direction: str) -> tuple[KernelEntry, ...]:
        if direction == LATERAL:
            offsets = tuple((coord.q, coord.r, "lateral_neighbor") for coord in hex_ring(AxialCoord(0, 0), 1))
        elif profile_id == "aligned_baseline_v1":
            offsets = ((0, 0, "aligned_center"),)
        elif profile_id == "eisenstein_exact_v1":
            offsets = (
                ((0, 0, "eisenstein_exact"), (1, 0, "eisenstein_exact"), (0, 1, "eisenstein_exact"))
                if direction == COVERAGE_UP
                else ((0, 0, "eisenstein_exact"), (-1, 0, "eisenstein_exact"), (0, -1, "eisenstein_exact"))
            )
        else:
            offsets = ((0, 0, "boundary_ambiguous"), (1, 0, "boundary_ambiguous"), (0, 1, "boundary_ambiguous"))
        weights = normalize_q16_weights([1] * len(offsets))
        delta = -1 if direction == COVERAGE_UP else 1 if direction == COVERAGE_DOWN else 0
        return tuple(
            sorted(
                (
                    KernelEntry(delta, dq, dr, weight, "coverage_template", (flag,))
                    for (dq, dr, flag), weight in zip(offsets, weights)
                ),
                key=lambda item: (item.layer_delta, item.dq, item.dr, item.kernel_type, item.flags),
            )
        )
