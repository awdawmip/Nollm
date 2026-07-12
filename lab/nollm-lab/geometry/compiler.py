from __future__ import annotations

from compile_support import (
    DEFAULT_FANOUT_LIMIT,
    DIRECTIONS,
    LAYER_INDEX_DIRECTION,
    Q16_ONE,
    CompileKernelEntry,
    CompileMetadata,
    CompileTemplate,
    hex_ring_one,
    normalize_q16_weights,
)
from research_profiles import research_profile


class CoverageTemplateCompiler:
    """Lab-owned compiler for the canonical Core runtime artifact."""

    def __init__(self, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> None:
        if type(fanout_limit) is not int or fanout_limit <= 0:
            raise ValueError("fanout_limit must be positive")
        self.fanout_limit = fanout_limit

    def compile(self, profile_id: str, direction: str, from_layer_mod: int = 0, source_phase: str | None = None) -> CompileTemplate:
        profile = research_profile(profile_id)
        if direction not in DIRECTIONS or type(from_layer_mod) is not int:
            raise ValueError("invalid coverage request")
        entries = self._entries(profile_id, direction)
        if len(entries) > self.fanout_limit:
            raise ValueError("template fanout exceeds hard bound")
        flags = tuple(sorted({flag for entry in entries for flag in entry.flags}))
        total = sum(entry.weight_q16 for entry in entries)
        metadata = CompileMetadata(
            "grf1a_coverage_template_compiler",
            "symbolic_research_template_with_residual" if profile_id == "dream_quasi_v1" else "integer_template_lookup",
            profile.weight_format,
            self.fanout_limit,
            LAYER_INDEX_DIRECTION,
            flags,
        )
        delta = -1 if direction == "coverage_up" else 1 if direction == "coverage_down" else 0
        return CompileTemplate(profile_id, direction, from_layer_mod, from_layer_mod + delta, source_phase, entries, total, Q16_ONE - total, Q16_ONE // 16 if profile_id == "dream_quasi_v1" else 0, metadata)

    def _entries(self, profile_id: str, direction: str) -> tuple[CompileKernelEntry, ...]:
        if direction == "lateral":
            offsets = tuple((q, r, "lateral_neighbor") for q, r in hex_ring_one())
        elif profile_id == "aligned_baseline_v1":
            offsets = ((0, 0, "aligned_center"),)
        elif profile_id == "eisenstein_exact_v1":
            offsets = (((0, 0, "eisenstein_exact"), (1, 0, "eisenstein_exact"), (0, 1, "eisenstein_exact")) if direction == "coverage_up" else ((0, 0, "eisenstein_exact"), (-1, 0, "eisenstein_exact"), (0, -1, "eisenstein_exact")))
        else:
            offsets = ((0, 0, "boundary_ambiguous"), (1, 0, "boundary_ambiguous"), (0, 1, "boundary_ambiguous"))
        weights = normalize_q16_weights(len(offsets))
        delta = -1 if direction == "coverage_up" else 1 if direction == "coverage_down" else 0
        return tuple(sorted((CompileKernelEntry(delta, dq, dr, weight, "coverage_template", (flag,)) for (dq, dr, flag), weight in zip(offsets, weights)), key=lambda item: (item.layer_delta, item.dq, item.dr, item.kernel_type, item.flags)))
