from __future__ import annotations

from math import log
from typing import Mapping, Sequence

from nollm.geometry import Coverage, HexAddress, coverage_map
from nollm.geometry_profiles import (
    GeometryProfile,
    canonical_geometry_profiles,
    get_geometry_profile,
    layer_spec_from_profile,
)

SCHEMA = "nollm.multi_step_coverage.v1"
STATUS = "experimental_internal_only"
SOURCE = HexAddress(0, 0, 0)
TOLERANCE = 1e-9


def multi_step_coverage_report(profile_id: str, max_step: int = 8) -> dict[str, object]:
    _require_positive_step(max_step, "max_step")
    profile = get_geometry_profile(profile_id)
    return _profile_report(profile, max_step)


def multi_profile_coverage_report(
    profile_ids: Sequence[str] | None = None,
    max_step: int = 8,
) -> dict[str, object]:
    _require_positive_step(max_step, "max_step")
    selected = (
        canonical_geometry_profiles()
        if profile_ids is None
        else tuple(get_geometry_profile(profile_id) for profile_id in profile_ids)
    )
    profiles = [_profile_report(profile, max_step) for profile in selected]
    report = {
        "schema": SCHEMA,
        "status": STATUS,
        "profiles": profiles,
    }
    validate_multi_profile_coverage_report(report)
    return report


def coverage_support(profile_id: str, step: int) -> list[dict[str, object]]:
    _require_positive_step(step, "step")
    profile = get_geometry_profile(profile_id)
    rows = _coverage_rows(profile, step)
    return [_coverage_record(row) for row in rows]


def validate_multi_profile_coverage_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("coverage report must be a mapping")
    for key in ("schema", "status", "profiles"):
        if key not in report:
            raise ValueError(f"missing coverage report field: {key}")
    if report["schema"] != SCHEMA:
        raise ValueError("unsupported coverage report schema")
    if report["status"] != STATUS:
        raise ValueError("coverage report status must be experimental_internal_only")
    profiles = report["profiles"]
    if not isinstance(profiles, list):
        raise ValueError("profiles must be a list")
    if not _is_json_primitive(report):
        raise ValueError("coverage report must be JSON-primitive serializable")


def _profile_report(profile: GeometryProfile, max_step: int) -> dict[str, object]:
    steps = [_step_metrics(profile, step) for step in range(1, max_step + 1)]
    return {
        "profile_id": profile.profile_id,
        "role": profile.role,
        "tiling_model": profile.tiling_model,
        "orientation": profile.orientation,
        "steps": steps,
    }


def _step_metrics(profile: GeometryProfile, step: int) -> dict[str, object]:
    rows = _coverage_rows(profile, step)
    shares = [row.source_share for row in rows]
    target_shares = [row.target_share for row in rows]
    source_share_sum = sum(shares)
    squared_sum = sum(value * value for value in shares)
    entropy = -sum(value * log(value) for value in shares if value > 0)
    layer = layer_spec_from_profile(profile, step)
    return {
        "profile_id": profile.profile_id,
        "step": step,
        "beta": profile.beta,
        "theta_deg": profile.theta_deg,
        "scale_ratio": layer.side_length,
        "rotation_deg": layer.rotation_deg,
        "coverage_count": len(rows),
        "source_share_sum": source_share_sum,
        "participation_ratio": 1.0 / squared_sum if squared_sum > 0 else 0.0,
        "entropy": entropy,
        "exact_containment_count": sum(1 for value in target_shares if _almost_equal(value, 1.0)),
        "boundary_ambiguity_count": sum(1 for value in target_shares if value > TOLERANCE and value < 1.0 - TOLERANCE),
        "coverage": [_coverage_record(row) for row in rows],
    }


def _coverage_rows(profile: GeometryProfile, step: int) -> list[Coverage]:
    source_layer = layer_spec_from_profile(profile, 0)
    target_layer = layer_spec_from_profile(profile, step)
    search_radius = max(2, int(profile.beta**step) + 3)
    return sorted(
        coverage_map(SOURCE, source_layer, target_layer, search_radius=search_radius),
        key=lambda row: (row.target.q, row.target.r),
    )


def _coverage_record(row: Coverage) -> dict[str, object]:
    return {
        "q": row.target.q,
        "r": row.target.r,
        "source_share": row.source_share,
        "target_share": row.target_share,
    }


def _require_positive_step(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{label} must be a positive integer")


def _almost_equal(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE


def _is_json_primitive(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_primitive(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_primitive(item) for key, item in value.items())
    return False


__all__ = [
    "SCHEMA",
    "STATUS",
    "coverage_support",
    "multi_step_coverage_report",
    "multi_profile_coverage_report",
    "validate_multi_profile_coverage_report",
]
