from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nollm.archive import create_archive_snapshot, load_manifest, verify_archive_snapshot
from nollm.archive_manifest import manifest_hash, read_json, sha256_bytes, write_json
from nollm.legacy_import import (
    plan_legacy_import,
    recover_legacy_import,
    run_legacy_import,
    validate_legacy_import,
)
from nollm.native_field import admit_current_publication, load_field_head, move_staged_shards, stage_shards
from nollm.path_safety import validate_batch_id
from nollm.provenance import validate_deep_provenance
from nollm.source_spans import build_source_span_inventory


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("source_object_id", "archive_source_source_object_id_mismatch"),
        ("source_policy_id", "invalid_source_policy_id"),
        ("epistemic_state", "archive_source_epistemic_state_mismatch"),
        ("origin_kind", "archive_source_origin_kind_mismatch"),
        ("operational_state", "archive_source_operational_state_mismatch"),
        ("archived_path", "archive_source_archived_path_mismatch"),
        ("original_relative_path", "source_path_not_allowed"),
        ("duplicate_source_id", "duplicate_source_object_id"),
        ("duplicate_path", "duplicate_original_relative_path"),
        ("legacy_objects", "legacy_objects_field_forbidden"),
        ("legacy_source_entries", "legacy_source_entries_field_forbidden"),
        ("legacy_archive_object_id", "legacy_archive_object_id_forbidden"),
        ("v2_schema", "legacy_mt1_archive_v2_requires_rearchive"),
    ],
)
def test_archive_v3_source_semantics_reject_mutable_claims(tmp_path: Path, case: str, expected: str) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n", "DREAMS.md": "Atlas dreams of Mira.\n"})
    memory_root, snapshot_id = snapshot_with_inventory(workspace, tmp_path / "memory-root")
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest = read_json(manifest_path)

    if case == "source_object_id":
        manifest["sources"][0]["source_object_id"] = "src_" + "f" * 24
    elif case == "source_policy_id":
        manifest["source_policy_id"] = "arbitrary_policy_v999"
    elif case == "epistemic_state":
        manifest["sources"][0]["epistemic_state"] = "confirmed"
    elif case == "origin_kind":
        manifest["sources"][0]["origin_kind"] = "model_derived"
    elif case == "operational_state":
        manifest["sources"][0]["operational_state"] = "sealed"
    elif case == "archived_path":
        manifest["sources"][0]["archived_path"] += "-forged"
    elif case == "original_relative_path":
        manifest["sources"][0]["original_relative_path"] = "../MEMORY.md"
    elif case == "duplicate_source_id":
        manifest["sources"][1]["source_object_id"] = manifest["sources"][0]["source_object_id"]
    elif case == "duplicate_path":
        manifest["sources"][1]["original_relative_path"] = manifest["sources"][0]["original_relative_path"]
    elif case == "legacy_objects":
        manifest["objects"] = list(manifest["sources"])
    elif case == "legacy_source_entries":
        manifest["source_entries"] = list(manifest["sources"])
    elif case == "legacy_archive_object_id":
        manifest["sources"][0]["archive_object_id"] = manifest["sources"][0]["source_object_id"]
    elif case == "v2_schema":
        manifest["schema"] = "nollm.archive_manifest.v2"
    refresh_archive_manifest(manifest_path, manifest)

    verify = verify_archive_snapshot(memory_root, snapshot_id)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")

    assert verify["ok"] is False
    assert any(expected in error for error in verify["errors"])
    assert plan["ok"] is False
    assert_no_raw_exception_name(plan)


def test_post_publication_archive_state_rewrite_still_fails_closed(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_workspace(
        workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"}),
        tmp_path / "memory-root",
    )
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest = read_json(manifest_path)
    manifest["sources"][0]["epistemic_state"] = "confirmed"
    refresh_archive_manifest(manifest_path, manifest)
    refresh_active_archive_hashes(memory_root, revision_id, manifest["archive_manifest_hash"])

    admission = admit_current_publication(memory_root)
    provenance = validate_deep_provenance(memory_root, snapshot_id, revision_id)
    validation = validate_legacy_import(memory_root, batch_id)

    assert admission["publication"] is None
    assert provenance["ok"] is False
    assert validation["ok"] is False
    assert any("archive_source_epistemic_state_mismatch" in error for error in admission["errors"] + validation["errors"])


def test_saferoot_rejects_external_staging_publication_ingress_and_ledger_writes(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root, snapshot_id = snapshot_with_inventory(workspace, tmp_path / "memory-root")
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True
    batch_id = str(plan["batch_id"])
    sentinel = tmp_path / "external"
    sentinel.mkdir()
    before = directory_fingerprint(sentinel)

    shutil_symlink_or_skip(memory_root / "field" / ".staging", sentinel)
    staging_blocked = run_legacy_import(memory_root, batch_id, commit=True)
    assert staging_blocked["ok"] is False
    assert directory_fingerprint(sentinel) == before
    assert load_field_head(memory_root) is None
    (memory_root / "field" / ".staging").unlink()

    batch_dir = memory_root / "ingress" / "legacy-import" / batch_id
    remove_tree(batch_dir)
    shutil_symlink_or_skip(batch_dir, sentinel)
    ingress_blocked = run_legacy_import(memory_root, batch_id, dry_run=True)
    assert ingress_blocked["ok"] is False
    assert directory_fingerprint(sentinel) == before
    batch_dir.unlink()

    ledger = memory_root / "ledger"
    remove_tree(ledger)
    shutil_symlink_or_skip(ledger, sentinel)
    ledger_blocked = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert ledger_blocked["ok"] is False
    assert directory_fingerprint(sentinel) == before


def test_obsolete_flat_writers_reject_traversal_without_io(tmp_path: Path) -> None:
    memory_root = tmp_path / "memory-root"
    stage = stage_shards(memory_root, "../../escape", [])
    move = move_staged_shards(memory_root, "../../escape")

    assert stage["ok"] is False
    assert move["ok"] is False
    assert stage["errors"] == ["unsupported_legacy_flat_writer"]
    assert move["errors"] == ["unsupported_legacy_flat_writer"]
    assert not memory_root.exists()


def test_post_head_provenance_failure_deactivates_candidate_without_prior(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import nollm.legacy_import as legacy_import_module

    memory_root, batch_id, _snapshot_id = planned_workspace(workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"}), tmp_path / "memory-root")

    monkeypatch.setattr(legacy_import_module, "validate_deep_provenance", lambda *args, **kwargs: {"ok": False, "errors": ["forced_post_head_provenance_failure"]})
    result = run_legacy_import(memory_root, batch_id, commit=True)

    assert result["ok"] is False
    assert result["state"] == "quarantined"
    assert result["recovery_required"] is True
    assert load_field_head(memory_root) is None


def test_repeated_recovery_ids_remain_valid_and_later_commit_succeeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_root, batch_id, _snapshot_id = planned_workspace(workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"}), tmp_path / "memory-root")

    monkeypatch.setenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD", "1")
    first_failed = run_legacy_import(memory_root, batch_id, commit=True)
    first_recovery = recover_legacy_import(memory_root, batch_id)
    first_recovery_id = str(first_recovery["replacement_batch_id"])
    second_failed = run_legacy_import(memory_root, first_recovery_id, commit=True)
    second_recovery = recover_legacy_import(memory_root, first_recovery_id)
    second_recovery_id = str(second_recovery["replacement_batch_id"])
    monkeypatch.delenv("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD")
    committed = run_legacy_import(memory_root, second_recovery_id, commit=True)

    assert first_failed["ok"] is False
    assert second_failed["ok"] is False
    assert first_recovery_id.endswith("_r1")
    assert second_recovery_id.endswith("_r2")
    assert not second_recovery_id.endswith("_recovery_recovery")
    assert validate_batch_id(first_recovery_id) == []
    assert validate_batch_id(second_recovery_id) == []
    assert committed["ok"] is True
    assert validate_legacy_import(memory_root, second_recovery_id)["ok"] is True


def test_public_error_contract_for_invalid_field_and_malformed_ledger(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root, snapshot_id = snapshot_with_inventory(workspace, tmp_path / "memory-root")
    invalid_field = plan_legacy_import(memory_root, snapshot_id, target_field_id="../../evil\nfield")
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True
    (memory_root / "ledger" / "events.jsonl").write_text("{ malformed", encoding="utf-8")

    report = validate_legacy_import(memory_root, str(plan["batch_id"]))

    assert invalid_field["ok"] is False
    assert "invalid_field_id" in invalid_field["errors"]
    assert report["ok"] is False
    assert "malformed_jsonl:ledger" in report["errors"]
    assert_no_raw_exception_name(invalid_field)
    assert_no_raw_exception_name(report)


def planned_workspace(workspace: Path, memory_root: Path) -> tuple[Path, str, str]:
    root, snapshot_id = snapshot_with_inventory(workspace, memory_root)
    plan = plan_legacy_import(root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True
    return root, str(plan["batch_id"]), snapshot_id


def commit_workspace(workspace: Path, memory_root: Path) -> tuple[Path, str, str, str]:
    root, batch_id, snapshot_id = planned_workspace(workspace, memory_root)
    commit = run_legacy_import(root, batch_id, commit=True)
    assert commit["ok"] is True
    return root, batch_id, snapshot_id, str(commit["field_revision_id"])


def snapshot_with_inventory(workspace: Path, memory_root: Path) -> tuple[Path, str]:
    snapshot = create_archive_snapshot(workspace, memory_root)
    assert snapshot["ok"] is True
    inventory = build_source_span_inventory(memory_root, str(snapshot["snapshot_id"]))
    assert inventory["ok"] is True
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


def directory_fingerprint(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_bytes(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def remove_tree(path: Path) -> None:
    if path.exists() and path.is_dir() and not path.is_symlink():
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        path.rmdir()
    elif path.exists():
        path.unlink()


def shutil_symlink_or_skip(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink unavailable on this Windows host: {exc}")


def assert_no_raw_exception_name(result: dict[str, Any]) -> None:
    joined = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for forbidden in ["Traceback", "JSONDecodeError", "KeyError", "IsADirectoryError", "FileNotFoundError"]:
        assert forbidden not in joined
