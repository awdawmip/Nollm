from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from nollm.geometry_profiles import canonical_geometry_profiles
from nollm.gravity import (
    GravityMark,
    GravityWell,
    create_gravity_report,
    gravity_mark_to_record,
    gravity_report_to_record,
    gravity_well_to_record,
)
from nollm.minimal_ablation_experiment import ablation_fixture_from_record, build_minimal_ablation_report
from nollm.mode3_trace_experiment import (
    build_mode3_trace,
    mode3_trace_fixture_from_record,
    mode3_trace_result_to_record,
)
from nollm.multi_step_coverage import multi_profile_coverage_report
from nollm.offset_sampling import offset_sampling_report

SCHEMA = "nollm.g_series_engineering_closure.v1"
STATUS = "experimental_internal_only"
REQUIRED_STEPS = ("G0", "G1", "G2", "G3", "G4", "G5", "G5b", "G6", "G7", "G8")

DEFAULT_DOCS = (
    "docs/roadmap/NOLLM_ENGINEERING_ROADMAP_V4_20260616.md",
    "docs/geometry/NOLLM_TRUE_TILING_ENGINEERING_REQUIREMENTS_20260616.md",
    "docs/geometry/NOLLM_PARAMETER_PROFILE_REGISTRY.md",
    "docs/geometry/G3_MULTI_STEP_COVERAGE_METRICS.md",
    "docs/geometry/G4_OFFSET_SAMPLING.md",
    "docs/geometry/G5_REVERSE_COVER_MILP.md",
    "docs/engineering/G6_GRAVITY_REPORT_V1.md",
    "docs/experiments/G7_MODE3_FREE_DRIFT_TRACE_EXPERIMENT.md",
    "docs/experiments/G8_MINIMAL_ABLATION_EXPERIMENT.md",
)
DEFAULT_PROTOCOLS = (
    "protocol/PARAMETER_PROFILES.md",
    "protocol/GRAVITY_WELL.md",
    "protocol/GRAVITY_MARK.md",
    "protocol/DRIFT_REPORT.md",
    "protocol/RETURN_VECTOR.md",
)
DEFAULT_REPORTS = (
    "out/nollm_runtime/multi_step_coverage_report.json",
    "out/nollm_runtime/offset_sampling_report.json",
    "out/nollm_runtime/reverse_cover_report.json",
    "out/nollm_runtime/gravity_report_demo.json",
    "out/nollm_runtime/mode3_trace_experiment_report.json",
    "out/nollm_runtime/minimal_ablation_experiment_report.json",
)


def build_g_series_engineering_closure_report(
    repo_root: Path,
    *,
    generate_reports: bool = False,
    docs: Sequence[str] = DEFAULT_DOCS,
    protocols: Sequence[str] = DEFAULT_PROTOCOLS,
    reports: Sequence[str] = DEFAULT_REPORTS,
) -> dict[str, object]:
    repo_root = Path(repo_root).resolve()
    if generate_reports:
        generate_g_series_runtime_reports(repo_root)
    artifacts = {
        "docs": _path_presence(repo_root, docs),
        "protocols": _path_presence(repo_root, protocols),
        "reports": _path_presence(repo_root, reports),
    }
    metrics_presence = _metrics_presence(repo_root)
    forbidden_semantics = {
        "stable_recall_surface": False,
        "auto_writeback": False,
        "anchor_creation": False,
        "trust_status_mapping": False,
        "hard_drift_rejection": False,
        "parent_child_geometry": False,
    }
    failures = _artifact_failures(artifacts) + _metric_failures(metrics_presence)
    report = {
        "schema": SCHEMA,
        "status": STATUS,
        "ok": not failures and all(value is False for value in forbidden_semantics.values()),
        "commit_series": {"required_steps": list(REQUIRED_STEPS)},
        "artifacts": artifacts,
        "metrics_presence": metrics_presence,
        "forbidden_semantics": forbidden_semantics,
        "failures": failures,
    }
    if not _is_json_primitive(report):
        raise ValueError("closure report must be JSON-primitive serializable")
    return report


def generate_g_series_runtime_reports(repo_root: Path) -> None:
    repo_root = Path(repo_root).resolve()
    runtime = repo_root / "out" / "nollm_runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    _write_json(runtime / "multi_step_coverage_report.json", multi_profile_coverage_report(max_step=8))
    _write_json(runtime / "offset_sampling_report.json", offset_sampling_report(max_step=8))
    if not (runtime / "reverse_cover_report.json").exists():
        raise ValueError("reverse_cover_report.json is required before refresh mode; run the reverse-cover experiment explicitly")
    _write_json(runtime / "gravity_report_demo.json", _gravity_demo_report())

    mode3_fixture = json.loads((repo_root / "examples" / "openclaw_dream" / "mode3_trace_fixture.json").read_text(encoding="utf-8"))
    mode3_well, mode3_candidates = mode3_trace_fixture_from_record(mode3_fixture)
    _write_json(runtime / "mode3_trace_experiment_report.json", mode3_trace_result_to_record(build_mode3_trace(mode3_well, mode3_candidates)))

    ablation_fixture = json.loads((repo_root / "examples" / "openclaw_dream" / "minimal_ablation_fixture.json").read_text(encoding="utf-8"))
    _write_json(
        runtime / "minimal_ablation_experiment_report.json",
        build_minimal_ablation_report(ablation_fixture_from_record(ablation_fixture)),
    )


def write_closure_report(report: Mapping[str, object], output: Path) -> None:
    _write_json(output, report)


def _metrics_presence(repo_root: Path) -> dict[str, object]:
    runtime = repo_root / "out" / "nollm_runtime"
    multi_step = _read_json(runtime / "multi_step_coverage_report.json")
    offset = _read_json(runtime / "offset_sampling_report.json")
    reverse = _read_json(runtime / "reverse_cover_report.json")
    gravity = _read_json(runtime / "gravity_report_demo.json")
    mode3 = _read_json(runtime / "mode3_trace_experiment_report.json")
    ablation = _read_json(runtime / "minimal_ablation_experiment_report.json")
    return {
        "profiles": _profile_metrics(),
        "multi_step": _multi_step_metrics(multi_step),
        "offset_sampling": _offset_metrics(offset),
        "reverse_cover": _reverse_metrics(reverse),
        "gravity": _gravity_metrics(gravity),
        "mode3": _mode3_metrics(mode3),
        "ablation": _ablation_metrics(ablation),
    }


def _profile_metrics() -> dict[str, bool]:
    ids = {profile.profile_id for profile in canonical_geometry_profiles()}
    return {
        "default_dream": "default_dream" in ids,
        "medium_practical": "medium_practical" in ids,
        "benchmarks_present": {"benchmark_aligned", "benchmark_single_step", "benchmark_eisenstein"}.issubset(ids),
    }


def _multi_step_metrics(report: object) -> dict[str, bool]:
    profiles = _profiles(report)
    default = _profile_by_id(profiles, "default_dream")
    medium = _profile_by_id(profiles, "medium_practical")
    all_steps = [step for profile in profiles for step in profile.get("steps", []) if isinstance(step, Mapping)]
    return {
        "n_1_to_8_present": {step.get("step") for step in all_steps}.issuperset(set(range(1, 9))),
        "default_dream_n8_present": _has_step(default, 8),
        "medium_practical_n8_present": _has_step(medium, 8),
    }


def _offset_metrics(report: object) -> dict[str, bool]:
    profiles = _profiles(report)
    steps = [step for profile in profiles for step in profile.get("steps", []) if isinstance(step, Mapping)]
    aggregates = [step.get("aggregates") for step in steps if isinstance(step.get("aggregates"), Mapping)]
    return {
        "deterministic_samples_present": any(int(step.get("sample_count", 0)) >= 9 for step in steps),
        "random_seed_present": isinstance(report, Mapping) and "seed" in report,
        "variance_metrics_present": any("participation_ratio_variance" in aggregate for aggregate in aggregates),
    }


def _reverse_metrics(report: object) -> dict[str, bool]:
    cases = [case for profile in _profiles(report) for case in profile.get("cases", []) if isinstance(case, Mapping)]
    optimal_status_present = any(isinstance(case.get("milp"), Mapping) and case["milp"].get("status") == "OPTIMAL" for case in cases)
    return {
        "nontrivial_case_pack_present": any(case.get("case_pack") == "nontrivial" for case in cases),
        "optimal_status_present": optimal_status_present,
        "greedy_gap_metrics_present": any("gap" in case for case in cases),
    }


def _gravity_metrics(report: object) -> dict[str, object]:
    drift_reports = report.get("drift_reports", []) if isinstance(report, Mapping) else []
    first_report = drift_reports[0] if isinstance(drift_reports, list) and drift_reports else {}
    return {
        "gravity_well_present": isinstance(report, Mapping) and isinstance(report.get("gravity_well"), Mapping),
        "gravity_mark_present": isinstance(report, Mapping) and isinstance(report.get("gravity_marks"), list),
        "gravity_report_present": isinstance(first_report, Mapping),
        "A_anchor_similarity_range_v1": "[0,1]",
        "projection_method_present": isinstance(first_report, Mapping) and "projection_method" in first_report,
    }


def _mode3_metrics(report: object) -> dict[str, bool]:
    return {
        "candidate_filtering_by_drift": False,
        "drift_class_distribution_present": isinstance(report, Mapping) and isinstance(report.get("drift_class_counts"), Mapping),
    }


def _ablation_metrics(report: object) -> dict[str, bool]:
    conditions = report.get("conditions", []) if isinstance(report, Mapping) else []
    condition_ids = {condition.get("condition") for condition in conditions if isinstance(condition, Mapping)}
    metrics = [condition.get("metrics") for condition in conditions if isinstance(condition, Mapping)]
    return {
        "n0_to_n5_present": set(CONDITION_SERIES).issubset(condition_ids),
        "drift_visibility_gain_present": any(isinstance(item, Mapping) and "drift_visibility_gain" in item for item in metrics),
        "return_vector_visibility_present": any(isinstance(item, Mapping) and "return_vector_visible" in item for item in metrics),
    }


CONDITION_SERIES = ("N0", "N1", "N2", "N3", "N4", "N5")


def _gravity_demo_report() -> dict[str, object]:
    well = GravityWell(
        well_id="gw_closure_demo",
        entry_query="closure demo",
        geometry_profile="default_dream",
        chart_id="chart_closure",
        layer=0,
        q=0,
        r=0,
        anchor_vector={"field.alpha": 1.0, "field.beta": 0.5},
        created_at="2026-06-18T00:00:00Z",
    )
    marks = [
        GravityMark(
            content_id="closure_core",
            geometry_profile="default_dream",
            chart_id="chart_closure",
            layer=0,
            q=0,
            r=0,
            anchor_vector={"field.alpha": 1.0, "field.beta": 0.5},
            provenance="experiment",
        ),
        GravityMark(
            content_id="closure_far",
            geometry_profile="default_dream",
            chart_id="chart_closure",
            layer=0,
            q=4,
            r=0,
            anchor_vector={"field.alpha": 1.0},
            provenance="experiment",
        ),
    ]
    reports = [create_gravity_report(well, mark) for mark in marks]
    return {
        "status": STATUS,
        "gravity_well": gravity_well_to_record(well),
        "gravity_marks": [gravity_mark_to_record(mark) for mark in marks],
        "drift_reports": [gravity_report_to_record(report) for report in reports],
    }


def _profiles(report: object) -> list[Mapping[str, object]]:
    if not isinstance(report, Mapping):
        return []
    profiles = report.get("profiles")
    return [profile for profile in profiles if isinstance(profile, Mapping)] if isinstance(profiles, list) else []


def _profile_by_id(profiles: Sequence[Mapping[str, object]], profile_id: str) -> Mapping[str, object] | None:
    for profile in profiles:
        if profile.get("profile_id") == profile_id:
            return profile
    return None


def _has_step(profile: Mapping[str, object] | None, step_number: int) -> bool:
    if profile is None:
        return False
    steps = profile.get("steps")
    return any(isinstance(step, Mapping) and step.get("step") == step_number for step in steps) if isinstance(steps, list) else False


def _artifact_failures(artifacts: Mapping[str, object]) -> list[str]:
    failures: list[str] = []
    for group_name, group in artifacts.items():
        if not isinstance(group, Mapping):
            failures.append(f"artifact_group_missing:{group_name}")
            continue
        for path, exists in group.items():
            if exists is not True:
                failures.append(f"missing_{group_name}:{path}")
    return failures


def _metric_failures(metrics_presence: Mapping[str, object]) -> list[str]:
    failures: list[str] = []
    _collect_false_metrics(metrics_presence, (), failures)
    return failures


EXPECTED_FALSE_METRICS = {
    ("mode3", "candidate_filtering_by_drift"),
}


def _collect_false_metrics(value: object, path: tuple[str, ...], failures: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _collect_false_metrics(item, path + (str(key),), failures)
    elif value is False and path not in EXPECTED_FALSE_METRICS:
        failures.append("missing_metric:" + ".".join(path))


def _path_presence(repo_root: Path, paths: Sequence[str]) -> dict[str, bool]:
    return {path: (repo_root / path).exists() for path in paths}


def _read_json(path: Path) -> object:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


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
    "build_g_series_engineering_closure_report",
    "generate_g_series_runtime_reports",
    "write_closure_report",
]
