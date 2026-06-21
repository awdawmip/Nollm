from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nollm.archive import create_archive_snapshot
from nollm.archive_manifest import read_json, sha256_bytes, write_json
from nollm.legacy_import import (
    legacy_import_report,
    plan_legacy_import,
    reconcile_legacy_import,
    recover_legacy_import,
    run_legacy_import,
    validate_legacy_import,
)
from nollm.native_field import admit_current_publication, current_publication
from nollm.provenance import validate_deep_provenance


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_t1_forged_valid_handoff_cannot_finalize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_root, batch_id, _snapshot_id = planned_fixture(tmp_path)
    monkeypatch.setenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD", "1")
    pending = run_legacy_import(memory_root, batch_id, commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD")
    assert pending["ok"] is True
    head_before = (memory_root / "field" / "HEAD.json").read_bytes()
    handoff_path = batch_dir(memory_root, batch_id) / "publish-handoff.json"
    handoff = read_json(handoff_path)
    handoff["batch_id"] = "batch_forged"
    handoff["candidate_revision_id"] = "fieldrev_forged"
    handoff["candidate_manifest_hash"] = "sha256:" + "0" * 64
    write_json(handoff_path, handoff)

    result = reconcile_legacy_import(memory_root, batch_id)

    assert result["ok"] is False
    assert result["recovery_required"] is True
    assert result["state"] == "publishing"
    assert any("publish_handoff_" in error for error in result["errors"])
    assert state(memory_root, batch_id) == "publishing"
    assert (memory_root / "field" / "HEAD.json").read_bytes() == head_before
    assert current_publication(memory_root) is not None


def test_t2_forged_origin_kind_cannot_bypass_legacy_profile(tmp_path: Path) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path)
    publication = memory_root / "field" / "publications" / revision_id
    shard_path = next((publication / "shards").glob("*.json"))
    shard = read_json(shard_path)
    shard["origin_kind"] = "native_import"
    shard["batch_id"] = "batch_forged"
    shard["source_policy_id"] = "source_policy_forged"
    shard["idempotence_key"] = "sha256:" + "0" * 64
    write_json(shard_path, shard)
    rehash_publication_head(memory_root, revision_id)

    admission = admit_current_publication(memory_root)
    provenance = validate_deep_provenance(memory_root, snapshot_id, revision_id)
    validation = validate_legacy_import(memory_root, batch_id)

    assert admission["publication"] is None
    assert any("legacy_shard_origin_kind_mismatch" in error for error in admission["errors"])
    assert provenance["ok"] is False
    assert validation["ok"] is False


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("epistemic_state", "confirmed", "legacy_shard_epistemic_state_mismatch"),
        ("operational_state", "pinned", "legacy_shard_operational_state_mismatch"),
        ("geometry_intent", {"mode": "manual"}, "legacy_shard_geometry_intent_mismatch"),
        ("anchor_field_weights", {"alpha": 1}, "legacy_shard_anchor_field_weights_mismatch"),
        ("unknown_extra", "forged", "legacy_shard_unknown_field"),
    ],
)
def test_t3_semantic_shard_drift_is_rejected(tmp_path: Path, field: str, value: Any, expected: str) -> None:
    memory_root, batch_id, snapshot_id, revision_id = commit_fixture(tmp_path / field)
    publication = memory_root / "field" / "publications" / revision_id
    shard_path = next((publication / "shards").glob("*.json"))
    shard = read_json(shard_path)
    shard[field] = value
    write_json(shard_path, shard)
    rehash_publication_head(memory_root, revision_id)

    admission = admit_current_publication(memory_root)

    assert admission["publication"] is None
    assert any(expected in error for error in admission["errors"])
    assert validate_deep_provenance(memory_root, snapshot_id, revision_id)["ok"] is False
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False


@pytest.mark.parametrize(
    ("field", "mutator", "expected"),
    [
        ("schema", lambda value: "nollm.legacy_import_receipt.forged", "ingress_receipt_schema_mismatch"),
        ("snapshot_id", lambda value: "snap_forged", "ingress_receipt_snapshot_id_mismatch"),
        ("target_field_id", lambda value: "field_forged", "ingress_receipt_target_field_id_mismatch"),
        ("created_shard_count", lambda value: value + 1, "ingress_receipt_created_shard_count_mismatch"),
        ("duplicate_count", lambda value: "forged", "ingress_receipt_duplicate_count_invalid"),
        ("committed_at", lambda value: "not-a-timestamp", "ingress_receipt_committed_at_invalid"),
    ],
)
def test_t4_ingress_receipt_mismatch_is_rejected(tmp_path: Path, field: str, mutator: Any, expected: str) -> None:
    memory_root, batch_id, _snapshot_id, _revision_id = commit_fixture(tmp_path / field)
    receipt_path = batch_dir(memory_root, batch_id) / "import-receipt.json"
    receipt = read_json(receipt_path)
    receipt[field] = mutator(receipt[field])
    write_json(receipt_path, receipt)

    result = validate_legacy_import(memory_root, batch_id)

    assert result["ok"] is False
    assert "ingress_receipt_publication_receipt_mismatch" in result["errors"]
    assert expected in result["errors"]


@pytest.mark.parametrize("artifact", ["state.json", "import-request.json", "import-receipt.json", "publish-handoff.json"])
@pytest.mark.parametrize("mode", ["missing", "malformed"])
def test_t5_missing_or_malformed_metadata_is_structured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artifact: str, mode: str) -> None:
    memory_root, batch_id, snapshot_id = planned_fixture(tmp_path / f"{artifact}-{mode}")
    monkeypatch.setenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD", "1")
    pending = run_legacy_import(memory_root, batch_id, commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD")
    revision_id = str(pending["field_revision_id"])
    target = batch_dir(memory_root, batch_id) / artifact
    if mode == "missing":
        target.unlink()
    else:
        target.write_text("{ malformed", encoding="utf-8")

    results = [
        plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture"),
        run_legacy_import(memory_root, batch_id, commit=True),
        reconcile_legacy_import(memory_root, batch_id),
        recover_legacy_import(memory_root, batch_id),
        validate_legacy_import(memory_root, batch_id),
        legacy_import_report(memory_root, batch_id),
        validate_deep_provenance(memory_root, snapshot_id, revision_id),
        admit_current_publication(memory_root),
    ]

    for result in results:
        assert isinstance(result, dict)
        assert_no_raw_parser_error(result)
    assert current_publication(memory_root) is not None


@pytest.mark.parametrize(
    "fault_env",
    [
        "NOLLM_MT1_FORCE_FAIL_BEFORE_ACTIVATION_RECORD",
        "NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD",
        "NOLLM_MT1_FORCE_FAIL_DURING_HEAD_PREPARATION",
    ],
)
def test_t6_pre_head_failures_never_publish_active_pointer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault_env: str) -> None:
    memory_root, batch_id, _snapshot_id = planned_fixture(tmp_path / fault_env)
    monkeypatch.setenv(fault_env, "1")

    result = run_legacy_import(memory_root, batch_id, commit=True)

    assert result["ok"] is False
    assert not (memory_root / "field" / "HEAD.json").exists()
    assert current_publication(memory_root) is None


def test_t6_post_head_audit_failure_keeps_verified_package_and_reconciles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_root, batch_id, _snapshot_id = planned_fixture(tmp_path)
    monkeypatch.setenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD", "1")
    pending = run_legacy_import(memory_root, batch_id, commit=True)
    monkeypatch.delenv("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD")
    head_before = (memory_root / "field" / "HEAD.json").read_bytes()
    publications_before = publication_dirs(memory_root)

    result = reconcile_legacy_import(memory_root, batch_id)

    assert pending["ok"] is True
    assert pending["reconciliation_pending"] is True
    assert current_publication(memory_root) is not None
    assert result["ok"] is True
    assert result["state"] == "committed"
    assert (memory_root / "field" / "HEAD.json").read_bytes() == head_before
    assert publication_dirs(memory_root) == publications_before


def planned_fixture(tmp_path: Path) -> tuple[Path, str, str]:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True
    return memory_root, str(plan["batch_id"]), snapshot_id


def commit_fixture(tmp_path: Path) -> tuple[Path, str, str, str]:
    memory_root, batch_id, snapshot_id = planned_fixture(tmp_path)
    commit = run_legacy_import(memory_root, batch_id, commit=True)
    assert commit["ok"] is True
    return memory_root, batch_id, snapshot_id, str(commit["field_revision_id"])


def batch_dir(memory_root: Path, batch_id: str) -> Path:
    return memory_root / "ingress" / "legacy-import" / batch_id


def publication_dirs(memory_root: Path) -> set[str]:
    return {path.name for path in (memory_root / "field" / "publications").iterdir() if path.is_dir()}


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


def state(memory_root: Path, batch_id: str) -> str:
    return str(read_json(batch_dir(memory_root, batch_id) / "state.json")["state"])


def assert_no_raw_parser_error(result: dict[str, Any]) -> None:
    errors = [str(error) for error in result.get("errors", [])]
    joined = "\n".join(errors)
    assert "Traceback" not in joined
    assert "JSONDecodeError" not in joined
    assert "Expecting value" not in joined


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
