from __future__ import annotations

import json
from pathlib import Path

from nollm.archive import create_archive_snapshot
from nollm.archive_manifest import read_json, write_json
from nollm.coverage import validate_source_coverage
from nollm.legacy_import import plan_legacy_import, reconcile_legacy_import, recover_legacy_import, run_legacy_import, validate_legacy_import
from nollm.native_field import current_publication, existing_shards_by_key
from nollm.provenance import validate_deep_provenance


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_t1_staging_corruption_never_reaches_head(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    before = file_hashes(workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_and_plan(workspace, memory_root)["snapshot_id"]
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_CORRUPT_STAGING_TEXT", "1")

    result = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)

    assert result["ok"] is False
    assert not (memory_root / "field" / "HEAD.json").exists()
    assert existing_shards_by_key(memory_root) == {}
    assert validate_source_coverage(memory_root, snapshot_id, require_linked=True)["ok"] is False
    assert file_hashes(workspace) == before


def test_t2_post_head_journal_failure_reconciles_without_new_shards(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_and_plan(workspace, memory_root)["snapshot_id"]
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_JOURNAL_OSERROR_AFTER_HEAD", "1")

    result = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    revision_id = str(result["field_revision_id"])
    receipt_before = (memory_root / "ingress" / "legacy-import" / str(plan["batch_id"]) / "import-receipt.json").read_bytes()
    shard_ids = sorted(existing_shards_by_key(memory_root))
    reconcile = reconcile_legacy_import(memory_root, str(plan["batch_id"]))

    assert result["ok"] is True
    assert result["published"] is True
    assert result["reconciliation_pending"] is True
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is True
    assert validate_source_coverage(memory_root, snapshot_id, require_linked=True)["ok"] is True
    assert reconcile["ok"] is True
    assert sorted(existing_shards_by_key(memory_root)) == shard_ids
    assert (memory_root / "ingress" / "legacy-import" / str(plan["batch_id"]) / "import-receipt.json").read_bytes() == receipt_before


def test_t3_manifest_and_payload_tamper_fail_closed(tmp_path: Path) -> None:
    for rel in [
        "publication-manifest.json",
        "revision.json",
        "receipt.json",
        "source-span-links.jsonl",
        "source-span-projection.jsonl",
    ]:
        memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path / rel.replace("/", "_"))
        path = memory_root / "field" / "publications" / revision_id / rel
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        assert current_publication(memory_root) is None
        assert existing_shards_by_key(memory_root) == {}
        assert validate_source_coverage(memory_root, snapshot_id, require_linked=True)["ok"] is False
        assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False
    memory_root, _batch_id, snapshot_id, revision_id = commit_fixture(tmp_path / "shard")
    shard_path = next((memory_root / "field" / "publications" / revision_id / "shards").glob("*.json"))
    shard = read_json(shard_path)
    shard["text"] = "tampered"
    write_json(shard_path, shard)
    assert current_publication(memory_root) is None
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False


def test_t4_projection_cannot_relabel_real_text_as_non_memory(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path)
    publication = memory_root / "field" / "publications" / revision_id
    revision = read_json(publication / "revision.json")
    revision["shard_ids"] = revision["shard_ids"][1:]
    write_json(publication / "revision.json", revision)
    receipt = read_json(publication / "receipt.json")
    receipt["created_shard_ids"] = receipt["created_shard_ids"][1:]
    write_json(publication / "receipt.json", receipt)
    (publication / "source-span-links.jsonl").write_text("", encoding="utf-8")
    projection = [json.loads(line) for line in (publication / "source-span-projection.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    for span in projection:
        if span["disposition"] == "sharded":
            span["disposition"] = "non_memory"
            span["reason"] = "blank"
            span["related_shard_ids"] = []
            break
    (publication / "source-span-projection.jsonl").write_text("\n".join(json.dumps(span, sort_keys=True) for span in projection) + "\n", encoding="utf-8")

    assert validate_source_coverage(memory_root, snapshot_id, require_linked=True)["ok"] is False
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False


def test_t5_canonical_non_memory_classification_is_constrained(tmp_path: Path) -> None:
    memory_root, _batch_id, snapshot_id, revision_id = commit_workspace(tmp_path, "# Heading\n\nReal text\n")
    projection_path = memory_root / "field" / "publications" / revision_id / "source-span-projection.jsonl"
    projection = [json.loads(line) for line in projection_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert projection[0]["disposition"] == "non_memory"
    projection[0]["reason"] = "blank"
    projection_path.write_text("\n".join(json.dumps(span, sort_keys=True) for span in projection) + "\n", encoding="utf-8")
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False


def test_t6_failed_batch_creates_deterministic_replacement(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_and_plan(workspace, memory_root)["snapshot_id"]
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD", "1")
    failed = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD")

    recovery = recover_legacy_import(memory_root, str(plan["batch_id"]))
    again = recover_legacy_import(memory_root, str(plan["batch_id"]))
    replacement_commit = run_legacy_import(memory_root, recovery["replacement_batch_id"], commit=True)

    assert failed["ok"] is False
    assert recovery["replacement_batch_id"] != plan["batch_id"]
    assert again["replacement_batch_id"] == recovery["replacement_batch_id"]
    assert replacement_commit["ok"] is True
    old_state = read_json(memory_root / "ingress" / "legacy-import" / str(plan["batch_id"]) / "state.json")
    assert old_state["state"] == "failed"


def test_t8_source_scope_and_no_generic_active_path(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    before = file_hashes(workspace)
    memory_root, _batch_id, _snapshot_id, revision_id = commit_existing_workspace(workspace, tmp_path / "memory-root")

    assert file_hashes(workspace) == before
    assert not (memory_root / "field" / "shards").exists() or not list((memory_root / "field" / "shards").glob("*.json"))
    assert current_publication(memory_root) == memory_root / "field" / "publications" / revision_id


def snapshot_and_plan(workspace: Path, memory_root: Path) -> dict[str, str]:
    return create_archive_snapshot(workspace, memory_root)


def commit_fixture(tmp_path: Path) -> tuple[Path, str, str, str]:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    return commit_existing_workspace(workspace, tmp_path / "memory-root")


def commit_workspace(tmp_path: Path, content: str) -> tuple[Path, str, str, str]:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "MEMORY.md").write_text(content, encoding="utf-8")
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


def file_hashes(root: Path) -> dict[str, str]:
    import hashlib

    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.rglob("*.md"))}
