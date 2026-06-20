from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.openclaw_memory_adapter import (
    FORBIDDEN_SEMANTICS,
    build_sidecar_store,
    get_sidecar_item,
    parse_openclaw_memory_workspace,
    search_sidecar,
    sidecar_status,
    write_candidate,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference/python"
FIXTURE = ROOT / "examples/openclaw_memory_fixture"
SCRIPT = REFERENCE_PYTHON / "scripts/run_openclaw_nollm_memory.py"


def test_sidecar_index_is_deterministic(tmp_path: Path) -> None:
    first_out = tmp_path / "first"
    second_out = tmp_path / "second"

    first = build_sidecar_store(ROOT, FIXTURE, first_out)
    second = build_sidecar_store(ROOT, FIXTURE, second_out)

    assert first["candidate_count"] == second["candidate_count"]
    assert first["shard_count"] == second["shard_count"]
    assert first["geometry_mark_count"] == second["geometry_mark_count"]
    for name in ["candidates.jsonl", "shards.jsonl", "geometry_marks.jsonl"]:
        left = (first_out / name).read_text(encoding="utf-8")
        right = (second_out / name).read_text(encoding="utf-8")
        assert left == right
    left_manifest = json.loads((first_out / "sidecar_manifest.json").read_text(encoding="utf-8"))
    right_manifest = json.loads((second_out / "sidecar_manifest.json").read_text(encoding="utf-8"))
    left_manifest["out_dir"] = "<out>"
    right_manifest["out_dir"] = "<out>"
    assert left_manifest == right_manifest


def test_sidecar_candidates_preserve_source_paths_and_line_ranges(tmp_path: Path) -> None:
    build_sidecar_store(ROOT, FIXTURE, tmp_path)
    candidates = _read_jsonl(tmp_path / "candidates.jsonl")

    assert candidates
    for candidate in candidates:
        assert "\\" not in candidate["source_path"]
        assert candidate["line_start"] >= 1
        assert candidate["line_start"] <= candidate["line_end"]
        assert candidate["version_status"] == "fixture_current"
        assert candidate["trust_level"] == "unverified_fixture"
    assert {item["source_kind"] for item in candidates} >= {"long_term", "daily"}
    assert {item["source_kind"] for item in candidates} >= {"dream"}
    assert any(item.get("date") == "2026-06-19" for item in candidates)


def test_sidecar_search_get_status_and_gravity_reports(tmp_path: Path) -> None:
    search = search_sidecar(ROOT, FIXTURE, tmp_path, query="gravity report", limit=5)
    status = sidecar_status(ROOT, FIXTURE, tmp_path)
    first = search["results"][0]
    get_by_candidate = get_sidecar_item(ROOT, FIXTURE, tmp_path, first["candidate_id"])
    get_by_memory = get_sidecar_item(ROOT, FIXTURE, tmp_path, first["memory_id"])
    get_by_shard = get_sidecar_item(ROOT, FIXTURE, tmp_path, first["shard_id"])

    assert search["ok"] is True
    assert search["result_count"] > 0
    assert "gravity_report" in first
    assert {"memory_id", "candidate_id", "shard_id", "line_range", "provenance"} <= set(first)
    assert first["provenance"]["source_ref"] == f"{first['source_path']}:{first['line_start']}-{first['line_end']}"
    assert {"R_column_ring", "S_scale_delta", "A_anchor_similarity", "drift_class"} <= set(first["gravity_report"])
    assert "trust" not in first["gravity_report"]
    assert "status" in first["gravity_report"]
    assert get_by_candidate["ok"] is True
    assert get_by_memory["ok"] is True
    assert get_by_shard["ok"] is True
    assert get_by_candidate["candidate"]["candidate_id"] == first["candidate_id"]
    assert get_by_memory["candidate"]["candidate_id"] == first["candidate_id"]
    assert get_by_shard["candidate"]["candidate_id"] == first["candidate_id"]
    assert status["counts"]["candidates"] == len(_read_jsonl(tmp_path / "candidates.jsonl"))
    assert status["accepted_get_id_forms"] == ["candidate_id", "memory_id", "shard_id"]
    assert status["source_roles_present"] == ["durable_memory", "daily_memory", "dreams"]
    assert status["durable_memory_mutation"] is False
    assert status["manifest"]["durable_memory_mutation"] is False
    assert all(value is False for value in status["forbidden_semantics"].values())


def test_sidecar_search_does_not_hard_filter_by_drift_class(tmp_path: Path) -> None:
    report = search_sidecar(ROOT, FIXTURE, tmp_path, query="unrelated image settings", limit=20)
    indexed = _read_jsonl(tmp_path / "candidates.jsonl")

    assert report["result_count"] == len(indexed)
    assert report["warnings"] == ["drift_class is instrumentation, not trust/status or a hard filter"]


def test_write_candidate_uses_pending_store_and_does_not_modify_memory_files(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(FIXTURE, workspace)
    before = _source_hashes(workspace)

    report = write_candidate(ROOT, workspace, tmp_path / "sidecar", text="Remember this only as pending.", source="user")

    assert report["ok"] is True
    assert report["candidate"]["durable_write"] is False
    assert report["candidate"]["target_files_mutated"] is False
    assert report["candidate"]["durable_memory_mutation"] is False
    assert (tmp_path / "sidecar/pending_writes.jsonl").exists()
    assert _source_hashes(workspace) == before


def test_cli_commands_work_offline(tmp_path: Path) -> None:
    out = tmp_path / "sidecar"
    index = _run_cli("index", "--workspace", str(FIXTURE), "--out", str(out))
    search = _run_cli("search", "--workspace", str(FIXTURE), "--query", "gravity report", "--limit", "5", "--out", str(out))
    item_id = search["results"][0]["shard_id"]
    get = _run_cli("get", "--workspace", str(FIXTURE), "--id", item_id, "--out", str(out))
    write = _run_cli(
        "write-candidate",
        "--workspace",
        str(FIXTURE),
        "--text",
        "Candidate only.",
        "--source",
        "user",
        "--out",
        str(out),
    )
    status = _run_cli("status", "--workspace", str(FIXTURE), "--out", str(out))

    assert index["ok"] is True
    assert search["ok"] is True
    assert get["ok"] is True
    assert write["ok"] is True
    assert status["counts"]["pending_writes"] == 1


def test_parser_remains_deterministic() -> None:
    assert parse_openclaw_memory_workspace(FIXTURE).to_record() == parse_openclaw_memory_workspace(FIXTURE).to_record()


def test_forbidden_semantics_are_false() -> None:
    assert all(value is False for value in FORBIDDEN_SEMANTICS.values())


def _run_cli(*args: str) -> dict[str, object]:
    result = run_subprocess(
        [sys.executable, str(SCRIPT), *args],
        cwd=REFERENCE_PYTHON,
        timeout_seconds=60,
    )
    assert result.returncode == 0, subprocess_failure_message(result, REFERENCE_PYTHON)
    return json.loads(result.stdout)


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _source_hashes(workspace: Path) -> dict[str, str]:
    import hashlib

    paths = [workspace / "MEMORY.md", workspace / "DREAMS.md", *sorted((workspace / "memory").glob("*.md"))]
    return {path.relative_to(workspace).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
