from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from .fixed_point import WEIGHT_FORMAT

PROFILE_REGISTRY_VERSION = "nollm_geometry_profiles_v4"
DEFAULT_PROFILE_ID = "default_dream_v1"
GEOMETRY_CONTRACT_VERSION = "nollm_translation_covariant_physical_coverage_v1"
LEGACY_ROTATED_TEMPLATE_CONTRACT_VERSION = "nollm_rotated_physical_field_v1"


@dataclass(frozen=True, order=True)
class RuntimeProfile:
    profile_id: str
    coordinate_model: str
    weight_format: str
    runtime_polygon: bool
    runtime_float_allowed: bool
    geometry_contract_version: str
    theta_step_turn_numerator: int
    theta_step_turn_denominator: int
    beta_algebraic: str
    orientation: str
    increasing_layer_direction: str
    phase_period: int

    def __post_init__(self) -> None:
        for name in (
            "profile_id", "coordinate_model", "weight_format",
            "geometry_contract_version", "beta_algebraic", "orientation",
            "increasing_layer_direction",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise TypeError(f"{name} must be a non-empty string")
        if type(self.runtime_polygon) is not bool or type(self.runtime_float_allowed) is not bool:
            raise TypeError("runtime flags must be booleans")
        for name in ("theta_step_turn_numerator", "theta_step_turn_denominator", "phase_period"):
            if type(getattr(self, name)) is not int:
                raise TypeError(f"{name} must be an integer")
        if self.theta_step_turn_denominator <= 0 or self.phase_period <= 0:
            raise ValueError("profile periods must be positive")

    def orientation_turn(self, physical_layer: int) -> tuple[int, int]:
        if type(physical_layer) is not int:
            raise TypeError("physical_layer must be an integer")
        if self.profile_id == DEFAULT_PROFILE_ID:
            # 7.5-degree units over one turn; modulo eight units is hexagonal 60-degree symmetry.
            return (physical_layer * 3) % 8, 48
        return 0, 1


def _legacy(profile_id: str) -> RuntimeProfile:
    return RuntimeProfile(
        profile_id, "integer_axial_cube", WEIGHT_FORMAT, False, False,
        "nollm_legacy_geometry_v2", 0, 1, "legacy", "pointy_top",
        "finer_with_increasing_index", 1,
    )


_RUNTIME_PROFILES = {
    "aligned_baseline_v1": _legacy("aligned_baseline_v1"),
    DEFAULT_PROFILE_ID: RuntimeProfile(
        DEFAULT_PROFILE_ID,
        "integer_axial_with_decimal_physical_overlap",
        WEIGHT_FORMAT,
        True,
        False,
        GEOMETRY_CONTRACT_VERSION,
        1,
        16,
        "beta=positive_root(x^4-2)",
        "pointy_top",
        "finer_with_increasing_index",
        8,
    ),
    "dream_quasi_v1": _legacy("dream_quasi_v1"),
    "eisenstein_exact_v1": _legacy("eisenstein_exact_v1"),
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
    payload = json.dumps(
        [asdict(_RUNTIME_PROFILES[key]) for key in sorted(_RUNTIME_PROFILES)],
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return sha256(payload).hexdigest()
