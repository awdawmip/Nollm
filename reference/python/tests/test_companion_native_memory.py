from __future__ import annotations

import json
import sys
import subprocess
import threading
from pathlib import Path

import pytest

from nollm.companion_memory_store import (
    CompanionMemoryError,
    get_native_memory,
    native_store_summary,
    recall_native_memory,
    remember_native_memory,
)
from nollm.openclaw_memory_adapter import (
    get_native_companion_memory,
    recall_native_companion_memory,
    remember_native_companion_memory,
    sidecar_status,
)
from subprocess_harness import run_subprocess, subprocess_failure_message

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "reference/python/scripts/run_openclaw_nollm_memory.py"


def _out_dir(tmp_path: Path) -> Path:
    return tmp_path / "sidecar"


def test_p1_native_remember_writes_one_valid_record(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    result = remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity", scope="user")

    assert result["ok"] is True
    assert result["created"] is True
    assert result["deduplicated"] is False
    assert result["memory_id"].startswith("nmem_")
    assert result["shard_id"].startswith("shard_")
    assert result["revision_id"].startswith("nrev_")
    assert result["text_excerpt"] == "用户叫卡卡布拉。"
    assert result["store"] == "nollm_native_companion"

    store_dir = out / "native-companion-v1"
    assert (store_dir / "manifest.json").exists()
    assert (store_dir / "records.jsonl").exists()
    assert (store_dir / "index.json").exists()
    assert native_store_summary(out)["record_count"] == 1


def test_p2_repeated_canonical_memory_deduplicates(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    first = remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity")
    second = remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity")

    assert first["memory_id"] == second["memory_id"]
    assert second["created"] is False
    assert second["deduplicated"] is True
    assert native_store_summary(out)["record_count"] == 1


def test_p3_native_recall_identity_alias_returns_identity_record(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity")
    result = recall_native_memory(ROOT, tmp_path / "workspace", out, query="我叫什么？", limit=5)

    assert result["ok"] is True
    assert len(result["results"]) == 1
    assert result["results"][0]["text"] == "用户叫卡卡布拉。"
    assert result["results"][0]["kind"] == "identity"


def test_p4_native_recall_preference_alias_returns_preference_record(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户偏好简洁回答。", kind="preference")
    result = recall_native_memory(ROOT, tmp_path / "workspace", out, query="我偏好什么？", limit=5)

    assert result["ok"] is True
    assert len(result["results"]) == 1
    assert result["results"][0]["text"] == "用户偏好简洁回答。"
    assert result["results"][0]["kind"] == "preference"


def test_p5_native_get_accepts_only_nmem_native_id(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    stored = remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity")
    result = get_native_memory(ROOT, tmp_path / "workspace", out, stored["memory_id"])

    assert result["ok"] is True
    assert result["record"]["text"] == "用户叫卡卡布拉。"

    with pytest.raises(CompanionMemoryError):
        get_native_memory(ROOT, tmp_path / "workspace", out, "not_a_native_id")


def test_p6_file_path_and_legacy_locator_rejects(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    for bad_id in ["file:MEMORY.md", "C:/memory.md", "nollm://legacy/foo", "memory/2026-06-21.md:1-3"]:
        with pytest.raises(CompanionMemoryError):
            get_native_memory(ROOT, tmp_path / "workspace", out, bad_id)


def test_p7_secret_like_input_rejects_with_no_write(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    with pytest.raises(CompanionMemoryError) as exc_info:
        remember_native_memory(ROOT, tmp_path / "workspace", out, memory="Bearer abc123secret")
    assert exc_info.value.code == "memory_content_rejected"
    assert native_store_summary(out)["record_count"] == 0


def test_p8_malformed_records_fails_structured(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity")
    records_path = out / "native-companion-v1" / "records.jsonl"
    records_path.write_text(records_path.read_text(encoding="utf-8") + "not valid json\n", encoding="utf-8")

    with pytest.raises(CompanionMemoryError) as exc_info:
        recall_native_memory(ROOT, tmp_path / "workspace", out, query="卡卡布拉")
    assert exc_info.value.code == "corrupt_records"


def test_p9_legacy_source_files_unchanged(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    memory = workspace / "MEMORY.md"
    memory.write_text("# Legacy\n\nOriginal content.\n", encoding="utf-8")
    before = _source_hashes(workspace)
    remember_native_memory(ROOT, workspace, _out_dir(tmp_path), memory="用户叫卡卡布拉。", kind="identity")
    assert _source_hashes(workspace) == before


def test_p10_records_survive_process_restart(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity")
    result = recall_native_memory(ROOT, tmp_path / "workspace", out, query="我叫什么？", limit=5)
    assert result["results"]


def test_p11_revision_id_changes_only_on_actual_store_change(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    first = remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity")
    second = remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity")
    third = remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户偏好简洁回答。", kind="preference")

    assert first["revision_id"] == second["revision_id"]
    assert third["revision_id"] != first["revision_id"]


def test_p12_status_reports_native_store_count_and_revision(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    remember_native_memory(ROOT, tmp_path / "workspace", out, memory="用户叫卡卡布拉。", kind="identity")
    status = sidecar_status(ROOT, tmp_path / "workspace", out)

    assert status["ok"] is True
    native = status["native_companion_memory"]
    assert native["record_count"] == 1
    assert native["store_available"] is True
    assert native["active_revision_id"].startswith("nrev_")


def test_p13_concurrent_duplicate_writes_produce_one_active_record(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    procs: list[subprocess.Popen[str]] = []
    for _ in range(6):
        p = subprocess.Popen(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(ROOT),
                "native-remember",
                "--workspace",
                str(workspace),
                "--out",
                str(out),
                "--memory",
                "用户叫卡卡布拉。",
                "--kind",
                "identity",
                "--scope",
                "user",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        procs.append(p)
    results: list[dict[str, object]] = []
    for p in procs:
        stdout, _stderr = p.communicate(timeout=60)
        results.append(json.loads(stdout) if stdout.strip() else {})

    assert sum(1 for r in results if r.get("ok")) == 6
    assert sum(1 for r in results if r.get("created")) == 1
    assert sum(1 for r in results if r.get("deduplicated")) == 5
    assert native_store_summary(out)["record_count"] == 1

    records_path = out / "native-companion-v1" / "records.jsonl"
    records = [
        json.loads(line)
        for line in records_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len([r for r in records if r.get("status") == "active"]) == 1


def test_p14_adapter_exposes_native_commands(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    remembered = remember_native_companion_memory(
        ROOT, tmp_path / "workspace", out, memory="W1 adapter memory.", kind="note", scope="user"
    )
    assert remembered["ok"] is True

    recalled = recall_native_companion_memory(ROOT, tmp_path / "workspace", out, query="W1 adapter")
    assert recalled["ok"] is True
    assert len(recalled["results"]) == 1

    fetched = get_native_companion_memory(ROOT, tmp_path / "workspace", out, remembered["memory_id"])
    assert fetched["ok"] is True
    assert fetched["record"]["text"] == "W1 adapter memory."


def test_cli_native_remember_recall_and_get(tmp_path: Path) -> None:
    out = _out_dir(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    remember = _run_cli(
        "native-remember",
        "--workspace", str(workspace),
        "--out", str(out),
        "--memory", "用户喜欢紫色标签。",
        "--kind", "preference",
        "--scope", "user",
    )
    assert remember["ok"] is True
    assert remember["memory_id"].startswith("nmem_")

    recall = _run_cli("native-recall", "--workspace", str(workspace), "--out", str(out), "--query", "喜欢什么标签颜色？")
    assert recall["ok"] is True
    assert any("紫色标签" in r["text"] for r in recall["results"])

    fetched = _run_cli("native-get", "--workspace", str(workspace), "--out", str(out), "--id", remember["memory_id"])
    assert fetched["ok"] is True
    assert fetched["record"]["text"] == "用户喜欢紫色标签。"

    repeated = _run_cli(
        "native-remember",
        "--workspace", str(workspace),
        "--out", str(out),
        "--memory", "用户喜欢紫色标签。",
        "--kind", "preference",
        "--scope", "user",
    )
    assert repeated["deduplicated"] is True
    assert native_store_summary(out)["record_count"] == 1

    secret_result = run_subprocess(
        [sys.executable, str(SCRIPT), "native-remember", "--workspace", str(workspace), "--out", str(out), "--memory", "sk-abc123", "--kind", "note"],
        cwd=ROOT / "reference/python",
        timeout_seconds=60,
    )
    secret = json.loads(secret_result.stdout)
    assert secret["ok"] is False
    assert secret["error"] == "memory_content_rejected"
    assert native_store_summary(out)["record_count"] == 1


def _run_cli(*args: str) -> dict[str, object]:
    result = run_subprocess(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT / "reference/python",
        timeout_seconds=60,
    )
    assert result.returncode == 0, subprocess_failure_message(result, ROOT / "reference/python")
    return json.loads(result.stdout)


def _source_hashes(workspace: Path) -> dict[str, str]:
    import hashlib

    paths = [workspace / "MEMORY.md", workspace / "DREAMS.md", *sorted((workspace / "memory").glob("*.md"))]
    return {path.relative_to(workspace).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.exists()}
