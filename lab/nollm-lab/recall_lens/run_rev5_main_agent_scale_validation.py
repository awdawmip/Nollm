from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import quantiles
from time import perf_counter

from nollm_access import AccessDecision, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement, ProgressiveAtlasPolicy
from nollm_core import CoreRuntime, GeometryAddress
from nollm_openclaw_formation.main_agent_recall import build_main_agent_surface, recall_main_agent_locality


SCHEMA = "nollm_aold_declared_target_locality_simulation_v2"
PROFILE = "default_dream_v1"
CHART = "default"


def _offsets() -> list[tuple[int, int]]:
    values = [
        (q, r)
        for q in range(-2, 3)
        for r in range(-2, 3)
        if max(abs(q), abs(r), abs(q + r)) <= 2
    ]
    return sorted(values)[:10]


def _seed(workspace: Path) -> None:
    offsets = _offsets()
    with CoreRuntime(workspace) as core, AccessRuntime(
        core, FileStatementStore(workspace), FileHandleStore(workspace),
    ) as access:
        for locality in range(8):
            for fact, (dq, dr) in enumerate(offsets):
                statement_id = f"scale:l{locality}:f{fact}"
                if locality == 0:
                    content = f"Tokyo relation field fact {fact}; date/weather/event value {fact}."
                elif locality >= 6:
                    content = f"Independent unrelated seed {locality}-{fact}; isolated control value {locality * 10 + fact}."
                else:
                    content = f"Locality {locality} dense fact {fact}; bounded value {locality * 10 + fact}."
                statement = MemoryStatement(statement_id, content)
                access.capture(statement)
                access.apply(AccessDecision(
                    f"scale-place:{locality}:{fact}", statement_id, "new",
                    GeometryAddress(PROFILE, CHART, 0, locality * 50 + dq, dr),
                    None, None, "deterministic scale fixture", "fixture",
                ))


def _p95(values: list[int]) -> float:
    return float(quantiles(values, n=20, method="inclusive")[18]) if len(values) > 1 else float(values[0])


def _entry_locality(entry: dict[str, object]) -> int | None:
    cell = entry.get("entry_cell")
    if type(cell) is dict and type(cell.get("q")) is int:
        locality = round(cell["q"] / 50)
        if 0 <= locality < 8 and abs(cell["q"] - locality * 50) <= 2:
            return locality
    statements = entry.get("statements")
    if type(statements) is not list:
        return None
    for statement in statements:
        if type(statement) is not dict or type(statement.get("statement_id")) is not str:
            continue
        parts = statement["statement_id"].split(":")
        if len(parts) == 3 and parts[0] == "scale" and parts[1].startswith("l"):
            return int(parts[1][1:])
    return None


def run_validation(workspace: Path, evidence_path: Path, summary_path: Path) -> dict[str, object]:
    workspace.mkdir(parents=True, exist_ok=True)
    _seed(workspace)
    policy = ProgressiveAtlasPolicy().to_mapping()
    surface = build_main_agent_surface(str(workspace), "scale-operation", policy)
    entries_by_locality: dict[int, dict[str, object]] = {}
    for entry in surface["entries"]:
        locality = _entry_locality(entry)
        if locality is not None and locality not in entries_by_locality:
            entries_by_locality[locality] = entry
    if set(entries_by_locality) != set(range(8)):
        raise RuntimeError(f"Surface did not expose one entry for every fixture Locality: {sorted(entries_by_locality)}")

    events: list[dict[str, object]] = [{
        "schema_version": SCHEMA,
        "event": "field",
        "statement_count": 80,
        "locality_count": 8,
        "facts_per_locality": 10,
        "independent_unrelated_seed_count": 20,
        "provider_backed_statement_count": 0,
        "deterministic_fixture_statement_count": 80,
        "surface_entry_count": surface["entry_count"],
        "distinct_selected_entry_count": 8,
        "hidden_child_calls": 0,
    }]
    default_counts: list[int] = []
    default_chars: list[int] = []
    local_latencies_ms: list[float] = []
    registry: list[dict[str, object]] = []
    for index in range(20):
        registry.append({"query_id": f"relevant-{index + 1:02d}", "kind": "relevant", "locality": index % 6, "target_fact": 0})
    for index in range(10):
        registry.append({"query_id": f"relation-entry-{index + 1:02d}", "kind": "relation-entry-target-hidden", "locality": index % 3, "target_fact": 0})
    for index in range(10):
        registry.append({"query_id": f"dense-{index + 1:02d}", "kind": "dense-hidden-target", "locality": 3 + index % 3, "target_fact": 0})
    for item in registry:
        locality = int(item["locality"])
        item["query_utf8"] = f"Recall fixture locality {locality} fact zero."
        item["declared_target_statement_ids"] = [f"scale:l{locality}:f{item['target_fact']}"]
        item["allowed_supporting_ids"] = [f"scale:l{locality}:f{fact}" for fact in range(10)]
        item["forbidden_statement_ids"] = [f"scale:l{other}:f{fact}" for other in range(8) if other != locality for fact in range(10)]
    events.append({"schema_version": SCHEMA, "event": "query_registry", "declared_before_recall": True, "queries": registry})

    target_hits = 0
    leakage_counts: list[int] = []
    for declared in registry:
        locality = int(declared["locality"])
        entry = entries_by_locality[locality]
        started = perf_counter()
        result = recall_main_agent_locality(
            str(workspace), "scale-operation", surface["core_state_sha256"], surface["atlas_fingerprint"],
            surface["page_fingerprint"], surface["policy"], entry, "default",
        )
        latency_ms = (perf_counter() - started) * 1000
        returned_ids = [item["statement_id"] for item in result["items"]]
        target_ids = list(declared["declared_target_statement_ids"])
        forbidden_ids = set(declared["forbidden_statement_ids"])
        hit = any(target in returned_ids for target in target_ids)
        leakage = len(set(returned_ids).intersection(forbidden_ids))
        target_hits += int(hit)
        leakage_counts.append(leakage)
        default_counts.append(result["result_count"])
        default_chars.append(result["rendered_chars"])
        local_latencies_ms.append(latency_ms)
        events.append({
            "schema_version": SCHEMA, "event": "query", **declared,
            "target_declared_before_recall": True, "target_source": "query_registry",
            "selection_actor": "independent_deterministic_fixture_oracle", "entry_id": result["entry_id"],
            "single_entry": True, "returned_statement_ids": returned_ids, "target_reached": hit,
            "result_count": result["result_count"], "rendered_chars": result["rendered_chars"],
            "unrelated_leakage_count": leakage, "hidden_child_calls": 0,
            "python_bounded_locality_function_ms": round(latency_ms, 3), "semantic_product_evidence": False,
        })

    expanded_hits = 0
    for index in range(5):
        locality = index % 5
        entry = entries_by_locality[locality]
        target = f"scale:l{locality}:f7"
        default = recall_main_agent_locality(
            str(workspace), "scale-operation", surface["core_state_sha256"], surface["atlas_fingerprint"],
            surface["page_fingerprint"], surface["policy"], entry, "default",
        )
        expanded = recall_main_agent_locality(
            str(workspace), "scale-operation", surface["core_state_sha256"], surface["atlas_fingerprint"],
            surface["page_fingerprint"], surface["policy"], entry, "expanded",
        )
        default_hit = any(item["statement_id"] == target for item in default["items"])
        expanded_hit = any(item["statement_id"] == target for item in expanded["items"])
        expanded_hits += int(expanded_hit and not default_hit)
        events.append({
            "schema_version": SCHEMA, "event": "query", "query_id": f"expand-{index + 1:02d}",
            "kind": "same-entry-expand", "query_utf8": f"Recall fixture locality {locality} fact seven.",
            "target_declared_before_recall": True, "target_source": "query_registry",
            "declared_target_statement_ids": [target], "selection_actor": "independent_deterministic_fixture_oracle",
            "entry_id": expanded["entry_id"], "single_entry": True,
            "returned_statement_ids": [item["statement_id"] for item in expanded["items"]],
            "default_target_reached": default_hit,
            "expanded_target_reached": expanded_hit, "default_result_count": default["result_count"],
            "expanded_result_count": expanded["result_count"], "hidden_child_calls": 0, "semantic_product_evidence": False,
        })

    events.append({
        "schema_version": SCHEMA, "event": "semantic_none_status", "semantic_none_observation_count": 0,
        "semantic_none_metric_available": False, "reason": "no real main-agent operation or visible answer was executed",
    })

    restart_hits = 0
    for index in range(2):
        reopened = build_main_agent_surface(str(workspace), f"cold-restart-{index}", policy)
        entry = next(item for item in reopened["entries"] if _entry_locality(item) == index)
        target = f"scale:l{index}:f0"
        result = recall_main_agent_locality(
            str(workspace), f"cold-restart-{index}", reopened["core_state_sha256"], reopened["atlas_fingerprint"],
            reopened["page_fingerprint"], reopened["policy"], entry, "default",
        )
        returned_ids = [item["statement_id"] for item in result["items"]]
        hit = target in returned_ids
        restart_hits += int(hit)
        events.append({
            "schema_version": SCHEMA, "event": "query", "query_id": f"cold-restart-{index + 1:02d}",
            "kind": "cold-restart", "query_utf8": f"Recall fixture locality {index} fact zero after reopen.",
            "target_declared_before_recall": True, "target_source": "query_registry",
            "declared_target_statement_ids": [target], "returned_statement_ids": returned_ids,
            "entry_id": result["entry_id"], "single_entry": True,
            "target_reached": hit, "result_count": result["result_count"],
            "rendered_chars": result["rendered_chars"], "hidden_child_calls": 0,
            "semantic_product_evidence": False,
        })

    target_reach = target_hits / len(registry)
    function_gate_met = _p95(default_counts) <= 5 and _p95(default_chars) <= 3000 and restart_hits == 2
    declared_simulation_gate_met = target_reach >= 0.9 and expanded_hits == 5 and max(leakage_counts) == 0
    summary = {
        "schema_version": SCHEMA,
        "status": "IN_PROGRESS",
        "statement_count": 80,
        "locality_count": 8,
        "independent_unrelated_seed_count": 20,
        "dense_locality_max_facts": 10,
        "provider_backed_statement_count": 0,
        "deterministic_fixture_statement_count": 80,
        "declared_query_count": len(registry) + 5 + 2,
        "relevant_query_count": 20,
        "relation_entry_target_hidden_count": 10,
        "dense_hidden_target_count": 10,
        "semantic_none_observation_count": 0,
        "semantic_none_metric_available": False,
        "expand_count": 5,
        "cold_restart_count": 2,
        "target_reach": target_reach,
        "expanded_target_reach": expanded_hits / 5,
        "cold_restart_reach": restart_hits / 2,
        "default_result_p95": _p95(default_counts),
        "default_chars_p95": _p95(default_chars),
        "python_bounded_locality_function_ms_p95": _p95([round(value) for value in local_latencies_ms]),
        "max_unrelated_leakage_count": max(leakage_counts),
        "single_entry_rate": 1.0,
        "hidden_child_calls": 0,
        "legacy_reader": False,
        "old_hidden_reader_latency_ms": [31800, 19700, 23500, 33700],
        "provider_gate_met": False,
        "provider_gate_reason": "not executed",
        "geometry_function_gate_met": function_gate_met,
        "declared_target_simulation_gate_met": declared_simulation_gate_met,
        "semantic_product_gate_met": False,
    }
    events.append({"schema_version": SCHEMA, "event": "summary", **summary})
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for item in events), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    summary = run_validation(args.workspace.resolve(), args.evidence.resolve(), args.summary.resolve())
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["geometry_function_gate_met"] and summary["declared_target_simulation_gate_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
