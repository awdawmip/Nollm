from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from nollm.dream_experiment_batch import build_batch_experiment_report, load_batch_fixture
from nollm.dream_pipeline import (
    FORBIDDEN_REPORT_FIELDS,
    build_dream_geometry_run_report,
    load_dream_geometry_fixture,
)
from nollm.dream_regression import build_dream_regression_report

SUITE_WARNINGS = (
    "E4 is internal experiment infrastructure",
    "E4 is not a stable V1 recall/tool surface",
    "E4 does not write cards or confirm memories",
)


def build_dream_geometry_suite_report(repo_root: Path | str) -> dict[str, object]:
    root = Path(repo_root)
    shards, placements = load_dream_geometry_fixture(root)
    pipeline_report = build_dream_geometry_run_report(shards, placements)
    batch_report = build_batch_experiment_report(load_batch_fixture(root))
    regression_report = build_dream_regression_report()

    batch_checks = batch_report["invariants"]["checks"]  # type: ignore[index]
    regression_cases = regression_report["cases"]  # type: ignore[index]
    report = {
        "schema": "nollm.dream_geometry_suite.v1",
        "status": "experimental_candidate",
        "ok": bool(
            pipeline_report["status"] == "experimental_candidate"
            and batch_report["invariants"]["ok"]  # type: ignore[index]
            and regression_report["summary"]["ok"]  # type: ignore[index]
        ),
        "components": {
            "pipeline": {
                "ok": pipeline_report["status"] == "experimental_candidate",
                "shard_count": len(pipeline_report["shards"]),  # type: ignore[arg-type]
                "placement_count": len(pipeline_report["ranked_placements"]),  # type: ignore[arg-type]
            },
            "batch": {
                "ok": bool(batch_report["invariants"]["ok"]),  # type: ignore[index]
                "fixture_count": batch_report["fixture_count"],
                "invariant_check_count": len(batch_checks),  # type: ignore[arg-type]
                "failed_invariant_count": sum(1 for check in batch_checks if not check["ok"]),
            },
            "regression": {
                "ok": bool(regression_report["summary"]["ok"]),  # type: ignore[index]
                "case_count": regression_report["case_count"],
                "failed_case_count": sum(1 for case in regression_cases if not case["ok"]),
            },
        },
        "forbidden_semantics": {
            "parent_child": _has_forbidden_field(pipeline_report) or _has_forbidden_field(batch_report),
            "anchor_ownership": _has_forbidden_field(pipeline_report) or _has_forbidden_field(batch_report),
            "folder_tree": _has_forbidden_field(pipeline_report) or _has_forbidden_field(batch_report),
            "confirmed_placement": _has_confirmed_status(pipeline_report) or _has_confirmed_status(batch_report),
        },
        "warnings": list(SUITE_WARNINGS),
    }
    if any(report["forbidden_semantics"].values()):  # type: ignore[union-attr]
        report["ok"] = False
    validate_dream_geometry_suite_report(report)
    return report


def validate_dream_geometry_suite_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("suite report must be a mapping")
    for key in ("schema", "status", "ok", "components", "forbidden_semantics", "warnings"):
        if key not in report:
            raise ValueError(f"missing suite report field: {key}")
    if report["schema"] != "nollm.dream_geometry_suite.v1":
        raise ValueError("unsupported suite report schema")
    if report["status"] != "experimental_candidate":
        raise ValueError("suite report status must be experimental_candidate")
    if _has_forbidden_field(report):
        raise ValueError("suite report contains forbidden tree/ownership field")
    if not _is_json_primitive(report):
        raise ValueError("suite report must be JSON-primitive serializable")


def write_dream_geometry_suite_report(report: Mapping[str, object], output_path: Path | str) -> None:
    validate_dream_geometry_suite_report(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def run_dream_geometry_suite(repo_root: Path | str, output_path: Path | str | None = None) -> dict[str, object]:
    report = build_dream_geometry_suite_report(repo_root)
    if output_path is not None:
        write_dream_geometry_suite_report(report, output_path)
    return report


def _has_forbidden_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(key in FORBIDDEN_REPORT_FIELDS or _has_forbidden_field(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_forbidden_field(item) for item in value)
    return False


def _has_confirmed_status(value: object) -> bool:
    if isinstance(value, Mapping):
        if value.get("status") == "confirmed":
            return True
        return any(_has_confirmed_status(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_confirmed_status(item) for item in value)
    return False


def _is_json_primitive(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_primitive(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_primitive(item) for key, item in value.items())
    return False


__all__ = [
    "SUITE_WARNINGS",
    "build_dream_geometry_suite_report",
    "validate_dream_geometry_suite_report",
    "write_dream_geometry_suite_report",
    "run_dream_geometry_suite",
]
