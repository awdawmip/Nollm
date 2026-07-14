from __future__ import annotations

from decimal import Decimal

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
from physical_geometry import axial_transform_q32, canonical_overlap, decimal_text, q16
from research_profiles import research_profile


GEOMETRY_CONTRACT_VERSION = "nollm_rotated_physical_field_v1"


class CoverageTemplateCompiler:
    """Lab-owned compiler for immutable Core runtime geometry artifacts."""

    def __init__(self, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> None:
        if type(fanout_limit) is not int or fanout_limit <= 0:
            raise ValueError("fanout_limit must be positive")
        self.fanout_limit = fanout_limit

    def compile(self, profile_id: str, direction: str, from_layer_mod: int = 0, source_phase: str | None = None) -> CompileTemplate:
        profile = research_profile(profile_id)
        if direction not in DIRECTIONS or type(from_layer_mod) is not int:
            raise ValueError("invalid coverage request")
        if profile_id == "default_dream_v1" and not 0 <= from_layer_mod < 8:
            raise ValueError("default_dream_v1 requires phase 0 through 7")
        if profile_id != "default_dream_v1" and from_layer_mod != 0:
            raise ValueError("legacy profiles only provide phase 0")
        entries = self._entries(profile_id, direction, from_layer_mod)
        if len(entries) > self.fanout_limit:
            raise ValueError("template fanout exceeds hard bound")
        flags = tuple(sorted({flag for entry in entries for flag in entry.flags}))
        total = sum(entry.weight_q16 for entry in entries)
        method = "decimal_interval_rotated_hex_envelope_v1" if profile_id == "default_dream_v1" else "symbolic_research_template_with_residual" if profile_id == "dream_quasi_v1" else "integer_template_lookup"
        metadata = CompileMetadata(
            "grf1a_coverage_template_compiler",
            method,
            profile.weight_format,
            self.fanout_limit,
            LAYER_INDEX_DIRECTION,
            flags,
            GEOMETRY_CONTRACT_VERSION if profile_id == "default_dream_v1" else "nollm_legacy_geometry_v2",
            "nollm_lab_rotated_hex_compiler_v2",
        )
        delta = -1 if direction == "coverage_up" else 1 if direction == "coverage_down" else 0
        approximation = max((entry.certification_residual_q16 for entry in entries), default=0)
        if profile_id == "dream_quasi_v1":
            approximation = Q16_ONE // 16
        relation = "same_layer" if direction == "lateral" else "source_side/target_side=beta^-1" if direction == "coverage_up" else "source_side/target_side=beta"
        certification = "decimal72_canonical_overlap_plus_conservative_nearest_cell_envelope" if profile_id == "default_dream_v1" else "legacy_template"
        return CompileTemplate(
            profile_id, direction, from_layer_mod, from_layer_mod + delta,
            source_phase, entries, total, Q16_ONE - total, approximation,
            metadata, axial_transform_q32(direction) if profile_id == "default_dream_v1" else (1 << 32, 0, 0, 1 << 32),
            relation, certification,
        )

    def _entries(self, profile_id: str, direction: str, from_layer_mod: int) -> tuple[CompileKernelEntry, ...]:
        if profile_id == "default_dream_v1":
            return self._physical_entries(direction, from_layer_mod)
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
        return tuple(sorted((CompileKernelEntry(delta, dq, dr, weight, "coverage_template", (flag,), "0", "0", 0, 0, 0) for (dq, dr, flag), weight in zip(offsets, weights)), key=lambda item: (item.layer_delta, item.dq, item.dr, item.kernel_type, item.flags)))

    def _physical_entries(self, direction: str, phase: int) -> tuple[CompileKernelEntry, ...]:
        delta = -1 if direction == "coverage_up" else 1 if direction == "coverage_down" else 0
        offsets = hex_ring_one() if direction == "lateral" else ((0, 0), *hex_ring_one())
        samples = tuple(canonical_overlap(phase, direction, dq, dr) for dq, dr in offsets) if direction != "lateral" else ()
        if direction == "lateral":
            weights = normalize_q16_weights(len(offsets))
        else:
            mutable = [max(1, q16(sample[1])) for sample in samples]
            mutable[max(range(len(mutable)), key=mutable.__getitem__)] += Q16_ONE - sum(mutable)
            weights = tuple(mutable)
        output = []
        for index, ((dq, dr), weight) in enumerate(zip(offsets, weights)):
            if direction == "lateral":
                output.append(CompileKernelEntry(delta, dq, dr, weight, "coverage_template", ("lateral_neighbor", "world_transform_certified"), "0", "0", 0, 0, 0))
                continue
            area, source_share, target_share = samples[index]
            sample_share = q16(source_share)
            residual = abs(weight - sample_share)
            flags = ("boundary_ambiguous", "certified_candidate_envelope", "phase_origin_sample")
            upper = max(area, Decimal("0")) + Decimal("1e-48")
            output.append(CompileKernelEntry(delta, dq, dr, weight, "coverage_template", flags, "0", decimal_text(upper), sample_share, q16(target_share), residual))
        return tuple(sorted(output))
