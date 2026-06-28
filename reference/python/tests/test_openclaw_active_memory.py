from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from nollm.companion_memory_store import remember_native_memory, native_store_summary
from nollm.openclaw_active_memory_adapter import (
    active_capture,
    active_prepare,
    active_status,
    active_trial_report,
)

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "reference/python/scripts/run_openclaw_nollm_active_memory.py"
IDENTITY = {"agent_id": "agent-1", "session_id": "session-1", "run_id": "run-1"}


def _out_dir(tmp_path: Path) -> Path:
    return tmp_path / ".nollm-memory"


def _native_store_root(tmp_path: Path) -> Path:
    return _out_dir(tmp_path) / "native-companion-v1"


def _trial_root(tmp_path: Path) -> Path:
    return _out_dir(tmp_path) / "active-trials"


def _seed_identity(tmp_path: Path) -> None:
    remember_native_memory(ROOT, tmp_path / "workspace", _out_dir(tmp_path), memory="用户叫卡卡布拉。", kind="identity")


def _seed_preference(tmp_path: Path) -> None:
    remember_native_memory(ROOT, tmp_path / "workspace", _out_dir(tmp_path), memory="用户喜欢紫色标签。", kind="preference")


def _seed_project(tmp_path: Path) -> None:
    remember_native_memory(ROOT, tmp_path / "workspace", _out_dir(tmp_path), memory="项目决定周五发版。", kind="project")


def _source_hashes(workspace: Path) -> dict[str, str]:
    paths = [workspace / "MEMORY.md", workspace / "DREAMS.md", *sorted((workspace / "memory").glob("*.md"))]
    return {path.relative_to(workspace).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.exists()}


def test_p1_active_prepare_uses_native_store_not_alpha_fixture(tmp_path: Path) -> None:
    _seed_identity(tmp_path)
    result = active_prepare(
        _native_store_root(tmp_path),
        "我叫什么？",
        {"max_facts": 4, "max_context_characters": 1400},
    )
    assert result["ok"] is True
    assert result["schema"] == "nollm.provider.prepare.v2"
    assert result["context"]["schema"] == "NOLLM_MEMORY_CONTEXT_V1"
    assert result["context"]["freshness"] == "fresh"
    assert len(result["context"]["facts"]) == 1
    assert "卡卡布拉" in result["context"]["facts"][0]["claim"]


def test_p2_active_prepare_does_not_touch_legacy_files(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "MEMORY.md").write_text("# Legacy\n\nOriginal.\n", encoding="utf-8")
    before = _source_hashes(workspace)
    _seed_identity(tmp_path)
    result = active_prepare(
        _native_store_root(tmp_path),
        "明天东京天气怎样？",
        {"max_facts": 4, "max_context_characters": 1400},
    )
    assert result["context"]["freshness"] == "none"
    assert _source_hashes(workspace) == before


def test_p3_active_prepare_returns_relevant_kind_facts(tmp_path: Path) -> None:
    _seed_identity(tmp_path)
    _seed_preference(tmp_path)
    _seed_project(tmp_path)

    identity = active_prepare(_native_store_root(tmp_path), "我叫什么？", {"max_facts": 4, "max_context_characters": 1400})
    assert len(identity["context"]["facts"]) == 1
    assert identity["context"]["facts"][0]["kind"] == "identity"

    preference = active_prepare(_native_store_root(tmp_path), "我偏好什么？", {"max_facts": 4, "max_context_characters": 1400})
    assert len(preference["context"]["facts"]) == 1
    assert preference["context"]["facts"][0]["kind"] == "preference"

    project = active_prepare(_native_store_root(tmp_path), "项目何时发版？", {"max_facts": 4, "max_context_characters": 1400})
    assert len(project["context"]["facts"]) == 1
    assert project["context"]["facts"][0]["kind"] == "project"


def test_p4_active_prepare_unrelated_query_returns_no_facts(tmp_path: Path) -> None:
    _seed_identity(tmp_path)
    result = active_prepare(_native_store_root(tmp_path), "明天东京天气怎样？", {"max_facts": 4, "max_context_characters": 1400})
    assert result["context"]["freshness"] == "none"
    assert result["context"]["facts"] == []
    assert result["metrics"]["recall_mode"] == "none"


def test_p4b_active_prepare_weather_query_with_response_instruction_returns_no_facts(tmp_path: Path) -> None:
    _seed_identity(tmp_path)
    _seed_preference(tmp_path)
    result = active_prepare(
        _native_store_root(tmp_path),
        "明天东京天气如何？不要使用工具。简短回答。",
        {"max_facts": 4, "max_context_characters": 1400},
    )
    assert result["context"]["freshness"] == "none"
    assert result["context"]["facts"] == []
    assert result["metrics"]["recall_mode"] == "none"


def test_p5_active_prepare_respects_max_context_characters(tmp_path: Path) -> None:
    for i in range(5):
        remember_native_memory(
            ROOT, tmp_path / "workspace", _out_dir(tmp_path),
            memory=f"这是一段很长的占位记忆内容用于测试预算限制编号 {i}。" + "重复" * 20,
            kind="note",
        )
    result = active_prepare(
        _native_store_root(tmp_path),
        "有哪些记忆？",
        {"max_facts": 5, "max_context_characters": 400},
    )
    assert result["ok"] is True
    assert result["metrics"]["rendered_context_characters"] <= 400


def test_p6_active_capture_explicit_remember_promotes(tmp_path: Path) -> None:
    result = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "请记住：我的 W2-01 标签颜色偏好是 CORAL-SIGNAL-22。"}],
        success=True,
        identity=IDENTITY,
    )
    assert result["ok"] is True
    assert result["capture"]["promoted_count"] == 1
    assert native_store_summary(_out_dir(tmp_path))["record_count"] == 1

    recalled = active_prepare(_native_store_root(tmp_path), "我偏好什么？", {"max_facts": 4, "max_context_characters": 1400})
    assert recalled["context"]["freshness"] == "fresh"
    assert "CORAL-SIGNAL-22" in recalled["context"]["facts"][0]["claim"]


def test_p7_active_capture_identity_name_promotes(tmp_path: Path) -> None:
    result = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "我叫卡卡布拉。"}],
        success=True,
        identity=IDENTITY,
    )
    assert result["capture"]["promoted_count"] == 1
    assert native_store_summary(_out_dir(tmp_path))["record_count"] == 1


def test_p8_active_capture_preference_promotes(tmp_path: Path) -> None:
    result = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "我偏好简洁回答。"}],
        success=True,
        identity=IDENTITY,
    )
    assert result["capture"]["promoted_count"] == 1
    assert result["capture"]["records"][0]["kind"] == "preference"


def test_p9_active_capture_project_decision_promotes(tmp_path: Path) -> None:
    result = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "项目决定周五发版。"}],
        success=True,
        identity=IDENTITY,
    )
    assert result["capture"]["promoted_count"] == 1
    assert result["capture"]["records"][0]["kind"] == "project"


def test_p10_active_capture_rejects_history_batch(tmp_path: Path) -> None:
    result = active_capture(
        _native_store_root(tmp_path),
        [
            {"role": "assistant", "content": "我叫卡卡布拉。"},
            {"role": "user", "content": "好的。"},
        ],
        success=True,
        identity=IDENTITY,
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_event"
    assert native_store_summary(_out_dir(tmp_path))["record_count"] == 0


def test_p11_active_capture_ordinary_question_suppressed(tmp_path: Path) -> None:
    result = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "明天东京天气怎样？"}],
        success=True,
        identity=IDENTITY,
    )
    assert result["capture"]["promoted_count"] == 0
    assert native_store_summary(_out_dir(tmp_path))["record_count"] == 0


def test_p11b_active_capture_marker_question_suppressed(tmp_path: Path) -> None:
    result = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "我的 W2-02 身份 marker 是什么？"}],
        success=True,
        identity=IDENTITY,
    )
    assert result["capture"]["promoted_count"] == 0
    assert native_store_summary(_out_dir(tmp_path))["record_count"] == 0


def test_p12_active_capture_duplicate_deduplicates(tmp_path: Path) -> None:
    first = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "我叫卡卡布拉。"}],
        success=True,
        identity=IDENTITY,
    )
    second = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "我叫卡卡布拉。"}],
        success=True,
        identity=IDENTITY,
    )
    assert first["capture"]["promoted_count"] == 1
    assert second["capture"]["deduplicated_count"] == 1
    assert native_store_summary(_out_dir(tmp_path))["record_count"] == 1


def test_p13_active_capture_secret_rejected(tmp_path: Path) -> None:
    result = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "请记住：Bearer W2-01-NOT-A-REAL-SECRET"}],
        success=True,
        identity=IDENTITY,
    )
    assert result["capture"]["rejected_count"] == 1
    assert result["capture"]["promoted_count"] == 0
    assert native_store_summary(_out_dir(tmp_path))["record_count"] == 0


def test_p14_active_capture_malformed_input_no_side_effect(tmp_path: Path) -> None:
    missing_success = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "我叫卡卡布拉。"}],
        success=False,
        identity=IDENTITY,
    )
    assert missing_success["capture"]["promoted_count"] == 0

    bad_messages = active_capture(
        _native_store_root(tmp_path),
        "not a list",  # type: ignore[arg-type]
        success=True,
        identity=IDENTITY,
    )
    assert bad_messages["ok"] is False
    assert bad_messages["error"]["code"] == "invalid_event"

    missing_identity = active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "我叫卡卡布拉。"}],
        success=True,
    )
    assert missing_identity["ok"] is False
    assert missing_identity["error"]["code"] == "active_identity_incomplete"
    assert native_store_summary(_out_dir(tmp_path))["record_count"] == 0


def test_p15_active_trial_ledger_contains_only_hashes_and_metrics(tmp_path: Path) -> None:
    trial_id = "test-p15"
    active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "我叫卡卡布拉。"}],
        success=True,
        trial_id=trial_id,
        identity={"agent_id": "a1", "session_id": "s1", "run_id": "r1"},
        trial_root=_trial_root(tmp_path),
    )
    metrics_path = _trial_root(tmp_path) / trial_id / "trial-metrics.jsonl"
    assert metrics_path.exists()
    for line in metrics_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        raw = json.dumps(record, ensure_ascii=False)
        assert "卡卡布拉" not in raw
        assert "a1" not in raw and "s1" not in raw and "r1" not in raw
        assert "query_hash" in raw or "event_id" in raw


def test_p16_legacy_source_files_unchanged_after_capture(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "MEMORY.md").write_text("# Legacy\n\nOriginal.\n", encoding="utf-8")
    (workspace / "memory").mkdir(exist_ok=True)
    (workspace / "memory" / "note.md").write_text("note\n", encoding="utf-8")
    before = _source_hashes(workspace)
    active_capture(
        _native_store_root(tmp_path),
        [{"role": "user", "content": "我叫卡卡布拉。"}],
        success=True,
    )
    assert _source_hashes(workspace) == before


def test_p17_active_status_has_only_safe_runtime_fields(tmp_path: Path) -> None:
    remember_native_memory(ROOT, tmp_path / "workspace", _out_dir(tmp_path), memory="用户叫卡卡布拉。", kind="identity")
    status = active_status(_native_store_root(tmp_path))
    assert status["ok"] is True
    assert status["schema"] == "nollm.active_memory_status.v1"
    assert status["store"] == "nollm_native_companion"
    assert isinstance(status["native_record_count"], int)
    assert status["capture_mode"] == "deterministic_explicit_v1"
    allowed = {
        "schema",
        "ok",
        "store",
        "native_record_count",
        "active_revision_id",
        "python_executable",
        "capture_mode",
        "trial_mode",
    }
    forbidden = {"messages", "transcript", "session_id", "run_id", "raw_message", "environment", "env", "command_line"}
    assert set(status) == allowed
    assert not (set(status) & forbidden)


def test_p18_store_survives_active_sidecar_process_restart(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    native_store_root = _native_store_root(tmp_path)
    trial_root = _trial_root(tmp_path)
    capture_payload = {
        "command": "active-capture",
        "schema": "nollm.active_memory_capture.v1",
        "agent_id": "a1",
        "session_id": "s1",
        "run_id": "r1",
        "success": True,
        "messages": [{"role": "user", "content": "我的 W2-02 身份 marker 是 HARBOR-ONYX-51。"}],
        "trial_id": "w2-p18",
    }
    capture_result = _run_active_subprocess(native_store_root, trial_root, capture_payload)
    assert capture_result["ok"] is True
    assert capture_result["capture"]["promoted_count"] == 1

    prepare_payload = {
        "command": "active-prepare",
        "schema": "nollm.active_memory_prepare.v1",
        "agent_id": "a1",
        "session_id": "s1",
        "run_id": "r1",
        "query": "我的 W2-02 身份 marker 是什么？",
        "budget": {"max_facts": 4, "max_context_characters": 1400},
        "trial_id": "w2-p18",
    }
    prepare_result = _run_active_subprocess(native_store_root, trial_root, prepare_payload)
    assert prepare_result["ok"] is True
    assert prepare_result["context"]["freshness"] == "fresh"
    assert any("HARBOR-ONYX-51" in f["claim"] for f in prepare_result["context"]["facts"])

    report = active_trial_report(native_store_root, "w2-p18", trial_root=trial_root)
    assert report["capture_count"] >= 1
    assert report["prepare_count"] >= 1



def test_p19_active_capture_replay_receipt_excludes_duplicate_metric(tmp_path: Path) -> None:
    trial_id = "test-p19"
    trial_root = _trial_root(tmp_path)
    payload = [{"role": "user", "content": "我的 W2-03 身份 marker 是 MIST-COPPER-81。"}]
    first = active_capture(
        _native_store_root(tmp_path),
        payload,
        success=True,
        trial_id=trial_id,
        identity=IDENTITY,
        trial_root=trial_root,
    )
    second = active_capture(
        _native_store_root(tmp_path),
        payload,
        success=True,
        trial_id=trial_id,
        identity=IDENTITY,
        trial_root=trial_root,
    )
    assert first["capture"]["promoted_count"] == 1
    assert second["capture"]["reused_duplicate"] is True
    assert second["capture"]["promoted_count"] == 0
    assert second["capture"]["deduplicated_count"] == 0
    assert native_store_summary(_out_dir(tmp_path))["record_count"] == 1

    metrics_path = trial_root / trial_id / "trial-metrics.jsonl"
    metrics = [json.loads(line) for line in metrics_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    capture_metrics = [m for m in metrics if m.get("event") == "capture"]
    assert len(capture_metrics) == 1

    report = active_trial_report(_native_store_root(tmp_path), trial_id, trial_root=trial_root)
    assert report["capture_count"] == 1


def _run_active_subprocess(native_store_root: Path, trial_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    command = [
        sys.executable,
        str(SCRIPT),
        "--native-store-root", str(native_store_root),
        "--trial-root", str(trial_root),
    ]
    stdin = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    arbitrary_cwd = native_store_root.parent
    arbitrary_cwd.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        command,
        input=stdin,
        text=True,
        encoding="utf-8",
        cwd=arbitrary_cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    stdout_text = result.stdout
    stderr_text = result.stderr
    assert result.returncode == 0, f"exit={result.returncode}\nstdout={stdout_text}\nstderr={stderr_text}"
    return json.loads(stdout_text)
