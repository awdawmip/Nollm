from __future__ import annotations

import json
import base64
import ctypes
import os
import re
import shutil
import time
import threading
import uuid
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .archive import existing_memory_root_path, load_manifest, memory_root_path, utc_now, verify_archive_snapshot
from .archive_manifest import canonical_json, read_json, sha256_bytes, write_json
from .coverage import validate_source_coverage
from .legacy_extract import extract_legacy_spans, idempotence_key
from .native_field import (
    admit_current_publication,
    build_shard,
    existing_shards_by_key,
    load_field_head,
    current_publication,
    shard_id_for,
    validate_legacy_import_shard_profile,
    validate_publication_activation,
    validate_publication_manifest_closure,
    validate_publication_semantics,
    write_jsonl,
)
from .path_safety import contained_path, ensure_contained_parent, validate_batch_id, validate_field_id
from .provenance import build_source_span_links, validate_deep_provenance
from .provenance import validate_staged_publication
from .safe_storage import (
    SafeStorageError,
    read_jsonl_bytes,
    safe_append_jsonl,
    safe_read_file,
    safe_atomic_json,
    safe_atomic_jsonl,
    safe_atomic_write,
    safe_mkdirs,
    safe_read_regular,
)
from .source_spans import build_source_span_inventory


IMPORT_SCHEMA = "nollm.legacy_import_request.v1"
RECEIPT_SCHEMA = "nollm.legacy_import_receipt.v1"
ACTIVATION_SCHEMA = "nollm.field_activation.v1"
LEGACY_IMPORT_PROFILE = "nollm.legacy_import_shard_profile.v1"
_NO_HEAD_EXPECTATION = object()
IMPORT_REQUEST_FIELDS = {
    "archive_manifest_hash",
    "base_batch_id",
    "batch_id",
    "canonical_extraction_hash",
    "canonical_span_inventory_hash",
    "created_at",
    "dedupe_policy",
    "extraction_count",
    "geometry_policy",
    "logical_plan_id",
    "schema",
    "snapshot_id",
    "source_policy_id",
    "target_field_id",
}
STATE_FIELDS = {"state", "updated_at"}
PUBLISH_HANDOFF_FIELDS = {
    "batch_id",
    "candidate_activation_hash",
    "candidate_head_bytes_sha256",
    "candidate_manifest_hash",
    "candidate_revision_id",
    "fencing_token",
    "prior_head",
    "prior_head_bytes_sha256",
    "publish_started_at",
    "publish_transaction_id",
    "schema",
}
PUBLISH_JOURNAL_FIELDS = {
    "batch_id",
    "candidate_activation_hash",
    "candidate_head_bytes_sha256",
    "candidate_manifest_hash",
    "candidate_revision_id",
    "created_at",
    "fencing_token",
    "prior_head",
    "prior_head_absent",
    "prior_head_bytes_b64",
    "prior_head_bytes_sha256",
    "publish_transaction_id",
    "schema",
}


_LEDGER_LOCK = threading.RLock()


def _with_ledger_lock(func):
    def _wrapper(*args, **kwargs):
        with _LEDGER_LOCK:
            return func(*args, **kwargs)
    return _wrapper


def plan_legacy_import(memory_root: Path | str, snapshot_id: str, *, target_field_id: str) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": [str(exc)]}
    field_errors = validate_field_id(target_field_id)
    if field_errors:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": field_errors}
    ledger_errors = _ledger_errors(root)
    if ledger_errors:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": ledger_errors}
    archive = verify_archive_snapshot(root, snapshot_id)
    if not archive.get("ok"):
        return {"ok": False, "snapshot_id": snapshot_id, "errors": archive.get("errors", [])}
    span_path, span_path_errors = contained_path(root, "archive", "source-spans", f"{snapshot_id}.jsonl", label="source_span_inventory", must_exist=False, require_file=True)
    if span_path_errors:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": span_path_errors}
    if not span_path.exists():
        build_source_span_inventory(root, snapshot_id)
    coverage = validate_source_coverage(root, snapshot_id)
    if not coverage.get("ok"):
        return {"ok": False, "snapshot_id": snapshot_id, "errors": coverage.get("errors", [])}
    active_errors = _active_field_policy_errors(root, snapshot_id=snapshot_id, target_field_id=target_field_id)
    if active_errors:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": active_errors}
    plan_data, plan_errors = _build_import_plan(root, snapshot_id=snapshot_id, target_field_id=target_field_id)
    if plan_errors:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": plan_errors}
    extracted = plan_data["extracted"]
    if not extracted:
        return {"ok": True, "snapshot_id": snapshot_id, "archive_only": True, "state": "archive_only", "extraction_count": 0, "errors": []}
    request = dict(plan_data["request"])
    batch_id = str(request["batch_id"])
    batch_dir, batch_errors = _batch_dir_checked(root, batch_id, must_exist=False)
    if batch_errors:
        return {"ok": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "errors": batch_errors}
    request_path = batch_dir / "import-request.json"
    receipt_path = batch_dir / "import-receipt.json"
    created_batch = False
    if not batch_dir.exists():
        try:
            batch_dir.mkdir(parents=True)
            created_batch = True
        except FileExistsError:
            _wait_for_path(request_path)
    elif not request_path.exists():
        _wait_for_path(request_path)
    if batch_dir.exists() and not request_path.exists() and any(batch_dir.iterdir()):
        state, state_errors = _load_state_safe(batch_dir)
        return {"ok": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "state": state["state"], "recovery_required": True, "errors": state_errors + ["missing_import_request"]}
    if request_path.exists():
        request, request_errors = _read_json_safe(request_path, "import_request")
        state, state_errors = _load_state_safe(batch_dir)
        request_contract_errors = (
            _validate_planned_request_contract(
                request,
                batch_id=batch_id,
                expected_request=dict(plan_data["request"]),
            )
            if isinstance(request, dict)
            else []
        )
        if request_errors or not isinstance(request, dict) or state_errors:
            return {"ok": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "state": state["state"], "recovery_required": True, "errors": state_errors + request_errors + ([] if isinstance(request, dict) else ["invalid_import_request"])}
        if request_contract_errors:
            return {"ok": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "state": state["state"], "recovery_required": True, "errors": request_contract_errors}
        receipt, receipt_errors = _read_json_safe(receipt_path, "import_receipt") if receipt_path.exists() else (None, [])
        if receipt_errors:
            return {"ok": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "state": state["state"], "recovery_required": True, "errors": receipt_errors}
        if state["state"] in {"committed", "publishing"} and not receipt_path.exists():
            return {"ok": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "state": state["state"], "recovery_required": True, "errors": ["missing_import_receipt"]}
        if receipt_path.exists() and state["state"] not in {"committed", "publishing"}:
            return {"ok": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "state": state["state"], "recovery_required": True, "errors": [f"invalid_receipted_state:{state['state']}"]}
        if receipt_path.exists():
            handoff, handoff_errors = _read_json_safe(batch_dir / "publish-handoff.json", "publish_handoff")
            if handoff_errors or not isinstance(handoff, dict):
                return {"ok": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "state": state["state"], "recovery_required": True, "errors": handoff_errors or ["invalid_publish_handoff"]}
        return {
            "ok": True,
            "batch_id": batch_id,
            "snapshot_id": snapshot_id,
            "extraction_count": request.get("extraction_count", len(extracted)),
            "batch_dir": str(batch_dir),
            "state": state["state"],
            "field_revision_id": receipt.get("field_revision_id") if isinstance(receipt, dict) and not receipt_errors else None,
            "errors": receipt_errors,
            "reused": True,
        }
    if not created_batch:
        return {"ok": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "state": "recovery_required", "recovery_required": True, "errors": ["missing_import_request"]}
    _safe_write_json_path(root, request_path, request, "import_request")
    _write_state(batch_dir, "planned")
    _write_jsonl(batch_dir / "extraction.jsonl", extracted)
    _safe_write_json_path(root, batch_dir / "migration-report.json", _migration_report(root, batch_id, request, dry_run=True), "migration_report")
    _ensure_ledger_event(root / "ledger" / "events.jsonl", {"op": "legacy_import_plan", "event_id": f"legacy_import_plan:{batch_id}", "batch_id": batch_id, "timestamp": utc_now(), "state": "planned"})
    return {"ok": True, "batch_id": batch_id, "snapshot_id": snapshot_id, "extraction_count": len(extracted), "batch_dir": str(batch_dir), "state": "planned"}


def run_legacy_import(memory_root: Path | str, batch_id: str, *, dry_run: bool = False, commit: bool = False) -> dict[str, Any]:
    if dry_run == commit:
        return {"ok": False, "batch_id": batch_id, "errors": ["choose exactly one of dry_run or commit"]}
    id_errors = validate_batch_id(batch_id)
    if id_errors:
        return {"ok": False, "batch_id": batch_id, "errors": id_errors}
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return {"ok": False, "batch_id": batch_id, "errors": [str(exc)]}
    batch_dir, batch_errors = _batch_dir_checked(root, batch_id)
    if batch_errors:
        return {"ok": False, "batch_id": batch_id, "state": "recovery_required", "recovery_required": True, "errors": batch_errors}
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
    request_identity_errors = _validate_request_identity(request, batch_id=batch_id)
    if request_identity_errors:
        return _untrusted_ingress_result(root, batch_dir, batch_id, request_identity_errors)
    plan_errors = _validate_canonical_plan(root, batch_dir, batch_id, request)
    if plan_errors:
        return _untrusted_ingress_result(root, batch_dir, batch_id, plan_errors)
    receipt_path = batch_dir / "import-receipt.json"
    if commit and receipt_path.exists() and state["state"] not in {"committed", "publishing"}:
        return _untrusted_ingress_result(root, batch_dir, batch_id, [f"invalid_receipted_state:{state['state']}"])
    if commit and state["state"] == "committed" and receipt_path.exists():
        receipt, receipt_errors = _read_json_safe(receipt_path, "import_receipt")
        if receipt_errors or not isinstance(receipt, dict):
            return {"ok": False, "batch_id": batch_id, "state": "committed", "errors": receipt_errors or ["invalid_import_receipt"]}
        validation = validate_legacy_import(root, batch_id)
        if not validation.get("ok"):
            return {"ok": False, "batch_id": batch_id, "state": "committed", "errors": validation.get("errors", [])}
        _append_ledger_event(root, {"op": "legacy_import_duplicate_commit", "batch_id": batch_id, "timestamp": utc_now(), "duplicate_count": len(_read_jsonl(batch_dir / "extraction.jsonl"))})
        return {
            "ok": True,
            "batch_id": batch_id,
            "committed": True,
            "created_shard_count": 0,
            "duplicate_count": len(_read_jsonl(batch_dir / "extraction.jsonl")),
            "field_revision_id": receipt.get("field_revision_id"),
            "state": "committed",
        }
    if commit:
        lock_dir, lock_error = _acquire_writer_lock(root, batch_id)
        if lock_error is not None:
            return lock_error
        try:
            expected_head_bytes = _read_head_bytes(root)
        except ValueError as exc:
            _release_writer_lock(lock_dir)
            return {"ok": False, "batch_id": batch_id, "state": "retry_required", "retry_required": True, "errors": str(exc).split(",")}
        try:
            return _run_legacy_import_after_request(root, batch_id, batch_dir, state, request, dry_run=dry_run, expected_head_bytes=expected_head_bytes)
        finally:
            _release_writer_lock(lock_dir)
    return _run_legacy_import_after_request(root, batch_id, batch_dir, state, request, dry_run=dry_run)


def _run_legacy_import_after_request(
    root: Path,
    batch_id: str,
    batch_dir: Path,
    state: dict[str, Any],
    request: dict[str, Any],
    *,
    dry_run: bool,
    expected_head_bytes: bytes | None | object = _NO_HEAD_EXPECTATION,
) -> dict[str, Any]:
    archive = verify_archive_snapshot(root, str(request["snapshot_id"]))
    coverage = validate_source_coverage(root, str(request["snapshot_id"]), require_linked=False)
    if not archive.get("ok") or not coverage.get("ok"):
        return {"ok": False, "batch_id": batch_id, "errors": archive.get("errors", []) + coverage.get("errors", [])}
    active_errors = _active_field_policy_errors(root, snapshot_id=str(request["snapshot_id"]), target_field_id=str(request["target_field_id"]))
    if active_errors:
        return {"ok": False, "batch_id": batch_id, "errors": active_errors, "state": state["state"]}
    manifest = load_manifest(root, str(request["snapshot_id"]))
    source_policy_id = str(manifest["source_policy_id"])
    extracted, extraction_errors = _read_jsonl_safe(batch_dir / "extraction.jsonl", "extraction")
    if extraction_errors:
        return _untrusted_ingress_result(root, batch_dir, batch_id, extraction_errors)
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
        _safe_write_json_path(root, batch_dir / "dry-run-report.json", report, "dry_run_report")
        return {"ok": True, "batch_id": batch_id, "dry_run": True, "candidate_shard_count": len(shards), "duplicate_count": duplicate_count}
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "batch_id": batch_id,
        "snapshot_id": request["snapshot_id"],
        "target_field_id": request["target_field_id"],
        "source_policy_id": source_policy_id,
        "committed_at": utc_now(),
        "created_shard_ids": [str(shard["shard_id"]) for shard in shards],
        "created_shard_count": len(shards),
        "duplicate_count": duplicate_count,
    }
    head_written = False
    prior_head = load_field_head(root)
    try:
        _write_state(batch_dir, "staged")
        revision = _revision_candidate(root, batch_id=batch_id, target_field_id=str(request["target_field_id"]), shard_ids=[str(shard["shard_id"]) for shard in publication_shards])
        receipt["field_revision_id"] = revision["field_revision_id"]
        links = build_source_span_links(snapshot_id=str(request["snapshot_id"]), batch_id=batch_id, field_revision_id=str(revision["field_revision_id"]), shards=publication_shards)
        staging = _write_staging_package(root, batch_id, revision, publication_shards, links, str(request["snapshot_id"]), source_policy_id, receipt)
        if os.environ.get("NOLLM_MT1_CORRUPT_STAGING_TEXT") == "1":
            shard_path = next((staging / "shards").glob("*.json"))
            shard = read_json(shard_path)
            shard["text"] = "TAMPERED STAGING CONTENT"
            write_json(shard_path, shard)
        staged_validation = validate_staged_publication(root, batch_id, str(request["snapshot_id"]), str(revision["field_revision_id"]))
        if not staged_validation.get("ok"):
            raise ValueError("staged_validation_failed:" + ",".join(staged_validation.get("errors", [])))
        _write_state(batch_dir, "validated")
        _append_ledger_event(root, {"op": "legacy_import_validate_staging", "batch_id": batch_id, "timestamp": utc_now(), "state": "validated"})
        if os.environ.get("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD") == "1":
            raise RuntimeError("forced_failure_before_head")
        if os.environ.get("NOLLM_MT1_FORCE_OSERROR_DURING_PUBLISH") == "1":
            raise OSError("forced_oserror_during_publish")
        _write_state(batch_dir, "publishing")
        publication = _publish_package(root, batch_id, str(revision["field_revision_id"]))
        _safe_write_json_path(root, batch_dir / "import-receipt.json", receipt, "import_receipt")
        manifest_hash = _safe_hash_under_root(root, publication / "publication-manifest.json", "publication_manifest")
        activation_hash = _safe_hash_under_root(root, publication / "activation.json", "publication_activation")
        pre_head_errors = _pre_head_publication_errors(root, publication, str(revision["field_revision_id"]), str(request["target_field_id"]))
        if pre_head_errors:
            raise ValueError("pre_head_publication_validation_failed:" + ",".join(pre_head_errors))
        candidate_head = {
            "field_id": request["target_field_id"],
            "field_revision_id": revision["field_revision_id"],
            "publication_manifest_hash": manifest_hash,
            "activation_hash": activation_hash,
        }
        fencing_token = _current_fencing_token(root) if expected_head_bytes is not _NO_HEAD_EXPECTATION else ""
        publish_transaction_id = _write_publish_journal(root, batch_id, str(revision["field_revision_id"]), manifest_hash, activation_hash, prior_head, expected_head_bytes, candidate_head, fencing_token)
        _write_publish_handoff(batch_dir, batch_id, str(revision["field_revision_id"]), manifest_hash, activation_hash, prior_head, publish_transaction_id, candidate_head, expected_head_bytes, fencing_token)
        _write_head_atomic(
            root,
            candidate_head,
            expected_prior_head_bytes=expected_head_bytes,
            fencing_token=fencing_token,
        )
        head_written = True
        if os.environ.get("NOLLM_MT1_FORCE_JOURNAL_OSERROR_AFTER_HEAD") == "1":
            return {"ok": True, "batch_id": batch_id, "published": True, "reconciliation_pending": True, "field_revision_id": revision["field_revision_id"], "state": "publishing"}
        finalized = _finalize_verified_publication(root, batch_dir, request, receipt, publication, duplicate_count=duplicate_count)
        if not finalized.get("ok"):
            _quarantine_and_restore_head(root, batch_dir, prior_head, "published_provenance_failed:" + ",".join(finalized.get("errors", [])))
            return {"ok": False, "batch_id": batch_id, "errors": finalized.get("errors", []), "state": "quarantined", "recovery_required": True}
        return {"ok": True, "batch_id": batch_id, "committed": True, "created_shard_count": len(shards), "duplicate_count": duplicate_count, "field_revision_id": revision["field_revision_id"], "state": "committed"}
    except Exception as exc:
        if head_written:
            head = load_field_head(root)
            if head and head.get("field_revision_id") == receipt.get("field_revision_id"):
                provenance = validate_deep_provenance(root, str(request["snapshot_id"]), str(receipt.get("field_revision_id")))
                if provenance.get("ok"):
                    return {"ok": True, "batch_id": batch_id, "published": True, "reconciliation_pending": True, "field_revision_id": receipt.get("field_revision_id"), "state": _load_state(batch_dir)["state"]}
                _quarantine_and_restore_head(root, batch_dir, prior_head, str(exc))
                return {"ok": False, "batch_id": batch_id, "errors": [str(exc)], "state": "quarantined", "recovery_required": True}
        if _load_state(batch_dir)["state"] != "committed":
            _write_state(batch_dir, "failed")
        failure = {"schema": "nollm.legacy_import_failure.v1", "batch_id": batch_id, "timestamp": utc_now(), "error": str(exc), "state": "failed"}
        _safe_write_json_path(root, batch_dir / "failure.json", failure, "failure")
        _append_ledger_event(root, {"op": "legacy_import_failure", **failure})
        return {"ok": False, "batch_id": batch_id, "errors": [str(exc)], "state": "failed"}


def reconcile_legacy_import(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return {"ok": False, "batch_id": batch_id, "errors": [str(exc)], "recovery_required": True}
    lock_dir, lock_error = _acquire_writer_lock(root, batch_id, reclaim_stale=True)
    if lock_error is not None:
        return lock_error
    try:
        return _reconcile_legacy_import_locked(root, batch_id)
    finally:
        _release_writer_lock(lock_dir)


def _reconcile_legacy_import_locked(root: Path, batch_id: str) -> dict[str, Any]:
    id_errors = validate_batch_id(batch_id)
    if id_errors:
        return {"ok": False, "batch_id": batch_id, "errors": id_errors, "recovery_required": True}
    batch_dir, batch_errors = _batch_dir_checked(root, batch_id)
    if batch_errors:
        return {"ok": False, "batch_id": batch_id, "state": "recovery_required", "recovery_required": True, "errors": batch_errors}
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
        return {"ok": False, "batch_id": batch_id, "state": "quarantined", "recovery_required": True, "errors": ["head_not_at_receipt_revision"]}
    publication = current_publication(root)
    if not publication:
        _quarantine_and_restore_head(root, batch_dir, None, "reconcile_validation_failed:inactive_publication")
        return {"ok": False, "batch_id": batch_id, "state": "quarantined", "recovery_required": True, "errors": ["inactive_publication"]}
    try:
        request, request_errors = _read_json_safe(batch_dir / "import-request.json", "import_request")
        if request_errors or not isinstance(request, dict):
            return _untrusted_ingress_result(root, batch_dir, batch_id, request_errors or ["invalid_import_request"])
        contract_errors = _validate_receipt_and_handoff_contract(root, batch_dir, request, receipt, handoff)
        if contract_errors:
            return {"ok": False, "batch_id": batch_id, "state": state, "recovery_required": True, "errors": contract_errors}
        finalized = _finalize_verified_publication(root, batch_dir, request, receipt, publication, duplicate_count=int(receipt.get("duplicate_count", 0)), reconcile=True)
    except Exception as exc:
        return {"ok": True, "batch_id": batch_id, "published": True, "reconciliation_pending": True, "field_revision_id": receipt.get("field_revision_id"), "state": _load_state(batch_dir)["state"], "errors": [str(exc)]}
    if not finalized.get("ok"):
        _quarantine_and_restore_head(root, batch_dir, None, "reconcile_validation_failed:" + ",".join(finalized.get("errors", [])))
        return {"ok": False, "batch_id": batch_id, "state": "quarantined", "recovery_required": True, "errors": finalized.get("errors", [])}
    return {"ok": True, "batch_id": batch_id, "state": "committed", "changed": True, "field_revision_id": receipt.get("field_revision_id")}


def recover_legacy_import(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return {"ok": False, "batch_id": batch_id, "errors": [str(exc)], "recovery_required": True}
    lock_dir, lock_error = _acquire_writer_lock(root, batch_id, reclaim_stale=True)
    if lock_error is not None:
        return lock_error
    try:
        return _recover_legacy_import_locked(root, batch_id)
    finally:
        _release_writer_lock(lock_dir)


def _recover_legacy_import_locked(root: Path, batch_id: str) -> dict[str, Any]:
    id_errors = validate_batch_id(batch_id)
    if id_errors:
        return {"ok": False, "batch_id": batch_id, "errors": id_errors, "recovery_required": True}
    old_dir, old_errors = _batch_dir_checked(root, batch_id)
    if old_errors:
        return {"ok": False, "batch_id": batch_id, "errors": old_errors, "recovery_required": True}
    state_record, state_errors = _load_state_safe(old_dir)
    if state_errors:
        return _untrusted_ingress_result(root, old_dir, batch_id, state_errors)
    state = state_record["state"]
    if state == "publishing":
        return _reconcile_legacy_import_locked(root, batch_id)
    if state not in {"failed", "quarantined"}:
        return {"ok": False, "batch_id": batch_id, "state": state, "errors": [f"cannot_recover_state:{state}"]}
    old_request, request_errors = _read_json_safe(old_dir / "import-request.json", "import_request")
    if request_errors or not isinstance(old_request, dict):
        return {"ok": False, "batch_id": batch_id, "state": state, "errors": request_errors or ["invalid_import_request"]}
    request_identity_errors = _validate_request_identity(old_request, batch_id=batch_id)
    if request_identity_errors:
        return {"ok": False, "batch_id": batch_id, "state": state, "errors": request_identity_errors, "recovery_required": True}
    canonical_errors = _validate_canonical_plan(root, old_dir, batch_id, old_request)
    if canonical_errors:
        return {"ok": False, "batch_id": batch_id, "state": state, "errors": canonical_errors, "recovery_required": True}
    plan_data, plan_errors = _build_import_plan(root, snapshot_id=str(old_request["snapshot_id"]), target_field_id=str(old_request["target_field_id"]))
    if plan_errors:
        return {"ok": False, "batch_id": batch_id, "state": state, "errors": plan_errors, "recovery_required": True}
    replacement_id = _replacement_batch_id(batch_id)
    replacement_dir, replacement_errors = _batch_dir_checked(root, replacement_id, must_exist=False)
    if replacement_errors:
        return {"ok": False, "batch_id": batch_id, "replacement_batch_id": replacement_id, "errors": replacement_errors, "recovery_required": True}
    if replacement_dir.exists():
        return {"ok": True, "batch_id": batch_id, "replacement_batch_id": replacement_id, "reused": True}
    replacement_request = dict(old_request)
    replacement_request["batch_id"] = replacement_id
    replacement_dir.mkdir(parents=True, exist_ok=True)
    _safe_write_json_path(root, replacement_dir / "import-request.json", replacement_request, "import_request")
    _write_jsonl(replacement_dir / "extraction.jsonl", plan_data["extracted"])
    _write_state(replacement_dir, "planned")
    _append_ledger_event(root, {"op": "legacy_import_recovery_batch", "batch_id": replacement_id, "recovery_of": batch_id, "timestamp": utc_now(), "state": "planned"})
    return {"ok": True, "batch_id": batch_id, "replacement_batch_id": replacement_id, "reused": False}


def validate_legacy_import(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return {"ok": False, "batch_id": batch_id, "state": "invalid", "errors": [str(exc)]}
    id_errors = validate_batch_id(batch_id)
    if id_errors:
        return {"ok": False, "batch_id": batch_id, "state": "invalid", "errors": id_errors}
    errors: list[str] = []
    batch_dir, batch_errors = _batch_dir_checked(root, batch_id)
    if batch_errors:
        return {"ok": False, "batch_id": batch_id, "state": "invalid", "errors": batch_errors}
    state, state_errors = _load_state_safe(batch_dir)
    errors.extend(state_errors)
    request, request_errors = _read_json_safe(batch_dir / "import-request.json", "import_request")
    errors.extend(request_errors)
    ledger_errors = _ledger_errors(root)
    errors.extend(ledger_errors)
    if not isinstance(request, dict):
        return {"ok": False, "batch_id": batch_id, "state": state["state"], "errors": errors or ["invalid_import_request"]}
    errors.extend(_validate_request_identity(request, batch_id=batch_id))
    errors.extend(_validate_canonical_plan(root, batch_dir, batch_id, request))
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
        if state["state"] not in {"committed", "publishing"}:
            errors.append(f"batch_state_not_finalized:{state['state']}")
        provenance = validate_deep_provenance(root, str(request["snapshot_id"]), str(receipt.get("field_revision_id")))
        errors.extend(provenance.get("errors", []))
        publication = current_publication(root)
        handoff, handoff_errors = _read_json_safe(batch_dir / "publish-handoff.json", "publish_handoff")
        errors.extend(handoff_errors)
        if isinstance(handoff, dict):
            errors.extend(_validate_receipt_and_handoff_contract(root, batch_dir, request, receipt, handoff))
        else:
            errors.append("invalid_publish_handoff")
        for shard_id in receipt.get("created_shard_ids", []):
            shard_path = (publication / "shards" / f"{shard_id}.json") if publication else root / "field" / "missing-publication"
            if not shard_path.exists():
                errors.append(f"missing_shard:{shard_id}")
                continue
            shard, shard_errors = _read_json_safe(shard_path, f"publication_shard:{shard_id}")
            errors.extend(shard_errors)
            if not isinstance(shard, dict):
                errors.append(f"invalid_shard:{shard_id}")
                continue
            if not shard.get("source_refs") or not all(str(ref).startswith("archive://snapshot/") for ref in shard.get("source_refs", [])):
                errors.append(f"invalid_source_refs:{shard_id}")
        head = load_field_head(root)
        if not head or head.get("field_revision_id") != receipt.get("field_revision_id"):
            errors.append("field_head_does_not_match_receipt")
        if state["state"] == "committed" and not ledger_errors and not _has_finalization_ledger_event(root, receipt):
            errors.append("missing_finalization_ledger_event")
    else:
        errors.append("missing_import_receipt")
    return {"ok": not errors, "batch_id": batch_id, "state": state["state"], "errors": errors}


def legacy_import_report(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    id_errors = validate_batch_id(batch_id)
    if id_errors:
        return {"ok": False, "batch_id": batch_id, "state": "invalid", "recovery_required": True, "errors": id_errors}
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return {"ok": False, "batch_id": batch_id, "state": "invalid", "recovery_required": True, "errors": [str(exc)]}
    batch_dir, batch_errors = _batch_dir_checked(root, batch_id)
    if batch_errors:
        return {"ok": False, "batch_id": batch_id, "state": "invalid", "recovery_required": True, "errors": batch_errors}
    request, request_errors = _read_json_safe(batch_dir / "import-request.json", "import_request")
    if request_errors or not isinstance(request, dict):
        state, state_errors = _load_state_safe(batch_dir)
        return {"ok": False, "batch_id": batch_id, "state": state["state"], "recovery_required": True, "errors": state_errors + request_errors + ([] if isinstance(request, dict) else ["invalid_import_request"])}
    report_path = batch_dir / "migration-report.json"
    report, report_errors = _read_json_safe(report_path, "migration_report") if report_path.exists() else (_migration_report(root, batch_id, request), [])
    if report_errors or not isinstance(report, dict):
        return {"ok": False, "batch_id": batch_id, "state": _load_state_safe(batch_dir)[0]["state"], "recovery_required": True, "errors": report_errors or ["invalid_migration_report"]}
    report["validation"] = validate_legacy_import(root, batch_id) if (batch_dir / "import-receipt.json").exists() else {"ok": False, "errors": ["not_committed"]}
    report["ok"] = bool(report["validation"].get("ok"))
    state, state_errors = _load_state_safe(batch_dir)
    report["state"] = state["state"]
    if state_errors:
        report["ok"] = False
        report.setdefault("errors", []).extend(state_errors)
    return report


def _build_import_plan(root: Path, *, snapshot_id: str, target_field_id: str, batch_id: str | None = None) -> tuple[dict[str, Any], list[str]]:
    try:
        manifest = load_manifest(root, snapshot_id)
        extracted = extract_legacy_spans(root, snapshot_id)
    except (JSONDecodeError, ValueError, OSError) as exc:
        return {}, [_structured_exception("legacy_extract", exc)]
    extraction_bytes = _jsonl_bytes(extracted)
    span_path, span_errors = contained_path(root, "archive", "source-spans", f"{snapshot_id}.jsonl", label="source_span_inventory", must_exist=True, require_file=True)
    if span_errors:
        return {}, span_errors
    try:
        span_inventory_hash = "sha256:" + sha256_bytes(safe_read_regular(_infer_root_for_path(span_path), *span_path.relative_to(_infer_root_for_path(span_path)).parts, label="source_span_inventory"))
    except OSError as exc:
        return {}, [f"unreadable_jsonl:source_span_inventory:{exc.__class__.__name__}"]
    archive_manifest_hash = str(manifest.get("archive_manifest_hash", manifest.get("manifest_hash")))
    plan_seed = {
        "archive_manifest_hash": archive_manifest_hash,
        "canonical_extraction_hash": "sha256:" + sha256_bytes(extraction_bytes),
        "canonical_span_inventory_hash": span_inventory_hash,
        "dedupe_policy": "idempotence_key_active_head_only",
        "geometry_policy": "none_mt1_archive_ingest",
        "schema": IMPORT_SCHEMA,
        "snapshot_id": snapshot_id,
        "source_policy_id": manifest.get("source_policy_id"),
        "target_field_id": target_field_id,
    }
    logical_plan_id = "plan_" + sha256_bytes(canonical_json(plan_seed))[:24]
    base_batch_id = "batch_" + sha256_bytes(canonical_json({"logical_plan_id": logical_plan_id, **plan_seed}))[:20]
    actual_batch_id = batch_id or base_batch_id
    request = {
        "schema": IMPORT_SCHEMA,
        "logical_plan_id": logical_plan_id,
        "base_batch_id": base_batch_id,
        "batch_id": actual_batch_id,
        "snapshot_id": snapshot_id,
        "target_field_id": target_field_id,
        "source_policy_id": manifest.get("source_policy_id"),
        "archive_manifest_hash": archive_manifest_hash,
        "canonical_extraction_hash": plan_seed["canonical_extraction_hash"],
        "canonical_span_inventory_hash": span_inventory_hash,
        "dedupe_policy": plan_seed["dedupe_policy"],
        "geometry_policy": plan_seed["geometry_policy"],
        "created_at": utc_now(),
        "extraction_count": len(extracted),
    }
    return {"request": request, "extracted": extracted, "extraction_bytes": extraction_bytes}, []


def _base_batch_id(batch_id: str) -> str:
    match = re.match(r"^(batch_[0-9a-f]{20})(?:_r[1-9][0-9]*)?$", batch_id)
    return match.group(1) if match else batch_id


def _wait_for_path(path: Path, *, attempts: int = 50, delay: float = 0.02) -> None:
    for _ in range(attempts):
        if path.exists():
            return
        time.sleep(delay)


def _jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    return "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records).encode("utf-8")


def _validate_canonical_plan(root: Path, batch_dir: Path, batch_id: str, request: dict[str, Any]) -> list[str]:
    target = request.get("target_field_id")
    snapshot_id = request.get("snapshot_id")
    if not isinstance(target, str) or not isinstance(snapshot_id, str):
        return ["import_request_plan_identity_invalid"]
    plan_data, errors = _build_import_plan(root, snapshot_id=snapshot_id, target_field_id=target, batch_id=batch_id)
    if errors:
        return errors
    expected = dict(plan_data["request"])
    errors.extend(_compare_request_to_expected(request, expected))
    if _base_batch_id(batch_id) != expected.get("base_batch_id"):
        errors.append("import_request_base_batch_id_mismatch")
    extracted, extraction_errors = _read_jsonl_safe(batch_dir / "extraction.jsonl", "extraction")
    errors.extend(extraction_errors)
    if not extraction_errors:
        actual_hash = "sha256:" + sha256_bytes(_jsonl_bytes(extracted))
        if actual_hash != expected.get("canonical_extraction_hash"):
            errors.append("canonical_extraction_hash_mismatch")
        if _jsonl_bytes(extracted) != plan_data["extraction_bytes"]:
            errors.append("canonical_extraction_content_mismatch")
    return errors


def _compare_request_to_expected(request: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key, expected_value in expected.items():
        if key == "created_at":
            continue
        if request.get(key) != expected_value:
            errors.append(f"import_request_{key}_mismatch")
    return errors


def _batch_dir(root: Path, batch_id: str) -> Path:
    return root / "ingress" / "legacy-import" / batch_id


def _batch_dir_checked(root: Path, batch_id: str, *, must_exist: bool = True) -> tuple[Path, list[str]]:
    path, errors = contained_path(root, "ingress", "legacy-import", batch_id, label="ingress_batch", must_exist=False, require_file=False)
    if errors:
        return path, errors
    if must_exist and not path.exists():
        return path, ["path_missing:ingress_batch"]
    if path.exists():
        if path.is_symlink():
            return path, ["path_symlink:ingress_batch"]
        if not path.is_dir():
            return path, ["path_not_directory:ingress_batch"]
    return path, []


def _safe_write_json_path(root: Path, path: Path, data: dict[str, Any], label: str, *, replace: bool = True) -> None:
    try:
        parts = path.resolve(strict=False).relative_to(root.resolve()).parts
    except ValueError as exc:
        raise ValueError(f"path_escape:{label}") from exc
    safe_atomic_json(root, parts, data, label=label, replace=replace)


def _root_from_batch_dir(batch_dir: Path) -> Path:
    return batch_dir.parents[2]


def _infer_root_for_path(path: Path) -> Path:
    for parent in [path.parent, *path.parents]:
        if (parent / "archive").exists() or (parent / "ingress").exists() or (parent / "field").exists():
            return parent
    raise ValueError("memory_root_missing")


def _validate_request_identity(request: dict[str, Any], *, batch_id: str) -> list[str]:
    errors: list[str] = []
    errors.extend(_unknown_fields(request, IMPORT_REQUEST_FIELDS, "import_request"))
    if request.get("schema") != IMPORT_SCHEMA:
        errors.append("import_request_schema_mismatch")
    if request.get("batch_id") != batch_id:
        errors.append("import_request_batch_id_mismatch")
    if request.get("base_batch_id") != _base_batch_id(batch_id):
        errors.append("import_request_base_batch_id_mismatch")
    if not isinstance(request.get("logical_plan_id"), str) or not str(request.get("logical_plan_id")).startswith("plan_"):
        errors.append("import_request_logical_plan_id_invalid")
    for key in ("snapshot_id", "target_field_id", "source_policy_id"):
        if not isinstance(request.get(key), str) or not request.get(key):
            errors.append(f"import_request_{key}_invalid")
    errors.extend(f"import_request_{error}" for error in validate_field_id(request.get("target_field_id")))
    extraction_count = request.get("extraction_count")
    if not isinstance(extraction_count, int) or extraction_count < 0:
        errors.append("import_request_extraction_count_invalid")
    for key in ("archive_manifest_hash", "canonical_extraction_hash", "canonical_span_inventory_hash"):
        if not isinstance(request.get(key), str) or not str(request.get(key)).startswith("sha256:"):
            errors.append(f"import_request_{key}_invalid")
    return errors


def _validate_planned_request_contract(
    request: dict[str, Any],
    *,
    batch_id: str,
    expected_request: dict[str, Any],
) -> list[str]:
    errors = _validate_request_identity(request, batch_id=batch_id)
    errors.extend(_compare_request_to_expected(request, expected_request))
    if request.get("dedupe_policy") != "idempotence_key_active_head_only":
        errors.append("import_request_dedupe_policy_mismatch")
    if request.get("geometry_policy") != "none_mt1_archive_ingest":
        errors.append("import_request_geometry_policy_mismatch")
    created_at = request.get("created_at")
    if not isinstance(created_at, str) or not _is_utc_timestamp(created_at):
        errors.append("import_request_created_at_invalid")
    return errors


def _replacement_batch_id(batch_id: str) -> str:
    prefix, _, suffix = batch_id.partition("_r")
    if suffix:
        attempt = int(suffix) + 1
        replacement = f"{prefix}_r{attempt}"
    else:
        replacement = f"{batch_id}_r1"
    errors = validate_batch_id(replacement)
    if errors:
        raise ValueError(errors[0])
    return replacement


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


def _validate_receipt_and_handoff_contract(root: Path, batch_dir: Path, request: dict[str, Any], receipt: dict[str, Any], handoff: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_receipt_contract(request, receipt, "ingress_receipt"))
    admission = admit_current_publication(root)
    publication = admission.get("publication")
    head = admission.get("head")
    if not publication:
        errors.append("inactive_publication")
        errors.extend(str(error) for error in admission.get("errors", []))
        return errors
    package_receipt, package_receipt_errors = _read_json_safe(publication / "receipt.json", "publication_receipt")
    activation, activation_errors = _read_json_safe(publication / "activation.json", "publication_activation")
    manifest_path = publication / "publication-manifest.json"
    manifest, manifest_errors = _read_json_safe(manifest_path, "publication_manifest")
    errors.extend(package_receipt_errors + activation_errors + manifest_errors)
    if isinstance(package_receipt, dict):
        errors.extend(_validate_receipt_contract(request, package_receipt, "publication_receipt"))
        if canonical_json(package_receipt) != canonical_json(receipt):
            errors.append("ingress_receipt_publication_receipt_mismatch")
    else:
        errors.append("invalid_publication_receipt")
    if not isinstance(activation, dict):
        errors.append("invalid_publication_activation")
    if not isinstance(manifest, dict):
        errors.append("invalid_publication_manifest")
    if isinstance(package_receipt, dict) and isinstance(activation, dict) and isinstance(manifest, dict):
        errors.extend(_validate_handoff_contract(root, publication, request, package_receipt, activation, manifest, head, handoff))
    return errors


def _validate_receipt_contract(request: dict[str, Any], receipt: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    expected = {
        "schema": RECEIPT_SCHEMA,
        "batch_id": request.get("batch_id"),
        "snapshot_id": request.get("snapshot_id"),
        "target_field_id": request.get("target_field_id"),
        "source_policy_id": request.get("source_policy_id"),
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            errors.append(f"{label}_{key}_mismatch")
    revision_id = receipt.get("field_revision_id")
    if not isinstance(revision_id, str) or not revision_id:
        errors.append(f"{label}_field_revision_id_invalid")
    created_ids = receipt.get("created_shard_ids")
    if not isinstance(created_ids, list) or not all(isinstance(item, str) and item for item in created_ids):
        errors.append(f"{label}_created_shard_ids_invalid")
        created_ids = []
    if len(created_ids) != len(set(created_ids)):
        errors.append(f"{label}_created_shard_ids_duplicate")
    if receipt.get("created_shard_count") != len(created_ids):
        errors.append(f"{label}_created_shard_count_mismatch")
    duplicate_count = receipt.get("duplicate_count")
    if not isinstance(duplicate_count, int) or duplicate_count < 0:
        errors.append(f"{label}_duplicate_count_invalid")
    committed_at = receipt.get("committed_at")
    if not isinstance(committed_at, str) or not _is_utc_timestamp(committed_at):
        errors.append(f"{label}_committed_at_invalid")
    return errors


def _validate_handoff_contract(
    root: Path,
    publication: Path,
    request: dict[str, Any],
    package_receipt: dict[str, Any],
    activation: dict[str, Any],
    manifest: dict[str, Any],
    head: dict[str, Any] | None,
    handoff: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    errors.extend(_unknown_fields(handoff, PUBLISH_HANDOFF_FIELDS, "publish_handoff"))
    revision_id = str(package_receipt.get("field_revision_id"))
    manifest_hash = _required_file_hash(publication / "publication-manifest.json", "publication_manifest", errors)
    activation_hash = _required_file_hash(publication / "activation.json", "publication_activation", errors)
    if manifest_hash is None or activation_hash is None:
        return errors
    expected = {
        "schema": "nollm.legacy_import_publish_handoff.v1",
        "batch_id": request.get("batch_id"),
        "candidate_revision_id": revision_id,
        "candidate_manifest_hash": manifest_hash,
        "candidate_activation_hash": activation_hash,
    }
    for key, value in expected.items():
        if handoff.get(key) != value:
            errors.append(f"publish_handoff_{key}_mismatch")
    if not isinstance(handoff.get("publish_started_at"), str) or not _is_utc_timestamp(str(handoff.get("publish_started_at"))):
        errors.append("publish_handoff_started_at_invalid")
    if not isinstance(handoff.get("fencing_token"), str) or not str(handoff.get("fencing_token")).startswith("fence_"):
        errors.append("publish_handoff_fencing_token_invalid")
    if not isinstance(handoff.get("candidate_head_bytes_sha256"), str) or not str(handoff.get("candidate_head_bytes_sha256")).startswith("sha256:"):
        errors.append("publish_handoff_candidate_head_hash_invalid")
    journal = _load_publish_journal(root, handoff.get("publish_transaction_id"), errors)
    if isinstance(journal, dict):
        journal_expected = {
            "batch_id": request.get("batch_id"),
            "candidate_revision_id": revision_id,
            "candidate_manifest_hash": manifest_hash,
            "candidate_activation_hash": activation_hash,
            "candidate_head_bytes_sha256": handoff.get("candidate_head_bytes_sha256"),
            "prior_head_bytes_sha256": handoff.get("prior_head_bytes_sha256"),
            "fencing_token": handoff.get("fencing_token"),
        }
        for key, value in journal_expected.items():
            if journal.get(key) != value:
                errors.append(f"publish_journal_{key}_mismatch")
        if journal.get("prior_head") != handoff.get("prior_head"):
            errors.append("publish_journal_prior_head_mismatch")
    if not head:
        errors.append("missing_field_head")
    else:
        if head.get("field_revision_id") != revision_id:
            errors.append("publish_handoff_head_revision_mismatch")
        if head.get("publication_manifest_hash") != manifest_hash:
            errors.append("publish_handoff_head_manifest_hash_mismatch")
        if head.get("activation_hash") != activation_hash:
            errors.append("publish_handoff_head_activation_hash_mismatch")
    receipt_hash = _required_file_hash(publication / "receipt.json", "publication_receipt", errors)
    revision_hash = _required_file_hash(publication / "revision.json", "publication_revision", errors)
    links_hash = _required_file_hash(publication / "source-span-links.jsonl", "source_span_links", errors)
    projection_hash = _required_file_hash(publication / "source-span-projection.jsonl", "source_span_projection", errors)
    if None in {receipt_hash, revision_hash, links_hash, projection_hash}:
        return errors
    archive_manifest, archive_manifest_errors = _read_json_safe(root / "archive" / "manifests" / f"{request.get('snapshot_id')}.json", "archive_manifest")
    errors.extend(archive_manifest_errors)
    if not isinstance(archive_manifest, dict):
        errors.append("invalid_archive_manifest")
        archive_manifest = {}
    activation_expected = {
        "schema": ACTIVATION_SCHEMA,
        "field_id": request.get("target_field_id"),
        "field_revision_id": revision_id,
        "batch_id": request.get("batch_id"),
        "snapshot_id": request.get("snapshot_id"),
        "source_policy_id": request.get("source_policy_id"),
        "archive_manifest_schema": archive_manifest.get("schema"),
        "archive_manifest_hash": archive_manifest.get("archive_manifest_hash", archive_manifest.get("manifest_hash")),
        "receipt_hash": receipt_hash,
        "revision_hash": revision_hash,
        "source_span_links_hash": links_hash,
        "source_span_projection_hash": projection_hash,
        "legacy_import_profile": LEGACY_IMPORT_PROFILE,
    }
    for key, value in activation_expected.items():
        if activation.get(key) != value:
            errors.append(f"activation_{key}_mismatch")
    if manifest.get("field_revision_id") != revision_id:
        errors.append("publication_manifest_revision_mismatch")
    return errors


def _load_publish_journal(root: Path, transaction_id: object, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(transaction_id, str) or not re.match(r"^pubtx_[0-9a-f]{24}$", transaction_id):
        errors.append("invalid_publish_transaction_id")
        return None
    journal_path, path_errors = contained_path(root, "field", "publish-journal", f"{transaction_id}.json", label="publish_journal", must_exist=True, require_file=True)
    errors.extend(path_errors)
    if path_errors:
        return None
    journal, journal_errors = _read_json_safe(journal_path, "publish_journal")
    errors.extend(journal_errors)
    if not isinstance(journal, dict):
        errors.append("invalid_publish_journal")
        return None
    if journal.get("schema") != "nollm.publish_journal.v1":
        errors.append("invalid_publish_journal_schema")
    errors.extend(_unknown_fields(journal, PUBLISH_JOURNAL_FIELDS, "publish_journal"))
    expected_id = _publish_transaction_id(
        str(journal.get("batch_id")),
        str(journal.get("candidate_revision_id")),
        str(journal.get("candidate_manifest_hash")),
        str(journal.get("candidate_activation_hash")),
        journal.get("prior_head_bytes_sha256"),
        journal.get("candidate_head_bytes_sha256"),
        journal.get("fencing_token"),
    )
    if journal.get("publish_transaction_id") != expected_id:
        errors.append("publish_journal_transaction_id_mismatch")
    return journal


def _required_file_hash(path: Path, label: str, errors: list[str]) -> str | None:
    try:
        root = _infer_root_for_path(path)
        return "sha256:" + sha256_bytes(safe_read_regular(root, *path.relative_to(root).parts, label=label))
    except SafeStorageError as exc:
        errors.append(str(exc))
    except OSError as exc:
        errors.append(f"unreadable_file:{label}:{exc.__class__.__name__}")
    except ValueError as exc:
        errors.append(str(exc))
    return None


def _is_utc_timestamp(value: str) -> bool:
    if not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


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
    state, _state_errors = _load_state_safe(root / "ingress" / "legacy-import" / batch_id)
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
        "state": state["state"],
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


def _write_staging_package(
    root: Path,
    batch_id: str,
    revision: dict[str, Any],
    shards: list[dict[str, Any]],
    links: list[dict[str, Any]],
    snapshot_id: str,
    source_policy_id: str,
    receipt: dict[str, Any],
) -> Path:
    staging, staging_errors = contained_path(root, "field", ".staging", batch_id, "publication", label="field_staging", must_exist=False, require_file=False)
    if staging_errors:
        raise ValueError(",".join(staging_errors))
    if staging.exists() and staging.is_symlink():
        raise ValueError("path_symlink:field_staging")
    if staging.exists():
        raise ValueError("path_exists:field_staging")
    safe_mkdirs(root, ("field", ".staging", batch_id, "publication", "shards"), label="field_staging")
    for shard in shards:
        _safe_write_json_path(root, staging / "shards" / f"{shard['shard_id']}.json", shard, "publication_shard")
    _safe_write_json_path(root, staging / "revision.json", revision, "publication_revision")
    _write_jsonl(staging / "source-span-links.jsonl", links)
    spans = _project_spans(root, snapshot_id, links)
    _write_jsonl(staging / "source-span-projection.jsonl", spans)
    _safe_write_json_path(root, staging / "receipt.json", receipt, "publication_receipt")
    if os.environ.get("NOLLM_MT1_FORCE_FAIL_BEFORE_ACTIVATION_RECORD") == "1":
        raise RuntimeError("forced_failure_before_activation_record")
    _safe_write_json_path(root, staging / "activation.json", _activation_record(root, staging, revision, receipt, snapshot_id, source_policy_id), "publication_activation")
    tree_errors = _tree_regular_errors(staging, "field_staging")
    if tree_errors:
        raise ValueError(",".join(tree_errors))
    _safe_write_json_path(root, staging / "publication-manifest.json", _publication_manifest(staging, revision, receipt, snapshot_id), "publication_manifest")
    return staging


def _activation_record(root: Path, staging: Path, revision: dict[str, Any], receipt: dict[str, Any], snapshot_id: str, source_policy_id: str) -> dict[str, Any]:
    archive_manifest = load_manifest(root, snapshot_id)
    return {
        "schema": ACTIVATION_SCHEMA,
        "field_id": revision["field_id"],
        "field_revision_id": revision["field_revision_id"],
        "batch_id": receipt["batch_id"],
        "snapshot_id": snapshot_id,
        "source_policy_id": source_policy_id,
        "archive_manifest_schema": archive_manifest.get("schema"),
        "archive_manifest_hash": archive_manifest.get("archive_manifest_hash", archive_manifest.get("manifest_hash")),
        "receipt_hash": _safe_hash_under_root(root, staging / "receipt.json", "publication_receipt"),
        "revision_hash": _safe_hash_under_root(root, staging / "revision.json", "publication_revision"),
        "source_span_links_hash": _safe_hash_under_root(root, staging / "source-span-links.jsonl", "source_span_links"),
        "source_span_projection_hash": _safe_hash_under_root(root, staging / "source-span-projection.jsonl", "source_span_projection"),
        "legacy_import_profile": LEGACY_IMPORT_PROFILE,
    }


def _publish_package(root: Path, batch_id: str, field_revision_id: str) -> Path:
    staging, staging_errors = contained_path(root, "field", ".staging", batch_id, "publication", label="field_staging", must_exist=True, require_file=False)
    if staging_errors:
        raise ValueError(",".join(staging_errors))
    publication, publication_errors = contained_path(root, "field", "publications", field_revision_id, label="field_publication", must_exist=False, require_file=False)
    if publication_errors:
        raise ValueError(",".join(publication_errors))
    if publication.exists() and publication.is_symlink():
        raise ValueError("path_symlink:field_publication")
    if publication.exists():
        raise ValueError("path_exists:field_publication")
    tree_errors = _tree_regular_errors(staging, "field_staging")
    if tree_errors:
        raise ValueError(",".join(tree_errors))
    _safe_copy_tree(root, staging, publication, label="field_publication")
    copied_errors = _tree_regular_errors(publication, "field_publication")
    if copied_errors:
        raise ValueError(",".join(copied_errors))
    return publication


def _safe_copy_tree(root: Path, staging: Path, publication: Path, *, label: str) -> None:
    safe_mkdirs(root, tuple(publication.relative_to(root).parts), label=label)
    for path in sorted(staging.rglob("*")):
        rel = path.relative_to(staging)
        target_parts = tuple((publication / rel).relative_to(root).parts)
        if path.is_symlink():
            raise ValueError(f"path_symlink:{label}:{rel.as_posix()}")
        if path.is_dir():
            safe_mkdirs(root, target_parts, label=label)
            continue
        if not path.is_file():
            raise ValueError(f"path_not_regular:{label}:{rel.as_posix()}")
        source_parts = tuple(path.relative_to(root).parts)
        data = safe_read_regular(root, *source_parts, label=f"{label}_source")
        safe_atomic_write(root, target_parts, data, label=f"{label}_artifact", replace=False)


def _acquire_writer_lock(root: Path, batch_id: str, *, reclaim_stale: bool = True) -> tuple[Path | None, dict[str, Any] | None]:
    lock_dir, lock_errors = contained_path(root, "locks", "legacy-import-writer.lock", label="writer_lock", must_exist=False, require_file=False)
    if lock_errors:
        return None, {"ok": False, "batch_id": batch_id, "state": "retry_required", "retry_required": True, "errors": lock_errors}
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_dir.mkdir()
    except FileExistsError:
        if reclaim_stale and _reclaim_stale_lock(lock_dir):
            try:
                lock_dir.mkdir()
            except FileExistsError:
                pass
            else:
                _write_lock_owner(root, lock_dir, batch_id)
                return lock_dir, None
        return None, {
            "ok": False,
            "batch_id": batch_id,
            "state": "retry_required",
            "retry_required": True,
            "errors": ["writer_busy"],
        }
    try:
        _write_lock_owner(root, lock_dir, batch_id)
    except Exception:
        try:
            lock_dir.rmdir()
        except OSError:
            pass
        raise
    return lock_dir, None


def _reclaim_stale_lock(lock_dir: Path) -> bool:
    owner = lock_dir / "owner.json"
    try:
        if not lock_dir.is_dir() or lock_dir.is_symlink():
            return False
        if not owner.exists() or owner.is_symlink():
            return False
        data = read_json(owner)
        acquired_at = data.get("acquired_at") if isinstance(data, dict) else None
        if not isinstance(acquired_at, str) or not _is_utc_timestamp(acquired_at):
            return False
        owner_pid = data.get("owner_pid")
        if not isinstance(owner_pid, int) or _pid_is_alive(owner_pid):
            return False
        acquired = datetime.fromisoformat(acquired_at[:-1] + "+00:00")
        age_seconds = (datetime.now(acquired.tzinfo) - acquired).total_seconds()
        if age_seconds < 3600:
            return False
        owner.unlink()
        lock_dir.rmdir()
        return True
    except Exception:
        return False


def _write_lock_owner(root: Path, lock_dir: Path, batch_id: str) -> str:
    token = "fence_" + uuid.uuid4().hex
    _safe_write_json_path(
        root,
        lock_dir / "owner.json",
        {
            "schema": "nollm.legacy_import_writer_lock.v2",
            "batch_id": batch_id,
            "acquired_at": utc_now(),
            "owner_pid": os.getpid(),
            "owner_identity": _owner_identity(),
            "fencing_token": token,
        },
        "writer_lock_owner",
    )
    return token


def _current_fencing_token(root: Path) -> str:
    owner, errors = _read_json_safe(root / "locks" / "legacy-import-writer.lock" / "owner.json", "writer_lock_owner")
    if errors or not isinstance(owner, dict) or not isinstance(owner.get("fencing_token"), str):
        raise RuntimeError("writer_fencing_token_missing")
    return str(owner["fencing_token"])


def _owner_identity() -> str:
    return f"pid:{os.getpid()}"


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        process_query_limited_information = 0x1000
        still_active = 259
        handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _release_writer_lock(lock_dir: Path | None) -> None:
    if lock_dir is None:
        return
    owner = lock_dir / "owner.json"
    try:
        if owner.exists() and not owner.is_symlink():
            owner.unlink()
        lock_dir.rmdir()
    except OSError:
        # A retained lock directory is safer than blind deletion of unexpected contents.
        return


def _pre_head_publication_errors(root: Path, publication: Path, revision_id: str, field_id: str) -> list[str]:
    errors: list[str] = []
    manifest, manifest_errors = _read_json_safe(publication / "publication-manifest.json", "publication_manifest")
    errors.extend(manifest_errors)
    activation, activation_errors = _read_json_safe(publication / "activation.json", "publication_activation")
    errors.extend(activation_errors)
    errors.extend(validate_publication_manifest_closure(publication))
    errors.extend(validate_publication_semantics(publication, expected_revision_id=revision_id, expected_field_id=field_id))
    if isinstance(manifest, dict):
        errors.extend(validate_publication_activation(publication, manifest=manifest))
    else:
        errors.append("invalid_publication_manifest")
    if isinstance(activation, dict):
        errors.extend(validate_legacy_import_shard_profile(root, publication, activation))
    else:
        errors.append("invalid_publication_activation")
    return errors


def _safe_hash_under_root(root: Path, path: Path, label: str) -> str:
    try:
        parts = path.relative_to(root).parts
    except ValueError as exc:
        raise ValueError(f"path_escape:{label}") from exc
    return "sha256:" + sha256_bytes(safe_read_regular(root, *parts, label=label))


def _read_head_bytes(root: Path) -> bytes | None:
    target, errors = contained_path(root, "field", "HEAD.json", label="field_head", must_exist=False, require_file=True)
    if errors:
        raise ValueError(",".join(errors))
    if not target.exists():
        return None
    return safe_read_regular(root, "field", "HEAD.json", label="field_head")


def _write_head_atomic(root: Path, head: dict[str, Any], *, expected_prior_head_bytes: bytes | None | object = _NO_HEAD_EXPECTATION, fencing_token: str = "") -> None:
    target, target_errors = contained_path(root, "field", "HEAD.json", label="field_head", must_exist=False, require_file=True)
    tmp, tmp_errors = contained_path(root, "field", "HEAD.json.tmp", label="field_head_tmp", must_exist=False, require_file=True)
    errors = target_errors + tmp_errors
    errors.extend(ensure_contained_parent(root, target, "field_head"))
    errors.extend(ensure_contained_parent(root, tmp, "field_head_tmp"))
    if errors:
        raise ValueError(",".join(errors))
    if os.environ.get("NOLLM_MT1_FORCE_FAIL_DURING_HEAD_PREPARATION") == "1":
        raise OSError("forced_failure_during_head_preparation")
    if expected_prior_head_bytes is not _NO_HEAD_EXPECTATION:
        _assert_current_fencing_token(root, fencing_token)
        if os.environ.get("NOLLM_MT1_FORCE_HEAD_CHANGED_BEFORE_WRITE") == "1":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('{"forced":"head_changed"}\n', encoding="utf-8")
        if _read_head_bytes(root) != expected_prior_head_bytes:
            raise RuntimeError("head_changed")
    _safe_write_json_path(root, tmp, head, "field_head_tmp")
    safe_atomic_write(root, ("field", "HEAD.json"), _head_json_bytes(head), label="field_head", replace=True)
    if fencing_token:
        _assert_current_fencing_token(root, fencing_token)


def _write_publish_journal(
    root: Path,
    batch_id: str,
    revision_id: str,
    manifest_hash: str,
    activation_hash: str,
    prior_head: dict[str, Any] | None,
    prior_head_bytes: bytes | None | object,
    candidate_head: dict[str, Any],
    fencing_token: str,
) -> str:
    prior_bytes = None if prior_head_bytes is _NO_HEAD_EXPECTATION else prior_head_bytes
    prior_hash = "sha256:" + sha256_bytes(prior_bytes) if prior_bytes is not None else None
    candidate_bytes = _head_json_bytes(candidate_head)
    candidate_hash = "sha256:" + sha256_bytes(candidate_bytes)
    transaction_id = _publish_transaction_id(batch_id, revision_id, manifest_hash, activation_hash, prior_hash, candidate_hash, fencing_token)
    journal, journal_errors = contained_path(root, "field", "publish-journal", f"{transaction_id}.json", label="publish_journal", must_exist=False, require_file=True)
    if journal_errors:
        raise ValueError(",".join(journal_errors))
    _safe_write_json_path(
        root,
        journal,
        {
            "schema": "nollm.publish_journal.v1",
            "publish_transaction_id": transaction_id,
            "batch_id": batch_id,
            "candidate_revision_id": revision_id,
            "candidate_manifest_hash": manifest_hash,
            "candidate_activation_hash": activation_hash,
            "candidate_head_bytes_sha256": candidate_hash,
            "prior_head": prior_head,
            "prior_head_bytes_sha256": prior_hash,
            "prior_head_bytes_b64": base64.b64encode(prior_bytes).decode("ascii") if prior_bytes is not None else None,
            "prior_head_absent": prior_bytes is None,
            "fencing_token": fencing_token,
            "created_at": utc_now(),
        },
        "publish_journal",
    )
    return transaction_id


def _publish_transaction_id(batch_id: str, revision_id: str, manifest_hash: str, activation_hash: str, prior_hash: object, candidate_hash: object = None, fencing_token: object = None) -> str:
    transaction_seed = canonical_json(
        {
            "batch_id": batch_id,
            "candidate_activation_hash": activation_hash,
            "candidate_head_bytes_sha256": candidate_hash,
            "candidate_manifest_hash": manifest_hash,
            "candidate_revision_id": revision_id,
            "fencing_token": fencing_token,
            "prior_head_bytes_sha256": prior_hash,
        }
    )
    return "pubtx_" + sha256_bytes(transaction_seed)[:24]


def _write_publish_handoff(batch_dir: Path, batch_id: str, revision_id: str, manifest_hash: str, activation_hash: str, prior_head: dict[str, Any] | None, publish_transaction_id: str, candidate_head: dict[str, Any], prior_head_bytes: bytes | None | object, fencing_token: str) -> None:
    prior_bytes = None if prior_head_bytes is _NO_HEAD_EXPECTATION else prior_head_bytes
    _safe_write_json_path(
        _root_from_batch_dir(batch_dir),
        batch_dir / "publish-handoff.json",
        {
            "schema": "nollm.legacy_import_publish_handoff.v1",
            "batch_id": batch_id,
            "candidate_revision_id": revision_id,
            "candidate_manifest_hash": manifest_hash,
            "candidate_activation_hash": activation_hash,
            "candidate_head_bytes_sha256": "sha256:" + sha256_bytes(_head_json_bytes(candidate_head)),
            "publish_transaction_id": publish_transaction_id,
            "prior_head": prior_head,
            "prior_head_bytes_sha256": "sha256:" + sha256_bytes(prior_bytes) if prior_bytes is not None else None,
            "fencing_token": fencing_token,
            "publish_started_at": utc_now(),
        },
        "publish_handoff",
    )


def _head_json_bytes(head: dict[str, Any]) -> bytes:
    return json.dumps(head, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8") + b"\n"


def _assert_current_fencing_token(root: Path, fencing_token: str) -> None:
    if not fencing_token:
        raise RuntimeError("writer_fencing_token_missing")
    if _current_fencing_token(root) != fencing_token:
        raise RuntimeError("writer_fencing_token_mismatch")


def _restore_head(root: Path, prior_head: dict[str, Any] | None) -> None:
    target, errors = contained_path(root, "field", "HEAD.json", label="field_head", must_exist=False, require_file=True)
    if errors:
        raise ValueError(",".join(errors))
    if prior_head:
        _write_head_atomic(root, prior_head)
    elif target.exists():
        target.unlink()


def _quarantine_and_restore_head(root: Path, batch_dir: Path, prior_head: dict[str, Any] | None, reason: str) -> None:
    restored = _restore_head_cas(root, batch_dir, prior_head)
    _write_state(batch_dir, "quarantined")
    record = {"schema": "nollm.legacy_import_quarantine.v1", "batch_id": batch_dir.name, "timestamp": utc_now(), "reason": reason, "state": "quarantined", "head_restored": restored}
    _safe_write_json_path(root, batch_dir / "quarantine.json", record, "quarantine")
    if not restored:
        _safe_write_json_path(root, batch_dir / "recovery-conflict.json", {"schema": "nollm.legacy_import_recovery_conflict.v1", "batch_id": batch_dir.name, "timestamp": utc_now(), "reason": "head_conflict", "state": "recovery_required"}, "recovery_conflict")
    try:
        _append_ledger_event(root, {"op": "legacy_import_quarantine", **record})
    except ValueError:
        pass


def _restore_head_cas(root: Path, batch_dir: Path, prior_head: dict[str, Any] | None) -> bool:
    handoff, handoff_errors = _read_json_safe(batch_dir / "publish-handoff.json", "publish_handoff")
    if handoff_errors or not isinstance(handoff, dict):
        return False
    fencing_token = str(handoff.get("fencing_token", ""))
    try:
        _assert_current_fencing_token(root, fencing_token)
    except Exception:
        return False
    expected_candidate_hash = handoff.get("candidate_head_bytes_sha256")
    current = _read_head_bytes(root)
    current_hash = "sha256:" + sha256_bytes(current) if current is not None else None
    if current_hash != expected_candidate_hash:
        return False
    target, errors = contained_path(root, "field", "HEAD.json", label="field_head", must_exist=False, require_file=True)
    if errors:
        return False
    if prior_head:
        _write_head_atomic(root, prior_head, expected_prior_head_bytes=current, fencing_token=fencing_token)
    elif target.exists():
        target.unlink()
    return True


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
    _safe_write_json_path(root, batch_dir / "migration-report.json", report, "migration_report")
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


@_with_ledger_lock
def _ensure_ledger_event(path: Path, event: dict[str, Any]) -> None:
    root = path.parents[1]
    existing_errors = _ledger_errors(root)
    if existing_errors:
        raise ValueError(",".join(existing_errors))
    event_id = event.get("event_id")
    if path.exists():
        for record in _read_jsonl(path):
            if record.get("event_id") == event_id:
                return
    _append_ledger_event(root, event)


def _has_finalization_ledger_event(root: Path, receipt: dict[str, Any]) -> bool:
    path = root / "ledger" / "events.jsonl"
    event_id = _finalization_event_id(receipt)
    if not path.exists():
        return False
    try:
        return any(record.get("event_id") == event_id for record in _read_jsonl(path))
    except (JSONDecodeError, OSError, ValueError):
        return False


def _ledger_path(root: Path, *, must_exist: bool = False) -> tuple[Path, list[str]]:
    return contained_path(root, "ledger", "events.jsonl", label="ledger_events", must_exist=must_exist, require_file=True)


def _ledger_errors(root: Path) -> list[str]:
    path, path_errors = _ledger_path(root, must_exist=False)
    if path_errors:
        return path_errors
    if not path.exists():
        return []
    try:
        if path.exists():
            read_jsonl_bytes(safe_read_regular(root, "ledger", "events.jsonl", label="ledger_events"), "ledger")
    except JSONDecodeError:
        return ["malformed_jsonl:ledger"]
    except SafeStorageError as exc:
        message = str(exc)
        if message.startswith("malformed_json:"):
            return ["malformed_jsonl:ledger"]
        return [message]
    except OSError as exc:
        return [f"unreadable_jsonl:ledger:{exc.__class__.__name__}"]
    except Exception as exc:
        return [f"invalid_jsonl:ledger:{exc.__class__.__name__}"]
    return []


@_with_ledger_lock
def _append_ledger_event(root: Path, event: dict[str, Any]) -> None:
    path, path_errors = _ledger_path(root, must_exist=False)
    if path_errors:
        raise ValueError(",".join(path_errors))
    existing_errors = _ledger_errors(root)
    if existing_errors:
        raise ValueError(",".join(existing_errors))
    safe_append_jsonl(root, ("ledger", "events.jsonl"), event, label="ledger_events")


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
    memory_root = _infer_root_for_path(root)
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"publication_symlink:{path.relative_to(root).as_posix()}")
        if path.is_file() and path.name != "publication-manifest.json":
            parts = path.relative_to(memory_root).parts
            hashes[path.relative_to(root).as_posix()] = "sha256:" + sha256_bytes(safe_read_regular(memory_root, *parts, label="publication_artifact"))
    return {
        "schema": "nollm.publication_manifest.v1",
        "field_revision_id": revision["field_revision_id"],
        "field_id": revision["field_id"],
        "batch_id": receipt["batch_id"],
        "snapshot_id": snapshot_id,
        "artifact_hashes": hashes,
    }


def _tree_regular_errors(root: Path, label: str) -> list[str]:
    errors: list[str] = []
    if root.is_symlink():
        return [f"path_symlink:{label}"]
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            errors.append(f"path_symlink:{label}:{rel}")
        elif path.is_file():
            continue
        elif path.is_dir():
            continue
        else:
            errors.append(f"path_not_regular:{label}:{rel}")
    return errors


def _load_state(batch_dir: Path) -> dict[str, Any]:
    path = batch_dir / "state.json"
    if not path.exists():
        return {"state": "planned"}
    return read_json(path)



_VALID_BATCH_STATES = frozenset({"planned", "staged", "validated", "publishing", "committed", "failed", "quarantined"})
_VALID_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _is_valid_utc_timestamp(value: str) -> bool:
    if not isinstance(value, str) or not _VALID_TS_RE.match(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def _load_state_safe(batch_dir: Path) -> tuple[dict[str, Any], list[str]]:
    path = batch_dir / "state.json"
    if not path.exists():
        return {"state": "planned"}, []
    data, errors = _read_json_safe(path, "state")
    if errors:
        return {"state": "unknown"}, errors
    if not isinstance(data, dict) or not isinstance(data.get("state"), str):
        return {"state": "unknown"}, ["invalid_state"]
    if data["state"] not in _VALID_BATCH_STATES:
        return {"state": "unknown"}, [f"invalid_state_enum:{data['state']}"]
    updated = data.get("updated_at")
    if not isinstance(updated, str) or not _is_valid_utc_timestamp(updated):
        return {"state": "unknown"}, ["invalid_state_timestamp"]
    unknown = _unknown_fields(data, STATE_FIELDS, "state")
    if unknown:
        return {"state": "unknown"}, unknown
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


def _structured_exception(label: str, exc: Exception) -> str:
    if isinstance(exc, JSONDecodeError):
        return f"malformed_json:{label}"
    if isinstance(exc, ValueError):
        return str(exc)
    if isinstance(exc, OSError):
        return f"unreadable:{label}"
    return f"invalid:{label}:{exc.__class__.__name__}"


def _unknown_fields(record: dict[str, Any], allowed: set[str], label: str) -> list[str]:
    return [f"unknown_{label}_field:{field}" for field in sorted(set(record) - allowed)]


def _force_write_state(batch_dir: Path, state: str) -> None:
    _safe_write_json_path(_root_from_batch_dir(batch_dir), batch_dir / "state.json", {"state": state, "updated_at": utc_now()}, "state")


def _untrusted_ingress_result(root: Path, batch_dir: Path, batch_id: str, errors: list[str]) -> dict[str, Any]:
    handoff, handoff_errors = _read_json_safe(batch_dir / "publish-handoff.json", "publish_handoff")
    if isinstance(handoff, dict) and not handoff_errors:
        _force_write_state(batch_dir, "quarantined")
        record = {"schema": "nollm.legacy_import_quarantine.v1", "batch_id": batch_id, "timestamp": utc_now(), "reason": "untrusted_ingress:" + ",".join(errors), "state": "quarantined"}
        _safe_write_json_path(root, batch_dir / "quarantine.json", record, "quarantine")
        try:
            _append_ledger_event(root, {"op": "legacy_import_quarantine", **record})
        except ValueError:
            pass
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
    _safe_write_json_path(_root_from_batch_dir(batch_dir), batch_dir / "state.json", {"state": state, "updated_at": utc_now()}, "state")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    from .safe_storage import safe_read_file
    return read_jsonl_bytes(safe_read_file(path, label=path.name, require_private=False), path.name)


def _read_jsonl_strict(path: Path, label: str) -> list[dict[str, Any]]:
    from .safe_storage import safe_read_file
    return read_jsonl_bytes(safe_read_file(path, label=label, require_private=False), label)


def _read_jsonl_safe(path: Path, label: str) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], [f"missing_{label}"]
    records: list[dict[str, Any]] = []
    try:
        from .safe_storage import safe_read_file, read_jsonl_bytes
        raw = safe_read_file(path, label=label, require_private=False)
        records = read_jsonl_bytes(raw, label)
    except Exception as exc:
        msg = str(exc)
        if "malformed_json" in msg:
            return [], [f"malformed_jsonl:{label}"]
        return [], [f"unreadable_jsonl:{label}:{exc.__class__.__name__}"]
    return records, []


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    root = _root_from_batch_dir(path.parent) if "ingress" in path.parts else _infer_root_for_path(path)
    try:
        parts = path.resolve(strict=False).relative_to(root.resolve()).parts
    except ValueError as exc:
        raise ValueError("path_escape:jsonl") from exc
    safe_atomic_jsonl(root, parts, records, label=path.stem)
