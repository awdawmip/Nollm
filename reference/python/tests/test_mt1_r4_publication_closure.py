from __future__ import annotations

import json
from pathlib import Path

from nollm.archive import create_archive_snapshot
from nollm.archive_manifest import read_json, write_json
from nollm.coverage import validate_source_coverage
from nollm.legacy_import import plan_legacy_import, reconcile_legacy_import, run_legacy_import, validate_legacy_import
from nollm.native_field import current_publication, existing_shards_by_key
from nollm.provenance import validate_deep_provenance


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_t1_extra_artifact_or_symlink_cannot_become_active(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path)
    publication = memory_root / "field" / "publications" / revision_id
    injected = publication / "shards" / "shard_unmanifested_injected.json"
    template = read_json(next((publication / "shards").glob("*.json")))
    template["shard_id"] = "shard_unmanifested_injected"
    template["idempotence_key"] = "sha256:" + "9" * 64
    write_json(injected, template)

    assert current_publication(memory_root) is None
    assert existing_shards_by_key(memory_root) == {}
    assert validate_source_coverage(memory_root, snapshot_id, require_linked=True)["ok"] is False
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False

    injected.unlink()
    (publication / "unexpected.txt").write_text("not manifest-bound", encoding="utf-8")
    assert current_publication(memory_root) is None
    (publication / "unexpected.txt").unlink()
    try:
        (publication / "link.txt").symlink_to(publication / "revision.json")
    except OSError:
        return
    assert current_publication(memory_root) is None


def test_t2_active_shards_are_revision_limited(tmp_path: Path) -> None:
    memory_root, _batch_id, _snapshot_id, revision_id = commit_fixture(tmp_path)
    publication = memory_root / "field" / "publications" / revision_id
    revision = read_json(publication / "revision.json")
    active = existing_shards_by_key(memory_root)

    assert {item["shard_id"] for item in active.values()} == set(revision["shard_ids"])
    unlisted = publication / "shards" / "shard_valid_but_unlisted.json"
    shard = read_json(next((publication / "shards").glob("*.json")))
    shard["shard_id"] = "shard_valid_but_unlisted"
    shard["idempotence_key"] = "sha256:" + "8" * 64
    write_json(unlisted, shard)
    assert existing_shards_by_key(memory_root) == {}


def test_t3_post_head_finalization_error_is_publish_pending_not_failed_active(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_STATE_OSERROR_AFTER_HEAD", "1")

    result = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    state = read_json(memory_root / "ingress" / "legacy-import" / str(plan["batch_id"]) / "state.json")

    assert result["ok"] is True
    assert result["published"] is True
    assert result["reconciliation_pending"] is True
    assert state["state"] == "publishing"
    assert current_publication(memory_root) is not None
    assert validate_source_coverage(memory_root, snapshot_id, require_linked=True)["ok"] is True


def test_t4_tampered_pending_publication_quarantines_and_clears_head(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_JOURNAL_OSERROR_AFTER_HEAD", "1")
    pending = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    revision_id = str(pending["field_revision_id"])
    shard = next((memory_root / "field" / "publications" / revision_id / "shards").glob("*.json"))
    data = read_json(shard)
    data["text"] = "tampered after head"
    write_json(shard, data)

    result = reconcile_legacy_import(memory_root, str(plan["batch_id"]))

    assert result["ok"] is False
    assert read_json(memory_root / "ingress" / "legacy-import" / str(plan["batch_id"]) / "state.json")["state"] == "quarantined"
    assert current_publication(memory_root) is None
    assert not any("legacy_import_commit" in line and str(plan["batch_id"]) in line for line in (memory_root / "ledger" / "events.jsonl").read_text(encoding="utf-8").splitlines())


def test_t5_prior_head_rolls_back_when_pending_revision_corrupts(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root, first_batch, snapshot_id, first_revision = commit_existing_workspace(workspace, tmp_path / "memory-root")
    for path in workspace.rglob("*.md"):
        path.unlink()
    (workspace / "memory" / "2026-06-22.md").write_text("# Extra\n\n- second revision\n", encoding="utf-8")
    second_snapshot = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    second_plan = plan_legacy_import(memory_root, second_snapshot, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_JOURNAL_OSERROR_AFTER_HEAD", "1")
    second = run_legacy_import(memory_root, str(second_plan["batch_id"]), commit=True)
    second_revision = str(second["field_revision_id"])
    shard = next((memory_root / "field" / "publications" / second_revision / "shards").glob("*.json"))
    data = read_json(shard)
    data["text"] = "corrupt pending b"
    write_json(shard, data)

    result = reconcile_legacy_import(memory_root, str(second_plan["batch_id"]))

    assert result["ok"] is False
    assert read_json(memory_root / "field" / "HEAD.json")["field_revision_id"] == first_revision
    assert validate_deep_provenance(memory_root, snapshot_id, first_revision)["ok"] is True
    assert current_publication(memory_root) == memory_root / "field" / "publications" / first_revision


def test_t6_manifest_paths_and_symlink_closure_fail_closed(tmp_path: Path) -> None:
    for bad_path in ["../outside", "/absolute/path", "shards/../revision.json"]:
        memory_root, _batch_id, _snapshot_id, revision_id = commit_fixture(tmp_path / bad_path.replace("/", "_").replace("..", "dotdot"))
        publication = memory_root / "field" / "publications" / revision_id
        manifest = read_json(publication / "publication-manifest.json")
        manifest["artifact_hashes"][bad_path] = "sha256:" + "0" * 64
        write_json(publication / "publication-manifest.json", manifest)
        head = read_json(memory_root / "field" / "HEAD.json")
        head["publication_manifest_hash"] = "sha256:" + hash_file(publication / "publication-manifest.json")
        write_json(memory_root / "field" / "HEAD.json", head)
        assert current_publication(memory_root) is None


def commit_fixture(tmp_path: Path) -> tuple[Path, str, str, str]:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    return commit_existing_workspace(workspace, tmp_path / "memory-root")


def commit_existing_workspace(workspace: Path, memory_root: Path) -> tuple[Path, str, str, str]:
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


def hash_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()
