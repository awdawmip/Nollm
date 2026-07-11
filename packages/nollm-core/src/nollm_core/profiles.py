from __future__ import annotations

from dataclasses import dataclass

from .fixed_point import WEIGHT_FORMAT

PROFILE_REGISTRY_VERSION = "nollm_geometry_profiles_v2"

# Compatibility identity of the accepted v2 generated profile artifact. Research
# metadata that originally produced it is owned by Lab, not the Core runtime.
PROFILE_REGISTRY_ID = "c4238c61ddbde3c1ba6006fc7ac6a6849f9574f0230aef6ba8beabcd3b6dec43"


@dataclass(frozen=True, order=True)
class RuntimeProfile:
    profile_id: str
    coordinate_model: str
    weight_format: str
    runtime_polygon: bool
    runtime_float_allowed: bool

    def __post_init__(self) -> None:
        for name in ("profile_id", "coordinate_model", "weight_format"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise TypeError(f"{name} must be a non-empty string")
        if type(self.runtime_polygon) is not bool or type(self.runtime_float_allowed) is not bool:
            raise TypeError("runtime flags must be booleans")


_RUNTIME_PROFILES = {
    profile_id: RuntimeProfile(profile_id, "integer_axial_cube", WEIGHT_FORMAT, False, False)
    for profile_id in (
        "aligned_baseline_v1",
        "dream_quasi_v1",
        "eisenstein_exact_v1",
    )
}


def available_profile_ids() -> tuple[str, ...]:
    return tuple(sorted(_RUNTIME_PROFILES))


def runtime_profile(profile_id: object) -> RuntimeProfile:
    if type(profile_id) is not str:
        raise TypeError("profile_id must be a string")
    try:
        return _RUNTIME_PROFILES[profile_id]
    except KeyError as error:
        raise ValueError("unknown profile_id") from error


def profile_registry_digest() -> str:
    return PROFILE_REGISTRY_ID
