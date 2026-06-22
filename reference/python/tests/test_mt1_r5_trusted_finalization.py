from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from nollm.archive import create_archive_snapshot, load_manifest
from nollm.archive_manifest import read_json, sha256_bytes, write_json
from nollm.coverage import validate_source_coverage
from nollm.legacy_import import plan_legacy_import, reconcile_legacy_import, run_legacy_import, validate_legacy_import
from nollm.native_field import current_publication, existing_shards_by_key
from nollm.provenance import validate_deep_provenance


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


@pytest.mark.parametrize(
    "fault_env",
    [
        "NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD",
        "NOLLM_MT1_FORCE_COMMIT_LEDGER_OSERROR_AFTER_HEAD",
        "NOLLM_MT1_FORCE_STATE_OSERROR_AFTER_HEAD",
    ],
)
def test_t1_finalization_fault_remains_pending_and_reconciles_once(tmp_path: Path, monkeypatch, fault_env: str) -> None:
    memory_root, batch_id, snapshot_id, revision_id = planned_fixture(tmp_path)
    monkeypatch.setenv(fault_env, "1")

    result = run_legacy_import(memory_root, batch_id, commit=True)
    revision_id = str(result["field_revision_id"])

    assert result["ok"] is True
    assert result["published"] is True
    assert result["reconciliation_pending"] is True
    assert state(memory_root, batch_id) == "publishing"
    assert current_publication(memory_root) is not None
    if fault_env == "NOLLM_MT1_FORCE_COMMIT_LEDGER_OSERROR_AFTER_HEAD":
        assert finalization_event_count(memory_root, batch_id, result["field_revision_id"]) == 0

    monkeypatch.delenv(fault_env)
    reconciled = reconcile_legacy_import(memory_root, batch_id)
    repeated = reconcile_legacy_import(memory_root, batch_id)

    assert reconciled["ok"] is True
    assert reconciled["changed"] is True
    assert repeated["ok"] is True
    assert repeated["changed"] is False
    assert state(memory_root, batch_id) == "committed"
    assert finalization_event_count(memory_root, batch_id, revision_id) == 1
    assert validate_legacy_import(memory_root, batch_id)["ok"] is True
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is True


@pytest.mark.parametrize(
    "relative_path",
    [
        "field/HEAD.json",
        "field/publications/{revision}/publication-manifest.json",
        "field/publications/{revision}/revision.json",
        "field/publications/{revision}/receipt.json",
        "field/publications/{revision}/source-span-links.jsonl",
        "field/publications/{revision}/source-span-projection.jsonl",
        "field/publications/{revision}/shards/{first_shard}.json",
    ],
)
def test_t2_malformed_active_artifacts_fail_closed_without_raw_exceptions(tmp_path: Path, relative_path: str) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path)
    publication = memory_root / "field" / "publications" / revision_id
    revision = read_json(publication / "revision.json")
    first_shard = str(revision["shard_ids"][0])
    target = memory_root / relative_path.format(revision=revision_id, first_shard=first_shard)
    target.write_text("{ malformed", encoding="utf-8")
    if target.name == "publication-manifest.json":
        head = read_json(memory_root / "field" / "HEAD.json")
        head["publication_manifest_hash"] = "sha256:" + sha256_bytes(target.read_bytes())
        write_json(memory_root / "field" / "HEAD.json", head)
    elif target.name != "HEAD.json":
        rehash_publication_head(memory_root, revision_id)

    assert current_publication(memory_root) is None
    assert existing_shards_by_key(memory_root) == {}
    coverage = validate_source_coverage(memory_root, snapshot_id, require_linked=True)
    provenance = validate_deep_provenance(memory_root, snapshot_id, revision_id)
    validation = validate_legacy_import(memory_root, batch_id)

    assert coverage["ok"] is False
    assert provenance["ok"] is False
    assert validation["ok"] is False
    assert not any("Traceback" in error for error in provenance["errors"] + validation["errors"])


def test_t3_activation_path_symlinks_and_head_identity_fail_closed(tmp_path: Path) -> None:
    memory_root, _batch_id, snapshot_id, revision_id = commit_fixture(tmp_path / "head-field-id")
    head = read_json(memory_root / "field" / "HEAD.json")
    head["field_id"] = "field_tampered"
    write_json(memory_root / "field" / "HEAD.json", head)
    assert_inactive(memory_root, snapshot_id, revision_id)

    memory_root, _batch_id, snapshot_id, revision_id = commit_fixture(tmp_path / "head-link")
    external_head = tmp_path / "external-head.json"
    external_head.write_bytes((memory_root / "field" / "HEAD.json").read_bytes())
    (memory_root / "field" / "HEAD.json").unlink()
    try:
        (memory_root / "field" / "HEAD.json").symlink_to(external_head)
    except OSError:
        pytest.skip("symlink creation is not available on this Windows host")
    assert_inactive(memory_root, snapshot_id, revision_id)

    memory_root, _batch_id, snapshot_id, revision_id = commit_fixture(tmp_path / "publications-link")
    external_publications = tmp_path / "external-publications"
    shutil.move(str(memory_root / "field" / "publications"), external_publications)
    try:
        (memory_root / "field" / "publications").symlink_to(external_publications, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is not available on this Windows host")
    assert_inactive(memory_root, snapshot_id, revision_id)

    memory_root, _batch_id, snapshot_id, revision_id = commit_fixture(tmp_path / "publication-link")
    publication = memory_root / "field" / "publications" / revision_id
    external_publication = tmp_path / "external-publication"
    shutil.move(str(publication), external_publication)
    try:
        publication.symlink_to(external_publication, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is not available on this Windows host")
    assert_inactive(memory_root, snapshot_id, revision_id)


@pytest.mark.parametrize(
    "case",
    [
        "extra_non_memory_link",
        "extra_unknown_span_link",
        "extra_unknown_shard_link",
        "duplicate_exact_link",
        "projection_without_matching_link",
        "duplicate_projection_span",
    ],
)
def test_t4_relation_closure_rejects_extra_duplicate_and_orphan_links(tmp_path: Path, case: str) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path / case)
    publication = memory_root / "field" / "publications" / revision_id
    links_path = publication / "source-span-links.jsonl"
    projection_path = publication / "source-span-projection.jsonl"
    links = read_jsonl(links_path)
    projection = read_jsonl(projection_path)
    valid_link = dict(links[0])

    if case == "extra_non_memory_link":
        non_memory = next(span for span in projection if span["disposition"] == "non_memory")
        extra = dict(valid_link)
        extra["span_id"] = non_memory["span_id"]
        extra["source_ref"] = source_ref_for_span(memory_root, snapshot_id, non_memory)
        links.append(extra)
    elif case == "extra_unknown_span_link":
        extra = dict(valid_link)
        extra["span_id"] = "span_missing"
        links.append(extra)
    elif case == "extra_unknown_shard_link":
        extra = dict(valid_link)
        extra["shard_id"] = "shard_missing"
        links.append(extra)
    elif case == "duplicate_exact_link":
        links.append(dict(valid_link))
    elif case == "projection_without_matching_link":
        sharded = next(span for span in projection if span["disposition"] == "sharded")
        sharded["related_shard_ids"] = []
    elif case == "duplicate_projection_span":
        projection = projection[:-1] + [dict(projection[0])]

    write_jsonl(links_path, links)
    write_jsonl(projection_path, projection)
    rehash_publication_head(memory_root, revision_id)

    assert current_publication(memory_root) is None
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False


def test_t5_different_snapshot_or_target_field_cannot_replace_active_field(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root, _batch_id, snapshot_id, revision_id = commit_existing_workspace(workspace, tmp_path / "memory-root")
    head_before = (memory_root / "field" / "HEAD.json").read_bytes()
    roster_before = set(existing_shards_by_key(memory_root))

    for path in workspace.rglob("*.md"):
        path.unlink()
    (workspace / "memory" / "2026-06-22.md").write_text("# Extra\n\n- new material\n", encoding="utf-8")
    snapshot_b = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])

    cross_snapshot = plan_legacy_import(memory_root, snapshot_b, target_field_id="field_fixture")
    different_field = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_other")

    assert cross_snapshot["ok"] is False
    assert "cross_snapshot_replacement_not_supported" in cross_snapshot["errors"]
    assert different_field["ok"] is False
    assert "single_head_field_switch_not_supported" in different_field["errors"]
    assert (memory_root / "field" / "HEAD.json").read_bytes() == head_before
    assert current_publication(memory_root) == memory_root / "field" / "publications" / revision_id
    assert set(existing_shards_by_key(memory_root)) == roster_before


def planned_fixture(tmp_path: Path) -> tuple[Path, str, str, str]:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True
    batch_id = str(plan["batch_id"])
    revision_seed = run_legacy_import(memory_root, batch_id, dry_run=True)
    assert revision_seed["ok"] is True
    # The final revision id is deterministic but easiest to read after the pending commit.
    return memory_root, batch_id, snapshot_id, ""


def commit_fixture(tmp_path: Path) -> tuple[Path, str, str, str]:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    return commit_existing_workspace(workspace, tmp_path / "memory-root")


def commit_existing_workspace(workspace: Path, memory_root: Path) -> tuple[Path, str, str, str]:
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    assert commit["ok"] is True
    return memory_root, str(plan["batch_id"]), snapshot_id, str(commit["field_revision_id"])


def assert_inactive(memory_root: Path, snapshot_id: str, revision_id: str) -> None:
    assert current_publication(memory_root) is None
    assert existing_shards_by_key(memory_root) == {}
    assert validate_source_coverage(memory_root, snapshot_id, require_linked=True)["ok"] is False
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False


def rehash_publication_head(memory_root: Path, revision_id: str) -> None:
    publication = memory_root / "field" / "publications" / revision_id
    manifest = read_json(publication / "publication-manifest.json")
    hashes = {}
    for path in sorted(publication.rglob("*")):
        if path.is_file() and path.name != "publication-manifest.json":
            hashes[path.relative_to(publication).as_posix()] = "sha256:" + sha256_bytes(path.read_bytes())
    manifest["artifact_hashes"] = hashes
    write_json(publication / "publication-manifest.json", manifest)
    head = read_json(memory_root / "field" / "HEAD.json")
    head["publication_manifest_hash"] = "sha256:" + sha256_bytes((publication / "publication-manifest.json").read_bytes())
    write_json(memory_root / "field" / "HEAD.json", head)


def source_ref_for_span(memory_root: Path, snapshot_id: str, span: dict) -> str:
    manifest = load_manifest(memory_root, snapshot_id)
    by_object = {obj["source_object_id"]: obj for obj in manifest["sources"]}
    obj = by_object[span["source_object_id"]]
    digest = str(obj["content_hash"]).removeprefix("sha256:")
    return f"archive://snapshot/{snapshot_id}/source/{span['source_object_id']}/blob/sha256:{digest}#B{span['start_byte']}-B{span['end_byte_exclusive']}"


def finalization_event_count(memory_root: Path, batch_id: str, revision_id: str) -> int:
    event_id = f"legacy_import_commit:{batch_id}:{revision_id}"
    ledger = memory_root / "ledger" / "events.jsonl"
    if not ledger.exists():
        return 0
    return sum(1 for record in read_jsonl(ledger) if record.get("event_id") == event_id)


def state(memory_root: Path, batch_id: str) -> str:
    return str(read_json(memory_root / "ingress" / "legacy-import" / batch_id / "state.json")["state"])


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
