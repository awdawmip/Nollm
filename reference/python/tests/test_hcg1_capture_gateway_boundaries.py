from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from test_hcg1_file_first_capture_gateway import ROOT, SCRIPT, _capture_payload


def test_hcg1_07_strict_json_rejects_unknown_missing_and_duplicates(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    unknown = _capture_payload("hcg1_07_unknown", "cap_hcg1_07_unknown", "Unknown field.", "source:hcg1:unknown")
    unknown["capture_request"]["query_text"] = "forbidden"
    assert _run_raw(tmp_path, "capture", workspace, json.dumps(unknown))["error"]["code"] == "HCG_INVALID_REQUEST"

    missing = _capture_payload("hcg1_07_missing", "cap_hcg1_07_missing", "Missing field.", "source:hcg1:missing")
    del missing["capture_request"]["content"]
    assert _run_raw(tmp_path, "capture", workspace, json.dumps(missing))["error"]["code"] == "HCG_INVALID_REQUEST"

    duplicate = '{"request_id":"hcg1_07_dup","request_id":"hcg1_07_dup2"}'
    assert _run_raw(tmp_path, "capture", workspace, duplicate)["error"]["code"] == "HCG_INVALID_JSON"


def test_hcg1_08_ephemeral_and_current_turn_are_rejected_without_workspace_writes(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    payload = _capture_payload(
        "hcg1_08",
        "cap_hcg1_08",
        "Ephemeral rejected.",
        "source:hcg1:ephemeral",
        visibility="current_turn",
        allowed_visibility=["current_turn"],
        persistence="ephemeral",
        retention_class="transient",
        promotion_mode="disabled",
    )
    payload["capture_policy"]["lineage"] = "none"
    payload["capture_policy"]["diagnostics"] = "off"
    result = _run_raw(tmp_path, "capture", workspace, json.dumps(payload))
    assert result["error"]["code"] == "HCG_UNSUPPORTED_CAPTURE_MODE"
    assert not workspace.exists()


def test_hcg1_09_workspace_marker_and_repo_root_boundaries_are_enforced(tmp_path) -> None:
    valid_payload = _capture_payload("hcg1_09", "cap_hcg1_09", "Repo root rejected.", "source:hcg1:repo")
    repo_result = _run_raw(tmp_path, "capture", ROOT, json.dumps(valid_payload))
    assert repo_result["error"]["code"] == "HCG_WORKSPACE_NOT_OWNED"
    _assert_no_path_leak(repo_result)

    read_payload = {"request_id": "hcg1_09_read", "selector": {"scope": "source_window", "context_ref": "source:hcg1:repo"}}
    missing = _run_raw(tmp_path, "read", tmp_path / "missing", json.dumps(read_payload))
    assert missing["error"]["code"] == "HCG_WORKSPACE_NOT_OWNED"

    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / ".hx1_host_execution_root.json").write_text(json.dumps({"owner": "other"}), encoding="utf-8")
    foreign_result = _run_raw(tmp_path, "read", foreign, json.dumps(read_payload))
    assert foreign_result["error"]["code"] == "HCG_WORKSPACE_NOT_OWNED"


def test_hcg1_10_error_stdout_is_single_sanitized_json_envelope(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    payload = {"request_id": "hcg1_10", "selector": {"scope": "source_window", "query_text": "nope"}}
    request_path = tmp_path / "bad_read.json"
    request_path.write_text(json.dumps(payload), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "read", "--workspace", str(workspace), "--request", str(request_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=_env(),
        timeout=20,
    )
    assert completed.returncode == 2
    assert completed.stderr == ""
    assert completed.stdout.count("\n") == 1
    result = json.loads(completed.stdout)
    assert result["error"]["code"] == "HCG_UNSUPPORTED_READ_SELECTOR"
    _assert_no_path_leak(result)


def _run_raw(tmp_path: Path, command: str, workspace: Path, text: str) -> dict:
    request_path = tmp_path / (command + "_" + str(abs(hash(text))) + ".json")
    request_path.write_text(text, encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), command, "--workspace", str(workspace), "--request", str(request_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=_env(),
        timeout=20,
    )
    assert completed.returncode == 2
    assert completed.stderr == ""
    return json.loads(completed.stdout)


def _env() -> dict[str, str]:
    return {**os.environ, "PYTHONPATH": str(ROOT / "reference" / "python"), "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}


def _assert_no_path_leak(payload: dict) -> None:
    rendered = json.dumps(payload, sort_keys=True)
    assert str(ROOT) not in rendered
    assert "Traceback" not in rendered
    assert "nollm.dream_geometry" not in rendered
    assert ".py" not in rendered
