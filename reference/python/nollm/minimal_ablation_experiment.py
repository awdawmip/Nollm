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

SCHEMA = "nollm.minimal_ablation_experiment.v1"
STATUS = "experimental_internal_only"
CONDITIONS = ("N0", "N1", "N2", "N3", "N4", "N5")
DEFAULT_PROFILE = "default_dream"
MEDIUM_PROFILE = "medium_practical"


@dataclass(frozen=True)
class AblationCandidate:
    candidate_id: str
    text: str
    retrieval_score: float
    gravity_mark: GravityMark
    relevance_label: str
    expected_behavior: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.candidate_id, "candidate_id")
        _require_non_empty_string(self.text, "text")
        _require_number(self.retrieval_score, "retrieval_score")
        if not isinstance(self.gravity_mark, GravityMark):
            raise ValueError("gravity_mark must be a GravityMark")
        if self.relevance_label not in ("core_relevant", "lateral_useful", "misleading", "neutral"):
            raise ValueError("unsupported relevance_label")
        if self.expected_behavior not in ("use", "caution", "ignore", "return_home_visible"):
            raise ValueError("unsupported expected_behavior")


@dataclass(frozen=True)
class AblationQuestion:
    question_id: str
    entry_query: str
    gravity_well: GravityWell
    candidates: tuple[AblationCandidate, ...]

    def __post_init__(self) -> None:
        _require_non_empty_string(self.question_id, "question_id")
        _require_non_empty_string(self.entry_query, "entry_query")
        if not isinstance(self.gravity_well, GravityWell):
            raise ValueError("gravity_well must be a GravityWell")
        if not self.candidates:
            raise ValueError("candidates must be non-empty")


@dataclass(frozen=True)
class AblationCondition:
    condition: str
    profile: str
    expose_geometry: bool
    expose_gravity: bool
    expose_return_vector: bool

    def __post_init__(self) -> None:
        if self.condition not in CONDITIONS:
            raise ValueError("unsupported ablation condition")
        _require_non_empty_string(self.profile, "profile")


def default_ablation_conditions() -> tuple[AblationCondition, ...]:
    return (
        AblationCondition("N0", DEFAULT_PROFILE, False, False, False),
        AblationCondition("N1", DEFAULT_PROFILE, True, False, False),
        AblationCondition("N2", DEFAULT_PROFILE, True, True, False),
        AblationCondition("N3", DEFAULT_PROFILE, True, True, True),
        AblationCondition("N4", MEDIUM_PROFILE, True, True, False),
        AblationCondition("N5", DEFAULT_PROFILE, True, True, False),
    )


def build_minimal_ablation_report(
    questions: Sequence[AblationQuestion],
    conditions: Sequence[AblationCondition] | None = None,
) -> dict[str, object]:
    selected_conditions = default_ablation_conditions() if conditions is None else tuple(conditions)
    selected_questions = tuple(questions)
    if not selected_questions:
        raise ValueError("questions must be non-empty")
    condition_reports = [_condition_report(condition, selected_questions) for condition in selected_conditions]
    report = {
        "schema": SCHEMA,
        "status": STATUS,
        "condition_count": len(condition_reports),
        "question_count": len(selected_questions),
        "candidate_count": sum(len(question.candidates) for question in selected_questions),
        "conditions": condition_reports,
        "summary": _summary(condition_reports),
        "forbidden_semantics": {
            "stable_recall_surface": False,
            "auto_writeback": False,
            "anchor_creation": False,
            "trust_status_mapping": False,
        },
    }
    validate_minimal_ablation_report(report)
    return report


def ablation_fixture_from_record(record: Mapping[str, object]) -> tuple[AblationQuestion, ...]:
    if not isinstance(record, Mapping):
        raise ValueError("ablation fixture must be a mapping")
    questions = record.get("questions")
    if not isinstance(questions, list):
        raise ValueError("questions must be a list")
    return tuple(_question_from_record(question) for question in questions)


def validate_minimal_ablation_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("ablation report must be a mapping")
    for key in (
        "schema",
        "status",
        "condition_count",
        "question_count",
        "candidate_count",
        "conditions",
        "summary",
        "forbidden_semantics",
    ):
        if key not in report:
            raise ValueError(f"missing ablation report field: {key}")
    if report["schema"] != SCHEMA:
        raise ValueError("unsupported ablation report schema")
    if report["status"] != STATUS:
        raise ValueError("ablation report status must be experimental_internal_only")
    forbidden = report["forbidden_semantics"]
    if not isinstance(forbidden, Mapping) or any(value is not False for value in forbidden.values()):
        raise ValueError("forbidden_semantics values must all be false")
    _reject_forbidden_policy_keys(report)
    if not _is_json_primitive(report):
        raise ValueError("ablation report must be JSON-primitive serializable")


def _condition_report(
    condition: AblationCondition,
    questions: Sequence[AblationQuestion],
) -> dict[str, object]:
    item_results = [
        _item_result(condition, question, candidate)
        for question in questions
        for candidate in question.candidates
    ]
    return {
        "condition": condition.condition,
        "profile": condition.profile,
        "question_count": len(questions),
        "candidate_count": len(item_results),
        "drift_class_distribution": _drift_class_distribution(item_results),
        "metrics": _metrics(condition, item_results),
        "failures": _failures(condition, item_results),
        "items": item_results,
    }


def _item_result(
    condition: AblationCondition,
    question: AblationQuestion,
    candidate: AblationCandidate,
) -> dict[str, object]:
    well = _well_for_profile(question.gravity_well, condition.profile)
    mark = _mark_for_profile(candidate.gravity_mark, condition.profile)
    gravity_report = create_gravity_report(well, mark)
    record: dict[str, object] = {
        "question_id": question.question_id,
        "candidate_id": candidate.candidate_id,
        "retrieval_score": candidate.retrieval_score,
        "relevance_label": candidate.relevance_label,
        "expected_behavior": candidate.expected_behavior,
        "visible": {
            "retrieval_score": True,
            "geometry_mark": condition.expose_geometry,
            "gravity_report": condition.expose_gravity,
            "return_vector_placeholder": condition.expose_return_vector,
        },
        "candidate_action": _proxy_action(condition, gravity_report, candidate),
    }
    if condition.expose_geometry:
        record["geometry_mark"] = {
            "geometry_profile": mark.geometry_profile,
            "chart_id": mark.chart_id,
            "layer": mark.layer,
            "q": mark.q,
            "r": mark.r,
        }
    if condition.expose_gravity:
        record["gravity_report"] = gravity_report_to_record(gravity_report)
    if condition.expose_return_vector:
        record["return_vector"] = {
            "visible": True,
            "placeholder": "return_home_visible",
            "commands_return": False,
        }
    return record


def _metrics(condition: AblationCondition, item_results: Sequence[Mapping[str, object]]) -> dict[str, object]:
    gravity_visible = condition.expose_gravity
    return {
        "drift_visibility_gain": sum(1 for item in item_results if gravity_visible and _gravity_report(item) is not None),
        "useful_lateral_discovery_visible": sum(
            1
            for item in item_results
            if gravity_visible
            and item["relevance_label"] == "lateral_useful"
            and _drift_class(item) in ("near_drift", "far_coherent")
        ),
        "over_drift_risk_flagged": sum(
            1
            for item in item_results
            if gravity_visible
            and item["relevance_label"] == "misleading"
            and _drift_class(item) in ("far_weak", "semantic_break", "unglued", "chart_jump")
        ),
        "semantic_break_visible": sum(1 for item in item_results if gravity_visible and _drift_class(item) == "semantic_break"),
        "return_vector_visible": sum(1 for item in item_results if condition.expose_return_vector),
        "geometry_only_visibility": sum(1 for item in item_results if condition.expose_geometry and not gravity_visible),
    }


def _failures(condition: AblationCondition, item_results: Sequence[Mapping[str, object]]) -> list[str]:
    failures: list[str] = []
    if condition.expose_gravity:
        for item in item_results:
            if item["expected_behavior"] == "caution" and item["candidate_action"] != "caution_visible":
                failures.append(f"{item['question_id']}:{item['candidate_id']}:caution_not_visible")
    return failures


def _proxy_action(
    condition: AblationCondition,
    gravity_report: GravityReport,
    candidate: AblationCandidate,
) -> str:
    if not condition.expose_gravity:
        return "score_visible_only" if not condition.expose_geometry else "geometry_visible_only"
    if gravity_report.drift_class in ("semantic_break", "far_weak", "unglued", "chart_jump"):
        return "caution_visible"
    if candidate.relevance_label == "lateral_useful" and gravity_report.drift_class in ("near_drift", "far_coherent"):
        return "lateral_discovery_visible"
    return "use_visible"


def _summary(condition_reports: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_condition = {str(report["condition"]): report for report in condition_reports}
    return {
        "n0_vs_n2": _metric_delta(by_condition, "N0", "N2", "drift_visibility_gain"),
        "n2_vs_n3": _metric_delta(by_condition, "N2", "N3", "return_vector_visible"),
        "n4_vs_n5": {
            "metric": "profile_branch_comparison",
            "medium_practical_profile": MEDIUM_PROFILE,
            "default_dream_profile": DEFAULT_PROFILE,
            "medium_practical": _summary_metrics(by_condition.get("N4")),
            "default_dream": _summary_metrics(by_condition.get("N5")),
        },
    }


def _metric_delta(
    by_condition: Mapping[str, Mapping[str, object]],
    before: str,
    after: str,
    metric: str,
) -> dict[str, object]:
    before_value = _condition_metric(by_condition.get(before), metric)
    after_value = _condition_metric(by_condition.get(after), metric)
    return {
        "metric": metric,
        before: before_value,
        after: after_value,
        "delta": after_value - before_value,
    }


def _summary_metrics(report: Mapping[str, object] | None) -> dict[str, object]:
    if report is None:
        return {}
    metrics = report.get("metrics")
    if not isinstance(metrics, Mapping):
        return {}
    return {
        "useful_lateral_discovery_visible": metrics.get("useful_lateral_discovery_visible", 0),
        "over_drift_risk_flagged": metrics.get("over_drift_risk_flagged", 0),
        "semantic_break_visible": metrics.get("semantic_break_visible", 0),
    }


def _condition_metric(report: Mapping[str, object] | None, metric: str) -> int:
    if report is None:
        return 0
    metrics = report.get("metrics")
    if not isinstance(metrics, Mapping):
        return 0
    value = metrics.get(metric, 0)
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0


def _drift_class_distribution(item_results: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in item_results:
        drift_class = _drift_class(item)
        if drift_class is not None:
            counts[drift_class] = counts.get(drift_class, 0) + 1
    return dict(sorted(counts.items()))


def _drift_class(item: Mapping[str, object]) -> str | None:
    report = _gravity_report(item)
    if report is None:
        return None
    drift_class = report.get("drift_class")
    return drift_class if isinstance(drift_class, str) else None


def _gravity_report(item: Mapping[str, object]) -> Mapping[str, object] | None:
    report = item.get("gravity_report")
    return report if isinstance(report, Mapping) else None


def _question_from_record(record: object) -> AblationQuestion:
    if not isinstance(record, Mapping):
        raise ValueError("question must be a mapping")
    well_record = record.get("gravity_well")
    candidates_record = record.get("candidates")
    if not isinstance(well_record, Mapping):
        raise ValueError("gravity_well must be a mapping")
    if not isinstance(candidates_record, list):
        raise ValueError("candidates must be a list")
    return AblationQuestion(
        question_id=_record_string(record, "question_id"),
        entry_query=_record_string(record, "entry_query"),
        gravity_well=gravity_well_from_record(well_record),
        candidates=tuple(_candidate_from_record(candidate) for candidate in candidates_record),
    )


def _candidate_from_record(record: object) -> AblationCandidate:
    if not isinstance(record, Mapping):
        raise ValueError("candidate must be a mapping")
    mark_record = record.get("gravity_mark")
    if not isinstance(mark_record, Mapping):
        raise ValueError("gravity_mark must be a mapping")
    return AblationCandidate(
        candidate_id=_record_string(record, "candidate_id"),
        text=_record_string(record, "text"),
        retrieval_score=_record_number(record, "retrieval_score"),
        gravity_mark=gravity_mark_from_record(mark_record),
        relevance_label=_record_string(record, "relevance_label"),
        expected_behavior=_record_string(record, "expected_behavior"),
    )


def _well_for_profile(well: GravityWell, profile: str) -> GravityWell:
    record = gravity_well_to_record(well)
    record["geometry_profile"] = profile
    return gravity_well_from_record(record)


def _mark_for_profile(mark: GravityMark, profile: str) -> GravityMark:
    record = gravity_mark_to_record(mark)
    record["geometry_profile"] = profile
    return gravity_mark_from_record(record)


def _record_string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _record_number(record: Mapping[str, object], key: str) -> float:
    value = record.get(key)
    _require_number(value, key)
    return float(value)


def _require_non_empty_string(value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _require_number(value: object, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")


def _reject_forbidden_policy_keys(value: object) -> None:
    forbidden = {"trust", "memory_status", "write_permission", "rejection"}
    allowed_path = ("forbidden_semantics", "trust_status_mapping")
    _reject_forbidden_policy_keys_at(value, (), forbidden, allowed_path)


def _reject_forbidden_policy_keys_at(
    value: object,
    path: tuple[str, ...],
    forbidden: set[str],
    allowed_path: tuple[str, str],
) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            next_path = path + (key,)
            if key in forbidden and next_path != allowed_path:
                raise ValueError(f"forbidden ablation report key: {key}")
            _reject_forbidden_policy_keys_at(item, next_path, forbidden, allowed_path)
    elif isinstance(value, list):
        for item in value:
            _reject_forbidden_policy_keys_at(item, path, forbidden, allowed_path)


def _is_json_primitive(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_primitive(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_primitive(item) for key, item in value.items())
    return False


__all__ = [
    "AblationCandidate",
    "AblationCondition",
    "AblationQuestion",
    "DEFAULT_PROFILE",
    "MEDIUM_PROFILE",
    "STATUS",
    "SCHEMA",
    "ablation_fixture_from_record",
    "build_minimal_ablation_report",
    "default_ablation_conditions",
    "validate_minimal_ablation_report",
]
