from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from nollm.archive import create_archive_snapshot, verify_archive_snapshot
from nollm.archive_manifest import manifest_hash, read_json, sha256_bytes, write_json
from nollm.legacy_import import (
    legacy_import_report,
    plan_legacy_import,
    recover_legacy_import,
    reconcile_legacy_import,
    run_legacy_import,
    validate_legacy_import,
)
from nollm.native_field import admit_current_publication, load_field_head
from nollm.provenance import canonical_source_spans, validate_deep_provenance, validate_staged_publication
from nollm.source_spans import build_source_span_inventory


def test_target_field_rewrite_fails_before_staging(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(tmp_path, target_field_id="field_one")
    request_path = batch_dir(memory_root, batch_id) / "import-request.json"
    request = read_json(request_path)
    request["target_field_id"] = "field_two"
    write_json(request_path, request)

    result = run_legacy_import(memory_root, batch_id, commit=True)

    assert result["ok"] is False
    assert any("target_field_id_mismatch" in error or "base_batch_id_mismatch" in error for error in result["errors"])
    assert load_field_head(memory_root) is None
    assert not (memory_root / "field" / ".staging" / batch_id / "publication").exists()


def test_request_policy_rewrite_fails_before_staging(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(tmp_path)
    request_path = batch_dir(memory_root, batch_id) / "import-request.json"
    request = read_json(request_path)
    request["source_policy_id"] = "forged_policy"
    write_json(request_path, request)

    result = run_legacy_import(memory_root, batch_id, commit=True)

    assert result["ok"] is False
    assert any("source_policy_id_mismatch" in error for error in result["errors"])
    assert load_field_head(memory_root) is None


def test_malformed_extraction_returns_structured_quarantine(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(tmp_path)
    (batch_dir(memory_root, batch_id) / "extraction.jsonl").write_text("{ malformed", encoding="utf-8")

    dry_run = run_legacy_import(memory_root, batch_id, dry_run=True)
    commit = run_legacy_import(memory_root, batch_id, commit=True)

    for result in (dry_run, commit):
        assert result["ok"] is False
        assert any("malformed_jsonl:extraction" in error for error in result["errors"])
        assert_no_raw_exception_name(result)
    assert load_field_head(memory_root) is None


def test_recover_missing_extraction_returns_structured_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(tmp_path)
    monkeypatch.setenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD", "1")
    failed = run_legacy_import(memory_root, batch_id, commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD")
    (batch_dir(memory_root, batch_id) / "extraction.jsonl").unlink()

    recovery = recover_legacy_import(memory_root, batch_id)

    assert failed["ok"] is False
    assert recovery["ok"] is False
    assert any("missing_extraction" in error for error in recovery["errors"])
    assert_no_raw_exception_name(recovery)


def test_canonical_spans_never_read_external_content_hash_path(tmp_path: Path) -> None:
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest = read_json(manifest_path)
    external = tmp_path / "external.txt"
    external.write_text("external secret", encoding="utf-8")
    manifest["sources"][0]["content_hash"] = "sha256:" + external.resolve().as_posix()
    refresh_archive_manifest(manifest_path, manifest)

    with pytest.raises(ValueError):
        canonical_source_spans(memory_root, snapshot_id)


def test_staged_validator_rejects_external_symlink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_root, batch_id, snapshot_id = planned_workspace(tmp_path)
    monkeypatch.setenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD", "1")
    failed = run_legacy_import(memory_root, batch_id, commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD")
    staging_batch = memory_root / "field" / ".staging" / batch_id
    revision_id = str(read_json(staging_batch / "publication" / "revision.json")["field_revision_id"])
    external = tmp_path / "external-staging"
    copy_tree(staging_batch, external)
    remove_tree(staging_batch)
    symlink_or_skip(staging_batch, external)

    validation = validate_staged_publication(memory_root, batch_id, snapshot_id, revision_id)

    assert failed["ok"] is False
    assert validation["ok"] is False
    assert any("path_symlink" in error or "path_escape" in error for error in validation["errors"])


def test_load_head_rejects_field_symlink(tmp_path: Path) -> None:
    memory_root = tmp_path / "memory-root"
    external = tmp_path / "external-field"
    external.mkdir(parents=True)
    write_json(external / "HEAD.json", {"field_id": "field_fixture", "field_revision_id": "fieldrev_" + "a" * 20, "publication_manifest_hash": "sha256:" + "b" * 64, "activation_hash": "sha256:" + "c" * 64})
    symlink_or_skip(memory_root / "field", external)

    assert load_field_head(memory_root) is None
    assert admit_current_publication(memory_root)["publication"] is None


def test_source_swap_after_check_is_not_archived(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    external = tmp_path / "external.md"
    external.write_text("external", encoding="utf-8")
    import nollm.archive as archive_module

    original = archive_module.read_stable_source_bytes

    def swap_then_read(root: Path, relative: str) -> bytes:
        target = root / relative
        target.unlink()
        try:
            target.symlink_to(external)
        except OSError as exc:
            pytest.skip(f"symlink unavailable on this Windows host: {exc}")
        return original(root, relative)

    monkeypatch.setattr(archive_module, "read_stable_source_bytes", swap_then_read)
    result = create_archive_snapshot(workspace, memory_root)

    assert result["ok"] is False
    assert any("symlink" in error or "source_not_regular" in error for error in result["errors"])


def test_staging_swap_after_validation_copies_no_external_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(tmp_path)
    external = tmp_path / "external.txt"
    external.write_text("external secret", encoding="utf-8")
    import nollm.legacy_import as legacy_import_module

    original_validate = legacy_import_module.validate_staged_publication

    def validate_then_inject(*args: Any, **kwargs: Any) -> dict[str, Any]:
        result = original_validate(*args, **kwargs)
        leak = memory_root / "field" / ".staging" / batch_id / "publication" / "leak.txt"
        if result.get("ok"):
            try:
                leak.symlink_to(external)
            except OSError as exc:
                pytest.skip(f"symlink unavailable on this Windows host: {exc}")
        return result

    monkeypatch.setattr(legacy_import_module, "validate_staged_publication", validate_then_inject)
    result = run_legacy_import(memory_root, batch_id, commit=True)

    assert result["ok"] is False
    assert not list((memory_root / "field" / "publications").glob("**/leak.txt"))
    assert load_field_head(memory_root) is None


def test_receipt_target_field_must_equal_active_field(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_workspace(tmp_path)
    publication = publication_dir(memory_root, revision_id)
    receipt = read_json(publication / "receipt.json")
    receipt["target_field_id"] = "field_other"
    write_json(publication / "receipt.json", receipt)
    refresh_package_hashes(memory_root, revision_id)

    admission = admit_current_publication(memory_root)

    assert admission["publication"] is None
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False


def test_invalid_batch_id_cannot_be_active(tmp_path: Path) -> None:
    memory_root, _batch_id, _snapshot_id, revision_id = commit_workspace(tmp_path)
    publication = publication_dir(memory_root, revision_id)
    unsafe = "../../evil"
    for name in ("receipt.json", "revision.json", "activation.json", "publication-manifest.json"):
        data = read_json(publication / name)
        data["batch_id"] = unsafe
        write_json(publication / name, data)
    for shard_path in (publication / "shards").glob("*.json"):
        shard = read_json(shard_path)
        shard["batch_id"] = unsafe
        write_json(shard_path, shard)
    links = read_jsonl(publication / "source-span-links.jsonl")
    for link in links:
        link["batch_id"] = unsafe
    write_jsonl(publication / "source-span-links.jsonl", links)
    refresh_package_hashes(memory_root, revision_id)

    admission = admit_current_publication(memory_root)

    assert admission["publication"] is None
    assert any("invalid_batch_id" in error for error in admission["errors"])


def test_source_span_policy_state_drift_deactivates_publication(tmp_path: Path) -> None:
    memory_root, _batch_id, _snapshot_id, revision_id = commit_workspace(tmp_path, files={"DREAMS.md": "Atlas dreams of Mira.\n"})
    publication = publication_dir(memory_root, revision_id)
    projection = read_jsonl(publication / "source-span-projection.jsonl")
    projection[0]["epistemic_state"] = "legacy_recorded"
    write_jsonl(publication / "source-span-projection.jsonl", projection)
    refresh_package_hashes(memory_root, revision_id)

    admission = admit_current_publication(memory_root)

    assert admission["publication"] is None
    assert any("projection_epistemic_state_mismatch" in error for error in admission["errors"])


def test_unknown_authoritative_field_deactivates_publication(tmp_path: Path) -> None:
    memory_root, _batch_id, _snapshot_id, revision_id = commit_workspace(tmp_path)
    publication = publication_dir(memory_root, revision_id)
    for name in ("activation.json", "revision.json", "receipt.json"):
        data = read_json(publication / name)
        data["smuggled_semantic_override"] = True
        write_json(publication / name, data)
    refresh_package_hashes(memory_root, revision_id)

    admission = admit_current_publication(memory_root)

    assert admission["publication"] is None
    assert any("unknown_" in error for error in admission["errors"])


def test_concurrent_reconcile_has_one_finalization_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(tmp_path)
    monkeypatch.setenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD", "1")
    pending = run_legacy_import(memory_root, batch_id, commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD")

    first = reconcile_legacy_import(memory_root, batch_id)
    second = reconcile_legacy_import(memory_root, batch_id)
    receipt = read_json(batch_dir(memory_root, batch_id) / "import-receipt.json")

    assert pending["reconciliation_pending"] is True
    assert first["ok"] is True
    assert second["ok"] is True
    assert finalization_event_count(memory_root, str(receipt["batch_id"]), str(receipt["field_revision_id"])) == 1


def test_stale_lock_has_controlled_reclaim(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(tmp_path)
    lock = memory_root / "locks" / "legacy-import-writer.lock"
    lock.mkdir(parents=True)
    old = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    write_json(lock / "owner.json", {"schema": "nollm.legacy_import_writer_lock.v1", "batch_id": "batch_" + "f" * 20, "acquired_at": old})

    committed = run_legacy_import(memory_root, batch_id, commit=True)

    assert committed["ok"] is True
    assert load_field_head(memory_root) is not None


def test_manifest_top_level_schema_and_source_order_are_canonical(tmp_path: Path) -> None:
    memory_root, snapshot_id = snapshot_workspace(tmp_path, files={"MEMORY.md": "Mira.\n", "DREAMS.md": "Atlas.\n"})
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest = read_json(manifest_path)
    manifest["smuggled"] = True
    manifest["sources"] = list(reversed(manifest["sources"]))
    refresh_archive_manifest(manifest_path, manifest)

    result = verify_archive_snapshot(memory_root, snapshot_id)

    assert result["ok"] is False
    assert "unknown_archive_manifest_field:smuggled" in result["errors"]
    assert "archive_sources_not_canonical_order" in result["errors"]


def test_duplicate_blob_report_uses_unique_blob_count(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "same bytes\n", "DREAMS.md": "same bytes\n"})
    result = create_archive_snapshot(workspace, tmp_path / "memory-root")

    assert result["ok"] is True
    assert result["source_count"] == 2
    assert result["unique_blob_count"] == 1
    assert result["object_count"] == 1


def planned_workspace(tmp_path: Path, *, target_field_id: str = "field_fixture") -> tuple[Path, str, str]:
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id=target_field_id)
    assert plan["ok"] is True, plan
    return memory_root, str(plan["batch_id"]), snapshot_id


def commit_workspace(tmp_path: Path, *, files: dict[str, str] | None = None) -> tuple[Path, str, str, str]:
    memory_root, snapshot_id = snapshot_workspace(tmp_path, files=files)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True, plan
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    assert commit["ok"] is True, commit
    return memory_root, str(plan["batch_id"]), snapshot_id, str(commit["field_revision_id"])


def snapshot_workspace(tmp_path: Path, *, files: dict[str, str] | None = None) -> tuple[Path, str]:
    workspace = workspace_with(tmp_path, files or {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot = create_archive_snapshot(workspace, memory_root)
    assert snapshot["ok"] is True, snapshot
    inventory = build_source_span_inventory(memory_root, str(snapshot["snapshot_id"]))
    assert inventory["ok"] is True, inventory
    return memory_root, str(snapshot["snapshot_id"])


def workspace_with(tmp_path: Path, files: dict[str, str]) -> Path:
    workspace = tmp_path / "workspace"
    for rel, text in files.items():
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return workspace


def batch_dir(memory_root: Path, batch_id: str) -> Path:
    return memory_root / "ingress" / "legacy-import" / batch_id


def publication_dir(memory_root: Path, revision_id: str) -> Path:
    return memory_root / "field" / "publications" / revision_id


def refresh_archive_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["archive_manifest_hash"] = manifest_hash(manifest)
    manifest["manifest_hash"] = manifest["archive_manifest_hash"]
    write_json(path, manifest)


def refresh_package_hashes(memory_root: Path, revision_id: str) -> None:
    publication = publication_dir(memory_root, revision_id)
    activation = read_json(publication / "activation.json")
    hash_fields = {
        "receipt_hash": publication / "receipt.json",
        "revision_hash": publication / "revision.json",
        "source_span_links_hash": publication / "source-span-links.jsonl",
        "source_span_projection_hash": publication / "source-span-projection.jsonl",
    }
    for key, path in hash_fields.items():
        activation[key] = "sha256:" + sha256_bytes(path.read_bytes())
    write_json(publication / "activation.json", activation)
    manifest = read_json(publication / "publication-manifest.json")
    manifest["artifact_hashes"] = {
        path.relative_to(publication).as_posix(): "sha256:" + sha256_bytes(path.read_bytes())
        for path in sorted(publication.rglob("*"))
        if path.is_file() and not path.is_symlink() and path.name != "publication-manifest.json"
    }
    write_json(publication / "publication-manifest.json", manifest)
    head = read_json(memory_root / "field" / "HEAD.json")
    head["activation_hash"] = "sha256:" + sha256_bytes((publication / "activation.json").read_bytes())
    head["publication_manifest_hash"] = "sha256:" + sha256_bytes((publication / "publication-manifest.json").read_bytes())
    write_json(memory_root / "field" / "HEAD.json", head)


def finalization_event_count(memory_root: Path, batch_id: str, revision_id: str) -> int:
    event_id = f"legacy_import_commit:{batch_id}:{revision_id}"
    ledger = memory_root / "ledger" / "events.jsonl"
    if not ledger.exists():
        return 0
    return sum(1 for record in read_jsonl(ledger) if record.get("event_id") == event_id)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def copy_tree(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        target = dst / path.relative_to(src)
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file() and not path.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())


def remove_tree(path: Path) -> None:
    if path.exists() and path.is_dir() and not path.is_symlink():
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        path.rmdir()
    elif path.exists() or path.is_symlink():
        path.unlink()


def symlink_or_skip(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError as exc:
        pytest.skip(f"symlink unavailable on this Windows host: {exc}")


def assert_no_raw_exception_name(result: dict[str, Any]) -> None:
    joined = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for forbidden in ["Traceback", "JSONDecodeError", "KeyError", "IsADirectoryError", "FileNotFoundError"]:
        assert forbidden not in joined
