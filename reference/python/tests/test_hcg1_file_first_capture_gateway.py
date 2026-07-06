from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "reference" / "python" / "scripts" / "run_nollm_host_capture_gateway.py"
PYTHONPATH = str(ROOT / "reference" / "python")


def test_hcg1_01_capture_and_source_window_read_are_file_first(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    capture = _capture_payload("hcg1_01", "cap_hcg1_01", "HCG1 source-window alpha.", "source:hcg1:alpha")
    result = _run_gateway(tmp_path, "capture", workspace, capture)

    assert result["ok"] is True
    receipt = result["result"]["capture_receipt"]
    assert receipt["status"] == "captured"
    assert receipt["shard_id"].startswith("shard:ci1:")
    assert result["result"]["host_execution"]["completed_stages"] == ["capture"]

    read = _read_payload("hcg1_01_read", {"scope": "source_window", "context_ref": "source:hcg1:alpha"})
    read_result = _run_gateway(tmp_path, "read", workspace, read)
    assert read_result["ok"] is True
    assert [shard["shard_id"] for shard in read_result["result"]["shards"]] == [receipt["shard_id"]]
    assert read_result["result"]["shards"][0]["content"] == "HCG1 source-window alpha."
    assert "dream_shards" not in read_result["result"]
    assert "shard_ids" not in read_result["result"]
    _assert_no_stage_side_effects(workspace)


def test_hcg1_02_deferred_capture_publishes_candidate_without_admission(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    capture = _capture_payload(
        "hcg1_02",
        "cap_hcg1_02",
        "HCG1 deferred candidate beta.",
        "source:hcg1:beta",
        requested=True,
        triggers=["explicit_pin"],
        persistence="persistent",
        promotion_mode="manual",
    )
    result = _run_gateway(tmp_path, "capture", workspace, capture)

    receipt = result["result"]["capture_receipt"]
    assert result["ok"] is True
    assert receipt["status"] == "deferred"
    assert receipt["deferred_candidate_id"].startswith("dac:")
    _assert_no_stage_side_effects(workspace)


def test_hcg1_03_persistent_explicit_reads_selected_shards_with_public_dedupe(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    capture = _capture_payload(
        "hcg1_03",
        "cap_hcg1_03",
        "HCG1 persistent explicit gamma.",
        "source:hcg1:gamma",
        visibility="persistent_explicit",
        allowed_visibility=["persistent_explicit"],
        persistence="persistent",
        retention_class="durable",
    )
    result = _run_gateway(tmp_path, "capture", workspace, capture)
    shard_id = result["result"]["capture_receipt"]["shard_id"]

    read = _read_payload("hcg1_03_read", {"scope": "persistent_explicit", "shard_ids": [shard_id, shard_id]})
    read_result = _run_gateway(tmp_path, "read", workspace, read)
    assert read_result["ok"] is True
    assert [shard["shard_id"] for shard in read_result["result"]["shards"]] == [shard_id]
    assert read_result["result"]["shards"][0]["content"] == "HCG1 persistent explicit gamma."


def test_hcg1_04_context_windows_are_isolated_and_do_not_fallback(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    first = _run_gateway(tmp_path, "capture", workspace, _capture_payload("hcg1_04a", "cap_hcg1_04a", "Alpha isolated.", "source:hcg1:a"))
    second = _run_gateway(tmp_path, "capture", workspace, _capture_payload("hcg1_04b", "cap_hcg1_04b", "Beta isolated.", "source:hcg1:b"))

    read_a = _run_gateway(tmp_path, "read", workspace, _read_payload("hcg1_04_read_a", {"scope": "source_window", "context_ref": "source:hcg1:a"}))
    read_missing = _run_gateway(tmp_path, "read", workspace, _read_payload("hcg1_04_read_missing", {"scope": "source_window", "context_ref": "source:hcg1:missing"}))

    assert [shard["shard_id"] for shard in read_a["result"]["shards"]] == [first["result"]["capture_receipt"]["shard_id"]]
    assert second["result"]["capture_receipt"]["shard_id"] not in [shard["shard_id"] for shard in read_a["result"]["shards"]]
    assert read_missing["ok"] is True
    assert read_missing["result"]["shards"] == []


def test_hcg1_05_same_request_reopen_is_deterministic_and_read_only(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    payload = _capture_payload("hcg1_05", "cap_hcg1_05", "HCG1 reopen delta.", "source:hcg1:delta")
    first = _run_gateway(tmp_path, "capture", workspace, payload)
    ledger_before = (workspace / "evidence" / "ledger" / "events.jsonl").read_text(encoding="utf-8")
    second = _run_gateway(tmp_path, "capture", workspace, payload)
    ledger_after = (workspace / "evidence" / "ledger" / "events.jsonl").read_text(encoding="utf-8")

    assert second["ok"] is True
    assert second["result"]["host_execution"]["execution_input_fingerprint"] == first["result"]["host_execution"]["execution_input_fingerprint"]
    assert second["result"]["host_execution"]["output_fingerprint"] == first["result"]["host_execution"]["output_fingerprint"]
    assert ledger_after == ledger_before


def test_hcg1_06_same_request_id_drift_is_rejected_before_write(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    first_payload = _capture_payload("hcg1_06", "cap_hcg1_06", "HCG1 original epsilon.", "source:hcg1:epsilon")
    drift_payload = _capture_payload("hcg1_06", "cap_hcg1_06", "HCG1 changed epsilon.", "source:hcg1:epsilon")
    first = _run_gateway(tmp_path, "capture", workspace, first_payload)
    ledger_before = (workspace / "evidence" / "ledger" / "events.jsonl").read_text(encoding="utf-8")
    drift = _run_gateway(tmp_path, "capture", workspace, drift_payload, expect_success=False)

    assert first["ok"] is True
    assert drift["ok"] is False
    assert drift["error"]["code"] == "HCG_REOPEN_MISMATCH"
    assert (workspace / "evidence" / "ledger" / "events.jsonl").read_text(encoding="utf-8") == ledger_before


def test_hcg1_c1_05_preexisting_admission_and_cortex_bytes_are_preserved(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    first = _capture_payload("hcg1_c1_keep_first", "cap_hcg1_c1_keep_first", "HCG1 preserve first.", "source:hcg1:keep")
    assert _run_gateway(tmp_path, "capture", workspace, first)["ok"] is True

    admission_keep = workspace / "admission" / "keep.txt"
    cortex_keep = workspace / "cortex" / "keep.txt"
    admission_keep.parent.mkdir()
    cortex_keep.parent.mkdir()
    admission_bytes = b"admission sentinel bytes"
    cortex_bytes = b"cortex sentinel bytes"
    admission_keep.write_bytes(admission_bytes)
    cortex_keep.write_bytes(cortex_bytes)

    second = _capture_payload("hcg1_c1_keep_second", "cap_hcg1_c1_keep_second", "HCG1 preserve second.", "source:hcg1:keep")
    assert _run_gateway(tmp_path, "capture", workspace, second)["ok"] is True
    assert admission_keep.read_bytes() == admission_bytes
    assert cortex_keep.read_bytes() == cortex_bytes

    assert _run_gateway(tmp_path, "capture", workspace, second)["ok"] is True
    assert admission_keep.read_bytes() == admission_bytes
    assert cortex_keep.read_bytes() == cortex_bytes

    drift = _capture_payload("hcg1_c1_keep_second", "cap_hcg1_c1_keep_second", "HCG1 preserve drift.", "source:hcg1:keep")
    assert _run_gateway(tmp_path, "capture", workspace, drift, expect_success=False)["error"]["code"] == "HCG_REOPEN_MISMATCH"
    assert admission_keep.read_bytes() == admission_bytes
    assert cortex_keep.read_bytes() == cortex_bytes


def _run_gateway(tmp_path: Path, command: str, workspace: Path, payload: dict, *, expect_success: bool = True) -> dict:
    request_path = tmp_path / (payload["request_id"] + "_" + command + ".json")
    request_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": PYTHONPATH, "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), command, "--workspace", str(workspace), "--request", str(request_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        timeout=20,
    )
    assert completed.stderr == ""
    assert completed.stdout.endswith("\n")
    assert completed.stdout.count("\n") == 1
    result = json.loads(completed.stdout)
    assert completed.returncode == (0 if expect_success else 2)
    assert result["ok"] is expect_success
    if expect_success:
        assert result["warnings"] == []
    return result


def _capture_payload(
    request_id: str,
    capture_id: str,
    content: str,
    context_ref: str,
    *,
    visibility: str = "source_window",
    allowed_visibility: list[str] | None = None,
    requested: bool = False,
    triggers: list[str] | None = None,
    persistence: str = "captured",
    retention_class: str = "session",
    promotion_mode: str = "disabled",
) -> dict:
    return {
        "kind": "nollm_hcg_capture_request",
        "version": "1",
        "request_id": request_id,
        "capture": {
            "capture_id": capture_id,
            "content": content,
            "origin": {
                "kind": "user_utterance",
                "reference": "turn:" + request_id,
                "context_reference": context_ref,
                "role_label": "user",
            },
            "recorded_at": "2026-07-06T10:00:00+08:00",
            "context_refs": [context_ref],
            "requested_visibility_scope": visibility,
            "deferred_candidate_request": {"requested": requested, "trigger_refs": triggers or []},
            "diagnostic_retention_until": None,
        },
        "policy": {
            "policy_id": "cp_" + request_id,
            "policy_version": "1",
            "persistence": persistence,
            "lineage": "minimal",
            "diagnostics": "on_failure",
            "allowed_visibility_scopes": allowed_visibility or [visibility],
            "retention_class": retention_class,
            "promotion_mode": promotion_mode,
        },
    }


def _read_payload(request_id: str, selector: dict) -> dict:
    return {"kind": "nollm_hcg_read_request", "version": "1", "request_id": request_id, "selector": selector}


def _assert_no_stage_side_effects(workspace: Path) -> None:
    for name in ("admission", "assembly", "field", "recall", "cache", "database", "global-field"):
        assert not (workspace / name).exists()
