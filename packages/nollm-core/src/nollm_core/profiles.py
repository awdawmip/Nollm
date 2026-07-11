from __future__ import annotations

from dataclasses import dataclass


PROFILE_REGISTRY_VERSION = "nollm_geometry_profiles_v1"


@dataclass(frozen=True, order=True)
class Profile:
    profile_id: str
    role: str


_PROFILES = {
    "aligned_baseline_v1": Profile("aligned_baseline_v1", "baseline"),
    "dream_quasi_v1": Profile("dream_quasi_v1", "research"),
    "eisenstein_exact_v1": Profile("eisenstein_exact_v1", "production_candidate"),
}


def profiles() -> tuple[Profile, ...]:
    return tuple(_PROFILES[key] for key in sorted(_PROFILES))


def get_profile(profile_id: object) -> Profile:
    if type(profile_id) is not str:
        raise TypeError("profile_id must be a string")
    try:
        return _PROFILES[profile_id]
    except KeyError as error:
        raise ValueError("unknown profile_id") from error
