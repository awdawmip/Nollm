from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter
import uuid


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "packages/nollm-core/src"),
    str(ROOT / "packages/nollm-access/src"),
    str(ROOT / "integrations/openclaw/formation-loop/python"),
]

from nollm_access import AccessMemoryLoop  # noqa: E402
from nollm_core import CoreRuntime  # noqa: E402
from nollm_openclaw_formation.memory_loop import (  # noqa: E402
    FAST_RECALL_SCHEMA_VERSION,
    apply_fast_recall_selection,
    build_fast_recall_prompt,
)


TERMINAL_RANK = {"captured": 0, "processing": 1}
PRODUCT_QUERIES = ("tokyo", "meeting", "weather", "none")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _cell_key(value: dict[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _event_key(value: dict[str, object]) -> tuple[object, ...]:
    return (
        value["attempt"], value["event_epoch_ms"],
        TERMINAL_RANK.get(str(value["status"]), 2), value["event_id"],
    )


def _state_sha(workspace: Path) -> tuple[str, int, int]:
    with CoreRuntime(workspace) as core:
        state = core.export_state_bytes()
        return _sha(state), len(state), core.placement_count()


def _captures(workspace: Path) -> list[dict[str, object]]:
    spool = workspace / "openclaw-capture-spool"
    result = []
    for path in (spool / "captures").glob("*.json"):
        capture = json.loads(path.read_text(encoding="utf-8"))
        events = sorted(
            (json.loads(item.read_text(encoding="utf-8")) for item in (spool / "events" / capture["capture_id"]).glob("*.json")),
            key=_event_key,
        )
        result.append({**capture, "events": events, "terminal": events[-1]})
    return sorted(result, key=lambda item: (item["captured_epoch_ms"], item["capture_id"]))


def _host_envelope(stdout: str) -> dict[str, object] | None:
    decoder = json.JSONDecoder()
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if type(value) is dict and type(value.get("result")) is dict:
            return value
    return None


def _provider(openclaw: Path, prompt: str, session_id: str) -> dict[str, object]:
    prompt_path: Path | None = None
    started = perf_counter()
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", suffix=".txt", delete=False) as stream:
            stream.write(prompt)
            prompt_path = Path(stream.name)
        completed = subprocess.run(
            [
                str(openclaw), "agent", "--agent", "nollm-dream-agent",
                "--session-id", session_id, "--message-file", str(prompt_path),
                "--thinking", "off", "--json", "--timeout", "600",
            ],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=720,
        )
    finally:
        if prompt_path is not None:
            prompt_path.unlink(missing_ok=True)
    envelope = _host_envelope(completed.stdout)
    payloads = [] if envelope is None else envelope["result"].get("payloads", [])
    raw = "".join(item.get("text", "") for item in payloads if type(item) is dict)
    return {
        "exit_code": completed.returncode,
        "elapsed_ms": round((perf_counter() - started) * 1000, 3),
        "prompt_sha256": _sha(prompt.encode("utf-8")),
        "prompt_utf8_bytes": len(prompt.encode("utf-8")),
        "assistant_raw": raw,
        "assistant_raw_sha256": _sha(raw.encode("utf-8")),
        "host_envelope_parsed": envelope is not None,
        "host_stdout_sha256": _sha(completed.stdout.encode("utf-8")),
        "host_stderr": completed.stderr,
    }


def _capture_benchmark() -> dict[str, object]:
    completed = subprocess.run(
        ["node", str(ROOT / "lab/nollm-lab/absorption/capture_performance_validation.mjs")],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    if completed.returncode:
        raise RuntimeError(f"controlled Capture benchmark failed: {completed.stderr.strip()}")
    result = json.loads(completed.stdout)
    if type(result) is not dict or result.get("capture_count") != 150:
        raise RuntimeError("controlled Capture benchmark returned an invalid envelope")
    return result


def _target_hidden_prompt(query: str, entries: list[dict[str, object]]) -> str:
    return f"""You are a private background geometry-entry selector. Choose at most one supplied relation entry_id likely to reach memory useful for the query, or choose none. The target Cell and every target preview are intentionally absent. Do not invent entries, facts, coordinates, topics, vectors, graphs, or hidden routes. Do not reveal reasoning.
Return exactly one raw JSON object with no markdown.
select: {{"schema_version":"{FAST_RECALL_SCHEMA_VERSION}","outcome":"select","entry_id":"one supplied id"}}
none: {{"schema_version":"{FAST_RECALL_SCHEMA_VERSION}","outcome":"none","entry_id":null}}
query: {json.dumps(query, ensure_ascii=False)}
relation_entries: {json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""


def _statement_rows(workspace: Path, statement_ids: list[str]) -> tuple[dict[str, object], list[dict[str, object]]]:
    with AccessMemoryLoop(workspace) as loop:
        reopened = loop.verify_admitted_statements(statement_ids)
        rows = []
        for index, statement_id in enumerate(statement_ids):
            binding = loop.binding(statement_id)
            cell = binding["handle"]["geometry_address"]
            items = loop.local_context([cell], f"v311r4-freeze:{index}")
            item = next(value for value in items if value["statement_id"] == statement_id)
            rows.append({
                "statement_id": statement_id,
                "content_utf8": item["content_utf8"],
                "cell": cell,
            })
    return reopened, rows


def validate(workspace: Path, host_trace: Path, openclaw: Path, evidence: Path, summary_path: Path) -> dict[str, object]:
    captures = _captures(workspace)
    if len(captures) != 9 or any(item["terminal"]["status"] != "admitted" for item in captures):
        raise RuntimeError("expected exactly nine admitted durable Captures")
    statement_ids = [statement_id for item in captures for statement_id in item["terminal"].get("statement_ids", [])]
    reopened, statements = _statement_rows(workspace, statement_ids)
    state_before, state_bytes, placement_count = _state_sha(workspace)
    statement_by_id = {item["statement_id"]: item for item in statements}
    target = next(item for item in statements if "rained in Tokyo" in item["content_utf8"])
    audit = next(item for item in statements if "30天" in item["content_utf8"])
    backup = next(item for item in statements if "凌晨2点" in item["content_utf8"])

    trace_rows = [json.loads(line) for line in host_trace.read_text(encoding="utf-8").splitlines() if line]
    absorbed = [item for item in trace_rows if item.get("stage") == "absorption_batch" and item.get("status") == "completed"]
    outcomes = [outcome for item in absorbed for outcome in item.get("durable_outcomes", [])]
    action_counts = Counter(str(item["action"]) for item in outcomes)
    capture_publishes = [float(item["capture_publish_ms"]) for item in trace_rows if item.get("stage") == "capture"]
    live_capture_p95 = sorted(capture_publishes)[max(0, int(len(capture_publishes) * 0.95 + 0.999) - 1)]
    capture_benchmark = _capture_benchmark()
    wrong_dates = [item for item in statements if "2026年7月20日" in item["content_utf8"] or "July 20, 2026" in item["content_utf8"]]

    last_absorption_index = max(
        index for index, item in enumerate(trace_rows)
        if item.get("stage") == "absorption_batch" and item.get("status") == "completed"
    )
    post_absorption_recall = [
        (index, item) for index, item in enumerate(trace_rows)
        if index > last_absorption_index and item.get("stage") == "fast_recall"
    ]
    product = [item for _, item in post_absorption_recall[:4]]
    if len(product) != 4:
        raise RuntimeError("expected four product Recall terminal records")
    product_records = dict(zip(PRODUCT_QUERIES, product, strict=True))
    distinct_entries = {
        _cell_key(product_records[name]["selected_entry"])
        for name in PRODUCT_QUERIES[:3]
    }
    tokyo_target = next(
        (item for item in product_records["tokyo"].get("selected_paths", []) if item["statement_id"] == target["statement_id"]),
        None,
    )
    recall_only_regression_index, recall_only_regression = post_absorption_recall[-1]
    recall_only_tail = trace_rows[recall_only_regression_index + 1:]
    recall_only_write_stages = [
        item for item in recall_only_tail
        if item.get("stage") in {"formation", "parse_store", "placement_prompt", "placement_apply"}
        or item.get("status") == "started"
    ]

    built = build_fast_recall_prompt(
        "What weather caused the user to cancel the Asakusa itinerary on July 21, 2026?",
        str(workspace), "v311r4-target-hidden",
    )
    if built.get("status") != "entry_decision":
        raise RuntimeError("target-hidden Reader did not receive an entry decision")
    target_key = _cell_key(target["cell"])
    hidden_entries = []
    for entry in built["entries"]:
        if _cell_key(entry["entry_cell"]) == target_key:
            continue
        hidden_entries.append({
            **entry,
            "statements": [item for item in entry["statements"] if item.get("statement_id") != target["statement_id"]],
        })
    if any(
        item.get("statement_id") == target["statement_id"]
        for entry in hidden_entries for item in entry["statements"]
    ):
        raise RuntimeError("target preview leaked into target-hidden entries")
    prompt = _target_hidden_prompt(
        "What weather caused the user to cancel the Asakusa itinerary on July 21, 2026?",
        hidden_entries,
    )
    provider = _provider(openclaw, prompt, f"v311r4-target-hidden-{uuid.uuid4().hex[:8]}")
    try:
        hidden_result = apply_fast_recall_selection(
            provider["assistant_raw"], hidden_entries, str(workspace), "v311r4-target-hidden:apply",
        )
    except Exception as exc:
        correction = _provider(
            openclaw,
            prompt + f"\nThe previous response was rejected without writes: {exc}. Return only one corrected raw JSON object.",
            f"v311r4-target-hidden-correction-{uuid.uuid4().hex[:8]}",
        )
        provider["correction"] = correction
        hidden_result = apply_fast_recall_selection(
            correction["assistant_raw"], hidden_entries, str(workspace), "v311r4-target-hidden:correction",
        )
    hidden_target = next(
        (item for item in hidden_result.get("selected_paths", []) if item["statement_id"] == target["statement_id"]),
        None,
    )

    entry_by_cell = {_cell_key(item["entry_cell"]): item for item in built["entries"]}
    unrelated_results = []
    for index, unrelated in enumerate((audit, backup), 1):
        entry = entry_by_cell[_cell_key(unrelated["cell"])]
        raw = json.dumps({
            "schema_version": FAST_RECALL_SCHEMA_VERSION,
            "outcome": "select",
            "entry_id": entry["entry_id"],
        }, separators=(",", ":"))
        result = apply_fast_recall_selection(raw, built["entries"], str(workspace), f"v311r4-unrelated:{index}")
        unrelated_results.append({
            "statement_id": unrelated["statement_id"],
            "entry_cell": unrelated["cell"],
            "target_reached": any(item["statement_id"] == target["statement_id"] for item in result.get("selected_paths", [])),
            "result": result,
        })

    state_after, _, placement_after = _state_sha(workspace)
    cells = [_cell_key(item["cell"]) for item in statements]
    checks = {
        "nine_durable_captures": len(captures) == 9,
        "nine_unique_statements": len(statement_ids) == len(set(statement_ids)) == 9,
        "one_statement_atom_cell": len(cells) == len(set(cells)) == placement_count == 9,
        "durable_reopen": reopened.get("reopen_verified") is True,
        "wrong_date_zero": not wrong_dates,
        "related_growth_at_least_five": action_counts["new_local"] >= 5,
        "unrelated_independent_at_least_two": action_counts["independent_seed"] >= 2,
        "distinct_product_entries": len(distinct_entries) >= 3,
        "t0_product_recall": bool(tokyo_target and tokyo_target.get("path")),
        "target_hidden_causal": bool(hidden_target and hidden_target.get("path")),
        "unrelated_not_reached": all(not item["target_reached"] for item in unrelated_results),
        "none_after_restart": product_records["none"].get("outcome") == "none",
        "read_zero_write": state_before == state_after and placement_count == placement_after,
        "recall_only_no_formation_after_none": (
            recall_only_regression.get("outcome") == "none" and not recall_only_write_stages
        ),
        "capture_p95_within_budget": float(capture_benchmark["capture_publish_p95_ms"]) <= 100.0,
    }
    record = {
        "record_type": "v311r4_contextual_live_validation",
        "schema_version": "nollm_v311r4_contextual_live_validation_v1",
        "workspace": str(workspace),
        "captures": [{
            "capture_id": item["capture_id"], "user_utf8": item["user_utf8"],
            "current_status": item["terminal"]["status"], "attempt": item["terminal"]["attempt"],
            "statement_ids": item["terminal"]["statement_ids"],
        } for item in captures],
        "statements": statements,
        "action_counts": dict(sorted(action_counts.items())),
        "wrong_dates": wrong_dates,
        "context_capture_counts": [item.get("writer_context_capture_count", 0) for item in absorbed],
        "context_chars": [item.get("writer_context_chars", 0) for item in absorbed],
        "writer_provider_calls": [item.get("proposition_writer_provider_calls", 0) for item in absorbed],
        "cartographer_turns": [item.get("cartographer_turns", 0) for item in absorbed],
        "live_capture_observed_p95_ms": live_capture_p95,
        "live_capture_observed_sample_count": len(capture_publishes),
        "capture_benchmark": capture_benchmark,
        "product_recall": product_records,
        "distinct_product_entries": sorted(distinct_entries),
        "target_statement_id": target["statement_id"],
        "target_hidden_entry_count": len(hidden_entries),
        "target_hidden_provider": provider,
        "target_hidden_result": hidden_result,
        "unrelated_results": unrelated_results,
        "recall_only_regression": recall_only_regression,
        "recall_only_write_stages": recall_only_write_stages,
        "state_before_sha256": state_before,
        "state_after_sha256": state_after,
        "state_bytes": state_bytes,
        "placement_count": placement_count,
        "checks": checks,
        "passed": all(checks.values()),
    }
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(encoded)
    summary = {
        "schema_version": "nollm_v311r4_contextual_live_summary_v1",
        "validated_revision": _git_head(),
        "completion_status": "CONTEXTUAL_WRITER_SHARED_RETRIEVAL_GROWTH_VALIDATED",
        "provider": "meituan/LongCat-2.0",
        "capture_count": len(captures),
        "statement_count": len(statement_ids),
        "occupied_cell_count": len(set(cells)),
        "placement_count": placement_count,
        "action_counts": dict(sorted(action_counts.items())),
        "wrong_date_count": len(wrong_dates),
        "distinct_product_entry_count": len(distinct_entries),
        "target_hidden_path": None if hidden_target is None else hidden_target.get("path"),
        "unrelated_false_reach_count": sum(item["target_reached"] for item in unrelated_results),
        "none_after_restart": checks["none_after_restart"],
        "read_zero_write": checks["read_zero_write"],
        "capture_p95_ms": capture_benchmark["capture_publish_p95_ms"],
        "capture_max_ms": capture_benchmark["capture_publish_max_ms"],
        "capture_sample_count": capture_benchmark["capture_count"],
        "live_capture_observed_p95_ms": live_capture_p95,
        "live_capture_observed_sample_count": len(capture_publishes),
        "evidence_sha256": _sha(encoded),
        "evidence_utf8_bytes": len(encoded),
        "evidence_line_count": 1,
        "checks": checks,
        "passed": record["passed"],
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--host-trace", type=Path, required=True)
    parser.add_argument("--openclaw", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    summary = validate(*(path.resolve() for path in (
        args.workspace, args.host_trace, args.openclaw, args.evidence, args.summary,
    )))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
