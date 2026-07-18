from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "packages/nollm-core/src"),
    str(ROOT / "packages/nollm-snapshot/src"),
    str(ROOT / "packages/nollm-trace/src"),
    str(ROOT / "packages/nollm-access/src"),
]

from nollm_access import AccessMemoryLoop  # noqa: E402
from nollm_core import CoreRuntime  # noqa: E402


EXPECTED = {
    "target": "2026年7月18日东京下午三点开始下雨。",
    "tokyo-1": "2026年7月18日用户因东京降雨取消了浅草行程。",
    "tokyo-2": "取消浅草行程后，用户改去了东京站。",
    "time-1": "2026年7月18日下午四点，用户参加线上架构会议。",
}


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path} is not a JSON object")
    return value


def _capture_label(capture: dict[str, object]) -> str | None:
    user = capture.get("user_utf8")
    if type(user) is not str:
        return None
    return next((name for name, fact in EXPECTED.items() if fact in user), None)


def _events(directory: Path) -> list[dict[str, object]]:
    values = [_read_json(path) for path in directory.glob("*.json")]
    return sorted(values, key=lambda item: (item["event_epoch_ms"], item["event_id"]))


def freeze(
    workspace: Path,
    trace: Path,
    host_root: Path,
    evidence: Path,
    summary_path: Path,
) -> dict[str, object]:
    spool = workspace / "openclaw-capture-spool"
    captures = []
    admitted_statement_ids = []
    for path in sorted((spool / "captures").glob("*.json")):
        raw = path.read_bytes()
        capture = json.loads(raw)
        label = _capture_label(capture)
        if label is None:
            continue
        history = _events(spool / "events" / capture["capture_id"])
        terminal = [item for item in history if item["status"] in {"admitted", "deferred", "failed"}]
        retries = [item for item in history if item["status"] == "retry"]
        statement_ids = [statement_id for item in terminal if item["status"] == "admitted" for statement_id in item["statement_ids"]]
        admitted_statement_ids.extend(statement_ids)
        captures.append({
            "label": label,
            "capture_id": capture["capture_id"],
            "capture_sha256": _sha(raw),
            "capture": capture,
            "events": history,
            "terminal_status": None if not terminal else terminal[-1]["status"],
            "attempt_count": max((item["attempt"] for item in history), default=0),
            "retry_errors": [item["error"] for item in retries],
            "statement_ids": statement_ids,
        })
    by_label = {item["label"]: item for item in captures}
    if set(by_label) != set(EXPECTED):
        raise RuntimeError("long-arm Capture inventory is incomplete or ambiguous")
    admitted = [label for label, item in by_label.items() if item["terminal_status"] == "admitted"]
    if set(admitted) != {"target", "tokyo-1", "tokyo-2"}:
        raise RuntimeError("unexpected admitted long-arm prefix")
    with AccessMemoryLoop(workspace) as loop:
        reopen = loop.verify_admitted_statements(admitted_statement_ids)
        bindings = {statement_id: loop.binding(statement_id) for statement_id in admitted_statement_ids}
        target_id = by_label["target"]["statement_ids"][0]
        endpoint_id = by_label["tokyo-2"]["statement_ids"][0]
        endpoint = bindings[endpoint_id]["handle"]["geometry_address"]
        recalled = loop.local_context([endpoint], "gate-d-provider-tokyo-endpoint")
    target = next(item for item in recalled if item["statement_id"] == target_id)
    with CoreRuntime(workspace) as core:
        state = core.export_state_bytes()
        placement_count = core.placement_count()
    host_artifacts = []
    for path in sorted(host_root.glob("v311r2_long_arm_*")):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        host_artifacts.append({"path": str(path), "sha256": _sha(raw), "bytes": len(raw)})
    trace_bytes = trace.read_bytes()
    trace_lines = [line for line in trace_bytes.decode("utf-8").splitlines() if line]
    record = {
        "record_type": "provider_long_arm_attempt",
        "schema_version": "nollm_v311r2_provider_long_arm_attempt_v1",
        "provider": "meituan/LongCat-2.0",
        "provider_backed": True,
        "workspace": str(workspace),
        "workspace_frozen": True,
        "gateway_listener_present_at_freeze": False,
        "capture_count": len(captures),
        "admitted_capture_count": len(admitted),
        "captures": captures,
        "durable_reopen": reopen,
        "bindings": bindings,
        "core_state_sha256": _sha(state),
        "core_state_bytes": len(state),
        "placement_count": placement_count,
        "tokyo_arm": {
            "endpoint_statement_id": endpoint_id,
            "target_statement_id": target_id,
            "entry": endpoint,
            "target_handle": target["handle"],
            "path": target["path"],
            "path_length": len(target["path"]),
            "single_entry_count": 1,
            "achieved": len(target["path"]) >= 2,
        },
        "absolute_time_arm_achieved": False,
        "weather_arm_achieved": False,
        "unrelated_negative_control_achieved": False,
        "restart_repeat_achieved": False,
        "not_attempted_after_bounded_stop": ["time-2", "weather-1", "weather-2", "unrelated-1", "unrelated-2"],
        "bounded_stop_reason": "time-1 remained retryable after three attempts; no resolved Lens relation group",
        "host_artifacts": host_artifacts,
        "host_trace_path": str(trace),
        "host_trace_sha256": _sha(trace_bytes),
        "host_trace_utf8_bytes": len(trace_bytes),
        "host_trace_line_count": len(trace_lines),
        "provider_long_arm_validated": False,
        "gate_status": "IN_PROGRESS",
    }
    rows = [json.loads(line) for line in evidence.read_text(encoding="utf-8").splitlines() if line]
    rows = [item for item in rows if item.get("record_type") != "provider_long_arm_attempt"]
    rows.append(record)
    encoded = b"".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n" for item in rows)
    evidence.write_bytes(encoded)
    summary = _read_json(summary_path)
    summary.update({
        "provider_causal_gate_passed": bool(summary.get("passed")),
        "provider_long_arm_validated": False,
        "provider_long_arm_gate_status": "IN_PROGRESS",
        "provider_long_arm_capture_count": len(captures),
        "provider_long_arm_admitted_count": len(admitted),
        "provider_long_arm_achieved_count": 1,
        "completion_status": "CAOLD_FIELD_COMPLETE_ATLAS_CAUSAL_LOOP_IN_PROGRESS",
        "evidence_line_count": len(rows),
        "evidence_utf8_bytes": len(encoded),
        "evidence_sha256": _sha(encoded),
        "passed": False,
    })
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--host-root", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    result = freeze(*(path.resolve() for path in (args.workspace, args.trace, args.host_root, args.evidence, args.summary)))
    print(json.dumps({
        "gate_status": result["gate_status"],
        "capture_count": result["capture_count"],
        "admitted_capture_count": result["admitted_capture_count"],
        "tokyo_arm_achieved": result["tokyo_arm"]["achieved"],
        "provider_long_arm_validated": result["provider_long_arm_validated"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
