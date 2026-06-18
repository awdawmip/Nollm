from __future__ import annotations

from dataclasses import dataclass
from math import log
from random import Random
from typing import Mapping, Sequence

from nollm.geometry import (
    Axial,
    Coverage,
    HexAddress,
    Point,
    axial_to_local_xy,
    coverage_map,
    rotate_point,
)
from nollm.geometry_profiles import (
    GeometryProfile,
    get_geometry_profile,
    layer_spec_from_profile,
)

SCHEMA = "nollm.offset_sampling.v1"
STATUS = "experimental_internal_only"
DEFAULT_SEED = 20260616
DEFAULT_RANDOM_COUNT = 32
DEFAULT_PROFILE_IDS = ("default_dream", "medium_practical")
SOURCE = HexAddress(0, 0, 0)
TOLERANCE = 1e-9
FORBIDDEN_REPORT_KEYS = {
    "parent",
    "children",
    "folder",
    "owner",
    "belongs_to",
}


@dataclass(frozen=True)
class OffsetSample:
    sample_id: str
    u: float
    v: float

    def __post_init__(self) -> None:
        if not isinstance(self.sample_id, str) or not self.sample_id:
            raise ValueError("sample_id must be a non-empty string")
        _require_finite_number(self.u, "u")
        _require_finite_number(self.v, "v")


def deterministic_offset_samples() -> tuple[OffsetSample, ...]:
    return (
        OffsetSample("center", 0.0, 0.0),
        OffsetSample("q_quarter", 0.25, 0.0),
        OffsetSample("q_half", 0.5, 0.0),
        OffsetSample("r_quarter", 0.0, 0.25),
        OffsetSample("r_half", 0.0, 0.5),
        OffsetSample("diagonal_quarter", 0.25, 0.25),
        OffsetSample("diagonal_half", 0.5, 0.5),
        OffsetSample("neg_diag_quarter", -0.25, -0.25),
        OffsetSample("mixed_quarter", 0.25, -0.25),
    )


def seeded_random_offset_samples(
    *,
    seed: int = DEFAULT_SEED,
    sample_count: int = DEFAULT_RANDOM_COUNT,
) -> tuple[OffsetSample, ...]:
    _require_non_negative_int(sample_count, "sample_count")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    random = Random(seed)
    return tuple(
        OffsetSample(
            f"random_{index:03d}",
            random.uniform(-0.5, 0.5),
            random.uniform(-0.5, 0.5),
        )
        for index in range(sample_count)
    )


def offset_samples(
    *,
    seed: int = DEFAULT_SEED,
    random_count: int = DEFAULT_RANDOM_COUNT,
) -> tuple[OffsetSample, ...]:
    return deterministic_offset_samples() + seeded_random_offset_samples(
        seed=seed,
        sample_count=random_count,
    )


def offset_world_translation(profile: GeometryProfile, step: int, sample: OffsetSample) -> Point:
    _require_model_t(profile)
    _require_positive_int(step, "step")
    if not isinstance(sample, OffsetSample):
        raise ValueError("sample must be an OffsetSample")
    target_layer = layer_spec_from_profile(profile, step)
    q_basis = rotate_point(axial_to_local_xy(Axial(1, 0), target_layer.side_length, target_layer.orientation), target_layer.rotation_rad)
    r_basis = rotate_point(axial_to_local_xy(Axial(0, 1), target_layer.side_length, target_layer.orientation), target_layer.rotation_rad)
    return (
        sample.u * q_basis[0] + sample.v * r_basis[0],
        sample.u * q_basis[1] + sample.v * r_basis[1],
    )


def offset_sampling_report(
    profile_ids: Sequence[str] | None = None,
    *,
    max_step: int = 8,
    seed: int = DEFAULT_SEED,
    random_count: int = DEFAULT_RANDOM_COUNT,
) -> dict[str, object]:
    _require_positive_int(max_step, "max_step")
    samples = offset_samples(seed=seed, random_count=random_count)
    selected = DEFAULT_PROFILE_IDS if profile_ids is None else tuple(profile_ids)
    profiles = [_profile_report(get_geometry_profile(profile_id), max_step, samples) for profile_id in selected]
    report: dict[str, object] = {
        "schema": SCHEMA,
        "status": STATUS,
        "seed": seed,
        "random_count": random_count,
        "profiles": profiles,
        "comparison": _comparison(profiles),
    }
    validate_offset_sampling_report(report)
    return report


def validate_offset_sampling_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("offset sampling report must be a mapping")
    for key in ("schema", "status", "profiles", "comparison"):
        if key not in report:
            raise ValueError(f"missing offset sampling report field: {key}")
    if report["schema"] != SCHEMA:
        raise ValueError("unsupported offset sampling report schema")
    if report["status"] != STATUS:
        raise ValueError("offset sampling report status must be experimental_internal_only")
    if not isinstance(report["profiles"], list):
        raise ValueError("profiles must be a list")
    _reject_forbidden_keys(report)
    if not _is_json_primitive(report):
        raise ValueError("offset sampling report must be JSON-primitive serializable")


def _profile_report(
    profile: GeometryProfile,
    max_step: int,
    samples: Sequence[OffsetSample],
) -> dict[str, object]:
    _require_model_t(profile)
    return {
        "profile_id": profile.profile_id,
        "role": profile.role,
        "tiling_model": profile.tiling_model,
        "orientation": profile.orientation,
        "steps": [_step_report(profile, step, samples) for step in range(1, max_step + 1)],
    }


def _step_report(
    profile: GeometryProfile,
    step: int,
    samples: Sequence[OffsetSample],
) -> dict[str, object]:
    sample_metrics = [_sample_metrics(profile, step, sample) for sample in samples]
    return {
        "step": step,
        "sample_count": len(sample_metrics),
        "aggregates": _aggregates(sample_metrics),
        "samples": sample_metrics,
    }


def _sample_metrics(profile: GeometryProfile, step: int, sample: OffsetSample) -> dict[str, object]:
    rows = _coverage_rows(profile, step, sample)
    shares = [row.source_share for row in rows]
    target_shares = [row.target_share for row in rows]
    squared_sum = sum(value * value for value in shares)
    source_share_sum = sum(shares)
    return {
        "profile_id": profile.profile_id,
        "step": step,
        "sample_id": sample.sample_id,
        "u": sample.u,
        "v": sample.v,
        "coverage_count": len(rows),
        "source_share_sum": source_share_sum,
        "participation_ratio": 1.0 / squared_sum if squared_sum > 0 else 0.0,
        "entropy": -sum(value * log(value) for value in shares if value > 0),
        "exact_containment_count": sum(1 for value in target_shares if _almost_equal(value, 1.0)),
        "boundary_ambiguity_count": sum(1 for value in target_shares if value > TOLERANCE and value < 1.0 - TOLERANCE),
    }


def _coverage_rows(profile: GeometryProfile, step: int, sample: OffsetSample) -> list[Coverage]:
    source_layer = layer_spec_from_profile(profile, 0)
    target_layer = layer_spec_from_profile(
        profile,
        step,
        translation=offset_world_translation(profile, step, sample),
    )
    search_radius = max(2, int(profile.beta**step) + 4)
    return sorted(
        coverage_map(SOURCE, source_layer, target_layer, search_radius=search_radius),
        key=lambda row: (row.target.q, row.target.r),
    )


def _aggregates(samples: Sequence[Mapping[str, object]]) -> dict[str, object]:
    coverage_counts = [float(row["coverage_count"]) for row in samples]
    participation_ratios = [float(row["participation_ratio"]) for row in samples]
    entropies = [float(row["entropy"]) for row in samples]
    exact_counts = [float(row["exact_containment_count"]) for row in samples]
    source_sums = [float(row["source_share_sum"]) for row in samples]
    return {
        "coverage_count_mean": _mean(coverage_counts),
        "coverage_count_variance": _population_variance(coverage_counts),
        "participation_ratio_mean": _mean(participation_ratios),
        "participation_ratio_variance": _population_variance(participation_ratios),
        "entropy_mean": _mean(entropies),
        "entropy_variance": _population_variance(entropies),
        "exact_containment_count_mean": _mean(exact_counts),
        "exact_containment_count_variance": _population_variance(exact_counts),
        "source_share_sum_min": min(source_sums) if source_sums else 0.0,
        "source_share_sum_max": max(source_sums) if source_sums else 0.0,
    }


def _comparison(profiles: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_id = {str(profile["profile_id"]): profile for profile in profiles}
    if "default_dream" not in by_id or "medium_practical" not in by_id:
        return {}
    default_steps = by_id["default_dream"]["steps"]  # type: ignore[index]
    medium_steps = by_id["medium_practical"]["steps"]  # type: ignore[index]
    notes: list[str] = []
    if isinstance(default_steps, list) and isinstance(medium_steps, list):
        for default_step, medium_step in zip(default_steps, medium_steps):
            default_var = float(default_step["aggregates"]["participation_ratio_variance"])  # type: ignore[index]
            medium_var = float(medium_step["aggregates"]["participation_ratio_variance"])  # type: ignore[index]
            if medium_var < default_var:
                relation = "medium_practical_lower"
            elif medium_var > default_var:
                relation = "default_dream_lower"
            else:
                relation = "equal"
            notes.append(f"step_{default_step['step']}:{relation}")
    return {
        "default_dream_vs_medium_practical": {
            "metric": "participation_ratio_variance",
            "notes": notes,
        }
    }


def _require_model_t(profile: GeometryProfile) -> None:
    if not isinstance(profile, GeometryProfile):
        raise ValueError("profile must be a GeometryProfile")
    if profile.tiling_model != "T":
        raise ValueError("G4 offset sampling supports strict true tiling Model T only")


def _require_positive_int(value: object, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{label} must be a positive integer")


def _require_non_negative_int(value: object, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def _require_finite_number(value: object, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError(f"{label} must be a finite number")


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _population_variance(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = _mean(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def _almost_equal(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE


def _reject_forbidden_keys(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in FORBIDDEN_REPORT_KEYS:
                raise ValueError(f"forbidden offset sampling report key: {key}")
            _reject_forbidden_keys(item)
    elif isinstance(value, list):
        for item in value:
            _reject_forbidden_keys(item)


def _is_json_primitive(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_primitive(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_primitive(item) for key, item in value.items())
    return False


__all__ = [
    "DEFAULT_PROFILE_IDS",
    "DEFAULT_RANDOM_COUNT",
    "DEFAULT_SEED",
    "OffsetSample",
    "SCHEMA",
    "STATUS",
    "deterministic_offset_samples",
    "offset_samples",
    "offset_sampling_report",
    "offset_world_translation",
    "seeded_random_offset_samples",
    "validate_offset_sampling_report",
]
