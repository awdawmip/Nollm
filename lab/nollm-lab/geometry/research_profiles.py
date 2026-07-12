from __future__ import annotations

from dataclasses import dataclass

from compile_support import WEIGHT_FORMAT


@dataclass(frozen=True, order=True)
class ResearchProfile:
    profile_id: str
    role: str
    coordinate_model: str
    scale_model: str
    rotation_model: str
    weight_format: str
    runtime_polygon: bool
    runtime_float_allowed: bool
    description: str


_PROFILES = {
    "eisenstein_exact_v1": ResearchProfile("eisenstein_exact_v1", "production_candidate", "integer_axial_cube", "eisenstein_integer_norm", "eisenstein_integer_matrix", WEIGHT_FORMAT, False, False, "Performance main candidate for exact integer template lookup."),
    "aligned_baseline_v1": ResearchProfile("aligned_baseline_v1", "baseline", "integer_axial_cube", "unit_layer", "aligned_identity", WEIGHT_FORMAT, False, False, "Control profile for aligned integer coverage templates."),
    "dream_quasi_v1": ResearchProfile("dream_quasi_v1", "research", "integer_axial_cube", "symbolic_quasi", "symbolic_phase", WEIGHT_FORMAT, False, False, "Research profile with explicit residual and boundary ambiguity."),
}


def research_profiles() -> tuple[ResearchProfile, ...]:
    return tuple(_PROFILES[key] for key in sorted(_PROFILES))


def research_profile(profile_id: str) -> ResearchProfile:
    try:
        return _PROFILES[profile_id]
    except KeyError as error:
        raise ValueError("unknown profile_id") from error
