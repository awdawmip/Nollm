from __future__ import annotations

from dataclasses import dataclass
from math import ceil, inf, isfinite
from typing import Mapping, Sequence

from nollm.geometry import (
    Axial,
    HexAddress,
    axial_disk,
    axial_to_world,
    hex_overlap,
    world_to_axial,
)
from nollm.geometry_profiles import GeometryProfile, get_geometry_profile, layer_spec_from_profile

SCHEMA = "nollm.reverse_cover.v1"
STATUS = "experimental_internal_only"
DEFAULT_PROFILE_IDS = ("default_dream", "medium_practical")
DEFAULT_CASE_STEPS = (1, 2, 4, 8)
DEFAULT_TARGET_RADIUS = 1
SOURCE_LAYER = 0
TOLERANCE = 1e-9
SOLVER_NAME = "scipy.optimize.milp/HiGHS"
FORBIDDEN_REPORT_KEYS = {
    "parent",
    "children",
    "folder",
    "owner",
    "belongs_to",
}


@dataclass(frozen=True)
class ReverseCoverCase:
    step: int
    target_radius: int = DEFAULT_TARGET_RADIUS

    def __post_init__(self) -> None:
        _require_positive_int(self.step, "step")
        _require_non_negative_int(self.target_radius, "target_radius")

    @property
    def case_id(self) -> str:
        return f"center_ring_{self.target_radius}_step_{self.step}"


@dataclass(frozen=True)
class IncidenceProblem:
    profile: GeometryProfile
    case: ReverseCoverCase
    targets: tuple[HexAddress, ...]
    sources: tuple[HexAddress, ...]
    rows: tuple[tuple[int, ...], ...]


def default_reverse_cover_cases() -> tuple[ReverseCoverCase, ...]:
    return tuple(ReverseCoverCase(step=step, target_radius=DEFAULT_TARGET_RADIUS) for step in DEFAULT_CASE_STEPS)


def reverse_cover_report(
    profile_ids: Sequence[str] | None = None,
    cases: Sequence[ReverseCoverCase] | None = None,
    *,
    time_limit_seconds: float = 5.0,
) -> dict[str, object]:
    _require_positive_number(time_limit_seconds, "time_limit_seconds")
    selected_profiles = DEFAULT_PROFILE_IDS if profile_ids is None else tuple(profile_ids)
    selected_cases = default_reverse_cover_cases() if cases is None else tuple(cases)
    profiles = [
        _profile_report(get_geometry_profile(profile_id), selected_cases, time_limit_seconds)
        for profile_id in selected_profiles
    ]
    report: dict[str, object] = {
        "schema": SCHEMA,
        "status": STATUS,
        "profiles": profiles,
        "comparison": _comparison(profiles),
    }
    validate_reverse_cover_report(report)
    return report


def build_incidence_problem(profile: GeometryProfile, case: ReverseCoverCase) -> IncidenceProblem:
    _require_model_t(profile)
    if not isinstance(case, ReverseCoverCase):
        raise ValueError("case must be a ReverseCoverCase")
    target_layer = layer_spec_from_profile(profile, case.step)
    source_layer = layer_spec_from_profile(profile, SOURCE_LAYER)
    targets = tuple(
        HexAddress(case.step, cell.q, cell.r)
        for cell in sorted(axial_disk(Axial(0, 0), case.target_radius), key=lambda item: (item.q, item.r))
    )
    sources = _candidate_sources(profile, case, targets)
    rows: list[tuple[int, ...]] = []
    for target in targets:
        covered_by: list[int] = []
        for index, source in enumerate(sources):
            overlap = hex_overlap(source, source_layer, target, target_layer)
            if overlap.intersection_area > TOLERANCE:
                covered_by.append(index)
        rows.append(tuple(covered_by))
    return IncidenceProblem(profile=profile, case=case, targets=targets, sources=sources, rows=tuple(rows))


def greedy_reverse_cover(problem: IncidenceProblem) -> dict[str, object]:
    uncovered = set(range(len(problem.targets)))
    selected: list[int] = []
    source_order = sorted(range(len(problem.sources)), key=lambda index: (problem.sources[index].q, problem.sources[index].r))
    while uncovered:
        best_index: int | None = None
        best_gain = 0
        for source_index in source_order:
            gain = sum(1 for target_index in uncovered if source_index in problem.rows[target_index])
            if gain > best_gain:
                best_index = source_index
                best_gain = gain
        if best_index is None or best_gain <= 0:
            return {
                "status": "infeasible",
                "selected_count": len(selected),
                "selected_sources": [_address_record(problem.sources[index]) for index in selected],
            }
        selected.append(best_index)
        uncovered = {target_index for target_index in uncovered if best_index not in problem.rows[target_index]}
    return {
        "status": "feasible",
        "selected_count": len(selected),
        "selected_sources": [_address_record(problem.sources[index]) for index in selected],
    }


def solve_milp_reverse_cover(problem: IncidenceProblem, *, time_limit_seconds: float = 5.0) -> dict[str, object]:
    _require_positive_number(time_limit_seconds, "time_limit_seconds")
    try:
        from scipy.optimize import Bounds, LinearConstraint, milp  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return {
            "solver": SOLVER_NAME,
            "status": "UNAVAILABLE",
            "reason": "scipy.optimize.milp unavailable",
        }

    matrix = _dense_incidence_matrix(problem)
    constraints = LinearConstraint(matrix, lb=[1.0] * len(problem.targets), ub=[inf] * len(problem.targets))
    result = milp(
        c=[1.0] * len(problem.sources),
        integrality=[1] * len(problem.sources),
        bounds=Bounds(0, 1),
        constraints=constraints,
        options={"time_limit": time_limit_seconds},
    )
    status = normalize_solver_status(int(result.status))
    record: dict[str, object] = {"solver": SOLVER_NAME, "status": status}
    if status == "OPTIMAL":
        selected = _selected_indexes(result.x)
        record.update(
            {
                "objective": int(round(float(result.fun))),
                "selected_count": len(selected),
                "selected_sources": [_address_record(problem.sources[index]) for index in selected],
            }
        )
    elif status == "FEASIBLE_OR_LIMITED" and getattr(result, "x", None) is not None:
        selected = _selected_indexes(result.x)
        record["incumbent"] = {
            "objective": int(round(float(result.fun))) if isfinite(float(result.fun)) else None,
            "selected_count": len(selected),
            "selected_sources": [_address_record(problem.sources[index]) for index in selected],
        }
    return record


def solve_lp_lower_bound(problem: IncidenceProblem, *, time_limit_seconds: float = 5.0) -> dict[str, object]:
    _require_positive_number(time_limit_seconds, "time_limit_seconds")
    try:
        from scipy.optimize import Bounds, LinearConstraint, milp  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return {
            "solver": SOLVER_NAME,
            "status": "UNAVAILABLE",
            "reason": "scipy.optimize.milp unavailable",
        }

    matrix = _dense_incidence_matrix(problem)
    constraints = LinearConstraint(matrix, lb=[1.0] * len(problem.targets), ub=[inf] * len(problem.targets))
    result = milp(
        c=[1.0] * len(problem.sources),
        integrality=[0] * len(problem.sources),
        bounds=Bounds(0, 1),
        constraints=constraints,
        options={"time_limit": time_limit_seconds},
    )
    status = normalize_solver_status(int(result.status))
    record: dict[str, object] = {"solver": SOLVER_NAME, "status": status}
    if status == "OPTIMAL":
        record["objective"] = float(result.fun)
    return record


def normalize_solver_status(raw_status: int) -> str:
    if raw_status == 0:
        return "OPTIMAL"
    if raw_status == 1:
        return "FEASIBLE_OR_LIMITED"
    if raw_status == 2:
        return "INFEASIBLE"
    return "ERROR"


def validate_reverse_cover_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("reverse-cover report must be a mapping")
    for key in ("schema", "status", "profiles", "comparison"):
        if key not in report:
            raise ValueError(f"missing reverse-cover report field: {key}")
    if report["schema"] != SCHEMA:
        raise ValueError("unsupported reverse-cover report schema")
    if report["status"] != STATUS:
        raise ValueError("reverse-cover report status must be experimental_internal_only")
    if not isinstance(report["profiles"], list):
        raise ValueError("profiles must be a list")
    _reject_forbidden_keys(report)
    if not _is_json_primitive(report):
        raise ValueError("reverse-cover report must be JSON-primitive serializable")


def _profile_report(
    profile: GeometryProfile,
    cases: Sequence[ReverseCoverCase],
    time_limit_seconds: float,
) -> dict[str, object]:
    _require_model_t(profile)
    return {
        "profile_id": profile.profile_id,
        "role": profile.role,
        "tiling_model": profile.tiling_model,
        "orientation": profile.orientation,
        "cases": [_case_report(build_incidence_problem(profile, case), time_limit_seconds) for case in cases],
    }


def _case_report(problem: IncidenceProblem, time_limit_seconds: float) -> dict[str, object]:
    greedy = greedy_reverse_cover(problem)
    milp = solve_milp_reverse_cover(problem, time_limit_seconds=time_limit_seconds)
    lp_lower_bound = solve_lp_lower_bound(problem, time_limit_seconds=time_limit_seconds)
    lower_bounds = _lower_bounds(problem)
    record: dict[str, object] = {
        "case_id": problem.case.case_id,
        "step": problem.case.step,
        "target_cluster": {
            "layer": problem.case.step,
            "radius": problem.case.target_radius,
            "cell_count": len(problem.targets),
            "cells": [_address_record(target) for target in problem.targets],
        },
        "candidate_source_count": len(problem.sources),
        "incidence": {
            "target_count": len(problem.targets),
            "uncovered_target_count": sum(1 for row in problem.rows if not row),
            "row_cover_counts": [len(row) for row in problem.rows],
        },
        "greedy": greedy,
        "milp": milp,
        "lp_lower_bound": lp_lower_bound,
        "lower_bounds": lower_bounds,
        "diagnostic_bounds": {
            "component": 1 if problem.targets else 0,
            "diameter": problem.case.target_radius * 2,
        },
    }
    if milp["status"] == "OPTIMAL":
        objective = int(milp["objective"])
        if lp_lower_bound["status"] == "OPTIMAL" and float(lp_lower_bound["objective"]) > objective + TOLERANCE:
            raise ValueError("LP lower bound cannot exceed proven MILP optimum")
        if int(lower_bounds["capacity"]) > objective:
            raise ValueError("capacity lower bound cannot exceed proven MILP optimum")
        record["gap"] = {
            "greedy_minus_opt_over_opt": (int(greedy["selected_count"]) - objective) / objective if objective > 0 else 0.0
        }
    return record


def _candidate_sources(
    profile: GeometryProfile,
    case: ReverseCoverCase,
    targets: Sequence[HexAddress],
) -> tuple[HexAddress, ...]:
    source_layer = layer_spec_from_profile(profile, SOURCE_LAYER)
    target_layer = layer_spec_from_profile(profile, case.step)
    candidates: set[Axial] = set(axial_disk(Axial(0, 0), case.target_radius + 3))
    for target in targets:
        center = axial_to_world(target.axial, target_layer)
        source_center = world_to_axial(center, source_layer)
        candidates.update(axial_disk(source_center, 3))
    return tuple(
        HexAddress(SOURCE_LAYER, cell.q, cell.r)
        for cell in sorted(candidates, key=lambda item: (item.q, item.r))
    )


def _lower_bounds(problem: IncidenceProblem) -> dict[str, object]:
    max_cover = max((sum(1 for row in problem.rows if source_index in row) for source_index in range(len(problem.sources))), default=0)
    capacity = ceil(len(problem.targets) / max_cover) if max_cover > 0 else 0
    return {
        "capacity": capacity,
        "max_targets_covered_by_single_source": max_cover,
    }


def _comparison(profiles: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_id = {str(profile["profile_id"]): profile for profile in profiles}
    if "default_dream" not in by_id or "medium_practical" not in by_id:
        return {}
    default_cases = _cases_by_id(by_id["default_dream"])
    medium_cases = _cases_by_id(by_id["medium_practical"])
    notes: list[str] = []
    for case_id in sorted(set(default_cases) & set(medium_cases)):
        default_case = default_cases[case_id]
        medium_case = medium_cases[case_id]
        default_gap = _case_gap(default_case)
        medium_gap = _case_gap(medium_case)
        if default_gap is None or medium_gap is None:
            notes.append(f"{case_id}:insufficient_optimal_results")
        elif medium_gap < default_gap:
            notes.append(f"{case_id}:medium_practical_easier")
        elif default_gap < medium_gap:
            notes.append(f"{case_id}:default_dream_easier")
        else:
            notes.append(f"{case_id}:equal")
    return {
        "default_dream_vs_medium_practical": {
            "metric": "greedy_gap_when_milp_optimal",
            "notes": notes,
        }
    }


def _cases_by_id(profile: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    cases = profile["cases"]
    if not isinstance(cases, list):
        return {}
    return {str(case["case_id"]): case for case in cases if isinstance(case, Mapping)}


def _case_gap(case: Mapping[str, object]) -> float | None:
    gap = case.get("gap")
    if not isinstance(gap, Mapping):
        return None
    value = gap.get("greedy_minus_opt_over_opt")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _dense_incidence_matrix(problem: IncidenceProblem) -> list[list[float]]:
    matrix = [[0.0 for _ in problem.sources] for _ in problem.targets]
    for target_index, source_indexes in enumerate(problem.rows):
        for source_index in source_indexes:
            matrix[target_index][source_index] = 1.0
    return matrix


def _selected_indexes(values: object) -> list[int]:
    return [index for index, value in enumerate(values) if float(value) >= 0.5]  # type: ignore[arg-type]


def _address_record(address: HexAddress) -> dict[str, int]:
    return {"q": address.q, "r": address.r}


def _require_model_t(profile: GeometryProfile) -> None:
    if not isinstance(profile, GeometryProfile):
        raise ValueError("profile must be a GeometryProfile")
    if profile.tiling_model != "T":
        raise ValueError("G5 reverse cover supports strict true tiling Model T only")


def _require_positive_int(value: object, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{label} must be a positive integer")


def _require_non_negative_int(value: object, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def _require_positive_number(value: object, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a positive finite number")


def _reject_forbidden_keys(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in FORBIDDEN_REPORT_KEYS:
                raise ValueError(f"forbidden reverse-cover report key: {key}")
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
    "DEFAULT_CASE_STEPS",
    "DEFAULT_PROFILE_IDS",
    "DEFAULT_TARGET_RADIUS",
    "ReverseCoverCase",
    "SCHEMA",
    "STATUS",
    "build_incidence_problem",
    "default_reverse_cover_cases",
    "greedy_reverse_cover",
    "normalize_solver_status",
    "reverse_cover_report",
    "solve_lp_lower_bound",
    "solve_milp_reverse_cover",
    "validate_reverse_cover_report",
]
