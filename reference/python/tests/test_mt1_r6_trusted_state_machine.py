from __future__ import annotations

import json
from pathlib import Path

import pytest

from nollm.archive import create_archive_snapshot
from nollm.archive_manifest import read_json, sha256_bytes, write_json
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
def test_t1_publishing_commit_retry_delegates_to_reconcile(tmp_path: Path, monkeypatch, fault_env: str) -> None:
    memory_root, batch_id, snapshot_id = planned_fixture(tmp_path)
    monkeypatch.setenv(fault_env, "1")
    pending = run_legacy_import(memory_root, batch_id, commit=True)
    revision_id = str(pending["field_revision_id"])
    head_before = (memory_root / "field" / "HEAD.json").read_bytes()
    roster_before = set(existing_shards_by_key(memory_root))
    publications_before = publication_dirs(memory_root)

    still_pending = run_legacy_import(memory_root, batch_id, commit=True)

    assert still_pending["ok"] is True
    assert still_pending["reconciliation_pending"] is True
    assert state(memory_root, batch_id) == "publishing"
    assert (memory_root / "field" / "HEAD.json").read_bytes() == head_before
    assert set(existing_shards_by_key(memory_root)) == roster_before
    assert publication_dirs(memory_root) == publications_before

    monkeypatch.delenv(fault_env)
    committed = run_legacy_import(memory_root, batch_id, commit=True)

    assert committed["ok"] is True
    assert state(memory_root, batch_id) == "committed"
    assert (memory_root / "field" / "HEAD.json").read_bytes() == head_before
    assert publication_dirs(memory_root) == publications_before
    assert finalization_event_count(memory_root, batch_id, revision_id) == 1
    assert validate_legacy_import(memory_root, batch_id)["ok"] is True
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is True


def test_t2_duplicate_commit_after_active_corruption_is_not_success(tmp_path: Path) -> None:
    memory_root, batch_id, _snapshot_id, revision_id = commit_fixture(tmp_path)
    shard_path = next((memory_root / "field" / "publications" / revision_id / "shards").glob("*.json"))
    shard = read_json(shard_path)
    shard["text"] = "corrupted active text"
    write_json(shard_path, shard)
    state_before = state(memory_root, batch_id)

    result = run_legacy_import(memory_root, batch_id, commit=True)

    assert result["ok"] is False
    assert result["state"] == "committed"
    assert state(memory_root, batch_id) == state_before
    assert "committed" not in result.get("errors", [])


@pytest.mark.parametrize("corruption", ["shard", "head", "receipt"])
def test_t3_untrusted_existing_head_blocks_different_snapshot_without_batch(tmp_path: Path, corruption: str) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root, _batch_id, _snapshot_id, revision_id = commit_existing_workspace(workspace, tmp_path / "memory-root")
    ingress_before = existing_ingress_dirs(memory_root)

    if corruption == "shard":
        shard_path = next((memory_root / "field" / "publications" / revision_id / "shards").glob("*.json"))
        shard = read_json(shard_path)
        shard["text"] = "tampered"
        write_json(shard_path, shard)
    elif corruption == "head":
        (memory_root / "field" / "HEAD.json").write_text("{ malformed", encoding="utf-8")
    elif corruption == "receipt":
        receipt_path = memory_root / "field" / "publications" / revision_id / "receipt.json"
        receipt_path.write_text("{ malformed", encoding="utf-8")
        rehash_publication_head(memory_root, revision_id)
    head_after_corruption = (memory_root / "field" / "HEAD.json").read_bytes()
    publication_after_corruption = tree_digest(memory_root / "field" / "publications" / revision_id)

    for path in workspace.rglob("*.md"):
        path.unlink()
    (workspace / "memory" / "2026-06-22.md").write_text("# New\n\n- replacement attempt\n", encoding="utf-8")
    snapshot_b = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])

    result = plan_legacy_import(memory_root, snapshot_b, target_field_id="field_fixture")

    assert result["ok"] is False
    assert "active_field_integrity_unresolved" in result["errors"]
    assert existing_ingress_dirs(memory_root) == ingress_before
    assert (memory_root / "field" / "HEAD.json").read_bytes() == head_after_corruption
    assert tree_digest(memory_root / "field" / "publications" / revision_id) == publication_after_corruption


@pytest.mark.parametrize(
    "mutation",
    [
        "extra_continuity",
        "missing_continuity",
        "wrong_source_policy",
        "wrong_batch",
        "wrong_idempotence_key",
        "wrong_shard_id",
    ],
)
def test_t4_imported_shard_identity_tampering_is_rejected(tmp_path: Path, mutation: str) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path / mutation)
    publication = memory_root / "field" / "publications" / revision_id
    shard_path = next((publication / "shards").glob("*.json"))
    shard = read_json(shard_path)
    original_key = str(shard["idempotence_key"])
    if mutation == "extra_continuity":
        shard["continuity_refs"].append("span_injected")
    elif mutation == "missing_continuity":
        shard["continuity_refs"] = []
    elif mutation == "wrong_source_policy":
        shard["source_policy_id"] = "source_policy_wrong"
    elif mutation == "wrong_batch":
        shard["batch_id"] = "batch_wrong"
    elif mutation == "wrong_idempotence_key":
        shard["idempotence_key"] = "sha256:" + "0" * 64
    elif mutation == "wrong_shard_id":
        shard["shard_id"] = "shard_" + "1" * 24
    write_json(shard_path, shard)
    rehash_publication_head(memory_root, revision_id)

    provenance = validate_deep_provenance(memory_root, snapshot_id, revision_id)
    validation = validate_legacy_import(memory_root, batch_id)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")

    assert provenance["ok"] is False
    assert validation["ok"] is False
    assert plan["ok"] is False
    assert "active_field_integrity_unresolved" in plan["errors"]
    if mutation in {"wrong_idempotence_key", "wrong_shard_id"}:
        assert original_key not in existing_shards_by_key(memory_root) or mutation == "wrong_shard_id"


@pytest.mark.parametrize("artifact", ["import-request.json", "import-receipt.json", "publish-handoff.json", "state.json"])
def test_t5_malformed_pending_ingress_metadata_is_structured_and_safe(tmp_path: Path, monkeypatch, artifact: str) -> None:
    memory_root, batch_id, _snapshot_id = planned_fixture(tmp_path)
    monkeypatch.setenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD", "1")
    pending = run_legacy_import(memory_root, batch_id, commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD")
    head_before = (memory_root / "field" / "HEAD.json").read_bytes()
    batch_dir = memory_root / "ingress" / "legacy-import" / batch_id
    (batch_dir / artifact).write_text("{ malformed", encoding="utf-8")

    reconcile = reconcile_legacy_import(memory_root, batch_id)
    validate = validate_legacy_import(memory_root, batch_id)

    assert reconcile["ok"] is False
    assert validate["ok"] is False
    assert all("Traceback" not in error and "JSONDecodeError" not in error for error in reconcile.get("errors", []) + validate.get("errors", []))
    assert reconcile["recovery_required"] is True
    assert (memory_root / "field" / "HEAD.json").read_bytes() == head_before
    assert current_publication(memory_root) is not None
    if artifact != "publish-handoff.json":
        assert reconcile["state"] == "quarantined"
    else:
        assert reconcile["state"] == "recovery_required"
    assert pending["field_revision_id"]


def planned_fixture(tmp_path: Path) -> tuple[Path, str, str]:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True
    return memory_root, str(plan["batch_id"]), snapshot_id


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


def finalization_event_count(memory_root: Path, batch_id: str, revision_id: str) -> int:
    event_id = f"legacy_import_commit:{batch_id}:{revision_id}"
    ledger = memory_root / "ledger" / "events.jsonl"
    if not ledger.exists():
        return 0
    return sum(1 for record in read_jsonl(ledger) if record.get("event_id") == event_id)


def publication_dirs(memory_root: Path) -> set[str]:
    return {path.name for path in (memory_root / "field" / "publications").iterdir() if path.is_dir()}


def existing_ingress_dirs(memory_root: Path) -> set[str]:
    root = memory_root / "ingress" / "legacy-import"
    return {path.name for path in root.iterdir()} if root.exists() else set()


def tree_digest(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8") + b"\0" + item.read_bytes() + b"\0")
    return digest.hexdigest()


def state(memory_root: Path, batch_id: str) -> str:
    return str(read_json(memory_root / "ingress" / "legacy-import" / batch_id / "state.json")["state"])


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
