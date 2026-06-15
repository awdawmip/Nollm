from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from nollm.cluster_pressure import (
    coarse_emergence_to_record,
    pressure_sample_to_record,
    propose_coarse_emergence,
    summarize_pressure,
)
from nollm.dream_placement import (
    DreamPlacementCandidate,
    placement_candidate_from_record,
    placement_candidate_to_record,
    rank_placement_candidates,
)
from nollm.dream_shard import DreamShard, shard_from_record, shard_to_record
from nollm.parameter_experiments import (
    default_parameter_regimes,
    evaluate_parameter_regime,
    parameter_result_to_record,
    rank_parameter_results,
)
from nollm.scale_scan_traversal import make_linear_scale_scan_plan, scale_scan_plan_to_record

FORBIDDEN_REPORT_FIELDS = frozenset(
    {
        "parent",
        "parent_id",
        "children",
        "child_ids",
        "owner_anchor",
        "belongs_to_anchor",
        "folder",
        "path_parent",
    }
)

REPORT_WARNINGS = (
    "placements are candidates, not confirmed memory",
    "coarse emergence is candidate-only",
    "scale scan plans are traversal planning, not autonomous recall",
    "parameter results are diagnostics, not final parameter lock",
    "audit/history remain support organs, not the project center",
)


def load_dream_geometry_fixture(repo_root: Path | str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    root = Path(repo_root)
    fixture_dir = root / "examples" / "openclaw_dream"
    shards = _load_json_array(fixture_dir / "shards.json")
    placements = _load_json_array(fixture_dir / "placements.json")
    return shards, placements


def build_dream_geometry_run_report(
    shard_records: list[Mapping[str, object]],
    placement_records: list[Mapping[str, object]],
    run_id: str = "openclaw-dream-e1",
    chart_id: str = "openclaw-chart-demo",
) -> dict[str, object]:
    _require_non_empty_string(run_id, "run_id")
    _require_non_empty_string(chart_id, "chart_id")
    shards = [_roundtrip_shard(record) for record in shard_records]
    placements = [_roundtrip_placement(record) for record in placement_records]
    shard_ids = {shard.shard_id for shard in shards}
    for placement in placements:
        if placement.shard_id not in shard_ids:
            raise ValueError(f"placement references unknown shard_id: {placement.shard_id}")
        _require_non_empty_string(placement.chart_id, "placement chart_id")

    ranked_placements = rank_placement_candidates(placements)
    pressure_samples = summarize_pressure(ranked_placements, chart_id)
    coarse_candidates = []
    if ranked_placements:
        coarse_candidates.append(
            propose_coarse_emergence(
                pressure_samples,
                chart_id,
                ranked_placements[0].address,
                radius=1,
            )
        )

    scale_scan_plans = []
    first_by_shard = _first_placement_by_shard(ranked_placements)
    for shard in sorted(shards, key=lambda item: item.shard_id):
        placement = first_by_shard.get(shard.shard_id)
        if placement is not None:
            scale_scan_plans.append(
                make_linear_scale_scan_plan(
                    shard.shard_id,
                    placement.chart_id,
                    placement.address,
                    max_layers=1,
                    radius=1,
                )
            )

    parameter_results = rank_parameter_results(
        evaluate_parameter_regime(regime, 8) for regime in default_parameter_regimes()
    )

    report = {
        "run_id": run_id,
        "status": "experimental_candidate",
        "chart_id": chart_id,
        "shards": [shard_to_record(shard) for shard in sorted(shards, key=lambda item: item.shard_id)],
        "ranked_placements": [
            placement_candidate_to_record(placement) for placement in ranked_placements
        ],
        "pressure_samples": [pressure_sample_to_record(sample) for sample in pressure_samples],
        "coarse_emergence_candidates": [
            coarse_emergence_to_record(candidate) for candidate in coarse_candidates
        ],
        "scale_scan_plans": [scale_scan_plan_to_record(plan) for plan in scale_scan_plans],
        "parameter_results": [parameter_result_to_record(result) for result in parameter_results],
        "warnings": list(REPORT_WARNINGS),
    }
    validate_dream_geometry_run_report(report)
    return report


def dream_geometry_run_report_to_record(report: Mapping[str, object]) -> dict[str, object]:
    validate_dream_geometry_run_report(report)
    return dict(report)


def validate_dream_geometry_run_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("report must be a mapping")
    for key in (
        "run_id",
        "status",
        "chart_id",
        "shards",
        "ranked_placements",
        "pressure_samples",
        "coarse_emergence_candidates",
        "scale_scan_plans",
        "parameter_results",
        "warnings",
    ):
        if key not in report:
            raise ValueError(f"missing report field: {key}")
    if report["status"] != "experimental_candidate":
        raise ValueError("report status must be experimental_candidate")
    if _has_forbidden_field(report):
        raise ValueError("report contains forbidden tree/ownership field")
    if not _is_json_primitive(report):
        raise ValueError("report must be JSON-primitive serializable")


def write_dream_geometry_run_report(report: Mapping[str, object], output_path: Path | str) -> None:
    validate_dream_geometry_run_report(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _load_json_array(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError(f"{path} must contain JSON object records")
    return data


def _roundtrip_shard(record: Mapping[str, object]) -> DreamShard:
    return shard_from_record(shard_to_record(shard_from_record(record)))


def _roundtrip_placement(record: Mapping[str, object]) -> DreamPlacementCandidate:
    return placement_candidate_from_record(
        placement_candidate_to_record(placement_candidate_from_record(record))
    )


def _first_placement_by_shard(
    placements: list[DreamPlacementCandidate],
) -> dict[str, DreamPlacementCandidate]:
    result: dict[str, DreamPlacementCandidate] = {}
    for placement in placements:
        result.setdefault(placement.shard_id, placement)
    return result


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
    "FORBIDDEN_REPORT_FIELDS",
    "REPORT_WARNINGS",
    "build_dream_geometry_run_report",
    "dream_geometry_run_report_to_record",
    "validate_dream_geometry_run_report",
    "load_dream_geometry_fixture",
    "write_dream_geometry_run_report",
]
