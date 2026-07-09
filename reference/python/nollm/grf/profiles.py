"""GRF profile registry."""

from __future__ import annotations

from dataclasses import dataclass

from .fixed_point import WEIGHT_FORMAT


@dataclass(frozen=True, order=True)
class Profile:
    profile_id: str
    role: str
    coordinate_model: str
    scale_model: str
    rotation_model: str
    weight_format: str
    runtime_polygon: bool
    runtime_float_allowed: bool
    description: str


_PROFILES: dict[str, Profile] = {
    "eisenstein_exact_v1": Profile(
        "eisenstein_exact_v1",
        "production_candidate",
        "integer_axial_cube",
        "eisenstein_integer_norm",
        "eisenstein_integer_matrix",
        WEIGHT_FORMAT,
        False,
        False,
        "Performance main candidate for exact integer template lookup.",
    ),
    "aligned_baseline_v1": Profile(
        "aligned_baseline_v1",
        "baseline",
        "integer_axial_cube",
        "unit_layer",
        "aligned_identity",
        WEIGHT_FORMAT,
        False,
        False,
        "Control profile for aligned integer coverage templates.",
    ),
    "dream_quasi_v1": Profile(
        "dream_quasi_v1",
        "research",
        "integer_axial_cube",
        "symbolic_quasi",
        "symbolic_phase",
        WEIGHT_FORMAT,
        False,
        False,
        "Research profile with explicit residual and boundary ambiguity.",
    ),
}


def profiles() -> tuple[Profile, ...]:
    return tuple(_PROFILES[key] for key in sorted(_PROFILES))


def get_profile(profile_id: str) -> Profile:
    try:
        return _PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError("unknown profile_id") from exc


def performance_profile() -> Profile:
    return get_profile("eisenstein_exact_v1")
