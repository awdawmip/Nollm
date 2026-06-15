from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from nollm.cluster_pressure import pressure_sample_to_record, summarize_pressure
from nollm.dream_placement import (
    DreamPlacementCandidate,
    PlacementEnergy,
    placement_candidate_to_record,
    rank_placement_candidates,
)
from nollm.dream_shard import DreamShard, shard_to_record
from nollm.geometry import HexAddress
from nollm.parameter_experiments import (
    default_parameter_regimes,
    evaluate_parameter_regime,
    parameter_result_to_record,
    rank_parameter_results,
)
from nollm.scale_scan_traversal import make_linear_scale_scan_plan, scale_scan_plan_to_record

CORPUS_PATHS = (
    "README.md",
    "ARCHITECTURE.md",
    "ROADMAP.md",
    "protocol/DREAM_SHARD.md",
    "protocol/DREAM_PLACEMENT.md",
    "protocol/DREAM_SCALE_SCAN.md",
    "protocol/CLUSTER_PRESSURE.md",
    "docs/geometry/D1_PURE_GEOMETRY_KERNEL.md",
    "docs/geometry/D2_LOCAL_CHART_AND_GLUING_PROPOSAL.md",
    "docs/experiments/E4_ONE_COMMAND_DREAM_GEOMETRY_SUITE.md",
)

FORBIDDEN_FIELDS = frozenset(
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


def run_real_corpus_dry_run(root: Path | str, *, max_files: int = 8) -> dict[str, object]:
    repo_root = Path(root)
    if not isinstance(max_files, int) or isinstance(max_files, bool) or max_files <= 0:
        raise ValueError("max_files must be a positive integer")

    selected, skipped = _select_corpus_files(repo_root, max_files)
    shards = [_shard_from_file(repo_root, path, index) for index, path in enumerate(selected)]
    placements = [
        _placement_for_shard(shard, index)
        for index, shard in enumerate(shards)
    ]
    ranked = rank_placement_candidates(placements)
    pressure_samples = summarize_pressure(ranked, chart_id="real-corpus-dry-run")
    scan_plans = [
        make_linear_scale_scan_plan(
            shard.shard_id,
            "real-corpus-dry-run",
            ranked[index].address,
            max_layers=1,
            radius=1,
        )
        for index, shard in enumerate(shards)
        if index < len(ranked)
    ]
    parameter_results = rank_parameter_results(
        evaluate_parameter_regime(regime, 8)
        for regime in default_parameter_regimes()
    )
    report = {
        "ok": True,
        "mode": "real_corpus_dry_run",
        "status": "experimental_candidate",
        "file_count": len(selected),
        "shard_count": len(shards),
        "placement_count": len(ranked),
        "invariant_check_count": 4,
        "failed_invariant_count": 0,
        "processed_paths": [path.as_posix() for path in selected],
        "skipped_paths": skipped,
        "shards": [shard_to_record(shard) for shard in shards],
        "ranked_placements": [placement_candidate_to_record(placement) for placement in ranked],
        "pressure_samples": [pressure_sample_to_record(sample) for sample in pressure_samples],
        "scale_scan_plans": [scale_scan_plan_to_record(plan) for plan in scan_plans],
        "parameter_results": [parameter_result_to_record(result) for result in parameter_results],
        "forbidden_semantics": {
            "parent_child": False,
            "anchor_ownership": False,
            "folder_tree": False,
            "confirmed_placement": False,
        },
        "warnings": [
            "E5 is an internal dry-run experiment",
            "E5 does not write cards or confirm placement",
            "E5 does not create anchors or change stable recall/tool surface",
        ],
    }
    _apply_invariants(report)
    validate_real_corpus_dry_run_report(report)
    return report


def write_real_corpus_dry_run_report(report: Mapping[str, object], output_path: Path | str) -> None:
    validate_real_corpus_dry_run_report(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def validate_real_corpus_dry_run_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("dry-run report must be a mapping")
    for key in (
        "ok",
        "mode",
        "file_count",
        "shard_count",
        "placement_count",
        "invariant_check_count",
        "failed_invariant_count",
        "forbidden_semantics",
    ):
        if key not in report:
            raise ValueError(f"missing dry-run report field: {key}")
    if report["mode"] != "real_corpus_dry_run":
        raise ValueError("dry-run report mode must be real_corpus_dry_run")
    if _has_forbidden_field(report):
        raise ValueError("dry-run report contains forbidden ownership field")
    if not _is_json_primitive(report):
        raise ValueError("dry-run report must be JSON-primitive serializable")


def _select_corpus_files(root: Path, max_files: int) -> tuple[list[Path], list[str]]:
    selected: list[Path] = []
    skipped: list[str] = []
    for rel in CORPUS_PATHS:
        path = root / rel
        if path.exists():
            selected.append(Path(rel))
        else:
            skipped.append(rel)
        if len(selected) >= max_files:
            break
    return selected, skipped


def _shard_from_file(root: Path, relative_path: Path, index: int) -> DreamShard:
    text = (root / relative_path).read_text(encoding="utf-8", errors="replace")
    summary = _first_meaningful_line(text)
    return DreamShard(
        shard_id=f"real-corpus-shard-{index:04d}",
        text=f"{relative_path.as_posix()}: {summary}",
        source="imported_text",
        status="candidate",
        anchors_hint=("real-corpus",),
        metadata={"path": relative_path.as_posix()},
    )


def _first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().strip("#").strip()
        if len(stripped) >= 8:
            return stripped[:180]
    return "Repository document contributes dry-run text."


def _placement_for_shard(shard: DreamShard, index: int) -> DreamPlacementCandidate:
    return DreamPlacementCandidate(
        shard_id=shard.shard_id,
        chart_id="real-corpus-dry-run",
        address=HexAddress(layer=index % 3, q=index % 4, r=-(index % 4)),
        energy=PlacementEnergy(
            semantic_hint_cost=float(index % 3) / 10.0,
            geometric_distance_cost=float(index % 2) / 10.0,
            compute_cost=float(index) / 100.0,
        ),
        anchors_used=("real-corpus",),
        reasons=("deterministic corpus dry-run",),
        status="candidate",
    )


def _apply_invariants(report: dict[str, object]) -> None:
    failed = 0
    if _has_forbidden_field(report):
        failed += 1
        report["forbidden_semantics"]["parent_child"] = True  # type: ignore[index]
    if _has_confirmed_status(report):
        failed += 1
        report["forbidden_semantics"]["confirmed_placement"] = True  # type: ignore[index]
    report["failed_invariant_count"] = failed
    report["ok"] = failed == 0


def _has_forbidden_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(key in FORBIDDEN_FIELDS or _has_forbidden_field(item) for key, item in value.items())
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
    "CORPUS_PATHS",
    "run_real_corpus_dry_run",
    "write_real_corpus_dry_run_report",
    "validate_real_corpus_dry_run_report",
]
