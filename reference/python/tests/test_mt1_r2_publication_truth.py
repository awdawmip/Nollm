from __future__ import annotations

import json
from pathlib import Path

from nollm.archive import create_archive_snapshot
from nollm.archive_manifest import read_json, write_json
from nollm.coverage import validate_source_coverage
from nollm.legacy_import import plan_legacy_import, run_legacy_import, validate_legacy_import
from nollm.provenance import validate_deep_provenance


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_t5_link_record_fields_are_validated_fail_closed(tmp_path: Path) -> None:
    for field, value in [
        ("snapshot_id", "snap_fake"),
        ("field_revision_id", "fieldrev_fake"),
        ("shard_id", "shard_fake"),
        ("source_ref", "archive://object/sha256:" + "0" * 64 + "#B0-B1"),
        ("source_range_hash", "sha256:" + "1" * 64),
        ("text_hash", "sha256:" + "2" * 64),
    ]:
        memory_root, batch_id, revision_id, _snapshot_id = commit_fixture(tmp_path / field)
        link_path = memory_root / "field" / "publications" / revision_id / "source-span-links.jsonl"
        links = [json.loads(line) for line in link_path.read_text(encoding="utf-8").splitlines()]
        links[0][field] = value
        link_path.write_text("\n".join(json.dumps(link, sort_keys=True) for link in links) + "\n", encoding="utf-8")
        assert validate_legacy_import(memory_root, batch_id)["ok"] is False


def test_t6_physical_revision_without_head_is_unpublished(tmp_path: Path) -> None:
    memory_root, _batch_id, revision_id, snapshot_id = commit_fixture(tmp_path)
    (memory_root / "field" / "HEAD.json").unlink()

    report = validate_deep_provenance(memory_root, snapshot_id, revision_id)

    assert report["ok"] is False
    assert report["errors"] == [f"unpublished_revision:{revision_id}"]


def test_t7_forced_failure_before_head_has_no_published_truth(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD", "1")
    result = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)

    assert result["ok"] is False
    assert not (memory_root / "field" / "HEAD.json").exists()
    assert validate_source_coverage(memory_root, snapshot_id, require_linked=True)["ok"] is False
    publication_dirs = list((memory_root / "field" / "publications").glob("*")) if (memory_root / "field" / "publications").exists() else []
    if publication_dirs:
        report = validate_deep_provenance(memory_root, snapshot_id, publication_dirs[0].name)
        assert report["errors"] == [f"unpublished_revision:{publication_dirs[0].name}"]


def test_t8_real_publish_oserror_is_structured_terminal_and_invisible(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    before = file_hashes(workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    monkeypatch.setenv("NOLLM_MT1_FORCE_OSERROR_DURING_PUBLISH", "1")

    result = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)

    assert result["ok"] is False
    assert result["state"] == "failed"
    assert not (memory_root / "field" / "HEAD.json").exists()
    assert (memory_root / "ingress" / "legacy-import" / str(plan["batch_id"]) / "failure.json").exists()
    assert "legacy_import_failure" in (memory_root / "ledger" / "events.jsonl").read_text(encoding="utf-8")
    assert file_hashes(workspace) == before
    retry = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    assert retry["ok"] is False


def test_t11_successful_import_published_head_coverage_and_provenance(tmp_path: Path) -> None:
    memory_root, batch_id, revision_id, snapshot_id = commit_fixture(tmp_path)

    coverage = validate_source_coverage(memory_root, snapshot_id, require_linked=True)
    provenance = validate_deep_provenance(memory_root, snapshot_id, revision_id)

    assert coverage["ok"] is True
    assert coverage["coverage_ratio"] == 1.0
    assert provenance["ok"] is True
    assert validate_legacy_import(memory_root, batch_id)["ok"] is True


def commit_fixture(tmp_path: Path) -> tuple[Path, str, str, str]:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    assert commit["ok"] is True
    return memory_root, str(plan["batch_id"]), str(commit["field_revision_id"]), snapshot_id


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())


def file_hashes(root: Path) -> dict[str, str]:
    import hashlib

    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.rglob("*.md"))}
