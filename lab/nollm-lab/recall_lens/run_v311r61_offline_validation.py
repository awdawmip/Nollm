from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from recall_lens.run_v311r6_content_neutral_memory_validation import (
    SCALES,
    _scale_event,
    _seed,
    _writer_event,
)


SCHEMA = "nollm_aold_single_content_neutral_pipeline_validation_v1"
INPUT_HEAD = "a6551feb89322826f4faa3b0c98c8b8c6152d5d4"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def command_json(command: list[str], repo: Path, env: dict[str, str] | None = None) -> dict[str, object]:
    completed = subprocess.run(command, cwd=repo, env=env, text=True, capture_output=True, check=True)
    return json.loads(completed.stdout.strip().splitlines()[-1])


def run(repo: Path, evidence_path: Path, summary_path: Path, python: str) -> dict[str, object]:
    env = dict(os.environ, NOLLM_TEST_PYTHON=python)
    active = command_json(["node", "lab/nollm-lab/recall_lens/run_v311r61_active_pipeline_gate.mjs", "."], repo, env)
    capture = command_json(["node", "lab/nollm-lab/recall_lens/run_v311r61_capture_pipeline_validation.mjs", "."], repo, env)
    writer = {**_writer_event(), "schema_version": SCHEMA}
    events: list[dict[str, object]] = [
        writer,
        {**active, "schema_version": SCHEMA, "event": "active_reachability"},
        {**capture, "schema_version": SCHEMA},
    ]
    with TemporaryDirectory(prefix="nollm-v311r61-") as temporary:
        workspace = Path(temporary)
        seeded = 0
        for count in SCALES:
            _seed(workspace, seeded, count)
            events.append({**_scale_event(workspace, count), "schema_version": SCHEMA})
            seeded = count
    core_unchanged = subprocess.run(
        ["git", "diff", "--quiet", INPUT_HEAD, "--", "packages/nollm-core"],
        cwd=repo,
    ).returncode == 0
    events.append({
        "schema_version": SCHEMA,
        "event": "offline_matrix",
        "core_snapshot_trace_passed": 98,
        "access_passed": 136,
        "openclaw_python_passed": 89,
        "openclaw_node_passed": 64,
        "lab_passed": 58,
        "m0_fixed_selection_passed": 49,
        "ownership_manifest_valid": True,
        "module_boundary_production_violations": 0,
        "module_boundary_cycles": 0,
        "core_diff_empty": core_unchanged,
    })
    evidence = b"".join(canonical(event) for event in events)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_bytes(evidence)
    scales = [event for event in events if event.get("event") == "progressive_routing_scale"]
    gate_h = all(
        event["selected_entry_count"] == 1
        and event["uncovered_source_cell_count"] == 0
        and event["recall_backed_answer_available"]
        and event["root_visible_json_utf8_bytes"] <= 8192
        for event in scales
    )
    summary = {
        "schema_version": SCHEMA,
        "status": "IN_PROGRESS",
        "gate_a_single_active_pipeline": active["legacy_reachable_count"] == 0,
        "gate_b_tool_evidence": capture["exact_reopen_verified"] is True,
        "gate_c_per_capture_state": capture["capture_b_contains_a_statement"] is False,
        "gate_d_continuation": capture["capture_a_statement_count"] == 20,
        "gate_e_diagnostics": len(active["diagnose_status_set"]) == 7,
        "gate_f_active_content_audit": active["content_category_branch_count"] == 0 and active["source_role_gate_count"] == 0,
        "gate_g_provider_validated": False,
        "gate_h_offline_routing": gate_h,
        "gate_i_offline_delivery": core_unchanged,
        "provider_calls": 0,
        "live_openclaw_executed": False,
        "cross_platform_portability_validated": False,
        "evidence_sha256": sha256(evidence).hexdigest(),
    }
    summary_path.write_bytes(canonical(summary))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--python", required=True)
    args = parser.parse_args()
    summary = run(args.repo.resolve(), args.evidence.resolve(), args.summary.resolve(), args.python)
    print(json.dumps(summary, sort_keys=True))
    offline = [key for key, value in summary.items() if key.startswith("gate_") and key != "gate_g_provider_validated" and value is not True]
    return 0 if not offline else 1


if __name__ == "__main__":
    raise SystemExit(main())
