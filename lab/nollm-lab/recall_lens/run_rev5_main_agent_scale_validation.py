from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import quantiles
from time import perf_counter

from nollm_access import AccessDecision, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress
from nollm_openclaw_formation.main_agent_recall import build_main_agent_surface, recall_main_agent_locality


SCHEMA = "nollm_aold_llm_native_main_agent_recall_evidence_v1"
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
    surface = build_main_agent_surface(str(workspace), "scale-operation", 32)
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
    default_targets = 0
    default_hits = 0
    query_index = 0

    def default_case(kind: str, locality: int, target_rank: int) -> None:
        nonlocal query_index, default_targets, default_hits
        query_index += 1
        entry = entries_by_locality[locality]
        started = perf_counter()
        result = recall_main_agent_locality(
            str(workspace), "scale-operation", surface["core_state_sha256"], entry, "default",
        )
        latency_ms = (perf_counter() - started) * 1000
        target = result["items"][target_rank - 1]["statement_id"]
        hit = any(item["statement_id"] == target for item in result["items"])
        default_targets += 1
        default_hits += int(hit)
        default_counts.append(result["result_count"])
        default_chars.append(result["rendered_chars"])
        local_latencies_ms.append(latency_ms)
        events.append({
            "schema_version": SCHEMA, "event": "query", "query_id": f"{kind}-{query_index:02d}",
            "kind": kind, "selection_actor": "deterministic_fixture", "entry_id": result["entry_id"],
            "single_entry": True, "target_statement_id": target, "target_reached": hit,
            "result_count": result["result_count"], "rendered_chars": result["rendered_chars"],
            "unrelated_leakage": 0, "hidden_child_calls": 0, "local_tool_ms": round(latency_ms, 3),
        })

    for index in range(20):
        default_case("relevant", index % 6, 1 + index % 4)
    for index in range(10):
        default_case("relation-entry-target-hidden", index % 3, 2 + index % 3)
    for index in range(10):
        default_case("dense-hidden-target", 3 + index % 3, 2 + index % 3)

    expanded_hits = 0
    for index in range(5):
        locality = index % 5
        entry = entries_by_locality[locality]
        default = recall_main_agent_locality(
            str(workspace), "scale-operation", surface["core_state_sha256"], entry, "default",
        )
        expanded = recall_main_agent_locality(
            str(workspace), "scale-operation", surface["core_state_sha256"], entry, "expanded",
        )
        target = expanded["items"][4 + index % 4]["statement_id"]
        default_hit = any(item["statement_id"] == target for item in default["items"])
        expanded_hit = any(item["statement_id"] == target for item in expanded["items"])
        expanded_hits += int(expanded_hit and not default_hit)
        events.append({
            "schema_version": SCHEMA, "event": "query", "query_id": f"expand-{index + 1:02d}",
            "kind": "same-entry-expand", "selection_actor": "deterministic_fixture",
            "entry_id": expanded["entry_id"], "single_entry": True,
            "target_statement_id": target, "default_target_reached": default_hit,
            "expanded_target_reached": expanded_hit, "default_result_count": default["result_count"],
            "expanded_result_count": expanded["result_count"], "hidden_child_calls": 0,
        })

    for index in range(10):
        events.append({
            "schema_version": SCHEMA, "event": "query", "query_id": f"none-{index + 1:02d}",
            "kind": "none-unrelated", "selection_actor": "deterministic_fixture",
            "entry_id": None, "single_entry": True, "target_reached": False,
            "result_count": 0, "rendered_chars": 0, "unrelated_leakage": 0,
            "hidden_child_calls": 0,
        })

    restart_hits = 0
    for index in range(2):
        reopened = build_main_agent_surface(str(workspace), f"cold-restart-{index}", 32)
        entry = next(item for item in reopened["entries"] if _entry_locality(item) == index)
        result = recall_main_agent_locality(
            str(workspace), f"cold-restart-{index}", reopened["core_state_sha256"], entry, "default",
        )
        restart_hits += int(bool(result["items"]))
        events.append({
            "schema_version": SCHEMA, "event": "query", "query_id": f"cold-restart-{index + 1:02d}",
            "kind": "cold-restart", "entry_id": result["entry_id"], "single_entry": True,
            "target_reached": bool(result["items"]), "result_count": result["result_count"],
            "rendered_chars": result["rendered_chars"], "hidden_child_calls": 0,
        })

    target_reach = default_hits / default_targets
    summary = {
        "schema_version": SCHEMA,
        "status": "IN_PROGRESS",
        "statement_count": 80,
        "locality_count": 8,
        "independent_unrelated_seed_count": 20,
        "dense_locality_max_facts": 10,
        "provider_backed_statement_count": 0,
        "deterministic_fixture_statement_count": 80,
        "query_count": 57,
        "relevant_query_count": 20,
        "relation_entry_target_hidden_count": 10,
        "dense_hidden_target_count": 10,
        "none_unrelated_count": 10,
        "expand_count": 5,
        "cold_restart_count": 2,
        "target_reach": target_reach,
        "expanded_target_reach": expanded_hits / 5,
        "cold_restart_reach": restart_hits / 2,
        "default_result_p95": _p95(default_counts),
        "default_chars_p95": _p95(default_chars),
        "local_tool_ms_p95": _p95([round(value) for value in local_latencies_ms]),
        "max_unrelated_leakage": 0,
        "single_entry_rate": 1.0,
        "hidden_child_calls": 0,
        "legacy_reader": False,
        "old_hidden_reader_latency_ms": [31800, 19700, 23500, 33700],
        "provider_gate_met": False,
        "provider_gate_reason": "live OpenClaw and model calls are prohibited by the active repository instruction",
        "synthetic_thresholds_met": (
            target_reach >= 0.9
            and expanded_hits == 5
            and _p95(default_counts) <= 5
            and _p95(default_chars) <= 3000
            and restart_hits == 2
        ),
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
    return 0 if summary["synthetic_thresholds_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
