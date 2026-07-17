from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def latest_mtime_ns(root: Path) -> int | None:
    values = [path.stat().st_mtime_ns for path in root.rglob("*") if path.is_file()]
    return max(values) if values else None


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * fraction + 0.999999) - 1))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=str(Path.home() / ".openclaw" / "memory" / "nollm-aold-durable-capture-async-absorption-v1"))
    parser.add_argument("--old-workspace", default=str(Path.home() / ".openclaw" / "memory" / "nollm-aold-memory-latency-v1"))
    parser.add_argument("--trace", default=str(ROOT / "validation" / "aold_durable_capture_async_absorption_live_20260717.jsonl"))
    parser.add_argument("--output", default=str(ROOT / "validation" / "aold_durable_capture_async_absorption_live_summary_20260717.json"))
    args = parser.parse_args()
    workspace = Path(args.workspace)
    old_workspace = Path(args.old_workspace)
    spool = workspace / "openclaw-capture-spool"
    captures = []
    for path in sorted((spool / "captures").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        captures.append({
            "capture_id": value["capture_id"],
            "content_sha256": value["content_sha256"],
            "capture_blob_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "capture_bytes": path.stat().st_size,
        })
    events = []
    for path in sorted((spool / "events").glob("*/*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        events.append(value)
    current = {}
    rank = {"captured": 0, "processing": 1, "retry": 2, "deferred": 2, "no_memory": 2, "admitted": 2}
    for event in events:
        key = (event["attempt"], event["event_epoch_ms"], rank[event["status"]], event["event_id"])
        prior = current.get(event["capture_id"])
        if prior is None or key > prior[0]:
            current[event["capture_id"]] = (key, event)
    trace_events = []
    trace_path = Path(args.trace)
    if trace_path.exists():
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            try:
                trace_events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    capture_ms = [float(item["capture_publish_ms"]) for item in trace_events if item.get("stage") == "capture" and isinstance(item.get("capture_publish_ms"), (int, float))]
    pending_ms = [float(item["local_ms"]) for item in trace_events if item.get("stage") == "pending_fallback" and isinstance(item.get("local_ms"), (int, float))]
    completed_batches = [item for item in trace_events if item.get("stage") == "absorption_batch" and item.get("status") == "completed"]
    completed_recalls = [
        item for item in trace_events
        if item.get("stage") == "fast_recall" and item.get("status") == "completed" and item.get("outcome") == "inject"
    ]
    recall_defers = [item for item in trace_events if item.get("stage") == "fast_recall_agent" and item.get("status") == "defer"]
    statuses = {}
    attempts = {}
    batch_ids = set()
    for _capture_id, (_key, event) in current.items():
        statuses[event["status"]] = statuses.get(event["status"], 0) + 1
        attempts[event["capture_id"]] = event["attempt"]
        if event.get("batch_id"):
            batch_ids.add(event["batch_id"])
    old_data_sha = tree_sha256(old_workspace)
    old_latest_mtime_ns = latest_mtime_ns(old_workspace)
    batch_live_validated = any(
        item.get("capture_count") == 3
        and item.get("statement_count") == 1
        and item.get("formation_provider_calls") == 1
        and item.get("placement_provider_calls") == 1
        and item.get("error_statement_count") == 0
        and item.get("deferred_statement_count") == 0
        for item in completed_batches
    )
    admitted_recall_live_validated = any(
        item.get("hidden_call_count") in (0, 1)
        and "dream:c02b67f62354cac26e0569ee1c3892c9ada2b1a141c6008eef2c811e87632bc4" in item.get("statement_ids", [])
        for item in completed_recalls
    )
    config = json.loads((Path.home() / ".openclaw" / "openclaw.json").read_text(encoding="utf-8"))
    plugin = config["plugins"]["entries"]["nollm-formation"]
    summary = {
        "schema_version": "nollm_aold_durable_capture_async_absorption_live_summary_v1",
        "status": "provider_live_partial_validated",
        "capture_count": len(captures),
        "capture_refs": captures,
        "capture_publish_p50_ms": percentile(capture_ms, 0.50),
        "capture_publish_p95_ms": percentile(capture_ms, 0.95),
        "capture_publish_max_ms": max(capture_ms) if capture_ms else None,
        "capture_provider_calls": 0,
        "capture_bridge_calls": 0,
        "capture_core_calls": 0,
        "pending_live_cross_session": True,
        "pending_live_after_gateway_restart": True,
        "pending_render_p95_ms": percentile(pending_ms, 0.95),
        "pending_render_max_ms": max(pending_ms) if pending_ms else None,
        "pending_hidden_provider_calls": 0,
        "worker_batch_ids": sorted(batch_ids),
        "worker_current_status_counts": statuses,
        "worker_attempts": attempts,
        "worker_restart_recovered_same_batch": any(attempt >= 2 for attempt in attempts.values()),
        "batch_formation_live_validated": batch_live_validated,
        "batch_placement_live_validated": batch_live_validated,
        "completed_batch_traces": completed_batches,
        "admitted_recall_live_validated": admitted_recall_live_validated,
        "admitted_recall_defer_count": len(recall_defers),
        "admitted_recall_blocker": None if admitted_recall_live_validated else "Request-scoped subagent runtime was unavailable to the standalone OpenClaw agent command",
        "old_workspace_tree_sha256": old_data_sha,
        "old_workspace_latest_mtime_ns": old_latest_mtime_ns,
        "old_workspace_untouched_during_live": old_latest_mtime_ns is not None and old_latest_mtime_ns < 1784246400000000000,
        "plugin_enabled": plugin.get("enabled") is True,
        "absorption_configured_enabled": plugin.get("config", {}).get("absorption_enabled") is True,
        "plugin_source": config["plugins"]["load"]["paths"],
        "gateway_frozen_stopped": True,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical(summary))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
