from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest

from nollm.archive import create_archive_snapshot, inspect_archive_snapshot, verify_archive_snapshot
from nollm.archive_manifest import manifest_hash, read_json, sha256_bytes, write_json
from nollm.coverage import validate_source_coverage
from nollm.legacy_import import (
    legacy_import_report,
    plan_legacy_import,
    reconcile_legacy_import,
    run_legacy_import,
    validate_legacy_import,
)
from nollm.native_field import (
    admit_current_publication,
    build_shard,
    current_publication,
    existing_shards_by_key,
    load_field_head,
    move_staged_shards,
    publish_field_revision,
    stage_shards,
)
from nollm.provenance import validate_deep_provenance, validate_staged_publication
from nollm.source_spans import build_source_span_inventory


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"
SOURCE_REF_RE = re.compile(r"/source/(src_[0-9a-f]{24})/blob/sha256:([0-9a-f]{64})#B([0-9]+)-B([0-9]+)$")


def test_t01_duplicate_valid_looking_source_link_rejects_active(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path)
    publication = publication_dir(memory_root, revision_id)
    links = read_jsonl(publication / "source-span-links.jsonl")
    links.append(dict(links[0]))
    write_jsonl(publication / "source-span-links.jsonl", links)
    refresh_package_hashes(memory_root, revision_id)

    admission = admit_current_publication(memory_root)

    assert admission["publication"] is None
    assert any("duplicate_source_span_link" in error for error in admission["errors"])
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False


def test_t02_removed_shard_and_matching_metadata_rewrite_rejects_active(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path)
    publication = publication_dir(memory_root, revision_id)
    revision = read_json(publication / "revision.json")
    receipt = read_json(publication / "receipt.json")
    removed = str(revision["shard_ids"][0])
    revision["shard_ids"] = [item for item in revision["shard_ids"] if item != removed]
    revision["shard_count"] = len(revision["shard_ids"])
    receipt["created_shard_ids"] = [item for item in receipt["created_shard_ids"] if item != removed]
    receipt["created_shard_count"] = len(receipt["created_shard_ids"])
    write_json(publication / "revision.json", revision)
    write_json(publication / "receipt.json", receipt)
    (publication / "shards" / f"{removed}.json").unlink()
    links = [link for link in read_jsonl(publication / "source-span-links.jsonl") if link.get("shard_id") != removed]
    write_jsonl(publication / "source-span-links.jsonl", links)
    projection = read_jsonl(publication / "source-span-projection.jsonl")
    for span in projection:
        if removed in [str(item) for item in span.get("related_shard_ids", [])]:
            span["disposition"] = "classified_pending"
            span["related_shard_ids"] = []
            span["lifecycle"] = "classified"
            span["reason"] = "legacy_import_candidate"
    write_jsonl(publication / "source-span-projection.jsonl", projection)
    refresh_package_hashes(memory_root, revision_id)

    admission = admit_current_publication(memory_root)

    assert admission["publication"] is None
    assert any("projection_candidate_not_sharded" in error or "pending_span_not_linked" in error for error in admission["errors"])
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False


def test_t03_projection_only_relation_forge_rejects_active(tmp_path: Path) -> None:
    memory_root, _batch_id, snapshot_id, revision_id = commit_fixture(tmp_path)
    publication = publication_dir(memory_root, revision_id)
    projection = read_jsonl(publication / "source-span-projection.jsonl")
    first = next(span for span in projection if span.get("disposition") == "sharded")
    first["related_shard_ids"] = list(first["related_shard_ids"]) + ["shard_" + "0" * 24]
    write_jsonl(publication / "source-span-projection.jsonl", projection)
    refresh_package_hashes(memory_root, revision_id)

    admission = admit_current_publication(memory_root)

    assert admission["publication"] is None
    assert any("projection_related_shard_not_in_revision" in error for error in admission["errors"])
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False


def test_t04_package_integrity_failure_after_head_fails_closed(tmp_path: Path) -> None:
    memory_root, _batch_id, snapshot_id, revision_id = commit_fixture(tmp_path)
    publication = publication_dir(memory_root, revision_id)
    (publication / "revision.json").write_text('{"tampered": true}\n', encoding="utf-8")

    admission = admit_current_publication(memory_root)
    coverage = validate_source_coverage(memory_root, snapshot_id, require_linked=True)

    assert admission["publication"] is None
    assert existing_shards_by_key(memory_root) == {}
    assert coverage["ok"] is False
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False


def test_t05_workflow_only_post_head_fault_keeps_active_and_reconciles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_root, batch_id, _snapshot_id = planned_fixture(tmp_path)
    monkeypatch.setenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD", "1")
    pending = run_legacy_import(memory_root, batch_id, commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD")

    reconciled = reconcile_legacy_import(memory_root, batch_id)

    assert pending["ok"] is True
    assert pending["reconciliation_pending"] is True
    assert current_publication(memory_root) is not None
    assert reconciled["ok"] is True
    assert validate_legacy_import(memory_root, batch_id)["ok"] is True


def test_t06_corrupted_ingress_after_active_package_is_structured_and_active_stays(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id, _revision_id = commit_fixture(tmp_path)
    (batch_dir(memory_root, batch_id) / "import-request.json").write_text("{ malformed", encoding="utf-8")

    results = [
        run_legacy_import(memory_root, batch_id, commit=True),
        reconcile_legacy_import(memory_root, batch_id),
        legacy_import_report(memory_root, batch_id),
    ]

    assert current_publication(memory_root) is not None
    for result in results:
        assert result["ok"] is False
        assert_no_raw_exception_name(result)


def test_t07_manifest_symlink_to_byte_identical_external_file_rejects(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_with_inventory(workspace, memory_root)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    external = tmp_path / "external-manifest.json"
    external.write_bytes(manifest_path.read_bytes())
    manifest_path.unlink()
    symlink_or_skip(manifest_path, external)

    result = verify_archive_snapshot(memory_root, snapshot_id)

    assert result["ok"] is False
    assert any("archive_manifest" in error and ("path_symlink" in error or "path_escape" in error) for error in result["errors"])


def test_t08_archive_object_symlink_to_byte_identical_external_file_rejects(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_with_inventory(workspace, memory_root)
    manifest = read_json(memory_root / "archive" / "manifests" / f"{snapshot_id}.json")
    digest = str(manifest["objects"][0]["content_hash"]).removeprefix("sha256:")
    object_path = memory_root / "archive" / "objects" / "sha256" / digest
    external = tmp_path / "external-object"
    external.write_bytes(object_path.read_bytes())
    object_path.unlink()
    symlink_or_skip(object_path, external)

    result = verify_archive_snapshot(memory_root, snapshot_id)

    assert result["ok"] is False
    assert any("archive_object" in error and ("path_symlink" in error or "path_escape" in error) for error in result["errors"])


def test_t09_manifest_filename_internal_snapshot_mismatch_rejects(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_with_inventory(workspace, memory_root)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest = read_json(manifest_path)
    manifest["snapshot_id"] = "snap_20990101_000000_000000000000"
    manifest["archive_manifest_hash"] = manifest_hash(manifest)
    manifest["manifest_hash"] = manifest["archive_manifest_hash"]
    write_json(manifest_path, manifest)

    result = verify_archive_snapshot(memory_root, snapshot_id)

    assert result["ok"] is False
    assert "archive_snapshot_id_mismatch" in result["errors"]


def test_t10_malformed_manifest_and_wrong_objects_type_are_structured(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_with_inventory(workspace, memory_root)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    original = read_json(manifest_path)
    manifest_path.write_text("{ malformed", encoding="utf-8")

    malformed = verify_archive_snapshot(memory_root, snapshot_id)

    original["objects"] = "not-a-list"
    original["archive_manifest_hash"] = manifest_hash(original)
    original["manifest_hash"] = original["archive_manifest_hash"]
    write_json(manifest_path, original)
    wrong_type = verify_archive_snapshot(memory_root, snapshot_id)

    assert malformed["ok"] is False
    assert malformed["errors"] == ["malformed_json:archive_manifest"]
    assert wrong_type["ok"] is False
    assert "invalid_archive_objects" in wrong_type["errors"]


def test_t11_preexisting_wrong_blob_refuses_snapshot_and_manifest(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    digest = sha256_bytes((workspace / "MEMORY.md").read_bytes())
    memory_root = tmp_path / "memory-root"
    wrong_blob = memory_root / "archive" / "objects" / "sha256" / digest
    wrong_blob.parent.mkdir(parents=True, exist_ok=True)
    wrong_blob.write_bytes(b"wrong bytes")

    result = create_archive_snapshot(workspace, memory_root)

    assert result["ok"] is False
    assert any("archive_object_hash_mismatch_existing" in error for error in result["errors"])
    assert not list((memory_root / "archive" / "manifests").glob("*.json"))


def test_t12_malformed_source_span_inventory_fails_active_and_public_apis_structured(tmp_path: Path) -> None:
    memory_root, _batch_id, snapshot_id, _revision_id = commit_fixture(tmp_path)
    (memory_root / "archive" / "source-spans" / f"{snapshot_id}.jsonl").write_text("{ malformed", encoding="utf-8")

    admission = admit_current_publication(memory_root)
    coverage = validate_source_coverage(memory_root, snapshot_id)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")

    assert admission["publication"] is None
    assert coverage["ok"] is False
    assert plan["ok"] is False
    for result in (admission, coverage, plan):
        assert_no_raw_exception_name(result)


def test_t13_snapshot_and_batch_traversal_ids_reject_before_escape(tmp_path: Path) -> None:
    memory_root = tmp_path / "memory-root"
    outside = tmp_path / "escape"
    outside.mkdir()

    archive = verify_archive_snapshot(memory_root, "../../escape")
    run = run_legacy_import(memory_root, "../../../escape-batch", dry_run=True)
    report = legacy_import_report(memory_root, "../../../escape-batch")

    assert archive["ok"] is False
    assert "invalid_snapshot_id" in archive["errors"]
    assert run["ok"] is False and "invalid_batch_id" in run["errors"]
    assert report["ok"] is False and "invalid_batch_id" in report["errors"]
    assert list(outside.iterdir()) == []


def test_t14_equal_memory_and_dreams_bytes_keep_distinct_source_entries_spans_and_shards(tmp_path: Path) -> None:
    text = "Mira coordinates Atlas across rooms.\n"
    workspace = workspace_with(tmp_path, {"MEMORY.md": text, "DREAMS.md": text})
    memory_root, batch_id, snapshot_id, revision_id = commit_workspace(workspace, tmp_path / "memory-root")
    manifest = read_json(memory_root / "archive" / "manifests" / f"{snapshot_id}.json")
    spans = read_jsonl(memory_root / "archive" / "source-spans" / f"{snapshot_id}.jsonl")
    publication = publication_dir(memory_root, revision_id)
    revision = read_json(publication / "revision.json")

    source_ids = [obj["source_object_id"] for obj in manifest["objects"]]
    source_refs = [link["source_ref"] for link in read_jsonl(publication / "source-span-links.jsonl")]

    assert len(manifest["objects"]) == 2
    assert len({obj["content_hash"] for obj in manifest["objects"]}) == 1
    assert len(set(source_ids)) == 2
    assert len({span["span_id"] for span in spans}) == 2
    assert len(set(source_refs)) == 2
    assert revision["shard_count"] == 2
    assert validate_legacy_import(memory_root, batch_id)["ok"] is True


def test_t15_dreams_remains_tentative_and_memory_remains_legacy_recorded(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n", "DREAMS.md": "Atlas dreams of Mira.\n"})
    memory_root, _batch_id, snapshot_id, revision_id = commit_workspace(workspace, tmp_path / "memory-root")
    manifest = read_json(memory_root / "archive" / "manifests" / f"{snapshot_id}.json")
    states_by_source = {obj["source_object_id"]: obj["epistemic_state"] for obj in manifest["objects"]}
    source_by_path = {obj["original_relative_path"]: obj["source_object_id"] for obj in manifest["objects"]}
    publication = publication_dir(memory_root, revision_id)
    shard_states: dict[str, str] = {}
    for shard_path in (publication / "shards").glob("*.json"):
        shard = read_json(shard_path)
        source_id = source_id_from_ref(shard["source_refs"][0])
        shard_states[source_id] = shard["epistemic_state"]

    assert states_by_source[source_by_path["DREAMS.md"]] == "tentative"
    assert states_by_source[source_by_path["MEMORY.md"]] == "legacy_recorded"
    assert shard_states[source_by_path["DREAMS.md"]] == "tentative"
    assert shard_states[source_by_path["MEMORY.md"]] == "legacy_recorded"


def test_t16_duplicate_source_entry_id_or_original_path_rejects_manifest(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n", "DREAMS.md": "Atlas dreams of Mira.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_with_inventory(workspace, memory_root)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest = read_json(manifest_path)
    manifest["objects"][1]["source_object_id"] = manifest["objects"][0]["source_object_id"]
    manifest["objects"][1]["archive_object_id"] = manifest["objects"][0]["source_object_id"]
    manifest["archive_manifest_hash"] = manifest_hash(manifest)
    manifest["manifest_hash"] = manifest["archive_manifest_hash"]
    write_json(manifest_path, manifest)
    duplicate_id = verify_archive_snapshot(memory_root, snapshot_id)

    snapshot_id = snapshot_with_inventory(workspace, tmp_path / "memory-root-2")
    memory_root_2 = tmp_path / "memory-root-2"
    manifest_path_2 = memory_root_2 / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest_2 = read_json(manifest_path_2)
    manifest_2["objects"][1]["original_relative_path"] = manifest_2["objects"][0]["original_relative_path"]
    manifest_2["archive_manifest_hash"] = manifest_hash(manifest_2)
    manifest_2["manifest_hash"] = manifest_2["archive_manifest_hash"]
    write_json(manifest_path_2, manifest_2)
    duplicate_path = verify_archive_snapshot(memory_root_2, snapshot_id)

    assert any("duplicate_source_object_id" in error for error in duplicate_id["errors"])
    assert any("duplicate_original_relative_path" in error for error in duplicate_path["errors"])


def test_t17_source_ref_with_correct_blob_but_wrong_source_object_rejects(tmp_path: Path) -> None:
    text = "Mira coordinates Atlas across rooms.\n"
    workspace = workspace_with(tmp_path, {"MEMORY.md": text, "DREAMS.md": text})
    memory_root, _batch_id, snapshot_id, revision_id = commit_workspace(workspace, tmp_path / "memory-root")
    publication = publication_dir(memory_root, revision_id)
    manifest = read_json(memory_root / "archive" / "manifests" / f"{snapshot_id}.json")
    source_ids = [obj["source_object_id"] for obj in manifest["objects"]]
    shard_path = next((publication / "shards").glob("*.json"))
    shard = read_json(shard_path)
    old_ref = shard["source_refs"][0]
    wrong_source = source_ids[1] if source_ids[0] in old_ref else source_ids[0]
    new_ref = re.sub(r"/source/src_[0-9a-f]{24}/", f"/source/{wrong_source}/", old_ref)
    shard["source_refs"] = [new_ref]
    write_json(shard_path, shard)
    links = read_jsonl(publication / "source-span-links.jsonl")
    for link in links:
        if link["shard_id"] == shard["shard_id"]:
            link["source_ref"] = new_ref
    write_jsonl(publication / "source-span-links.jsonl", links)
    refresh_package_hashes(memory_root, revision_id)

    admission = admit_current_publication(memory_root)

    assert admission["publication"] is None
    assert any(
        "source_ref_has_no_exact_span" in error
        or "legacy_shard_idempotence_key_mismatch" in error
        or "missing_continuity_ref" in error
        or "link_span_id_mismatch" in error
        for error in admission["errors"]
    )


def test_t18_archive_only_snapshot_does_not_claim_head_and_later_substantive_import_commits(tmp_path: Path) -> None:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "# Heading Only\n"})
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_with_inventory(workspace, memory_root)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    no_head_after_archive_only = load_field_head(memory_root) is None

    (workspace / "MEMORY.md").write_text("Mira remembers Atlas.\n", encoding="utf-8")
    next_snapshot = snapshot_with_inventory(workspace, memory_root)
    next_plan = plan_legacy_import(memory_root, next_snapshot, target_field_id="field_fixture")
    commit = run_legacy_import(memory_root, str(next_plan["batch_id"]), commit=True)

    assert plan["ok"] is True and plan["archive_only"] is True
    assert no_head_after_archive_only is True
    assert next_plan["ok"] is True and "batch_id" in next_plan
    assert commit["ok"] is True
    assert current_publication(memory_root) is not None


def test_t19_obsolete_flat_publisher_cannot_modify_active_head(tmp_path: Path) -> None:
    memory_root, _batch_id, _snapshot_id, _revision_id = commit_fixture(tmp_path)
    before = (memory_root / "field" / "HEAD.json").read_bytes()
    shard = build_shard(
        {
            "text": "fixture",
            "text_hash": "sha256:" + "a" * 64,
            "source_ref": "archive://snapshot/snap_20990101_000000_000000000000/source/src_" + "b" * 24 + "/blob/sha256:" + "c" * 64 + "#B0-B7",
            "span_id": "span_" + "b" * 24 + "_0000",
        },
        batch_id="batch_" + "d" * 20,
        source_policy_id="openclaw_legacy_v1",
        idempotence_key="sha256:" + "e" * 64,
    )
    stage_shards(memory_root, "batch_" + "d" * 20, [shard])
    moved = move_staged_shards(memory_root, "batch_" + "d" * 20)
    result = publish_field_revision(memory_root, batch_id="batch_" + "d" * 20, target_field_id="field_fixture", shard_ids=moved)

    assert result["ok"] is False
    assert (memory_root / "field" / "HEAD.json").read_bytes() == before
    assert current_publication(memory_root) is not None


def test_t20_writer_busy_prevents_publication_side_effects_and_retry_can_commit(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id = planned_fixture(tmp_path)
    lock_dir = memory_root / "locks" / "legacy-import-writer.lock"
    lock_dir.mkdir(parents=True)
    write_json(lock_dir / "owner.json", {"batch_id": "batch_" + "f" * 20})

    busy = run_legacy_import(memory_root, batch_id, commit=True)
    publications_after_busy = (memory_root / "field" / "publications").exists()
    shutil.rmtree(lock_dir)
    committed = run_legacy_import(memory_root, batch_id, commit=True)

    assert busy["ok"] is False
    assert busy["retry_required"] is True
    assert "writer_busy" in busy["errors"]
    assert publications_after_busy is False
    assert committed["ok"] is True
    assert validate_legacy_import(memory_root, batch_id)["ok"] is True


def test_t21_public_malformed_identifier_apis_are_structured(tmp_path: Path) -> None:
    memory_root = tmp_path / "memory-root"

    results = [
        inspect_archive_snapshot(memory_root, "../../escape"),
        validate_deep_provenance(memory_root, "../../escape", "../../field"),
        validate_staged_publication(memory_root, "../../../batch", "../../escape", "../../field"),
        run_legacy_import(memory_root, "../../../batch", commit=True),
        validate_legacy_import(memory_root, "../../../batch"),
        legacy_import_report(memory_root, "../../../batch"),
    ]

    for result in results:
        assert result["ok"] is False if "ok" in result else result.get("publication") is None
        assert_no_raw_exception_name(result)


def planned_fixture(tmp_path: Path) -> tuple[Path, str, str]:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = snapshot_with_inventory(workspace, memory_root)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True
    assert "batch_id" in plan
    return memory_root, str(plan["batch_id"]), snapshot_id


def commit_fixture(tmp_path: Path) -> tuple[Path, str, str, str]:
    memory_root, batch_id, snapshot_id = planned_fixture(tmp_path)
    commit = run_legacy_import(memory_root, batch_id, commit=True)
    assert commit["ok"] is True
    return memory_root, batch_id, snapshot_id, str(commit["field_revision_id"])


def commit_workspace(workspace: Path, memory_root: Path) -> tuple[Path, str, str, str]:
    snapshot_id = snapshot_with_inventory(workspace, memory_root)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    assert commit["ok"] is True
    return memory_root, str(plan["batch_id"]), snapshot_id, str(commit["field_revision_id"])


def snapshot_with_inventory(workspace: Path, memory_root: Path) -> str:
    snapshot = create_archive_snapshot(workspace, memory_root)
    assert snapshot["ok"] is True
    inventory = build_source_span_inventory(memory_root, str(snapshot["snapshot_id"]))
    assert inventory["ok"] is True
    return str(snapshot["snapshot_id"])


def workspace_with(tmp_path: Path, files: dict[str, str]) -> Path:
    workspace = tmp_path / "workspace"
    for rel, text in files.items():
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return workspace


def publication_dir(memory_root: Path, revision_id: str) -> Path:
    return memory_root / "field" / "publications" / revision_id


def batch_dir(memory_root: Path, batch_id: str) -> Path:
    return memory_root / "ingress" / "legacy-import" / batch_id


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
        if path.exists():
            activation[key] = "sha256:" + sha256_bytes(path.read_bytes())
    write_json(publication / "activation.json", activation)
    manifest = read_json(publication / "publication-manifest.json")
    manifest["artifact_hashes"] = {
        path.relative_to(publication).as_posix(): "sha256:" + sha256_bytes(path.read_bytes())
        for path in sorted(publication.rglob("*"))
        if path.is_file() and path.name != "publication-manifest.json"
    }
    write_json(publication / "publication-manifest.json", manifest)
    head_path = memory_root / "field" / "HEAD.json"
    if head_path.exists():
        head = read_json(head_path)
        if head.get("field_revision_id") == revision_id:
            head["activation_hash"] = "sha256:" + sha256_bytes((publication / "activation.json").read_bytes())
            head["publication_manifest_hash"] = "sha256:" + sha256_bytes((publication / "publication-manifest.json").read_bytes())
            write_json(head_path, head)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def source_id_from_ref(source_ref: str) -> str:
    match = SOURCE_REF_RE.search(source_ref)
    assert match is not None
    return match.group(1)


def symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink unavailable on this Windows host: {exc}")


def assert_no_raw_exception_name(result: dict[str, Any]) -> None:
    joined = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for forbidden in ["Traceback", "JSONDecodeError", "AttributeError", "KeyError", "FileNotFoundError"]:
        assert forbidden not in joined


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
