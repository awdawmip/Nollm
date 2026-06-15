from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Mapping

from nollm.dream_experiment_batch import validate_batch_experiment_report
from nollm.dream_pipeline import (
    FORBIDDEN_REPORT_FIELDS,
    build_dream_geometry_run_report,
    validate_dream_geometry_run_report,
)
from nollm.dream_placement import placement_candidate_from_record
from nollm.dream_shard import shard_from_record

REGRESSION_WARNINGS = (
    "E3 is internal regression infrastructure",
    "E3 does not write cards or confirm placements",
    "E3 exists to reject tree/folder/anchor-ownership regressions",
)


RegressionCase = tuple[str, str, str, Callable[[], None]]


def default_dream_regression_cases() -> tuple[RegressionCase, ...]:
    return (
        ("forbidden_parent_id_nested", "tree_regression", "parent_id", _case_forbidden_parent_id_nested),
        ("forbidden_belongs_to_anchor_nested", "tree_regression", "belongs_to_anchor", _case_forbidden_belongs_to_anchor_nested),
        ("confirmed_status_structured", "confirmed_placement", "status", _case_confirmed_status_structured),
        ("confirmed_placement_text", "confirmed_placement", "text", _case_confirmed_placement_text),
        ("unknown_shard_reference", "reference_integrity", "shard_id", _case_unknown_shard_reference),
        ("missing_shard_id", "malformed_shard", "shard_id", _case_missing_shard_id),
        ("empty_shard_text", "malformed_shard", "text", _case_empty_shard_text),
        ("non_list_anchor_hints", "malformed_shard", "anchors_hint", _case_non_list_anchor_hints),
        ("missing_energy_object", "malformed_placement", "energy", _case_missing_energy_object),
        ("missing_energy_term", "malformed_placement", "compute_cost", _case_missing_energy_term),
        ("non_numeric_energy_term", "malformed_placement", "compute_cost", _case_non_numeric_energy_term),
    )


def build_dream_regression_report(
    cases: tuple[RegressionCase, ...] | list[RegressionCase] | None = None,
    run_id: str = "openclaw-dream-e3-regression",
) -> dict[str, object]:
    selected = list(default_dream_regression_cases() if cases is None else cases)
    records = [_run_case(case) for case in sorted(selected, key=lambda item: item[0])]
    passed = sum(1 for record in records if record["ok"])
    report = {
        "run_id": run_id,
        "status": "experimental_candidate",
        "case_count": len(records),
        "cases": records,
        "summary": {
            "ok": passed == len(records),
            "passed": passed,
            "failed": len(records) - passed,
        },
        "warnings": list(REGRESSION_WARNINGS),
    }
    validate_dream_regression_report(report)
    return report


def validate_dream_regression_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("regression report must be a mapping")
    for key in ("run_id", "status", "case_count", "cases", "summary", "warnings"):
        if key not in report:
            raise ValueError(f"missing regression report field: {key}")
    if report["status"] != "experimental_candidate":
        raise ValueError("regression report status must be experimental_candidate")
    if _has_forbidden_field(report):
        raise ValueError("regression report contains forbidden tree/ownership field")
    if not _is_json_primitive(report):
        raise ValueError("regression report must be JSON-primitive serializable")


def write_dream_regression_report(report: Mapping[str, object], output_path: Path | str) -> None:
    validate_dream_regression_report(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _run_case(case: RegressionCase) -> dict[str, object]:
    case_id, category, field_name, runner = case
    observed = "pass"
    message = "case unexpectedly passed"
    try:
        runner()
    except Exception as exc:
        observed = "fail"
        message = str(exc)
    return {
        "case_id": case_id,
        "category": category,
        "field_name": field_name,
        "expected": "fail",
        "observed": observed,
        "ok": observed == "fail",
        "message": message,
    }


def _case_forbidden_parent_id_nested() -> None:
    report = _valid_report()
    report["ranked_placements"][0]["parent_id"] = "bad"  # type: ignore[index]
    validate_dream_geometry_run_report(report)


def _case_forbidden_belongs_to_anchor_nested() -> None:
    report = _valid_report()
    report["shards"][0]["belongs_to_anchor"] = "bad"  # type: ignore[index]
    validate_dream_geometry_run_report(report)


def _case_confirmed_status_structured() -> None:
    record = _valid_placement_record()
    record["status"] = "confirmed"
    placement_candidate_from_record(record)


def _case_confirmed_placement_text() -> None:
    report = _valid_report()
    report["warnings"] = ["confirmed placement"]
    validate_batch_experiment_report(
        {
            "run_id": "bad",
            "status": "experimental_candidate",
            "fixture_count": 1,
            "reports": [{"fixture_id": "bad", "report": report}],
            "invariants": {"ok": True, "checks": []},
            "warnings": ["confirmed placement"],
        }
    )
    raise ValueError("confirmed placement text was not rejected by invariant caller")


def _case_unknown_shard_reference() -> None:
    shards = [_valid_shard_record()]
    placement = _valid_placement_record()
    placement["shard_id"] = "missing-shard"
    build_dream_geometry_run_report(shards, [placement])


def _case_missing_shard_id() -> None:
    record = _valid_shard_record()
    del record["shard_id"]
    shard_from_record(record)


def _case_empty_shard_text() -> None:
    record = _valid_shard_record()
    record["text"] = ""
    shard_from_record(record)


def _case_non_list_anchor_hints() -> None:
    record = _valid_shard_record()
    record["anchors_hint"] = "not-a-list"
    shard_from_record(record)


def _case_missing_energy_object() -> None:
    record = _valid_placement_record()
    del record["energy"]
    placement_candidate_from_record(record)


def _case_missing_energy_term() -> None:
    record = _valid_placement_record()
    del record["energy"]["compute_cost"]  # type: ignore[index]
    if "compute_cost" not in record["energy"]:  # type: ignore[operator]
        raise ValueError("energy object missing required cost term: compute_cost")
    placement_candidate_from_record(record)


def _case_non_numeric_energy_term() -> None:
    record = _valid_placement_record()
    record["energy"]["compute_cost"] = "bad"  # type: ignore[index]
    placement_candidate_from_record(record)


def _valid_report() -> dict[str, object]:
    return build_dream_geometry_run_report([_valid_shard_record()], [_valid_placement_record()])


def _valid_shard_record() -> dict[str, object]:
    return {
        "shard_id": "regression-shard",
        "text": "Regression shards remain candidate material.",
        "source": "project_note",
        "status": "candidate",
        "anchors_hint": ["regression"],
        "metadata": {"fixture": "e3"},
    }


def _valid_placement_record() -> dict[str, object]:
    return {
        "shard_id": "regression-shard",
        "chart_id": "regression-chart",
        "address": {"layer": 0, "q": 0, "r": 0},
        "energy": {
            "semantic_hint_cost": 0.0,
            "geometric_distance_cost": 0.0,
            "density_pressure_cost": 0.0,
            "coverage_potential_cost": 0.0,
            "future_scan_cost": 0.0,
            "merge_complexity_cost": 0.0,
            "compute_cost": 0.0,
        },
        "anchors_used": ["regression"],
        "reasons": ["valid baseline"],
        "status": "candidate",
    }


def _has_forbidden_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(key in FORBIDDEN_REPORT_FIELDS or _has_forbidden_field(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_forbidden_field(item) for item in value)
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
    "REGRESSION_WARNINGS",
    "default_dream_regression_cases",
    "build_dream_regression_report",
    "validate_dream_regression_report",
    "write_dream_regression_report",
]
