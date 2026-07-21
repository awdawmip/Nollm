from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


SCHEMA_VERSION = "nollm_caold_atomic_growth_evidence_v1"
EXPECTED_GROWTH_TURNS = 9
EXPECTED_RECALL_TURNS = 6


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _read_events(path: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL at line {line_number}: {error}") from error
        if type(value) is not dict:
            raise ValueError(f"evidence line {line_number} is not an object")
        events.append(value)
    return events


def _address_text(address: object) -> str | None:
    if type(address) is not dict:
        return None
    return ":".join(str(address.get(key)) for key in ("profile_id", "chart_id", "layer", "q", "r", "phase"))


def _capture_state_snapshot(root: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    files = sorted(path for path in root.rglob("*.json") if path.is_file())
    digest = sha256()
    parsed: list[dict[str, object]] = []
    for path in files:
        payload = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8") + b"\0" + payload + b"\0")
        value = json.loads(payload)
        if type(value) is not dict:
            raise ValueError(f"capture state file is not an object: {relative}")
        parsed.append(value)
    capture_count = sum(1 for value in parsed if value.get("schema_version") == "nollm_openclaw_durable_capture_v1")
    event_count = sum(1 for value in parsed if value.get("schema_version") == "nollm_openclaw_capture_state_event_v1")
    if capture_count != EXPECTED_GROWTH_TURNS:
        raise ValueError(f"expected {EXPECTED_GROWTH_TURNS} frozen Captures, found {capture_count}")
    return parsed, {
        "sha256": digest.hexdigest(),
        "file_count": len(files),
        "capture_count": capture_count,
        "event_count": event_count,
        "bytes": sum(path.stat().st_size for path in files),
    }


def build_records(evidence_path: Path, freeze_metadata_path: Path, capture_state_root: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    evidence_bytes = evidence_path.read_bytes()
    events = _read_events(evidence_path)
    freeze = json.loads(freeze_metadata_path.read_text(encoding="utf-8"))
    digest = sha256(evidence_bytes).hexdigest()
    if freeze.get("sha256") != digest:
        raise ValueError("freeze metadata SHA-256 does not match evidence bytes")
    if freeze.get("bytes") != len(evidence_bytes):
        raise ValueError("freeze metadata byte count does not match evidence bytes")
    capture_state, capture_state_metadata = _capture_state_snapshot(capture_state_root)

    absorption_indexes = [index for index, event in enumerate(events) if event.get("stage") == "absorption_batch"]
    if len(absorption_indexes) != EXPECTED_GROWTH_TURNS:
        raise ValueError(f"expected {EXPECTED_GROWTH_TURNS} absorption batches, found {len(absorption_indexes)}")

    records: list[dict[str, object]] = [{
        "record_type": "frozen_evidence",
        "schema_version": SCHEMA_VERSION,
        "sha256": digest,
        "bytes": len(evidence_bytes),
        "line_count": len(events),
        "source_stable": freeze.get("source_stability", {}).get("stable"),
        "gateway_probe_before": freeze.get("gateway_probe_before"),
        "gateway_probe_after": freeze.get("gateway_probe_after"),
        "active_writer_paths": freeze.get("plugin_config", {}).get("active_writer_paths"),
        "capture_state": capture_state_metadata,
    }]
    growth: list[dict[str, object]] = []
    for turn_index, event_index in enumerate(absorption_indexes):
        event = events[event_index]
        outcomes = event.get("durable_outcomes")
        plans = event.get("validated_plans")
        if type(outcomes) is not list or len(outcomes) != 1 or type(plans) is not list or len(plans) != 1:
            raise ValueError(f"T{turn_index} is not one durable outcome and one validated plan")
        outcome = outcomes[0]
        plan = plans[0]
        if type(outcome) is not dict or type(plan) is not dict:
            raise ValueError(f"T{turn_index} plan or outcome is not an object")
        statement = plan.get("statement")
        commit = outcome.get("durable_commit")
        if type(statement) is not dict or type(commit) is not dict:
            raise ValueError(f"T{turn_index} lacks statement or durable commit")
        lenses = plan.get("lenses") if type(plan.get("lenses")) is list else []
        relation_groups = plan.get("relation_groups") if type(plan.get("relation_groups")) is list else []
        writer = event.get("writer_resolved") if type(event.get("writer_resolved")) is dict else {}
        cartographers = event.get("cartographer_resolved") if type(event.get("cartographer_resolved")) is list else []
        cartographer = cartographers[0] if cartographers and type(cartographers[0]) is dict else {}
        row = {
            "record_type": "growth_turn",
            "turn": f"T{turn_index}",
            "capture_ids": event.get("capture_ids"),
            "statement_id": statement.get("statement_id"),
            "statement_count": event.get("statement_count"),
            "action": outcome.get("action"),
            "placement_mode": outcome.get("placement_mode"),
            "cell": _address_text(commit.get("handle", {}).get("geometry_address") if type(commit.get("handle")) is dict else None),
            "commit_state": commit.get("commit_state"),
            "reopen_verified": commit.get("reopen_verified"),
            "relation_group_count": len(relation_groups),
            "resolved_lens_count": sum(1 for lens in lenses if type(lens) is dict and lens.get("unresolved") is False),
            "lens_count": len(lenses),
            "writer_model_ref": writer.get("resolved_model_ref"),
            "cartographer_model_ref": cartographer.get("resolved_model_ref"),
        }
        growth.append(row)
        records.append(row)

    retry_events = [event for event in capture_state if event.get("status") == "retry"]
    for event in retry_events:
        records.append({
            "record_type": "worker_retry",
            "capture_id": event.get("capture_id"),
            "attempt": event.get("attempt"),
            "batch_id": event.get("batch_id"),
            "error": event.get("error"),
        })

    recall_events = [
        event for event in events[absorption_indexes[-1] + 1:]
        if event.get("stage") == "fast_recall" and event.get("status") in {"completed", "complete_none", "completed_none"}
    ]
    if len(recall_events) != EXPECTED_RECALL_TURNS:
        raise ValueError(f"expected {EXPECTED_RECALL_TURNS} post-growth Recall events, found {len(recall_events)}")
    recalls: list[dict[str, object]] = []
    for recall_index, event in enumerate(recall_events):
        paths = event.get("selected_paths") if type(event.get("selected_paths")) is list else []
        path_lengths = [len(item.get("path", [])) for item in paths if type(item) is dict and type(item.get("path")) is list]
        row = {
            "record_type": "recall",
            "recall_index": recall_index,
            "request_id": event.get("request_id"),
            "status": event.get("status"),
            "selected_entry": _address_text(event.get("selected_entry")),
            "statement_ids": event.get("statement_ids", []),
            "path_lengths": path_lengths,
            "hidden_provider_calls": event.get("hidden_provider_calls"),
            "resolved_model_ref": event.get("resolved_model_ref"),
        }
        recalls.append(row)
        records.append(row)

    t0_statement_id = growth[0]["statement_id"]
    selected_entries = {row["selected_entry"] for row in recalls if row["selected_entry"] is not None}
    t0_recall_count = sum(1 for row in recalls if t0_statement_id in row["statement_ids"])
    nonempty_path_count = sum(1 for row in recalls for length in row["path_lengths"] if length > 0)
    provider_refs = sorted({
        ref for row in growth for ref in (row["writer_model_ref"], row["cartographer_model_ref"])
        if type(ref) is str
    })
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "RUNTIME_INTEGRITY_AND_RELATION_ENTRY_COLLISION_CHECKPOINT_AT_c40f8bf6a5be6184e5e56236c96d2817fed4bee5",
        "frozen_evidence": {"sha256": digest, "bytes": len(evidence_bytes), "line_count": len(events)},
        "frozen_capture_state": capture_state_metadata,
        "growth": {
            "capture_count": len(growth),
            "statement_count": sum(int(row["statement_count"]) for row in growth),
            "all_single_statement": all(row["statement_count"] == 1 for row in growth),
            "all_reopen_verified": all(row["reopen_verified"] is True and row["commit_state"] == "reopen_verified" for row in growth),
            "related_growth_count": sum(1 for row in growth if row["placement_mode"] == "related_growth"),
            "independent_seed_count": sum(1 for row in growth if row["placement_mode"] == "independent_seed"),
            "provider_model_refs": provider_refs,
            "retry_event_count": len(retry_events),
        },
        "recall": {
            "attempt_count": len(recalls),
            "t0_statement_id": t0_statement_id,
            "t0_recall_count": t0_recall_count,
            "nonempty_path_count": nonempty_path_count,
            "distinct_selected_entry_count": len(selected_entries),
            "none_count": sum(1 for row in recalls if row["status"] in {"complete_none", "completed_none"}),
            "single_hidden_call_max": max(int(row["hidden_provider_calls"] or 0) for row in recalls),
        },
        "gate_d": {
            "passed": False,
            "reason": "Provider atomic growth formed only one related edge; three distinct relation entries with non-empty paths to T0 were not realized.",
            "multi_cell_authorized": False,
        },
    }
    records.append({"record_type": "summary", **summary})
    return records, summary


def write_artifacts(records: list[dict[str, object]], summary: dict[str, object], jsonl_path: Path, summary_path: Path) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.write_bytes(b"\n".join(_canonical(record) for record in records) + b"\n")
    summary_path.write_bytes(_canonical(summary) + b"\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--freeze-metadata", type=Path, required=True)
    parser.add_argument("--capture-state-root", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    arguments = parser.parse_args()
    records, summary = build_records(arguments.evidence, arguments.freeze_metadata, arguments.capture_state_root)
    write_artifacts(records, summary, arguments.output_jsonl, arguments.output_summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
