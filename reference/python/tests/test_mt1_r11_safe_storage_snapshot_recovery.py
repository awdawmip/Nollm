from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

import nollm.archive as archive_module
from nollm.archive import create_archive_snapshot, verify_archive_snapshot, workspace_identity_for, snapshot_seed_digest
from nollm.archive_manifest import manifest_hash, read_json, sha256_bytes, write_json
from nollm.legacy_import import plan_legacy_import, recover_legacy_import, run_legacy_import, validate_legacy_import
from nollm.native_field import admit_current_publication, load_field_head
from nollm.provenance import validate_deep_provenance
from nollm.source_spans import build_source_span_inventory


def test_rejected_memory_root_inside_workspace_has_zero_source_side_effect(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    before = tree_fingerprint(workspace)
    result = create_archive_snapshot(workspace, workspace / "nollm-memory")

    assert result["ok"] is False
    assert any("memory root must not be inside workspace" in error for error in result["errors"])
    assert not (workspace / "nollm-memory").exists()
    assert tree_fingerprint(workspace) == before


def test_archive_v4_workspace_identity_prevents_same_content_collision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(archive_module, "utc_now", lambda: "2026-06-22T00:00:00Z")
    workspace_a = workspace_with(tmp_path / "a", {"MEMORY.md": "same\n"})
    workspace_b = workspace_with(tmp_path / "b", {"MEMORY.md": "same\n"})

    first = create_archive_snapshot(workspace_a, tmp_path / "memory-a")
    second = create_archive_snapshot(workspace_b, tmp_path / "memory-b")

    assert first["ok"] is True
    assert second["ok"] is True
    assert first["snapshot_id"] != second["snapshot_id"]


def test_archive_v4_idempotent_reuse_and_collision_refuse_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(archive_module, "utc_now", lambda: "2026-06-22T00:00:00Z")
    workspace = workspace_with(tmp_path, {"MEMORY.md": "same\n"})
    memory_root = tmp_path / "memory-root"
    first = create_archive_snapshot(workspace, memory_root)
    manifest_path = memory_root / "archive" / "manifests" / f"{first['snapshot_id']}.json"
    before = manifest_path.read_bytes()
    before_stat = manifest_path.stat()

    reused = create_archive_snapshot(workspace, memory_root)
    assert reused["ok"] is True
    assert reused["reused"] is True
    assert manifest_path.read_bytes() == before
    assert manifest_path.stat().st_mtime_ns == before_stat.st_mtime_ns

    tampered = read_json(manifest_path)
    tampered["workspace_identity"] = "sha256:" + "f" * 64
    tampered["archive_manifest_hash"] = manifest_hash(tampered)
    tampered["manifest_hash"] = tampered["archive_manifest_hash"]
    write_json(manifest_path, tampered)
    tampered_bytes = manifest_path.read_bytes()

    collision = create_archive_snapshot(workspace, memory_root)
    assert collision["ok"] is False
    assert "snapshot_id_collision" in collision["errors"]
    assert manifest_path.read_bytes() == tampered_bytes


def test_workspace_identity_tamper_deactivates_publication(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_workspace(tmp_path)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest = read_json(manifest_path)
    manifest["workspace_identity"] = "sha256:" + "a" * 64
    refresh_archive_manifest(manifest_path, manifest)
    refresh_active_archive_hashes(memory_root, revision_id, manifest["archive_manifest_hash"])

    admission = admit_current_publication(memory_root)
    provenance = validate_deep_provenance(memory_root, snapshot_id, revision_id)

    assert admission["publication"] is None
    assert provenance["ok"] is False
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False


def test_archive_manifest_boolean_integer_rejected(tmp_path: Path) -> None:
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest = read_json(manifest_path)
    manifest["sources"][0]["byte_length"] = True
    manifest["sources"][0]["line_count"] = True
    refresh_archive_manifest(manifest_path, manifest)

    verify = verify_archive_snapshot(memory_root, snapshot_id)

    assert verify["ok"] is False
    assert any("invalid_byte_length" in error for error in verify["errors"])
    assert any("invalid_line_count" in error for error in verify["errors"])


def test_source_parent_replacement_symlink_is_structured_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = workspace_with(tmp_path, {"memory/entry.md": "inside\n"})
    external = tmp_path / "external"
    external.mkdir()
    (external / "entry.md").write_text("outside\n", encoding="utf-8")
    original = archive_module.read_stable_source_bytes

    def swap_parent(root: Path, relative: str) -> bytes:
        memory_dir = root / "memory"
        remove_tree(memory_dir)
        symlink_or_skip(memory_dir, external)
        return original(root, relative)

    monkeypatch.setattr(archive_module, "read_stable_source_bytes", swap_parent)
    result = create_archive_snapshot(workspace, tmp_path / "memory-root")

    assert result["ok"] is False
    assert any("symlink" in error or "source_unreadable" in error for error in result["errors"])


def test_hardlinked_ledger_is_rejected_without_external_append(tmp_path: Path) -> None:
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    external = tmp_path / "external-events.jsonl"
    external.write_text("", encoding="utf-8")
    ledger = memory_root / "ledger" / "events.jsonl"
    ledger.parent.mkdir(parents=True)
    hardlink_or_skip(external, ledger)
    before = external.read_bytes()

    result = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")

    assert result["ok"] is False
    assert external.read_bytes() == before


def test_canonical_inventory_locator_tamper_deactivates_publication(tmp_path: Path) -> None:
    memory_root, _batch_id, snapshot_id, revision_id = commit_workspace(tmp_path)
    inventory = memory_root / "archive" / "source-spans" / f"{snapshot_id}.jsonl"
    records = read_jsonl(inventory)
    records[0]["locator"]["start_line"] = 99
    write_jsonl(inventory, records)

    admission = admit_current_publication(memory_root)
    provenance = validate_deep_provenance(memory_root, snapshot_id, revision_id)

    assert admission["publication"] is None
    assert provenance["ok"] is False


def test_duplicate_json_key_manifest_fails_closed(tmp_path: Path) -> None:
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest_path.write_text('{"schema":"x","schema":"y"}\n', encoding="utf-8")

    verify = verify_archive_snapshot(memory_root, snapshot_id)

    assert verify["ok"] is False
    assert any("duplicate_json_key" in error for error in verify["errors"])


def test_plan_concurrency_has_single_plan_ledger_event(tmp_path: Path) -> None:
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    results: list[dict[str, Any]] = []
    barrier = threading.Barrier(2)

    def worker() -> None:
        barrier.wait()
        results.append(plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture"))

    threads = [threading.Thread(target=worker), threading.Thread(target=worker)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 2
    assert all(result["ok"] for result in results)
    assert sum(1 for result in results if result.get("reused")) == 1
    batch_id = str(results[0]["batch_id"])
    events = read_jsonl(memory_root / "ledger" / "events.jsonl")
    assert sum(1 for event in events if event.get("event_id") == f"legacy_import_plan:{batch_id}") == 1


def test_recover_publishing_does_not_self_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(tmp_path)
    monkeypatch.setenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD", "1")
    pending = run_legacy_import(memory_root, batch_id, commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD")

    recovered = recover_legacy_import(memory_root, batch_id)

    assert pending["reconciliation_pending"] is True
    assert "writer_busy" not in recovered.get("errors", [])
    assert recovered["state"] in {"committed", "publishing", "quarantined"}


def test_live_stale_writer_is_not_reclaimed(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(tmp_path)
    lock = memory_root / "locks" / "legacy-import-writer.lock"
    lock.mkdir(parents=True)
    old = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    write_json(lock / "owner.json", {"schema": "nollm.legacy_import_writer_lock.v2", "batch_id": "batch_" + "f" * 20, "acquired_at": old, "owner_pid": os.getpid(), "fencing_token": "fence_live"})

    result = run_legacy_import(memory_root, batch_id, commit=True)

    assert result["ok"] is False
    assert "writer_busy" in result["errors"]
    assert load_field_head(memory_root) is None


def test_read_apis_do_not_create_missing_memory_root(tmp_path: Path) -> None:
    memory_root = tmp_path / "missing-root"
    valid_snapshot = "snap_20260622_000000_" + "a" * 12
    valid_revision = "fieldrev_" + "b" * 20

    archive = verify_archive_snapshot(memory_root, valid_snapshot)
    admission = admit_current_publication(memory_root)
    provenance = validate_deep_provenance(memory_root, valid_snapshot, valid_revision)

    assert archive["ok"] is False
    assert admission["publication"] is None
    assert provenance["ok"] is False
    assert not memory_root.exists()


def planned_workspace(tmp_path: Path) -> tuple[Path, str, str]:
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True, plan
    return memory_root, str(plan["batch_id"]), snapshot_id


def commit_workspace(tmp_path: Path) -> tuple[Path, str, str, str]:
    memory_root, batch_id, snapshot_id = planned_workspace(tmp_path)
    commit = run_legacy_import(memory_root, batch_id, commit=True)
    assert commit["ok"] is True, commit
    return memory_root, batch_id, snapshot_id, str(commit["field_revision_id"])


def snapshot_workspace(tmp_path: Path) -> tuple[Path, str]:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
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


def refresh_archive_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["archive_manifest_hash"] = manifest_hash(manifest)
    manifest["manifest_hash"] = manifest["archive_manifest_hash"]
    write_json(path, manifest)


def refresh_active_archive_hashes(memory_root: Path, revision_id: str, archive_manifest_hash: str) -> None:
    publication = memory_root / "field" / "publications" / revision_id
    activation = read_json(publication / "activation.json")
    activation["archive_manifest_hash"] = archive_manifest_hash
    write_json(publication / "activation.json", activation)
    manifest = read_json(publication / "publication-manifest.json")
    manifest["artifact_hashes"] = {
        path.relative_to(publication).as_posix(): "sha256:" + sha256_bytes(path.read_bytes())
        for path in sorted(publication.rglob("*"))
        if path.is_file() and path.name != "publication-manifest.json"
    }
    write_json(publication / "publication-manifest.json", manifest)
    head = read_json(memory_root / "field" / "HEAD.json")
    head["activation_hash"] = "sha256:" + sha256_bytes((publication / "activation.json").read_bytes())
    head["publication_manifest_hash"] = "sha256:" + sha256_bytes((publication / "publication-manifest.json").read_bytes())
    write_json(memory_root / "field" / "HEAD.json", head)


def tree_fingerprint(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256_bytes(path.read_bytes()) for path in sorted(root.rglob("*")) if path.is_file()}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


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
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError as exc:
        pytest.skip(f"symlink unavailable on this host: {exc}")


def hardlink_or_skip(source: Path, target: Path) -> None:
    try:
        os.link(source, target)
    except OSError as exc:
        pytest.skip(f"hardlink unavailable on this host: {exc}")
