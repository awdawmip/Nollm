from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Literal, Mapping

from nollm.geometry import LayerSpec, Orientation, Point

ProfileRole = Literal["default", "secondary", "benchmark"]
TilingModel = Literal["T", "O"]


@dataclass(frozen=True)
class GeometryProfile:
    profile_id: str
    beta: float
    theta_deg: float
    role: ProfileRole
    tiling_model: TilingModel = "T"
    orientation: Orientation = "pointy"
    description: str = ""

    def __post_init__(self) -> None:
        _require_non_empty_string(self.profile_id, "profile_id")
        _require_positive_finite_number(self.beta, "beta")
        _require_non_negative_finite_number(self.theta_deg, "theta_deg")
        if self.role not in ("default", "secondary", "benchmark"):
            raise ValueError("role must be default, secondary, or benchmark")
        if self.tiling_model not in ("T", "O"):
            raise ValueError("tiling_model must be T or O")
        if self.orientation not in ("pointy", "flat"):
            raise ValueError("orientation must be pointy or flat")
        _require_non_empty_string(self.description, "description")


def canonical_geometry_profiles() -> tuple[GeometryProfile, ...]:
    return (
        GeometryProfile(
            profile_id="default_dream",
            beta=2 ** 0.25,
            theta_deg=22.5,
            role="default",
            tiling_model="T",
            orientation="pointy",
            description="B default dream-field profile; slow densification; delays finite-depth recurrence",
        ),
        GeometryProfile(
            profile_id="medium_practical",
            beta=sqrt(2),
            theta_deg=15.0,
            role="secondary",
            tiling_model="T",
            orientation="pointy",
            description="A secondary practical comparison profile; better one-step spread and offset robustness",
        ),
        GeometryProfile(
            profile_id="benchmark_aligned",
            beta=2.0,
            theta_deg=0.0,
            role="benchmark",
            tiling_model="T",
            orientation="pointy",
            description="aligned reverse-cover / hidden-tree benchmark; not a default",
        ),
        GeometryProfile(
            profile_id="benchmark_single_step",
            beta=2.0,
            theta_deg=15.0,
            role="benchmark",
            tiling_model="T",
            orientation="pointy",
            description="single-step anti-tree benchmark; not a default",
        ),
        GeometryProfile(
            profile_id="benchmark_eisenstein",
            beta=sqrt(3),
            theta_deg=30.0,
            role="benchmark",
            tiling_model="T",
            orientation="pointy",
            description="hex/Eisenstein benchmark; not a default",
        ),
    )


def geometry_profile_registry() -> dict[str, GeometryProfile]:
    profiles = canonical_geometry_profiles()
    registry: dict[str, GeometryProfile] = {}
    for profile in profiles:
        if profile.profile_id in registry:
            raise ValueError(f"duplicate geometry profile id: {profile.profile_id}")
        registry[profile.profile_id] = profile
    return registry


def get_geometry_profile(profile_id: str) -> GeometryProfile:
    _require_non_empty_string(profile_id, "profile_id")
    try:
        return geometry_profile_registry()[profile_id]
    except KeyError as exc:
        raise ValueError(f"unknown geometry profile: {profile_id}") from exc


def default_geometry_profile() -> GeometryProfile:
    profile = get_geometry_profile("default_dream")
    if profile.role != "default":
        raise ValueError("default_dream profile must have role=default")
    return profile


def geometry_profile_to_record(profile: GeometryProfile) -> dict[str, object]:
    if not isinstance(profile, GeometryProfile):
        raise ValueError("profile must be a GeometryProfile")
    return {
        "profile_id": profile.profile_id,
        "beta": profile.beta,
        "theta_deg": profile.theta_deg,
        "role": profile.role,
        "tiling_model": profile.tiling_model,
        "orientation": profile.orientation,
        "description": profile.description,
    }


def geometry_profile_from_record(record: Mapping[str, object]) -> GeometryProfile:
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    return GeometryProfile(
        profile_id=_record_string(record, "profile_id"),
        beta=_record_number(record, "beta"),
        theta_deg=_record_non_negative_number(record, "theta_deg"),
        role=_record_string(record, "role"),  # type: ignore[arg-type]
        tiling_model=_record_string(record, "tiling_model"),  # type: ignore[arg-type]
        orientation=_record_string(record, "orientation"),  # type: ignore[arg-type]
        description=_record_string(record, "description"),
    )


def layer_spec_from_profile(
    profile: GeometryProfile,
    layer: int,
    *,
    s0: float = 1.0,
    origin: Point = (0.0, 0.0),
    translation: Point = (0.0, 0.0),
) -> LayerSpec:
    if not isinstance(profile, GeometryProfile):
        raise ValueError("profile must be a GeometryProfile")
    if profile.tiling_model != "T":
        raise ValueError("LayerSpec can only be created for strict true tiling Model T profiles")
    return LayerSpec(
        layer=layer,
        s0=s0,
        beta=profile.beta,
        theta_deg=profile.theta_deg,
        origin=origin,
        translation=translation,
        orientation=profile.orientation,
    )


def _require_non_empty_string(value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _require_positive_finite_number(value: object, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a positive finite number")


def _require_non_negative_finite_number(value: object, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a non-negative finite number")


def _record_string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _record_number(record: Mapping[str, object], key: str) -> float:
    value = record.get(key)
    _require_positive_finite_number(value, key)
    return float(value)


def _record_non_negative_number(record: Mapping[str, object], key: str) -> float:
    value = record.get(key)
    _require_non_negative_finite_number(value, key)
    return float(value)


__all__ = [
    "GeometryProfile",
    "ProfileRole",
    "TilingModel",
    "canonical_geometry_profiles",
    "geometry_profile_registry",
    "get_geometry_profile",
    "default_geometry_profile",
    "geometry_profile_to_record",
    "geometry_profile_from_record",
    "layer_spec_from_profile",
]
