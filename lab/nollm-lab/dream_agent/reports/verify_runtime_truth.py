from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1] / "runtime_truth"
TERMINAL = {"completed", "error", "timeout", "failed"}


class EvidenceError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _visible_payloads(raw: dict[str, Any]) -> list[str]:
    payloads = raw.get("result", {}).get("payloads", [])
    return [item["text"] for item in payloads if isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip()]


def _latency(receipt: dict[str, Any]) -> int:
    return int(receipt["main_command_returned_at"]) - int(receipt["main_started_at"])


def _percentile(values: list[int], percentile: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def verify(root: Path = ROOT) -> dict[str, Any]:
    enabled, disabled = root / "enabled", root / "disabled"
    enabled_raw = [_json(enabled / f"turn-{index:02d}.json") for index in range(1, 16)]
    disabled_raw = [_json(disabled / f"turn-{index:02d}.json") for index in range(1, 16)]
    enabled_receipts, disabled_receipts = _jsonl(enabled / "receipts.jsonl"), _jsonl(disabled / "receipts.jsonl")
    events = _jsonl(enabled / "events.jsonl")
    if len(enabled_receipts) != 15 or len(disabled_receipts) != 15:
        raise EvidenceError("expected exactly 15 enabled and 15 disabled receipts")
    for label, raws, receipts in (("enabled", enabled_raw, enabled_receipts), ("disabled", disabled_raw, disabled_receipts)):
        for index, (raw, receipt) in enumerate(zip(raws, receipts), 1):
            if raw.get("status") != "ok" or receipt.get("exit_code") != 0:
                raise EvidenceError(f"{label} turn {index} did not exit successfully")
            if len(_visible_payloads(raw)) != 1:
                raise EvidenceError(f"{label} turn {index} must contain exactly one visible assistant payload")
            agent_meta = raw.get("result", {}).get("meta", {}).get("agentMeta", {})
            if (agent_meta.get("provider"), agent_meta.get("model")) != ("meituan", "LongCat-2.0"):
                raise EvidenceError(f"{label} turn {index} has an unexpected actual main model")

    started = [event for event in events if event.get("status") == "started"]
    terminals = [event for event in events if event.get("status") in TERMINAL and event.get("stage") in {"parse_store", "subagent", "empty_output", "completion"}]
    hooks = [event for event in events if event.get("status") == "hook" and event.get("hook") in {"agent_end", "message_sent"}]
    if len(started) != 15 or len({event.get("turn_key_sha256") for event in started}) != 15:
        raise EvidenceError("enabled evidence must contain 15 unique Dream starts")
    if len(terminals) != 15 or {event.get("run_id") for event in terminals} != {event.get("run_id") for event in started}:
        raise EvidenceError("each Dream start must have exactly one terminal event")
    if len(hooks) != 15:
        raise EvidenceError("expected exactly one trigger Hook per enabled turn")
    durations = [int(event["hook_handler_duration_ms"]) for event in hooks]
    if _percentile(durations, 0.95) > 20 or max(durations) > 50:
        raise EvidenceError("Hook callback duration exceeds the live budget")
    for event in started:
        if event.get("deliver") is not False or event.get("duplicate_dream_suppressed_count") != 0:
            raise EvidenceError("Dream delivery or duplicate state is invalid")
        if event.get("trigger_phase") not in {"AFTER_TURN", "AFTER_DELIVERY"}:
            raise EvidenceError("invalid trigger phase")
        if event.get("source_hook") == "agent_end" and event.get("trigger_phase") != "AFTER_TURN":
            raise EvidenceError("agent_end must be classified as AFTER_TURN")
        turns = event.get("material", {}).get("turns", [])
        if not turns or any(turn.get("role") not in {"user", "assistant"} for turn in turns):
            raise EvidenceError("ConversationMaterial contains a forbidden or missing role")
        identities = [(turn.get("role"), turn.get("content_utf8")) for turn in turns]
        if len(identities) != len(set(identities)):
            raise EvidenceError("ConversationMaterial contains a duplicate role/content turn")
    for event in terminals:
        if event.get("resolved_model_ref") != "meituan/LongCat-2.0":
            raise EvidenceError("terminal child model is missing or does not match the actual parent model")
        if event.get("python_semantic_fallback") is not False:
            raise EvidenceError("Python semantic fallback was used")
        if event.get("visible_message_count") != 0:
            raise EvidenceError("Dream emitted a visible message")

    terminal_by_run = {event["run_id"]: event for event in terminals}
    after_return = 0
    for start, receipt in zip(started, enabled_receipts):
        event = terminal_by_run[start["run_id"]]
        session = str(start.get("session_key", "")).split(":")[-1]
        if session != receipt["session_id"]:
            raise EvidenceError("Dream start order cannot be correlated to the raw main receipt")
        after_return += int(event["dream_completed_at"]) > int(receipt["main_command_returned_at"])
    if after_return / len(terminals) < 0.9:
        raise EvidenceError("fewer than 90 percent of Dreams completed after main return")

    dedicated = _jsonl(root / "dedicated" / "events.jsonl")
    dedicated_starts = {event["run_id"]: event for event in dedicated if event.get("status") == "started" and event.get("model_mode") == "dedicated"}
    dedicated_terminals = [event for event in dedicated if event.get("run_id") in dedicated_starts and event.get("resolved_model_ref") == "meituan/LongCat-2.0"]
    if not dedicated_terminals:
        raise EvidenceError("no successful dedicated Host override and resolved-model evidence")

    enabled_latency = [_latency(item) for item in enabled_receipts]
    disabled_latency = [_latency(item) for item in disabled_receipts]
    result = {
        "enabled": {"count": 15, "median_ms": statistics.median(enabled_latency), "p95_ms": _percentile(enabled_latency, 0.95)},
        "disabled": {"count": 15, "median_ms": statistics.median(disabled_latency), "p95_ms": _percentile(disabled_latency, 0.95)},
        "hook": {"count": 15, "p95_ms": _percentile(durations, 0.95), "max_ms": max(durations)},
        "dream": {"terminal_count": 15, "completed_after_main_return": after_return, "inherit_resolved_model": "meituan/LongCat-2.0", "dedicated_resolved_model": "meituan/LongCat-2.0", "visible_messages": 0},
    }
    summary_path = root / "summary.json"
    if summary_path.exists() and _json(summary_path) != result:
        raise EvidenceError("summary does not match values recomputed from raw evidence")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root), indent=2, sort_keys=True))
    except (EvidenceError, FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as error:
        print(f"runtime truth verification failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
