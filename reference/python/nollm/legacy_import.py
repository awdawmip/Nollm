from __future__ import annotations

import json
import os
import shutil
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .archive import load_manifest, memory_root_path, utc_now, verify_archive_snapshot
from .archive_manifest import canonical_json, read_json, sha256_bytes, write_json
from .coverage import validate_source_coverage
from .legacy_extract import extract_legacy_spans, idempotence_key
from .native_field import (
    append_jsonl,
    admit_current_publication,
    build_shard,
    existing_shards_by_key,
    load_field_head,
    current_publication,
    shard_id_for,
    stage_shards,
    write_jsonl,
)
from .provenance import build_source_span_links, validate_deep_provenance
from .provenance import validate_staged_publication
from .source_spans import build_source_span_inventory, mark_spans_linked


IMPORT_SCHEMA = "nollm.legacy_import_request.v1"
RECEIPT_SCHEMA = "nollm.legacy_import_receipt.v1"


def plan_legacy_import(memory_root: Path | str, snapshot_id: str, *, target_field_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    archive = verify_archive_snapshot(root, snapshot_id)
    if not archive.get("ok"):
        return {"ok": False, "snapshot_id": snapshot_id, "errors": archive.get("errors", [])}
    span_path = root / "archive" / "source-spans" / f"{snapshot_id}.jsonl"
    if not span_path.exists():
        build_source_span_inventory(root, snapshot_id)
    coverage = validate_source_coverage(root, snapshot_id)
    if not coverage.get("ok"):
        return {"ok": False, "snapshot_id": snapshot_id, "errors": coverage.get("errors", [])}
    active_errors = _active_field_policy_errors(root, snapshot_id=snapshot_id, target_field_id=target_field_id)
    if active_errors:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": active_errors}
    manifest = load_manifest(root, snapshot_id)
    extracted = extract_legacy_spans(root, snapshot_id)
    batch_id = _batch_id(snapshot_id, target_field_id, extracted)
    batch_dir = root / "ingress" / "legacy-import" / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    request_path = batch_dir / "import-request.json"
    receipt_path = batch_dir / "import-receipt.json"
    if request_path.exists():
        request = read_json(request_path)
        state = _load_state(batch_dir)
        return {
            "ok": True,
            "batch_id": batch_id,
            "snapshot_id": snapshot_id,
            "extraction_count": request.get("extraction_count", len(extracted)),
            "batch_dir": str(batch_dir),
            "state": state["state"],
            "field_revision_id": read_json(receipt_path).get("field_revision_id") if receipt_path.exists() else None,
        }
    request = {
        "schema": IMPORT_SCHEMA,
        "batch_id": batch_id,
        "snapshot_id": snapshot_id,
        "target_field_id": target_field_id,
        "source_policy_id": manifest.get("source_policy_id"),
        "dedupe_policy": "idempotence_key_active_head_only",
        "geometry_policy": "none_mt1_archive_ingest",
        "created_at": utc_now(),
        "extraction_count": len(extracted),
    }
    write_json(request_path, request)
    _write_state(batch_dir, "planned")
    _write_jsonl(batch_dir / "extraction.jsonl", extracted)
    write_json(batch_dir / "migration-report.json", _migration_report(root, batch_id, request, dry_run=True))
    append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_plan", "batch_id": batch_id, "timestamp": utc_now(), "state": "planned"})
    return {"ok": True, "batch_id": batch_id, "snapshot_id": snapshot_id, "extraction_count": len(extracted), "batch_dir": str(batch_dir), "state": "planned"}


def run_legacy_import(memory_root: Path | str, batch_id: str, *, dry_run: bool = False, commit: bool = False) -> dict[str, Any]:
    if dry_run == commit:
        return {"ok": False, "batch_id": batch_id, "errors": ["choose exactly one of dry_run or commit"]}
    root = memory_root_path(memory_root)
    batch_dir = _batch_dir(root, batch_id)
    state, state_errors = _load_state_safe(batch_dir)
    if state_errors:
        return _untrusted_ingress_result(root, batch_dir, batch_id, state_errors)
    if commit and state["state"] == "publishing":
        return reconcile_legacy_import(root, batch_id)
    if commit and state["state"] in {"failed", "quarantined"}:
        return {
            "ok": False,
            "batch_id": batch_id,
            "state": state["state"],
            "errors": [f"invalid batch state transition: {state['state']} -> staged", f"cannot_commit_state:{state['state']}"],
        }
    request, request_errors = _read_json_safe(batch_dir / "import-request.json", "import_request")
    if request_errors or not isinstance(request, dict):
        return _untrusted_ingress_result(root, batch_dir, batch_id, request_errors or ["invalid_import_request"])
    receipt_path = batch_dir / "import-receipt.json"
    if commit and state["state"] == "committed" and receipt_path.exists():
        receipt, receipt_errors = _read_json_safe(receipt_path, "import_receipt")
        if receipt_errors or not isinstance(receipt, dict):
            return {"ok": False, "batch_id": batch_id, "state": "committed", "errors": receipt_errors or ["invalid_import_receipt"]}
        validation = validate_legacy_import(root, batch_id)
        if not validation.get("ok"):
            return {"ok": False, "batch_id": batch_id, "state": "committed", "errors": validation.get("errors", [])}
        append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_duplicate_commit", "batch_id": batch_id, "timestamp": utc_now(), "duplicate_count": len(_read_jsonl(batch_dir / "extraction.jsonl"))})
        return {
            "ok": True,
            "batch_id": batch_id,
            "committed": True,
            "created_shard_count": 0,
            "duplicate_count": len(_read_jsonl(batch_dir / "extraction.jsonl")),
            "field_revision_id": receipt.get("field_revision_id"),
            "state": "committed",
        }
    archive = verify_archive_snapshot(root, str(request["snapshot_id"]))
    coverage = validate_source_coverage(root, str(request["snapshot_id"]), require_linked=False)
    if not archive.get("ok") or not coverage.get("ok"):
        return {"ok": False, "batch_id": batch_id, "errors": archive.get("errors", []) + coverage.get("errors", [])}
    active_errors = _active_field_policy_errors(root, snapshot_id=str(request["snapshot_id"]), target_field_id=str(request["target_field_id"]))
    if active_errors:
        return {"ok": False, "batch_id": batch_id, "errors": active_errors, "state": state["state"]}
    manifest = load_manifest(root, str(request["snapshot_id"]))
    source_policy_id = str(manifest["source_policy_id"])
    extracted = _read_jsonl(batch_dir / "extraction.jsonl")
    existing = existing_shards_by_key(root)
    shards = []
    publication_shards_by_id: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    for record in extracted:
        key = idempotence_key(record, source_policy_id)
        if key in existing:
            duplicate_count += 1
            existing_shard = dict(existing[key])
            publication_shards_by_id[str(existing_shard["shard_id"])] = existing_shard
            continue
        shard = build_shard(record, batch_id=batch_id, source_policy_id=source_policy_id, idempotence_key=key)
        shards.append(shard)
        publication_shards_by_id[str(shard["shard_id"])] = shard
    publication_shards = [publication_shards_by_id[shard_id] for shard_id in sorted(publication_shards_by_id)]
    if dry_run:
        report = _migration_report(root, batch_id, request, dry_run=True, candidate_shards=shards, duplicate_count=duplicate_count)
        write_json(batch_dir / "dry-run-report.json", report)
        return {"ok": True, "batch_id": batch_id, "dry_run": True, "candidate_shard_count": len(shards), "duplicate_count": duplicate_count}
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "batch_id": batch_id,
        "snapshot_id": request["snapshot_id"],
        "target_field_id": request["target_field_id"],
        "committed_at": utc_now(),
        "created_shard_ids": [str(shard["shard_id"]) for shard in shards],
        "created_shard_count": len(shards),
        "duplicate_count": duplicate_count,
    }
    head_written = False
    prior_head = load_field_head(root)
    try:
        _write_state(batch_dir, "staged")
        stage_shards(root, batch_id, shards)
        revision = _revision_candidate(root, batch_id=batch_id, target_field_id=str(request["target_field_id"]), shard_ids=[str(shard["shard_id"]) for shard in publication_shards])
        receipt["field_revision_id"] = revision["field_revision_id"]
        links = build_source_span_links(snapshot_id=str(request["snapshot_id"]), batch_id=batch_id, field_revision_id=str(revision["field_revision_id"]), shards=publication_shards)
        staging = _write_staging_package(root, batch_id, revision, publication_shards, links, str(request["snapshot_id"]), receipt)
        if os.environ.get("NOLLM_MT1_CORRUPT_STAGING_TEXT") == "1":
            shard_path = next((staging / "shards").glob("*.json"))
            shard = read_json(shard_path)
            shard["text"] = "TAMPERED STAGING CONTENT"
            write_json(shard_path, shard)
        staged_validation = validate_staged_publication(root, batch_id, str(request["snapshot_id"]), str(revision["field_revision_id"]))
        if not staged_validation.get("ok"):
            raise ValueError("staged_validation_failed:" + ",".join(staged_validation.get("errors", [])))
        _write_state(batch_dir, "validated")
        append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_validate_staging", "batch_id": batch_id, "timestamp": utc_now(), "state": "validated"})
        if os.environ.get("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD") == "1":
            raise RuntimeError("forced_failure_before_head")
        if os.environ.get("NOLLM_MT1_FORCE_OSERROR_DURING_PUBLISH") == "1":
            raise OSError("forced_oserror_during_publish")
        _write_state(batch_dir, "publishing")
        publication = _publish_package(root, batch_id, str(revision["field_revision_id"]))
        write_json(batch_dir / "import-receipt.json", receipt)
        manifest_hash = "sha256:" + sha256_bytes((publication / "publication-manifest.json").read_bytes())
        _write_publish_handoff(batch_dir, batch_id, str(revision["field_revision_id"]), manifest_hash, prior_head)
        _write_head_atomic(root, {"field_id": request["target_field_id"], "field_revision_id": revision["field_revision_id"], "publication_manifest_hash": manifest_hash})
        head_written = True
        if os.environ.get("NOLLM_MT1_FORCE_JOURNAL_OSERROR_AFTER_HEAD") == "1":
            return {"ok": True, "batch_id": batch_id, "published": True, "reconciliation_pending": True, "field_revision_id": revision["field_revision_id"], "state": "publishing"}
        finalized = _finalize_verified_publication(root, batch_dir, request, receipt, publication, duplicate_count=duplicate_count)
        if not finalized.get("ok"):
            _quarantine_and_restore_head(root, batch_dir, prior_head, "published_provenance_failed:" + ",".join(finalized.get("errors", [])))
            return {"ok": False, "batch_id": batch_id, "errors": finalized.get("errors", []), "state": "quarantined"}
        return {"ok": True, "batch_id": batch_id, "committed": True, "created_shard_count": len(shards), "duplicate_count": duplicate_count, "field_revision_id": revision["field_revision_id"], "state": "committed"}
    except Exception as exc:
        if head_written:
            head = load_field_head(root)
            if head and head.get("field_revision_id") == receipt.get("field_revision_id"):
                provenance = validate_deep_provenance(root, str(request["snapshot_id"]), str(receipt.get("field_revision_id")))
                if provenance.get("ok"):
                    return {"ok": True, "batch_id": batch_id, "published": True, "reconciliation_pending": True, "field_revision_id": receipt.get("field_revision_id"), "state": _load_state(batch_dir)["state"]}
                _quarantine_and_restore_head(root, batch_dir, prior_head, str(exc))
                return {"ok": False, "batch_id": batch_id, "errors": [str(exc)], "state": "quarantined"}
        if _load_state(batch_dir)["state"] != "committed":
            _write_state(batch_dir, "failed")
        failure = {"schema": "nollm.legacy_import_failure.v1", "batch_id": batch_id, "timestamp": utc_now(), "error": str(exc), "state": "failed"}
        write_json(batch_dir / "failure.json", failure)
        append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_failure", **failure})
        return {"ok": False, "batch_id": batch_id, "errors": [str(exc)], "state": "failed"}


def reconcile_legacy_import(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    batch_dir = _batch_dir(root, batch_id)
    state_record, state_errors = _load_state_safe(batch_dir)
    if state_errors:
        return _untrusted_ingress_result(root, batch_dir, batch_id, state_errors)
    state = state_record["state"]
    if state == "committed":
        validation = validate_legacy_import(root, batch_id)
        if not validation.get("ok"):
            return {"ok": False, "batch_id": batch_id, "state": "committed", "changed": False, "errors": validation.get("errors", [])}
        return {"ok": True, "batch_id": batch_id, "state": "committed", "changed": False}
    if state != "publishing":
        return {"ok": False, "batch_id": batch_id, "state": state, "errors": [f"cannot_reconcile_state:{state}"]}
    receipt_path = batch_dir / "import-receipt.json"
    if not receipt_path.exists():
        return {"ok": False, "batch_id": batch_id, "state": state, "errors": ["missing_import_receipt"]}
    receipt, receipt_errors = _read_json_safe(receipt_path, "import_receipt")
    if receipt_errors or not isinstance(receipt, dict):
        return _untrusted_ingress_result(root, batch_dir, batch_id, receipt_errors or ["invalid_import_receipt"])
    handoff, handoff_errors = _read_json_safe(batch_dir / "publish-handoff.json", "publish_handoff")
    if handoff_errors or not isinstance(handoff, dict):
        return _untrusted_ingress_result(root, batch_dir, batch_id, handoff_errors or ["invalid_publish_handoff"])
    head = load_field_head(root)
    if not head or head.get("field_revision_id") != receipt.get("field_revision_id"):
        _write_state(batch_dir, "quarantined")
        return {"ok": False, "batch_id": batch_id, "state": "quarantined", "errors": ["head_not_at_receipt_revision"]}
    publication = current_publication(root)
    if not publication:
        handoff, _handoff_errors = _read_json_safe(batch_dir / "publish-handoff.json", "publish_handoff")
        prior_head = handoff.get("prior_head") if isinstance(handoff, dict) else None
        _quarantine_and_restore_head(root, batch_dir, prior_head, "reconcile_validation_failed:inactive_publication")
        return {"ok": False, "batch_id": batch_id, "state": "quarantined", "errors": ["inactive_publication"]}
    try:
        request, request_errors = _read_json_safe(batch_dir / "import-request.json", "import_request")
        if request_errors or not isinstance(request, dict):
            return _untrusted_ingress_result(root, batch_dir, batch_id, request_errors or ["invalid_import_request"])
        finalized = _finalize_verified_publication(root, batch_dir, request, receipt, publication, duplicate_count=int(receipt.get("duplicate_count", 0)), reconcile=True)
    except Exception as exc:
        return {"ok": True, "batch_id": batch_id, "published": True, "reconciliation_pending": True, "field_revision_id": receipt.get("field_revision_id"), "state": _load_state(batch_dir)["state"], "errors": [str(exc)]}
    if not finalized.get("ok"):
        handoff, _handoff_errors = _read_json_safe(batch_dir / "publish-handoff.json", "publish_handoff")
        prior_head = handoff.get("prior_head") if isinstance(handoff, dict) else None
        _quarantine_and_restore_head(root, batch_dir, prior_head, "reconcile_validation_failed:" + ",".join(finalized.get("errors", [])))
        return {"ok": False, "batch_id": batch_id, "state": "quarantined", "errors": finalized.get("errors", [])}
    return {"ok": True, "batch_id": batch_id, "state": "committed", "changed": True, "field_revision_id": receipt.get("field_revision_id")}


def recover_legacy_import(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    old_dir = _batch_dir(root, batch_id)
    state_record, state_errors = _load_state_safe(old_dir)
    if state_errors:
        return _untrusted_ingress_result(root, old_dir, batch_id, state_errors)
    state = state_record["state"]
    if state == "publishing":
        return reconcile_legacy_import(root, batch_id)
    if state not in {"failed", "quarantined"}:
        return {"ok": False, "batch_id": batch_id, "state": state, "errors": [f"cannot_recover_state:{state}"]}
    old_request, request_errors = _read_json_safe(old_dir / "import-request.json", "import_request")
    if request_errors or not isinstance(old_request, dict):
        return {"ok": False, "batch_id": batch_id, "state": state, "errors": request_errors or ["invalid_import_request"]}
    replacement_id = _replacement_batch_id(batch_id)
    replacement_dir = _batch_dir(root, replacement_id)
    if replacement_dir.exists():
        return {"ok": True, "batch_id": batch_id, "replacement_batch_id": replacement_id, "reused": True}
    replacement_request = dict(old_request)
    replacement_request["batch_id"] = replacement_id
    replacement_request["recovery_of"] = batch_id
    replacement_dir.mkdir(parents=True, exist_ok=True)
    write_json(replacement_dir / "import-request.json", replacement_request)
    (replacement_dir / "extraction.jsonl").write_text((old_dir / "extraction.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    _write_state(replacement_dir, "planned")
    append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_recovery_batch", "batch_id": replacement_id, "recovery_of": batch_id, "timestamp": utc_now(), "state": "planned"})
    return {"ok": True, "batch_id": batch_id, "replacement_batch_id": replacement_id, "reused": False}


def validate_legacy_import(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    errors: list[str] = []
    batch_dir = _batch_dir(root, batch_id)
    state, state_errors = _load_state_safe(batch_dir)
    errors.extend(state_errors)
    request, request_errors = _read_json_safe(batch_dir / "import-request.json", "import_request")
    errors.extend(request_errors)
    if not isinstance(request, dict):
        return {"ok": False, "batch_id": batch_id, "state": state["state"], "errors": errors or ["invalid_import_request"]}
    if state["state"] == "publishing":
        handoff, handoff_errors = _read_json_safe(batch_dir / "publish-handoff.json", "publish_handoff")
        errors.extend(handoff_errors)
        if not isinstance(handoff, dict):
            errors.append("invalid_publish_handoff")
    archive = verify_archive_snapshot(root, str(request["snapshot_id"]))
    coverage = validate_source_coverage(root, str(request["snapshot_id"]), require_linked=True)
    errors.extend(archive.get("errors", []))
    errors.extend(coverage.get("errors", []))
    receipt_path = batch_dir / "import-receipt.json"
    if receipt_path.exists():
        receipt, receipt_errors = _read_json_safe(receipt_path, "import_receipt")
        errors.extend(receipt_errors)
        if not isinstance(receipt, dict):
            return {"ok": False, "batch_id": batch_id, "state": state["state"], "errors": errors or ["invalid_import_receipt"]}
        provenance = validate_deep_provenance(root, str(request["snapshot_id"]), str(receipt.get("field_revision_id")))
        errors.extend(provenance.get("errors", []))
        publication = current_publication(root)
        for shard_id in receipt.get("created_shard_ids", []):
            shard_path = (publication / "shards" / f"{shard_id}.json") if publication else root / "field" / "missing-publication"
            if not shard_path.exists():
                errors.append(f"missing_shard:{shard_id}")
                continue
            shard = read_json(shard_path)
            if not shard.get("source_refs") or not all(str(ref).startswith("archive://object/sha256:") for ref in shard.get("source_refs", [])):
                errors.append(f"invalid_source_refs:{shard_id}")
        head = load_field_head(root)
        if not head or head.get("field_revision_id") != receipt.get("field_revision_id"):
            errors.append("field_head_does_not_match_receipt")
        if state["state"] == "committed" and not _has_finalization_ledger_event(root, receipt):
            errors.append("missing_finalization_ledger_event")
    else:
        errors.append("missing_import_receipt")
    return {"ok": not errors, "batch_id": batch_id, "state": state["state"], "errors": errors}


def legacy_import_report(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    request = read_json(_batch_dir(root, batch_id) / "import-request.json")
    report_path = _batch_dir(root, batch_id) / "migration-report.json"
    report = read_json(report_path) if report_path.exists() else _migration_report(root, batch_id, request)
    report["validation"] = validate_legacy_import(root, batch_id) if (_batch_dir(root, batch_id) / "import-receipt.json").exists() else {"ok": False, "errors": ["not_committed"]}
    report["ok"] = bool(report["validation"].get("ok"))
    report["state"] = _load_state(_batch_dir(root, batch_id))["state"]
    return report


def _batch_id(snapshot_id: str, target_field_id: str, extracted: list[dict[str, Any]]) -> str:
    payload = canonical_json({"snapshot_id": snapshot_id, "target_field_id": target_field_id, "items": [(item["span_id"], item["text_hash"]) for item in extracted]})
    return "batch_" + sha256_bytes(payload)[:20]


def _batch_dir(root: Path, batch_id: str) -> Path:
    return root / "ingress" / "legacy-import" / batch_id


def _replacement_batch_id(batch_id: str) -> str:
    return f"{batch_id}_recovery"


def _active_field_policy_errors(root: Path, *, snapshot_id: str, target_field_id: str) -> list[str]:
    errors: list[str] = []
    head_path = root / "field" / "HEAD.json"
    if not head_path.exists() and not head_path.is_symlink():
        return errors
    admission = admit_current_publication(root)
    if admission.get("publication") is None:
        errors.append("active_field_integrity_unresolved")
        errors.extend(str(error) for error in admission.get("errors", []))
        return errors
    head = admission.get("head")
    if head and head.get("field_id") != target_field_id:
        errors.append("single_head_field_switch_not_supported")
        return errors
    publication = admission["publication"]
    receipt_path = publication / "receipt.json"
    try:
        receipt = read_json(receipt_path)
    except Exception:
        return ["active_field_integrity_unresolved", "unreadable_active_receipt"]
    if receipt.get("snapshot_id") != snapshot_id:
        errors.append("cross_snapshot_replacement_not_supported")
        return errors
    provenance = validate_deep_provenance(root, snapshot_id, str(receipt.get("field_revision_id")))
    if not provenance.get("ok"):
        errors.append("active_field_integrity_unresolved")
        errors.extend(str(error) for error in provenance.get("errors", []))
    return errors


def _migration_report(
    root: Path,
    batch_id: str,
    request: dict[str, Any],
    *,
    dry_run: bool = False,
    candidate_shards: list[dict[str, Any]] | None = None,
    receipt: dict[str, Any] | None = None,
    duplicate_count: int = 0,
) -> dict[str, Any]:
    candidate_shards = candidate_shards or []
    return {
        "schema": "nollm.legacy_import_migration_report.v1",
        "batch_id": batch_id,
        "snapshot_id": request["snapshot_id"],
        "target_field_id": request["target_field_id"],
        "dry_run": dry_run,
        "candidate_shard_count": len(candidate_shards),
        "candidate_shard_ids": [shard_id_for(str(shard["idempotence_key"])) for shard in candidate_shards],
        "duplicate_count": duplicate_count,
        "receipt": receipt,
        "field_head": load_field_head(root),
        "state": _load_state(root / "ingress" / "legacy-import" / batch_id)["state"] if (root / "ingress" / "legacy-import" / batch_id / "state.json").exists() else "planned",
    }


def _revision_candidate(root: Path, *, batch_id: str, target_field_id: str, shard_ids: list[str]) -> dict[str, Any]:
    merged_ids = sorted(set(shard_ids))
    revision_seed = canonical_json({"batch_id": batch_id, "field_id": target_field_id, "shard_ids": merged_ids})
    revision_id = "fieldrev_" + sha256_bytes(revision_seed)[:20]
    return {
        "schema": "nollm.native_field_revision.v1",
        "field_revision_id": revision_id,
        "field_id": target_field_id,
        "batch_id": batch_id,
        "created_at": utc_now(),
        "shard_ids": merged_ids,
        "shard_count": len(merged_ids),
    }


def _publish_pre_head(root: Path, batch_id: str, revision: dict[str, Any], shards: list[dict[str, Any]], links: list[dict[str, Any]], snapshot_id: str) -> None:
    raise RuntimeError("_publish_pre_head is obsolete; use publication packages")


def _write_staging_package(root: Path, batch_id: str, revision: dict[str, Any], shards: list[dict[str, Any]], links: list[dict[str, Any]], snapshot_id: str, receipt: dict[str, Any]) -> Path:
    staging = root / "field" / ".staging" / batch_id / "publication"
    if staging.exists():
        shutil.rmtree(staging)
    (staging / "shards").mkdir(parents=True, exist_ok=True)
    for shard in shards:
        write_json(staging / "shards" / f"{shard['shard_id']}.json", shard)
    write_json(staging / "revision.json", revision)
    write_jsonl(staging / "source-span-links.jsonl", links)
    spans = _project_spans(root, snapshot_id, links)
    write_jsonl(staging / "source-span-projection.jsonl", spans)
    write_json(staging / "receipt.json", receipt)
    write_json(staging / "publication-manifest.json", _publication_manifest(staging, revision, receipt, snapshot_id))
    return staging


def _publish_package(root: Path, batch_id: str, field_revision_id: str) -> Path:
    staging = root / "field" / ".staging" / batch_id / "publication"
    publication = root / "field" / "publications" / field_revision_id
    if publication.exists():
        shutil.rmtree(publication)
    publication.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(staging, publication)
    return publication


def _write_head_atomic(root: Path, head: dict[str, Any]) -> None:
    target = root / "field" / "HEAD.json"
    tmp = root / "field" / "HEAD.json.tmp"
    write_json(tmp, head)
    os.replace(tmp, target)


def _write_publish_handoff(batch_dir: Path, batch_id: str, revision_id: str, manifest_hash: str, prior_head: dict[str, Any] | None) -> None:
    write_json(
        batch_dir / "publish-handoff.json",
        {
            "schema": "nollm.legacy_import_publish_handoff.v1",
            "batch_id": batch_id,
            "candidate_revision_id": revision_id,
            "candidate_manifest_hash": manifest_hash,
            "prior_head": prior_head,
            "publish_started_at": utc_now(),
        },
    )


def _restore_head(root: Path, prior_head: dict[str, Any] | None) -> None:
    target = root / "field" / "HEAD.json"
    if prior_head:
        _write_head_atomic(root, prior_head)
    elif target.exists():
        target.unlink()


def _quarantine_and_restore_head(root: Path, batch_dir: Path, prior_head: dict[str, Any] | None, reason: str) -> None:
    _restore_head(root, prior_head)
    _write_state(batch_dir, "quarantined")
    record = {"schema": "nollm.legacy_import_quarantine.v1", "batch_id": batch_dir.name, "timestamp": utc_now(), "reason": reason, "state": "quarantined"}
    write_json(batch_dir / "quarantine.json", record)
    append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_quarantine", **record})


def _finalize_verified_publication(
    root: Path,
    batch_dir: Path,
    request: dict[str, Any],
    receipt: dict[str, Any],
    publication: Path,
    *,
    duplicate_count: int,
    reconcile: bool = False,
) -> dict[str, Any]:
    state = _load_state(batch_dir)["state"]
    if state != "publishing":
        return {"ok": False, "errors": [f"cannot_finalize_state:{state}"]}
    provenance = validate_deep_provenance(root, str(request["snapshot_id"]), str(receipt.get("field_revision_id")))
    if not provenance.get("ok"):
        return {"ok": False, "errors": provenance.get("errors", [])}
    report = _migration_report(root, str(receipt["batch_id"]), request, receipt=receipt, duplicate_count=duplicate_count)
    if os.environ.get("NOLLM_MT1_FORCE_REPORT_OSERROR_AFTER_HEAD") == "1":
        raise OSError("forced_report_oserror_after_head")
    write_json(batch_dir / "migration-report.json", report)
    if os.environ.get("NOLLM_MT1_FORCE_COMMIT_LEDGER_OSERROR_AFTER_HEAD") == "1":
        raise OSError("forced_commit_ledger_oserror_after_head")
    event = {
        "op": "legacy_import_commit",
        "event_id": _finalization_event_id(receipt),
        "batch_id": receipt["batch_id"],
        "timestamp": utc_now(),
        "state": "committed",
        "reconciled": reconcile,
        "receipt": receipt,
        "publication": str(publication),
    }
    _ensure_ledger_event(root / "ledger" / "events.jsonl", event)
    if os.environ.get("NOLLM_MT1_FORCE_STATE_OSERROR_AFTER_HEAD") == "1":
        raise OSError("forced_state_oserror_after_head")
    _write_state(batch_dir, "committed")
    return {"ok": True}


def _finalization_event_id(receipt: dict[str, Any]) -> str:
    return f"legacy_import_commit:{receipt.get('batch_id')}:{receipt.get('field_revision_id')}"


def _ensure_ledger_event(path: Path, event: dict[str, Any]) -> None:
    event_id = event.get("event_id")
    if path.exists():
        for record in _read_jsonl(path):
            if record.get("event_id") == event_id:
                return
    append_jsonl(path, event)


def _has_finalization_ledger_event(root: Path, receipt: dict[str, Any]) -> bool:
    path = root / "ledger" / "events.jsonl"
    event_id = _finalization_event_id(receipt)
    if not path.exists():
        return False
    return any(record.get("event_id") == event_id for record in _read_jsonl(path))


def _project_spans(root: Path, snapshot_id: str, links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from .source_spans import load_source_spans

    spans = load_source_spans(root, snapshot_id)
    by_span: dict[str, list[str]] = {}
    for link in links:
        by_span.setdefault(str(link["span_id"]), []).append(str(link["shard_id"]))
    for span in spans:
        related = sorted(set(by_span.get(str(span["span_id"]), [])))
        if related:
            span["disposition"] = "sharded"
            span["related_shard_ids"] = related
            span["lifecycle"] = "linked"
            span["reason"] = "linked_to_committed_shard"
    return spans


def _publication_manifest(root: Path, revision: dict[str, Any], receipt: dict[str, Any], snapshot_id: str) -> dict[str, Any]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "publication-manifest.json":
            hashes[path.relative_to(root).as_posix()] = "sha256:" + sha256_bytes(path.read_bytes())
    return {
        "schema": "nollm.publication_manifest.v1",
        "field_revision_id": revision["field_revision_id"],
        "field_id": revision["field_id"],
        "batch_id": receipt["batch_id"],
        "snapshot_id": snapshot_id,
        "artifact_hashes": hashes,
    }


def _load_state(batch_dir: Path) -> dict[str, Any]:
    path = batch_dir / "state.json"
    if not path.exists():
        return {"state": "planned"}
    return read_json(path)


def _load_state_safe(batch_dir: Path) -> tuple[dict[str, Any], list[str]]:
    path = batch_dir / "state.json"
    if not path.exists():
        return {"state": "planned"}, []
    data, errors = _read_json_safe(path, "state")
    if errors:
        return {"state": "unknown"}, errors
    if not isinstance(data, dict) or not isinstance(data.get("state"), str):
        return {"state": "unknown"}, ["invalid_state"]
    return data, []


def _read_json_safe(path: Path, label: str) -> tuple[Any | None, list[str]]:
    if not path.exists():
        return None, [f"missing_{label}"]
    try:
        return read_json(path), []
    except JSONDecodeError:
        return None, [f"malformed_json:{label}"]
    except OSError as exc:
        return None, [f"unreadable_json:{label}:{exc.__class__.__name__}"]
    except Exception as exc:
        return None, [f"invalid_json:{label}:{exc.__class__.__name__}"]


def _force_write_state(batch_dir: Path, state: str) -> None:
    write_json(batch_dir / "state.json", {"state": state, "updated_at": utc_now()})


def _untrusted_ingress_result(root: Path, batch_dir: Path, batch_id: str, errors: list[str]) -> dict[str, Any]:
    handoff, handoff_errors = _read_json_safe(batch_dir / "publish-handoff.json", "publish_handoff")
    if isinstance(handoff, dict) and not handoff_errors:
        prior_head = handoff.get("prior_head")
        _restore_head(root, prior_head if isinstance(prior_head, dict) else None)
        _force_write_state(batch_dir, "quarantined")
        record = {"schema": "nollm.legacy_import_quarantine.v1", "batch_id": batch_id, "timestamp": utc_now(), "reason": "untrusted_ingress:" + ",".join(errors), "state": "quarantined"}
        write_json(batch_dir / "quarantine.json", record)
        append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_quarantine", **record})
        return {"ok": False, "batch_id": batch_id, "state": "quarantined", "recovery_required": True, "errors": errors}
    return {"ok": False, "batch_id": batch_id, "state": "recovery_required", "recovery_required": True, "errors": errors + handoff_errors}


def _write_state(batch_dir: Path, state: str) -> None:
    current = _load_state(batch_dir)["state"]
    allowed = {
        "planned": {"planned", "staged", "failed", "quarantined"},
        "staged": {"staged", "validated", "failed", "quarantined"},
        "validated": {"validated", "publishing", "failed", "quarantined"},
        "publishing": {"publishing", "committed", "failed", "quarantined"},
        "committed": {"committed"},
        "failed": {"failed"},
        "quarantined": {"quarantined"},
    }
    if state not in allowed.get(current, {current}):
        raise ValueError(f"invalid batch state transition: {current} -> {state}")
    write_json(batch_dir / "state.json", {"state": state, "updated_at": utc_now()})


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
