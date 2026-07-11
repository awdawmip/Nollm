from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .fixed_point import WEIGHT_FORMAT

PROFILE_REGISTRY_VERSION = "nollm_geometry_profiles_v2"


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

    def __post_init__(self) -> None:
        for name in ("profile_id", "role", "coordinate_model", "scale_model", "rotation_model", "weight_format", "description"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise TypeError(f"{name} must be a non-empty string")
        if type(self.runtime_polygon) is not bool or type(self.runtime_float_allowed) is not bool:
            raise TypeError("runtime flags must be booleans")

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


_PROFILES = {
    "eisenstein_exact_v1": Profile("eisenstein_exact_v1", "production_candidate", "integer_axial_cube", "eisenstein_integer_norm", "eisenstein_integer_matrix", WEIGHT_FORMAT, False, False, "Performance main candidate for exact integer template lookup."),
    "aligned_baseline_v1": Profile("aligned_baseline_v1", "baseline", "integer_axial_cube", "unit_layer", "aligned_identity", WEIGHT_FORMAT, False, False, "Control profile for aligned integer coverage templates."),
    "dream_quasi_v1": Profile("dream_quasi_v1", "research", "integer_axial_cube", "symbolic_quasi", "symbolic_phase", WEIGHT_FORMAT, False, False, "Research profile with explicit residual and boundary ambiguity."),
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


def profile_registry_digest() -> str:
    payload = json.dumps([profile.to_mapping() for profile in profiles()], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(payload).hexdigest()
