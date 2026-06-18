from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from nollm.gravity import (
    GravityMark,
    GravityReport,
    GravityWell,
    create_gravity_report,
    gravity_mark_from_record,
    gravity_mark_to_record,
    gravity_report_to_record,
    gravity_well_from_record,
    gravity_well_to_record,
)

SCHEMA = "nollm.mode3_trace_experiment.v1"
STATUS = "experimental_internal_only"


@dataclass(frozen=True)
class RecallCandidate:
    candidate_id: str
    text: str
    score: float
    rank: int
    gravity_mark: GravityMark

    def __post_init__(self) -> None:
        _require_non_empty_string(self.candidate_id, "candidate_id")
        _require_non_empty_string(self.text, "text")
        _require_number(self.score, "score")
        _require_positive_int(self.rank, "rank")
        if not isinstance(self.gravity_mark, GravityMark):
            raise ValueError("gravity_mark must be a GravityMark")


@dataclass(frozen=True)
class GravityTraceItem:
    candidate_id: str
    rank: int
    score: float
    text: str
    gravity_report: GravityReport
    llm_visibility_hint: str


@dataclass(frozen=True)
class Mode3TraceResult:
    well: GravityWell
    items: tuple[GravityTraceItem, ...]


def build_mode3_trace(
    well: GravityWell,
    candidates: Sequence[RecallCandidate],
    *,
    max_items: int | None = None,
) -> Mode3TraceResult:
    if not isinstance(well, GravityWell):
        raise ValueError("well must be a GravityWell")
    if max_items is not None:
        _require_positive_int(max_items, "max_items")
    ordered = sorted(candidates, key=lambda candidate: candidate.rank)
    if max_items is not None:
        ordered = ordered[:max_items]
    items = tuple(_trace_item(well, candidate) for candidate in ordered)
    return Mode3TraceResult(well=well, items=items)


def mode3_trace_result_to_record(result: Mode3TraceResult) -> dict[str, object]:
    if not isinstance(result, Mode3TraceResult):
        raise ValueError("result must be a Mode3TraceResult")
    reports = [item.gravity_report for item in result.items]
    rings = [report.R_column_ring for report in reports if report.R_column_ring is not None]
    record = {
        "schema": SCHEMA,
        "status": STATUS,
        "well": {
            "well_id": result.well.well_id,
            "chart_id": result.well.chart_id,
            "layer": result.well.layer,
            "q": result.well.q,
            "r": result.well.r,
        },
        "candidate_count": len(result.items),
        "trace_item_count": len(result.items),
        "drift_class_counts": _drift_class_counts(reports),
        "max_R_column_ring": max(rings) if rings else None,
        "items": [gravity_trace_item_to_record(item) for item in result.items],
    }
    validate_mode3_trace_record(record)
    return record


def gravity_trace_item_to_record(item: GravityTraceItem) -> dict[str, object]:
    if not isinstance(item, GravityTraceItem):
        raise ValueError("item must be a GravityTraceItem")
    return {
        "candidate_id": item.candidate_id,
        "rank": item.rank,
        "score": item.score,
        "text": item.text,
        "gravity_report": gravity_report_to_record(item.gravity_report),
        "llm_visibility_hint": item.llm_visibility_hint,
    }


def recall_candidate_to_record(candidate: RecallCandidate) -> dict[str, object]:
    if not isinstance(candidate, RecallCandidate):
        raise ValueError("candidate must be a RecallCandidate")
    return {
        "candidate_id": candidate.candidate_id,
        "text": candidate.text,
        "score": candidate.score,
        "rank": candidate.rank,
        "gravity_mark": gravity_mark_to_record(candidate.gravity_mark),
    }


def recall_candidate_from_record(record: Mapping[str, object]) -> RecallCandidate:
    if not isinstance(record, Mapping):
        raise ValueError("candidate record must be a mapping")
    gravity_mark = record.get("gravity_mark")
    if not isinstance(gravity_mark, Mapping):
        raise ValueError("gravity_mark must be a mapping")
    return RecallCandidate(
        candidate_id=_record_string(record, "candidate_id"),
        text=_record_string(record, "text"),
        score=_record_number(record, "score"),
        rank=_record_int(record, "rank"),
        gravity_mark=gravity_mark_from_record(gravity_mark),
    )


def mode3_trace_fixture_from_record(record: Mapping[str, object]) -> tuple[GravityWell, tuple[RecallCandidate, ...]]:
    if not isinstance(record, Mapping):
        raise ValueError("fixture record must be a mapping")
    well_record = record.get("gravity_well")
    candidates_record = record.get("candidates")
    if not isinstance(well_record, Mapping):
        raise ValueError("gravity_well must be a mapping")
    if not isinstance(candidates_record, list):
        raise ValueError("candidates must be a list")
    well = gravity_well_from_record(well_record)
    candidates = tuple(recall_candidate_from_record(candidate) for candidate in candidates_record)
    return (well, candidates)


def validate_mode3_trace_record(record: Mapping[str, object]) -> None:
    if not isinstance(record, Mapping):
        raise ValueError("mode3 trace record must be a mapping")
    for key in ("schema", "status", "well", "candidate_count", "trace_item_count", "drift_class_counts", "items"):
        if key not in record:
            raise ValueError(f"missing mode3 trace field: {key}")
    if record["schema"] != SCHEMA:
        raise ValueError("unsupported mode3 trace schema")
    if record["status"] != STATUS:
        raise ValueError("mode3 trace status must be experimental_internal_only")
    _reject_forbidden_policy_keys(record)
    if not _is_json_primitive(record):
        raise ValueError("mode3 trace record must be JSON-primitive serializable")


def _trace_item(well: GravityWell, candidate: RecallCandidate) -> GravityTraceItem:
    report = create_gravity_report(well, candidate.gravity_mark)
    return GravityTraceItem(
        candidate_id=candidate.candidate_id,
        rank=candidate.rank,
        score=candidate.score,
        text=candidate.text,
        gravity_report=report,
        llm_visibility_hint=_visibility_hint(report.drift_class),
    )


def _visibility_hint(drift_class: str) -> str:
    hints = {
        "core": "inside_entry_column",
        "halo": "entry_halo",
        "near_drift": "near_lateral_drift",
        "far_coherent": "far_but_semantically_coherent",
        "far_weak": "far_and_weak",
        "semantic_break": "semantic_break_visible",
        "chart_jump": "chart_jump_visible",
        "unglued": "unglued_visible",
    }
    try:
        return hints[drift_class]
    except KeyError as exc:
        raise ValueError(f"unsupported drift_class: {drift_class}") from exc


def _drift_class_counts(reports: Sequence[GravityReport]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for report in reports:
        counts[report.drift_class] = counts.get(report.drift_class, 0) + 1
    return dict(sorted(counts.items()))


def _reject_forbidden_policy_keys(value: object) -> None:
    forbidden = {"trust", "memory_status", "write_permission", "rejection"}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in forbidden:
                raise ValueError(f"forbidden mode3 trace key: {key}")
            _reject_forbidden_policy_keys(item)
    elif isinstance(value, list):
        for item in value:
            _reject_forbidden_policy_keys(item)


def _record_string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _record_number(record: Mapping[str, object], key: str) -> float:
    value = record.get(key)
    _require_number(value, key)
    return float(value)


def _record_int(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    _require_positive_int(value, key)
    return int(value)


def _require_non_empty_string(value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _require_number(value: object, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")


def _require_positive_int(value: object, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{label} must be a positive integer")


def _is_json_primitive(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_primitive(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_primitive(item) for key, item in value.items())
    return False


__all__ = [
    "GravityTraceItem",
    "Mode3TraceResult",
    "RecallCandidate",
    "build_mode3_trace",
    "gravity_trace_item_to_record",
    "mode3_trace_fixture_from_record",
    "mode3_trace_result_to_record",
    "recall_candidate_from_record",
    "recall_candidate_to_record",
    "validate_mode3_trace_record",
]
