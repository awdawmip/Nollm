from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.openclaw_memory_adapter import (
    FORBIDDEN_SEMANTICS,
    build_sidecar_store,
    commit_candidate,
    get_sidecar_item,
    parse_openclaw_memory_workspace,
    recall_sidecar,
    search_sidecar,
    sidecar_status,
    write_candidate,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference/python"
FIXTURE = ROOT / "examples/openclaw_memory_fixture"
FUNCTIONAL_FIXTURE = ROOT / "examples/openclaw_functional_memory_fixture"
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
    assert get_by_candidate["gravity_report"] == first["gravity_report"]
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


def test_semantic_geometry_calibrates_atlas_fixture(tmp_path: Path) -> None:
    report = search_sidecar(ROOT, FUNCTIONAL_FIXTURE, tmp_path, query="Atlas service owner credential", limit=10)
    results = report["results"]

    assert results[0]["source_path"] == "MEMORY.md"
    assert results[0]["gravity_report"]["drift_class"] in {"core", "halo"}
    daily = next(item for item in results if item["source_path"].startswith("memory/"))
    dream = next(item for item in results if item["source_path"] == "DREAMS.md")

    assert daily["gravity_report"]["drift_class"] in {"core", "halo", "near_drift"}
    assert dream["gravity_report"]["drift_class"] in {"far_weak", "semantic_break", "unglued"}
    assert dream["retrieval_score"] <= results[0]["retrieval_score"]
    assert results[0]["gravity_report"]["layout_method"] == "semantic_local_v1"
    assert "anchor_overlap" in results[0]["gravity_report"]


def test_semantic_layout_is_deterministic_for_functional_fixture(tmp_path: Path) -> None:
    first = search_sidecar(ROOT, FUNCTIONAL_FIXTURE, tmp_path / "first", query="Atlas service owner credential", limit=10)
    second = search_sidecar(ROOT, FUNCTIONAL_FIXTURE, tmp_path / "second", query="Atlas service owner credential", limit=10)

    assert first["results"] == second["results"]
    assert first["gravity_well"] == second["gravity_well"]


def test_recall_contract_separates_direct_and_lateral_context(tmp_path: Path) -> None:
    report = recall_sidecar(ROOT, FUNCTIONAL_FIXTURE, tmp_path, query="Who owns Atlas?", limit=10)

    assert report["ok"] is True
    assert report["candidate_source"] == "nollm_local"
    assert report["direct_evidence"]
    assert report["direct_evidence"][0]["source_path"] == "MEMORY.md"
    assert report["direct_evidence"][0]["line_range"]
    assert all("gravity_report" in item for item in report["direct_evidence"])
    assert any(item["source_role"] == "dream" for item in report["lateral_context"])
    assert any("DREAMS" in caution for caution in report["cautions"])


def test_unrelated_recall_returns_no_direct_evidence(tmp_path: Path) -> None:
    report = recall_sidecar(ROOT, FUNCTIONAL_FIXTURE, tmp_path, query="ceramic teapot glaze kiln schedule", limit=10)

    assert report["direct_evidence"] == []
    assert report["lateral_context"] == []
    assert "No relevant Nollm local memory evidence found." in report["cautions"]


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


def test_commit_candidate_requires_confirmation_and_preserves_unrelated_content(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(FUNCTIONAL_FIXTURE, workspace)
    out = tmp_path / "sidecar"
    before = _source_hashes(workspace)
    staged = write_candidate(
        ROOT,
        workspace,
        out,
        text="Atlas support rotation owner is Rowan Ives.",
        source="user_request",
    )
    candidate_id = staged["candidate"]["candidate_id"]

    rejected = commit_candidate(
        ROOT,
        workspace,
        out,
        candidate_id=candidate_id,
        explicit_confirmation=False,
        target="durable",
        reason="missing confirmation",
        source="test",
    )
    assert rejected["ok"] is False
    assert _source_hashes(workspace) == before

    committed = commit_candidate(
        ROOT,
        workspace,
        out,
        candidate_id=candidate_id,
        explicit_confirmation=True,
        target="durable",
        reason="user explicitly confirmed durable memory",
        source="test",
    )
    assert committed["ok"] is True
    assert committed["file_path"] == "MEMORY.md"
    assert committed["memory_core_reindex_required"] is True
    text = (workspace / "MEMORY.md").read_text(encoding="utf-8")
    assert "## Nollm Managed Memory" in text
    assert "Atlas support rotation owner is Rowan Ives." in text
    after = _source_hashes(workspace)
    assert after["DREAMS.md"] == before["DREAMS.md"]
    assert after["memory/2026-06-20.md"] == before["memory/2026-06-20.md"]
    assert after["MEMORY.md"] != before["MEMORY.md"]


def test_cli_commands_work_offline(tmp_path: Path) -> None:
    out = tmp_path / "sidecar"
    workspace = tmp_path / "workspace"
    shutil.copytree(FUNCTIONAL_FIXTURE, workspace)
    index = _run_cli("index", "--workspace", str(workspace), "--out", str(out))
    search = _run_cli("search", "--workspace", str(workspace), "--query", "Atlas owner", "--limit", "5", "--out", str(out))
    recall = _run_cli("recall", "--workspace", str(workspace), "--query", "Atlas owner", "--limit", "5", "--out", str(out))
    item_id = search["results"][0]["shard_id"]
    get = _run_cli("get", "--workspace", str(workspace), "--id", item_id, "--out", str(out))
    write = _run_cli(
        "write-candidate",
        "--workspace",
        str(workspace),
        "--text",
        "Candidate only.",
        "--source",
        "user",
        "--out",
        str(out),
    )
    commit = _run_cli(
        "commit-candidate",
        "--workspace",
        str(workspace),
        "--candidate-id",
        write["candidate"]["candidate_id"],
        "--explicit-confirmation",
        "--target",
        "durable",
        "--reason",
        "user confirmed",
        "--source",
        "test",
        "--out",
        str(out),
    )
    status = _run_cli("status", "--workspace", str(workspace), "--out", str(out))

    assert index["ok"] is True
    assert search["ok"] is True
    assert recall["direct_evidence"]
    assert get["ok"] is True
    assert write["ok"] is True
    assert commit["ok"] is True
    assert status["counts"]["pending_writes"] == 0
    assert status["counts"]["commit_ledger"] == 1


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
