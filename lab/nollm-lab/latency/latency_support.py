from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable


COMMIT_SCHEMA = "nollm_memory_commit_latency_v1"
RECALL_SCHEMA = "nollm_memory_recall_latency_v1"
SCHEMAS = frozenset({COMMIT_SCHEMA, RECALL_SCHEMA})


class LatencyEvidenceError(ValueError):
    pass


def load_records(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LatencyEvidenceError(f"line {line_number}: invalid JSON") from exc
        if type(value) is not dict or value.get("schema_version") not in SCHEMAS:
            raise LatencyEvidenceError(f"line {line_number}: invalid schema_version")
        if type(value.get("event_type")) is not str or type(value.get("event_epoch_ms")) not in {int, float}:
            raise LatencyEvidenceError(f"line {line_number}: missing event identity")
        if type(value.get("scenario_id")) is not str or type(value.get("validation_run_id")) is not str:
            raise LatencyEvidenceError(f"line {line_number}: missing validation identity")
        _reject_negative_durations(value, f"line {line_number}")
        records.append(value)
    if not records:
        raise LatencyEvidenceError("latency Evidence is empty")
    return records


def _reject_negative_durations(value: object, location: str) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if (key.endswith("_ms") or key.endswith("_us")) and type(item) in {int, float} and item < 0:
                raise LatencyEvidenceError(f"{location}: negative duration {key}")
            _reject_negative_durations(item, location)
    elif type(value) is list:
        for item in value:
            _reject_negative_durations(item, location)


def nearest_rank(values: Iterable[float], percentile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("values are required")
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def distribution(values: Iterable[float]) -> dict[str, object]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return {"status": "insufficient sample", "n": 0}
    result: dict[str, object] = {
        "status": "observed",
        "n": len(ordered),
        "min_ms": ordered[0],
        "median_ms": nearest_rank(ordered, 0.50),
        "max_ms": ordered[-1],
    }
    if len(ordered) >= 5:
        result.update({"p50_ms": nearest_rank(ordered, 0.50), "p90_ms": nearest_rank(ordered, 0.90)})
        result["p95_ms"] = nearest_rank(ordered, 0.95) if len(ordered) >= 20 else "not statistically meaningful"
    return result


def _number(value: object) -> float | None:
    return float(value) if type(value) in {int, float} else None


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    formations: dict[str, dict[str, object]] = {}
    placements: dict[str, list[dict[str, object]]] = {}
    recall_terminals: dict[str, dict[str, object]] = {}
    visible: dict[str, dict[str, object]] = {}
    write_host_turn_ids: set[str] = set()
    recall_host_turn_ids: set[str] = set()
    for record in records:
        if record.get("scenario_id") == "PREHEAT":
            continue
        event_type = record["event_type"]
        if event_type == "host_turn_receipt" and type(record.get("session_key_sha256")) is str:
            scenario = str(record.get("scenario_id", ""))
            if scenario.startswith("W_"):
                write_host_turn_ids.add(str(record["session_key_sha256"]))
            elif scenario.startswith("R_"):
                recall_host_turn_ids.add(str(record["session_key_sha256"]))
            continue
        if record["schema_version"] == COMMIT_SCHEMA:
            if not str(record.get("scenario_id", "")).startswith("W_"):
                continue
            turn_id = record.get("turn_correlation_id")
            if type(turn_id) is not str:
                continue
            if event_type == "formation_completed":
                formations[turn_id] = record
            elif event_type == "placement_terminal":
                placements.setdefault(turn_id, []).append(record)
        else:
            scenario = str(record.get("scenario_id", ""))
            if not scenario.startswith("R_"):
                continue
            request_id = record.get("recall_request_id")
            if type(request_id) is not str:
                continue
            if event_type == "recall_terminal":
                recall_terminals[request_id] = record
            elif event_type == "visible_answer":
                visible[request_id] = record

    write_attempts = []
    write_samples = []
    for turn_id, formation in sorted(formations.items()):
        turn_placements = sorted(placements.get(turn_id, []), key=lambda item: int(item.get("statement_index", 0)))
        durable = [item for item in turn_placements if item.get("final_outcome") == "applied" and type(item.get("durable_commit")) is dict and item["durable_commit"].get("verified") is True]
        durable_times = [float(item["turn_to_statement_durable_ms"]) for item in durable if type(item.get("turn_to_statement_durable_ms")) in {int, float}]
        sample = {
            "turn_correlation_id": turn_id,
            "scenario_id": formation.get("scenario_id"),
            "statement_count": formation.get("formation_statement_count", 0),
            "accepted_statement_count": len(durable),
            "turn_to_first_durable_ms": min(durable_times) if durable_times else None,
            "turn_to_all_durable_ms": max(durable_times) if durable_times else None,
            "formation_provider_total_ms": formation.get("formation_provider_total_ms"),
            "formation_local_total_ms": formation.get("formation_local_total_ms"),
            "placements": turn_placements,
            "turn_visible_source_valid": formation.get("turn_visible_source_valid") is True,
        }
        write_attempts.append(sample)
        if sample["turn_visible_source_valid"]:
            write_samples.append(sample)

    recall_samples = []
    for request_id, terminal in sorted(recall_terminals.items()):
        answer = visible.get(request_id)
        recall_samples.append({
            "recall_request_id": request_id,
            "scenario_id": terminal.get("scenario_id"),
            "outcome": terminal.get("recall_outcome"),
            "query_to_injection_ready_ms": terminal.get("query_to_injection_ready_ms"),
            "query_to_none_terminal_ms": terminal.get("query_to_none_terminal_ms"),
            "query_to_visible_answer_ms": None if answer is None else answer.get("query_to_visible_answer_ms"),
            "injection_to_visible_answer_ms": None if answer is None else answer.get("injection_to_visible_answer_ms"),
            "visible_answer_correlated": False if answer is None else answer.get("visible_answer_correlated") is True,
            "selected_statement_count": terminal.get("selected_statement_count", 0),
            "operation_timing": terminal.get("operation_timing", {}),
        })

    first = [value for sample in write_samples if (value := _number(sample["turn_to_first_durable_ms"])) is not None]
    all_durable = [value for sample in write_samples if (value := _number(sample["turn_to_all_durable_ms"])) is not None]
    injection = [value for sample in recall_samples if (value := _number(sample["query_to_injection_ready_ms"])) is not None]
    visible_latency = [value for sample in recall_samples if (value := _number(sample["query_to_visible_answer_ms"])) is not None]
    none_latency = [value for sample in recall_samples if (value := _number(sample["query_to_none_terminal_ms"])) is not None]
    write_provider_ms = sum(float(sample.get("formation_provider_total_ms") or 0) for sample in write_attempts)
    write_local_ms = sum(float(sample.get("formation_local_total_ms") or 0) for sample in write_attempts)
    for sample in write_attempts:
        for placement in sample["placements"]:
            write_provider_ms += float(placement.get("placement_provider_total_ms") or 0)
            write_local_ms += float(placement.get("placement_local_total_ms") or 0)
    recall_provider_ms = 0.0
    recall_total_ms = 0.0
    for sample in recall_samples:
        timing = sample["operation_timing"] if type(sample["operation_timing"]) is dict else {}
        recall_provider_ms += sum(float(timing.get(key) or 0) for key in ("surface_traversal_provider_ms", "traversal_correction_ms", "recall_selection_provider_ms"))
        recall_total_ms += float(timing.get("total_operation_ms") or 0)
    write_total_ms = write_provider_ms + write_local_ms
    cold_relevant = [sample for sample in recall_samples if sample["scenario_id"] == "R_RELEVANT_COLD" and sample["outcome"] == "inject"]
    warm_relevant = [sample for sample in recall_samples if sample["scenario_id"] == "R_RELEVANT_WARM" and sample["outcome"] == "inject"]
    dense_relevant = [sample for sample in recall_samples if sample["scenario_id"] == "R_DENSE_HIDDEN_PREVIEW" and sample["outcome"] == "inject"]
    explicit_none = [sample for sample in recall_samples if sample["scenario_id"] == "R_NONE" and sample["outcome"] == "none"]
    visible_correlated_count = sum(sample["visible_answer_correlated"] is True for sample in recall_samples)
    durable_attempt_count = sum(int(sample["accepted_statement_count"]) > 0 for sample in write_attempts)
    return {
        "schema_version": "nollm_memory_latency_summary_v1",
        "record_count": len(records),
        "evidence_sha256": None,
        "write_turn_attempt_count": len(write_attempts),
        "write_host_turn_count": len(write_host_turn_ids),
        "write_turn_count": len(write_samples),
        "durable_memory_attempt_turn_count": durable_attempt_count,
        "durable_memory_turn_count": len(first),
        "recall_query_count": len(recall_samples),
        "recall_host_turn_count": len(recall_host_turn_ids),
        "visible_answer_correlated_count": visible_correlated_count,
        "none_recall_count": sum(sample["outcome"] == "none" for sample in recall_samples),
        "write_latency": {"turn_to_first_durable": distribution(first), "turn_to_all_durable": distribution(all_durable)},
        "recall_latency": {"query_to_injection_ready": distribution(injection), "query_to_visible_answer": distribution(visible_latency), "query_to_none_terminal": distribution(none_latency)},
        "cohorts": {
            "cold_relevant_count": len(cold_relevant),
            "warm_relevant_count": len(warm_relevant),
            "dense_hidden_preview_inject_count": len(dense_relevant),
            "explicit_none_count": len(explicit_none),
            "max_selected_statement_count": max((int(sample["selected_statement_count"]) for sample in recall_samples), default=0),
            "cold_query_to_injection": distribution(sample["query_to_injection_ready_ms"] for sample in cold_relevant if type(sample["query_to_injection_ready_ms"]) in {int, float}),
            "warm_query_to_injection": distribution(sample["query_to_injection_ready_ms"] for sample in warm_relevant if type(sample["query_to_injection_ready_ms"]) in {int, float}),
            "dense_query_to_injection": distribution(sample["query_to_injection_ready_ms"] for sample in dense_relevant if type(sample["query_to_injection_ready_ms"]) in {int, float}),
        },
        "stage_shares": {
            "write_provider_total_ms": write_provider_ms,
            "write_local_total_ms": write_local_ms,
            "write_provider_share": None if write_total_ms == 0 else write_provider_ms / write_total_ms,
            "recall_provider_total_ms": recall_provider_ms,
            "recall_local_total_ms": max(0.0, recall_total_ms - recall_provider_ms),
            "recall_provider_share": None if recall_total_ms == 0 else recall_provider_ms / recall_total_ms,
            "main_agent_share": "insufficient sample: message_sent not observed",
        },
        "completion_gates": {
            "timing_semantics_corrected": True,
            "write_host_turns_at_least_12": len(write_host_turn_ids) >= 12,
            "formal_message_sent_write_turns_at_least_12": len(write_samples) >= 12,
            "durable_memory_turns_at_least_8": len(first) >= 8,
            "recall_queries_at_least_12": len(recall_samples) >= 12,
            "cold_relevant_at_least_2": len(cold_relevant) >= 2,
            "dense_hidden_preview_at_least_2": len(dense_relevant) >= 2,
            "explicit_none_at_least_2": len(explicit_none) >= 2,
            "query_to_injection_evidence": len(injection) > 0,
            "query_to_visible_evidence": visible_correlated_count > 0,
        },
        "write_attempts": write_attempts,
        "write_samples": write_samples,
        "recall_samples": recall_samples,
    }


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def evidence_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
