from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from nollm.dream_pipeline import (
    FORBIDDEN_REPORT_FIELDS,
    REPORT_WARNINGS,
    build_dream_geometry_run_report,
    validate_dream_geometry_run_report,
)

BATCH_WARNINGS = (
    "E2 batch reports are internal experiment infrastructure",
    "batch output does not write cards or confirm memories",
    "batch invariants reject tree/folder/anchor-ownership regressions",
)


def load_batch_fixture(repo_root: Path | str) -> list[dict[str, object]]:
    root = Path(repo_root)
    batch_root = root / "examples" / "openclaw_dream" / "batch"
    fixtures = []
    for fixture_dir in sorted(path for path in batch_root.iterdir() if path.is_dir()):
        shards_path = fixture_dir / "shards.json"
        placements_path = fixture_dir / "placements.json"
        if not shards_path.exists() or not placements_path.exists():
            continue
        fixtures.append(
            {
                "fixture_id": fixture_dir.name,
                "chart_id": f"{fixture_dir.name}-chart",
                "shards": _load_json_array(shards_path),
                "placements": _load_json_array(placements_path),
            }
        )
    if not fixtures:
        raise ValueError("no batch fixtures found")
    return fixtures


def build_batch_experiment_report(
    fixtures: list[Mapping[str, object]],
    run_id: str = "openclaw-dream-e2-batch",
) -> dict[str, object]:
    _require_non_empty_string(run_id, "run_id")
    reports = []
    checks = []

    for fixture in sorted(fixtures, key=lambda item: str(item.get("fixture_id", ""))):
        fixture_id = _record_string(fixture, "fixture_id")
        chart_id = _record_string(fixture, "chart_id")
        shards = _record_list(fixture, "shards")
        placements = _record_list(fixture, "placements")
        try:
            report = build_dream_geometry_run_report(
                shards,
                placements,
                run_id=f"{run_id}:{fixture_id}",
                chart_id=chart_id,
            )
            reports.append({"fixture_id": fixture_id, "report": report})
            checks.extend(_checks_for_report(fixture_id, report))
        except Exception as exc:
            checks.append(_check(f"fixture_valid:{fixture_id}", False, str(exc)))

    checks.append(_check("batch_output_ordering", _fixture_ids_sorted(reports), "fixture reports sorted by fixture_id"))
    ok = all(bool(check["ok"]) for check in checks)
    batch = {
        "run_id": run_id,
        "status": "experimental_candidate",
        "fixture_count": len(fixtures),
        "reports": reports,
        "invariants": {
            "ok": ok,
            "checks": checks,
        },
        "warnings": list(BATCH_WARNINGS),
    }
    validate_batch_experiment_report(batch)
    return batch


def validate_batch_experiment_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("batch report must be a mapping")
    for key in ("run_id", "status", "fixture_count", "reports", "invariants", "warnings"):
        if key not in report:
            raise ValueError(f"missing batch report field: {key}")
    if report["status"] != "experimental_candidate":
        raise ValueError("batch report status must be experimental_candidate")
    if _has_forbidden_field(report):
        raise ValueError("batch report contains forbidden tree/ownership field")
    if not _is_json_primitive(report):
        raise ValueError("batch report must be JSON-primitive serializable")
    invariants = report["invariants"]
    if not isinstance(invariants, Mapping) or "ok" not in invariants or "checks" not in invariants:
        raise ValueError("invariants must contain ok and checks")


def write_batch_experiment_report(report: Mapping[str, object], output_path: Path | str) -> None:
    validate_batch_experiment_report(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _checks_for_report(fixture_id: str, report: Mapping[str, object]) -> list[dict[str, object]]:
    checks = []
    checks.append(_check(f"json_primitive:{fixture_id}", _is_json_primitive(report), "report is JSON primitive"))
    checks.append(_check(f"status:{fixture_id}", report.get("status") == "experimental_candidate", "status is experimental_candidate"))
    checks.append(_check(f"no_tree_ownership_fields:{fixture_id}", not _has_forbidden_field(report), "no forbidden fields found"))
    checks.append(_check(f"placement_shards:{fixture_id}", _placements_reference_known_shards(report), "placements reference known shards"))
    checks.append(_check(f"placement_energy:{fixture_id}", _placements_have_energy(report), "ranked placements include energy fields"))
    checks.append(_check(f"scale_scan_candidate:{fixture_id}", _scale_scan_candidate_only(report), "scale scan plans are candidate-only"))
    checks.append(_check(f"no_confirmed_placement:{fixture_id}", not _claims_confirmed_placement(report), "no confirmed placement claimed"))
    checks.append(_check(f"parameter_diagnostics:{fixture_id}", _parameter_results_are_diagnostics(report), "parameter results are diagnostics"))
    checks.append(_check(f"audit_history_support:{fixture_id}", _audit_history_support_wording(report), "audit/history remain support organs"))
    return checks


def _check(check_id: str, ok: bool, message: str) -> dict[str, object]:
    return {"check_id": check_id, "ok": bool(ok), "message": message}


def _placements_reference_known_shards(report: Mapping[str, object]) -> bool:
    shard_ids = {item.get("shard_id") for item in _record_list(report, "shards") if isinstance(item, Mapping)}
    return all(item.get("shard_id") in shard_ids for item in _record_list(report, "ranked_placements") if isinstance(item, Mapping))


def _placements_have_energy(report: Mapping[str, object]) -> bool:
    required = {
        "semantic_hint_cost",
        "geometric_distance_cost",
        "density_pressure_cost",
        "coverage_potential_cost",
        "future_scan_cost",
        "merge_complexity_cost",
        "compute_cost",
    }
    for placement in _record_list(report, "ranked_placements"):
        if not isinstance(placement, Mapping):
            return False
        energy = placement.get("energy")
        if not isinstance(energy, Mapping) or not required.issubset(energy.keys()):
            return False
    return True


def _scale_scan_candidate_only(report: Mapping[str, object]) -> bool:
    return all(plan.get("status") == "candidate" for plan in _record_list(report, "scale_scan_plans") if isinstance(plan, Mapping))


def _claims_confirmed_placement(report: Mapping[str, object]) -> bool:
    text = json.dumps(report, sort_keys=True)
    return "confirmed placement" in text or '"status": "confirmed"' in text


def _parameter_results_are_diagnostics(report: Mapping[str, object]) -> bool:
    warnings = report.get("warnings")
    return isinstance(warnings, list) and any("diagnostics" in str(item) for item in warnings)


def _audit_history_support_wording(report: Mapping[str, object]) -> bool:
    warnings = report.get("warnings")
    return isinstance(warnings, list) and any("support organs" in str(item) for item in warnings)


def _fixture_ids_sorted(reports: list[Mapping[str, object]]) -> bool:
    ids = [str(item.get("fixture_id", "")) for item in reports]
    return ids == sorted(ids)


def _load_json_array(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError(f"{path} must contain a JSON object array")
    return data


def _record_string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _record_list(record: Mapping[str, object], key: str) -> list:
    value = record.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_non_empty_string(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


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
    "BATCH_WARNINGS",
    "load_batch_fixture",
    "build_batch_experiment_report",
    "validate_batch_experiment_report",
    "write_batch_experiment_report",
]
