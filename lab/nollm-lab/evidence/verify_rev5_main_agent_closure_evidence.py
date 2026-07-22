from __future__ import annotations

import json
from pathlib import Path

from recall_lens.rev5_metric_truth import declared_target_metric_valid, leakage_metric_valid


SCHEMA = "nollm_aold_declared_target_locality_simulation_v2"


def verify(evidence_path: Path, summary_path: Path) -> dict[str, object]:
    events = [json.loads(line) for line in evidence_path.read_text(encoding="utf-8").splitlines()]
    if not events or any(event.get("schema_version") != SCHEMA for event in events):
        raise ValueError("closure Evidence schema mismatch")
    registries = [event for event in events if event.get("event") == "query_registry"]
    summaries = [event for event in events if event.get("event") == "summary"]
    if len(registries) != 1 or registries[0].get("declared_before_recall") is not True or len(summaries) != 1:
        raise ValueError("one pre-Recall registry and one summary are required")
    queries = [event for event in events if event.get("event") == "query"]
    default_queries = [event for event in queries if event.get("kind") in {"relevant", "relation-entry-target-hidden", "dense-hidden-target"}]
    expand_queries = [event for event in queries if event.get("kind") == "same-entry-expand"]
    restart_queries = [event for event in queries if event.get("kind") == "cold-restart"]
    if len(default_queries) != 40 or len(expand_queries) != 5 or len(restart_queries) != 2:
        raise ValueError("declared query inventory mismatch")
    if any(not declared_target_metric_valid(event) or not leakage_metric_valid(event) for event in default_queries):
        raise ValueError("default query target or leakage evidence is not recomputable")
    if any(not declared_target_metric_valid(event) for event in [*expand_queries, *restart_queries]):
        raise ValueError("expanded or restart target evidence is not declared")
    computed = {
        "target_reach": sum(event.get("target_reached") is True for event in default_queries) / len(default_queries),
        "expanded_target_reach": sum(event.get("expanded_target_reached") is True for event in expand_queries) / len(expand_queries),
        "cold_restart_reach": sum(event.get("target_reached") is True for event in restart_queries) / len(restart_queries),
        "max_unrelated_leakage_count": max(event["unrelated_leakage_count"] for event in default_queries),
    }
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    event_summary = {key: value for key, value in summaries[0].items() if key != "event"}
    if summary != event_summary:
        raise ValueError("summary file does not match the frozen summary event")
    if any(summary.get(key) != value for key, value in computed.items()):
        raise ValueError("summary metrics do not recompute from Evidence")
    if summary.get("provider_backed_statement_count") != 0 or summary.get("provider_gate_met") is not False:
        raise ValueError("offline Evidence cannot claim Provider completion")
    if summary.get("semantic_none_metric_available") is not False or summary.get("semantic_product_gate_met") is not False:
        raise ValueError("offline Evidence cannot claim semantic NONE or product completion")
    return computed


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    print(json.dumps(verify(
        root / "validation/aold_main_agent_provider_live_selectivity_20260722.jsonl",
        root / "validation/aold_main_agent_provider_live_selectivity_summary_20260722.json",
    ), sort_keys=True))
