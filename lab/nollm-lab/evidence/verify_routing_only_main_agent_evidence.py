from __future__ import annotations

import json
from pathlib import Path

from recall_lens.rev5_metric_truth import declared_target_metric_valid, leakage_metric_valid


SCHEMA = "nollm_aold_routing_only_declared_target_simulation_v3"


def verify(evidence_path: Path, summary_path: Path) -> dict[str, object]:
    events = [json.loads(line) for line in evidence_path.read_text(encoding="utf-8").splitlines()]
    if not events or any(event.get("schema_version") != SCHEMA for event in events):
        raise ValueError("routing-only Evidence schema mismatch")
    fields = [event for event in events if event.get("event") == "field"]
    registries = [event for event in events if event.get("event") == "query_registry"]
    summaries = [event for event in events if event.get("event") == "summary"]
    if len(fields) != 1 or len(registries) != 1 or registries[0].get("declared_before_recall") is not True or len(summaries) != 1:
        raise ValueError("field, pre-Recall registry, and summary are required")
    queries = [event for event in events if event.get("event") == "query"]
    defaults = [event for event in queries if event.get("kind") in {"relevant", "relation-entry-target-hidden", "dense-hidden-target"}]
    expands = [event for event in queries if event.get("kind") == "same-entry-expand"]
    restarts = [event for event in queries if event.get("kind") == "cold-restart"]
    if len(defaults) != 40 or len(expands) != 5 or len(restarts) != 2:
        raise ValueError("declared query inventory mismatch")
    if any(not declared_target_metric_valid(event) or not leakage_metric_valid(event) for event in defaults):
        raise ValueError("default target or leakage evidence is not recomputable")
    if any(not declared_target_metric_valid(event) for event in [*expands, *restarts]):
        raise ValueError("expand or restart target was not declared")
    field = fields[0]
    computed = {
        "target_reach": sum(event.get("target_reached") is True for event in defaults) / len(defaults),
        "expanded_target_reach": sum(event.get("expanded_target_reached") is True for event in expands) / len(expands),
        "cold_restart_reach": sum(event.get("target_reached") is True for event in restarts) / len(restarts),
        "max_unrelated_leakage_count": max(event["unrelated_leakage_count"] for event in defaults),
        "routing_card_count": field["routing_card_count"],
        "routing_text_chars": field["routing_text_chars"],
        "visible_json_utf8_bytes": field["visible_json_utf8_bytes"],
        "full_statement_leakage_count": field["full_statement_leakage_count"],
    }
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary != {key: value for key, value in summaries[0].items() if key != "event"}:
        raise ValueError("summary file does not match Evidence")
    if any(summary.get(key) != value for key, value in computed.items()):
        raise ValueError("summary metrics do not recompute")
    if computed["routing_text_chars"] > 3000 or computed["visible_json_utf8_bytes"] > 8192 or computed["full_statement_leakage_count"] != 0:
        raise ValueError("routing-only Surface budget or leakage gate failed")
    if summary.get("provider_backed_statement_count") != 0 or summary.get("provider_gate_met") is not False:
        raise ValueError("offline Evidence cannot claim Provider completion")
    if summary.get("semantic_none_metric_available") is not False or summary.get("semantic_product_gate_met") is not False:
        raise ValueError("offline Evidence cannot claim semantic product completion")
    return computed


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    print(json.dumps(verify(
        root / "validation/aold_routing_only_real_main_agent_live_20260722.jsonl",
        root / "validation/aold_routing_only_real_main_agent_live_summary_20260722.json",
    ), sort_keys=True))
