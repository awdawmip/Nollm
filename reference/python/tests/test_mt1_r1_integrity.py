from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from nollm.archive import create_archive_snapshot
from nollm.archive_manifest import read_json, write_json
from nollm.coverage import validate_source_coverage
from nollm.legacy_import import plan_legacy_import, run_legacy_import, validate_legacy_import
from nollm.native_field import existing_shards_by_key
from nollm.provenance import validate_deep_provenance
from nollm.source_spans import build_source_span_inventory, load_source_spans


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_t1_heading_only_source_is_non_memory_not_zero_shard_sharded(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "MEMORY.md").write_text("# Heading Only\n", encoding="utf-8")
    snapshot = create_archive_snapshot(workspace, tmp_path / "memory-root")["snapshot_id"]
    build_source_span_inventory(tmp_path / "memory-root", str(snapshot))

    spans = load_source_spans(tmp_path / "memory-root", str(snapshot))

    assert spans[0]["disposition"] == "non_memory"
    assert spans[0]["reason"] == "structural_heading"
    assert spans[0]["related_shard_ids"] == []


def test_t2_t3_committed_sharded_spans_have_bidirectional_exact_links(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, field_revision_id = commit_fixture(tmp_path)
    spans = load_source_spans(memory_root, snapshot_id)
    sharded = [span for span in spans if span["disposition"] == "sharded"]

    assert sharded
    assert all(span["related_shard_ids"] for span in sharded)
    assert validate_deep_provenance(memory_root, snapshot_id, field_revision_id)["ok"] is True
    assert validate_legacy_import(memory_root, batch_id)["ok"] is True


def test_t4_nonexistent_digest_provenance_fails_closed(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, field_revision_id = commit_fixture(tmp_path)
    shard_path = next((memory_root / "field" / "shards").glob("*.json"))
    shard = read_json(shard_path)
    shard["source_refs"] = ["archive://object/sha256:" + "0" * 64 + "#B0-B1"]
    write_json(shard_path, shard)

    report = validate_legacy_import(memory_root, batch_id)

    assert report["ok"] is False
    assert any("source_ref_digest_not_in_manifest" in error for error in report["errors"])


def test_t5_t6_out_of_range_and_wrong_hash_fail_closed(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id, _field_revision_id = commit_fixture(tmp_path)
    shard_path = next((memory_root / "field" / "shards").glob("*.json"))
    shard = read_json(shard_path)
    ref = shard["source_refs"][0]
    digest = ref.split("sha256:", 1)[1].split("#", 1)[0]
    shard["source_refs"] = [f"archive://object/sha256:{digest}#B0-B999999"]
    write_json(shard_path, shard)
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False

    memory_root, batch_id, _snapshot_id, _field_revision_id = commit_fixture(tmp_path / "wrong_hash")
    shard_path = next((memory_root / "field" / "shards").glob("*.json"))
    shard = read_json(shard_path)
    shard["text_hash"] = "sha256:" + "1" * 64
    write_json(shard_path, shard)
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False


def test_t7_missing_continuity_or_reverse_link_fails_closed(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id, _field_revision_id = commit_fixture(tmp_path)
    shard_path = next((memory_root / "field" / "shards").glob("*.json"))
    shard = read_json(shard_path)
    shard["continuity_refs"] = []
    write_json(shard_path, shard)

    assert validate_legacy_import(memory_root, batch_id)["ok"] is False


def test_t8_forced_failure_before_head_leaves_no_dedupe_visible_orphan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD", "1")

    result = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)

    assert result["ok"] is False
    assert not (memory_root / "field" / "HEAD.json").exists()
    assert existing_shards_by_key(memory_root) == {}


def test_t9_recovery_after_interrupted_staging_is_deterministic_and_ledgers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD", "1")
    assert run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)["ok"] is False
    monkeypatch.delenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD")

    recovered = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    ledger = (memory_root / "ledger" / "events.jsonl").read_text(encoding="utf-8")

    assert recovered["ok"] is True
    assert "legacy_import_failure" in ledger
    assert "legacy_import_commit" in ledger


def test_t10_repeat_plan_and_commit_preserve_request_and_receipt_bytes(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, _field_revision_id = commit_fixture(tmp_path)
    batch_dir = memory_root / "ingress" / "legacy-import" / batch_id
    request_before = (batch_dir / "import-request.json").read_bytes()
    receipt_before = (batch_dir / "import-receipt.json").read_bytes()

    plan_again = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    commit_again = run_legacy_import(memory_root, batch_id, commit=True)

    assert plan_again["state"] == "committed"
    assert commit_again["created_shard_count"] == 0
    assert (batch_dir / "import-request.json").read_bytes() == request_before
    assert (batch_dir / "import-receipt.json").read_bytes() == receipt_before


def test_t11_memory_root_inside_workspace_and_workspace_inside_memory_root_fail(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)

    with pytest.raises(ValueError, match="memory root"):
        create_archive_snapshot(workspace, workspace / ".nollm")
    with pytest.raises(ValueError, match="workspace"):
        create_archive_snapshot(workspace, tmp_path)


def test_t13_internal_and_external_source_symlinks_fail(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    internal = workspace / "memory" / "internal.md"
    external_target = tmp_path / "external.md"
    external_target.write_text("external", encoding="utf-8")
    try:
        internal.symlink_to(workspace / "MEMORY.md")
    except OSError:
        pytest.skip("symlink creation unavailable")

    with pytest.raises(ValueError, match="symlink"):
        create_archive_snapshot(workspace, tmp_path / "memory-root")
    internal.unlink()
    (workspace / "memory" / "external.md").symlink_to(external_target)
    with pytest.raises(ValueError, match="symlink"):
        create_archive_snapshot(workspace, tmp_path / "memory-root")


def test_t16_source_hash_unchanged_after_negative_tests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    before = file_hashes(workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD", "1")
    run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)

    assert file_hashes(workspace) == before


def commit_fixture(tmp_path: Path) -> tuple[Path, str, str, str]:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    assert commit["ok"] is True
    return memory_root, str(plan["batch_id"]), snapshot_id, str(commit["field_revision_id"])


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())


def file_hashes(root: Path) -> dict[str, str]:
    import hashlib

    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.rglob("*.md"))}
