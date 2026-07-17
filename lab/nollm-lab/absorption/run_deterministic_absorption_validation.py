from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from time import perf_counter

from nollm_access import AccessMemoryLoop
from nollm_openclaw_formation.memory_loop import (
    BATCH_PLACEMENT_SCHEMA_VERSION,
    FAST_RECALL_SCHEMA_VERSION,
    apply_batch_placement,
    apply_fast_recall_selection,
    build_batch_placement_prompt,
    build_fast_recall_prompt,
)


ROOT = Path(__file__).resolve().parents[3]


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def statement(statement_id: str, content: str, capture_id: str) -> dict[str, object]:
    return {
        "statement_id": statement_id,
        "content_utf8": content,
        "source_handle": None,
        "context_refs": [f"capture:{capture_id}"],
    }


def apply_two(workspace: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    statements = [
        statement("dream:validation-one", "Validation retention is 41 days.", "capture-validation-one"),
        statement("dream:validation-two", "Validation label is durable-blue.", "capture-validation-two"),
    ]
    built = build_batch_placement_prompt(statements, str(workspace), "validation-batch")
    empty = [item for item in built["candidates"] if item["occupancy"]["count"] == 0]
    decisions = [
        {
            "statement_id": item["statement_id"], "outcome": "apply", "action": "expand_surface",
            "candidate_id": empty[index]["candidate_id"], "reason_text": "deterministic validation",
        }
        for index, item in enumerate(statements)
    ]
    applied = apply_batch_placement(
        json.dumps({"schema_version": BATCH_PLACEMENT_SCHEMA_VERSION, "decisions": decisions}),
        statements, str(workspace), "validation-batch", built["view_fingerprint"],
    )
    return applied, statements


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", default=str(ROOT / "validation" / "aold_durable_capture_async_absorption_20260717.jsonl"))
    parser.add_argument("--summary", default=str(ROOT / "validation" / "aold_durable_capture_async_absorption_summary_20260717.json"))
    args = parser.parse_args()
    plugin = ROOT / "integrations" / "openclaw" / "formation-loop"
    subprocess.run(["npm.cmd", "run", "build"], cwd=plugin, check=True, capture_output=True, text=True)
    node = subprocess.run(
        ["node", str(Path(__file__).with_name("capture_performance_validation.mjs"))],
        cwd=ROOT, capture_output=True, text=True,
    )
    if node.returncode:
        raise RuntimeError(f"Capture validation failed: {node.stderr.strip()}")
    capture = json.loads(node.stdout)

    with tempfile.TemporaryDirectory(prefix="nollm-aold-access-") as directory:
        workspace = Path(directory)
        batch_started = perf_counter()
        applied, statements = apply_two(workspace)
        batch_local_ms = (perf_counter() - batch_started) * 1000
        if [item["outcome"] for item in applied["outcomes"]] != ["applied", "applied"]:
            raise RuntimeError("deterministic batch Admission failed")
        fresh = build_batch_placement_prompt(statements, str(workspace), "validation-replay")
        empty = [item for item in fresh["candidates"] if item["occupancy"]["count"] == 0]
        replay_decisions = [
            {"statement_id": item["statement_id"], "outcome": "apply", "action": "expand_surface" if empty[index]["relation_kind"] == "expand_surface" else "new_local", "candidate_id": empty[index]["candidate_id"], "reason_text": "replay validation"}
            for index, item in enumerate(statements)
        ]
        replay = apply_batch_placement(
            json.dumps({"schema_version": BATCH_PLACEMENT_SCHEMA_VERSION, "decisions": replay_decisions}),
            statements, str(workspace), "validation-replay", fresh["view_fingerprint"],
        )
        if any(item.get("action") != "replay_existing" for item in replay["outcomes"]):
            raise RuntimeError("Admission replay was not idempotent")
        recall_started = perf_counter()
        recall = build_fast_recall_prompt("What is the validation retention?", str(workspace), "validation-recall")
        if recall["status"] != "entry_decision":
            raise RuntimeError("multi-entry Recall did not request one bounded selection")
        selected = next(item for item in recall["entries"] if any(value["statement_id"] == "dream:validation-one" for value in item["statements"]))
        recalled = apply_fast_recall_selection(
            json.dumps({"schema_version": FAST_RECALL_SCHEMA_VERSION, "outcome": "select", "entry_id": selected["entry_id"]}),
            recall["entries"], str(workspace), "validation-recall",
        )
        recall_local_ms = (perf_counter() - recall_started) * 1000
        with AccessMemoryLoop(workspace) as loop:
            binding_count = sum(1 for item in statements if loop.binding(item["statement_id"])["current_statement_id"] == item["statement_id"])

    events = [
        {"event": "capture", **capture},
        {"event": "batch_admission", "statement_count": 2, "formation_call_budget": 1, "placement_call_budget": 1, "independent_applied": 2, "binding_count": binding_count, "local_ms": batch_local_ms},
        {"event": "admission_replay", "replayed_statement_count": 2, "duplicate_write_count": 0},
        {"event": "admitted_recall", "hidden_call_count": recalled["hidden_call_count"], "statement_count": len(recalled["statement_ids"]), "local_ms": recall_local_ms},
    ]
    evidence = Path(args.evidence)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence_bytes = b"".join(canonical(item) for item in events)
    evidence.write_bytes(evidence_bytes)
    summary = {
        "schema_version": "nollm_aold_durable_capture_async_absorption_summary_v1",
        "status": "deterministic_validated_provider_live_pending",
        "provider_backed_live": False,
        "capture_publish_p50_ms": capture["capture_publish_p50_ms"],
        "capture_publish_p95_ms": capture["capture_publish_p95_ms"],
        "capture_publish_max_ms": capture["capture_publish_max_ms"],
        "pending_render_p95_ms": capture["pending_render_p95_ms"],
        "pending_render_max_ms": capture["pending_render_max_ms"],
        "batch_formation_call_budget": 1,
        "batch_placement_call_budget": 1,
        "admitted_recall_hidden_calls": recalled["hidden_call_count"],
        "evidence_lines": len(events),
        "evidence_bytes": len(evidence_bytes),
        "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
    }
    summary_path = Path(args.summary)
    summary_path.write_bytes(canonical(summary))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
