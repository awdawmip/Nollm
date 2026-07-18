from __future__ import annotations

import argparse
from collections import Counter
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


TERMINAL_RANK = {"captured": 0, "processing": 1}


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path} is not a JSON object")
    return value


def _event_key(value: dict[str, object]) -> tuple[object, ...]:
    return (
        value["attempt"],
        value["event_epoch_ms"],
        TERMINAL_RANK.get(str(value["status"]), 2),
        value["event_id"],
    )


def _canonical_rows(path: Path) -> tuple[list[dict[str, object]], bytes]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    encoded = b"".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        for item in rows
    )
    return rows, encoded


def freeze(
    workspace: Path,
    host_trace: Path,
    live_chat: Path,
    evidence: Path,
    summary_path: Path,
) -> dict[str, object]:
    spool = workspace / "openclaw-capture-spool"
    captures: list[dict[str, object]] = []
    for capture_path in sorted((spool / "captures").glob("*.json")):
        raw = capture_path.read_bytes()
        capture = json.loads(raw)
        event_dir = spool / "events" / capture["capture_id"]
        events = sorted((_json(path) for path in event_dir.glob("*.json")), key=_event_key)
        state = events[-1]
        captures.append({
            "capture_id": capture["capture_id"],
            "capture_sha256": _sha(raw),
            "content_sha256": capture["content_sha256"],
            "user_utf8": capture["user_utf8"],
            "assistant_utf8": capture["assistant_utf8"],
            "events": events,
            "current_status": state["status"],
            "current_attempt": state["attempt"],
            "statement_ids": state.get("statement_ids", []),
        })
    if len(captures) != 9:
        raise RuntimeError(f"expected 9 live Captures, found {len(captures)}")
    live_rows, live_bytes = _canonical_rows(live_chat)
    if len(live_rows) != 9 or any(item.get("exit_code") != 0 for item in live_rows):
        raise RuntimeError("live chat evidence is incomplete")
    admitted = [item for item in captures if item["current_status"] == "admitted"]
    if len(admitted) != 1:
        raise RuntimeError("expected the bounded live attempt to admit exactly T0")
    statement_ids = list(admitted[0]["statement_ids"])
    with AccessMemoryLoop(workspace) as loop:
        reopen = loop.verify_admitted_statements(statement_ids)
        bindings = {statement_id: loop.binding(statement_id) for statement_id in statement_ids}
    with CoreRuntime(workspace) as core:
        core_state = core.export_state_bytes()
        placement_count = core.placement_count()
    occupied_cells = {
        json.dumps(binding["handle"]["geometry_address"], sort_keys=True, separators=(",", ":"))
        for binding in bindings.values()
    }
    trace_bytes = host_trace.read_bytes()
    trace_rows = [json.loads(line) for line in trace_bytes.decode("utf-8").splitlines() if line]
    state_counts = Counter(str(item["current_status"]) for item in captures)
    record = {
        "record_type": "provider_free_field_growth",
        "schema_version": "nollm_v311r3_provider_free_field_growth_v1",
        "provider": "meituan/LongCat-2.0",
        "provider_backed": True,
        "workspace": str(workspace),
        "workspace_frozen": True,
        "gateway_listener_present_at_freeze": False,
        "live_chat_count": len(live_rows),
        "live_chat_process_success_count": len(live_rows),
        "live_chat_sha256": _sha(live_bytes),
        "live_chat_utf8_bytes": len(live_bytes),
        "captures": captures,
        "capture_state_counts": dict(sorted(state_counts.items())),
        "t0_statement_ids": statement_ids,
        "t0_statement_count": len(statement_ids),
        "t0_occupied_cell_count": len(occupied_cells),
        "placement_count": placement_count,
        "one_statement_atom_cell_achieved": len(statement_ids) == 1 and len(occupied_cells) == 1 and placement_count == 1,
        "durable_reopen": reopen,
        "bindings": bindings,
        "core_state_sha256": _sha(core_state),
        "core_state_bytes": len(core_state),
        "host_trace_sha256": _sha(trace_bytes),
        "host_trace_utf8_bytes": len(trace_bytes),
        "host_trace_line_count": len(trace_rows),
        "bounded_stop_reason": "T0 formed two Statements in two occupied Cells; a later four-Capture batch remained processing after provider timeout on attempt 6",
        "long_arms_validated": False,
        "gate_status": "IN_PROGRESS",
    }
    rows, _ = _canonical_rows(evidence)
    rows = [item for item in rows if item.get("record_type") != record["record_type"]]
    rows.append(record)
    evidence_bytes = b"".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        for item in rows
    )
    evidence.write_bytes(evidence_bytes)
    summary = _json(summary_path)
    summary.update({
        "provider_causal_gate_passed": bool(summary.get("passed")),
        "provider_free_field_growth_validated": False,
        "provider_free_field_growth_gate_status": "IN_PROGRESS",
        "provider_free_field_live_chat_count": len(live_rows),
        "provider_free_field_admitted_capture_count": len(admitted),
        "provider_free_field_t0_statement_count": len(statement_ids),
        "provider_free_field_t0_occupied_cell_count": len(occupied_cells),
        "one_statement_atom_cell_achieved": record["one_statement_atom_cell_achieved"],
        "completion_status": "AOLD_PROMPT_BOUNDED_CARTOGRAPHY_IN_PROGRESS",
        "evidence_line_count": len(rows),
        "evidence_utf8_bytes": len(evidence_bytes),
        "evidence_sha256": _sha(evidence_bytes),
        "passed": False,
    })
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--host-trace", type=Path, required=True)
    parser.add_argument("--live-chat", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    result = freeze(*(path.resolve() for path in (
        args.workspace, args.host_trace, args.live_chat, args.evidence, args.summary,
    )))
    print(json.dumps({
        "gate_status": result["gate_status"],
        "live_chat_count": result["live_chat_count"],
        "capture_state_counts": result["capture_state_counts"],
        "t0_statement_count": result["t0_statement_count"],
        "t0_occupied_cell_count": result["t0_occupied_cell_count"],
        "one_statement_atom_cell_achieved": result["one_statement_atom_cell_achieved"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
