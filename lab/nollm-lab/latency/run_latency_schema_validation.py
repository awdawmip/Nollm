from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from latency_support import COMMIT_SCHEMA, RECALL_SCHEMA, load_records, summarize


def main() -> None:
    records = [
        {"schema_version": COMMIT_SCHEMA, "event_type": "formation_completed", "event_epoch_ms": 1000, "scenario_id": "W_NEW_SINGLE", "validation_run_id": "fixture", "turn_correlation_id": "t1", "turn_visible_source_valid": True, "formation_statement_count": 1, "formation_provider_total_ms": 10, "formation_local_total_ms": 1},
        {"schema_version": COMMIT_SCHEMA, "event_type": "placement_terminal", "event_epoch_ms": 1020, "scenario_id": "W_NEW_SINGLE", "validation_run_id": "fixture", "turn_correlation_id": "t1", "statement_index": 0, "final_outcome": "applied", "turn_to_statement_durable_ms": 20, "durable_commit": {"verified": True}},
        {"schema_version": RECALL_SCHEMA, "event_type": "recall_terminal", "event_epoch_ms": 2000, "scenario_id": "R_RELEVANT_WARM", "validation_run_id": "fixture", "recall_request_id": "r1", "recall_outcome": "inject", "query_to_injection_ready_ms": 30, "selected_statement_count": 1},
        {"schema_version": RECALL_SCHEMA, "event_type": "visible_answer", "event_epoch_ms": 2050, "scenario_id": "R_RELEVANT_WARM", "validation_run_id": "fixture", "recall_request_id": "r1", "visible_answer_correlated": True, "query_to_visible_answer_ms": 50, "injection_to_visible_answer_ms": 20},
    ]
    with TemporaryDirectory(prefix="nollm-latency-schema-") as temporary:
        path = Path(temporary) / "evidence.jsonl"
        path.write_text("".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records), encoding="utf-8")
        summary = summarize(load_records(path))
    if summary["durable_memory_turn_count"] != 1 or summary["visible_answer_correlated_count"] != 1:
        raise AssertionError("latency schema fixture did not aggregate exactly")
    print(json.dumps({"schema_version": "nollm_latency_schema_validation_v1", "status": "pass", "record_count": len(records)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
