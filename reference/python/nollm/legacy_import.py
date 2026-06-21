from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .archive import load_manifest, memory_root_path, utc_now, verify_archive_snapshot
from .archive_manifest import canonical_json, read_json, sha256_bytes, write_json
from .coverage import validate_source_coverage
from .legacy_extract import extract_legacy_spans, idempotence_key
from .native_field import (
    append_jsonl,
    build_shard,
    existing_shards_by_key,
    load_field_head,
    shard_id_for,
    stage_shards,
    write_jsonl,
)
from .provenance import build_source_span_links, validate_deep_provenance
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
    request = read_json(batch_dir / "import-request.json")
    state = _load_state(batch_dir)
    receipt_path = batch_dir / "import-receipt.json"
    if commit and state["state"] == "committed" and receipt_path.exists():
        receipt = read_json(receipt_path)
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
    manifest = load_manifest(root, str(request["snapshot_id"]))
    source_policy_id = str(manifest["source_policy_id"])
    extracted = _read_jsonl(batch_dir / "extraction.jsonl")
    existing = existing_shards_by_key(root)
    shards = []
    duplicate_count = 0
    for record in extracted:
        key = idempotence_key(record, source_policy_id)
        if key in existing:
            duplicate_count += 1
            continue
        shards.append(build_shard(record, batch_id=batch_id, source_policy_id=source_policy_id, idempotence_key=key))
    if dry_run:
        report = _migration_report(root, batch_id, request, dry_run=True, candidate_shards=shards, duplicate_count=duplicate_count)
        write_json(batch_dir / "dry-run-report.json", report)
        return {"ok": True, "batch_id": batch_id, "dry_run": True, "candidate_shard_count": len(shards), "duplicate_count": duplicate_count}
    _write_state(batch_dir, "validated")
    append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_validate_staging", "batch_id": batch_id, "timestamp": utc_now(), "state": "validated"})
    stage_shards(root, batch_id, shards)
    revision = _revision_candidate(root, batch_id=batch_id, target_field_id=str(request["target_field_id"]), shard_ids=[str(shard["shard_id"]) for shard in shards])
    links = build_source_span_links(snapshot_id=str(request["snapshot_id"]), batch_id=batch_id, field_revision_id=str(revision["field_revision_id"]), shards=shards)
    _publish_pre_head(root, batch_id, revision, shards, links, str(request["snapshot_id"]))
    if os.environ.get("NOLLM_MT1_FORCE_FAIL_BEFORE_HEAD") == "1":
        _write_state(batch_dir, "failed")
        append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_failure", "batch_id": batch_id, "timestamp": utc_now(), "state": "failed", "reason": "forced_before_head"})
        return {"ok": False, "batch_id": batch_id, "errors": ["forced_failure_before_head"], "state": "failed"}
    provenance = validate_deep_provenance(root, str(request["snapshot_id"]), str(revision["field_revision_id"]))
    if not provenance.get("ok"):
        _write_state(batch_dir, "failed")
        append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_failure", "batch_id": batch_id, "timestamp": utc_now(), "state": "failed", "errors": provenance.get("errors", [])})
        return {"ok": False, "batch_id": batch_id, "errors": provenance.get("errors", []), "state": "failed"}
    write_json(root / "field" / "HEAD.json", {"field_id": request["target_field_id"], "field_revision_id": revision["field_revision_id"]})
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "batch_id": batch_id,
        "snapshot_id": request["snapshot_id"],
        "target_field_id": request["target_field_id"],
        "committed_at": utc_now(),
        "created_shard_ids": [str(shard["shard_id"]) for shard in shards],
        "created_shard_count": len(shards),
        "duplicate_count": duplicate_count,
        "field_revision_id": revision["field_revision_id"],
    }
    write_json(batch_dir / "import-receipt.json", receipt)
    _write_state(batch_dir, "committed")
    write_json(batch_dir / "migration-report.json", _migration_report(root, batch_id, request, receipt=receipt, duplicate_count=duplicate_count))
    append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_commit", "batch_id": batch_id, "timestamp": utc_now(), "receipt": receipt})
    return {"ok": True, "batch_id": batch_id, "committed": True, "created_shard_count": len(shards), "duplicate_count": duplicate_count, "field_revision_id": revision["field_revision_id"], "state": "committed"}


def validate_legacy_import(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    errors: list[str] = []
    batch_dir = _batch_dir(root, batch_id)
    request = read_json(batch_dir / "import-request.json")
    archive = verify_archive_snapshot(root, str(request["snapshot_id"]))
    coverage = validate_source_coverage(root, str(request["snapshot_id"]), require_linked=True)
    errors.extend(archive.get("errors", []))
    errors.extend(coverage.get("errors", []))
    receipt_path = batch_dir / "import-receipt.json"
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        provenance = validate_deep_provenance(root, str(request["snapshot_id"]), str(receipt.get("field_revision_id")))
        errors.extend(provenance.get("errors", []))
        for shard_id in receipt.get("created_shard_ids", []):
            shard_path = root / "field" / "shards" / f"{shard_id}.json"
            if not shard_path.exists():
                errors.append(f"missing_shard:{shard_id}")
                continue
            shard = read_json(shard_path)
            if not shard.get("source_refs") or not all(str(ref).startswith("archive://object/sha256:") for ref in shard.get("source_refs", [])):
                errors.append(f"invalid_source_refs:{shard_id}")
        head = load_field_head(root)
        if not head or head.get("field_revision_id") != receipt.get("field_revision_id"):
            errors.append("field_head_does_not_match_receipt")
    else:
        errors.append("missing_import_receipt")
    return {"ok": not errors, "batch_id": batch_id, "state": _load_state(batch_dir)["state"], "errors": errors}


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
    current = load_field_head(root)
    existing_ids: list[str] = []
    if current and current.get("field_id") == target_field_id:
        revision_path = root / "field" / "revisions" / f"{current['field_revision_id']}.json"
        if revision_path.exists():
            existing_ids = [str(item) for item in read_json(revision_path).get("shard_ids", [])]
    merged_ids = sorted(set(existing_ids).union(shard_ids))
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
    field_shards = root / "field" / "shards"
    field_shards.mkdir(parents=True, exist_ok=True)
    for shard in shards:
        write_json(field_shards / f"{shard['shard_id']}.json", shard)
    write_json(root / "field" / "revisions" / f"{revision['field_revision_id']}.json", revision)
    write_jsonl(root / "archive" / "source-span-links" / snapshot_id / f"{revision['field_revision_id']}.jsonl", links)
    mark_spans_linked(root, snapshot_id, links)
    write_json(root / "field" / ".staging" / batch_id / "receipt-candidate.json", {"field_revision_id": revision["field_revision_id"], "shard_count": len(shards)})


def _load_state(batch_dir: Path) -> dict[str, Any]:
    path = batch_dir / "state.json"
    if not path.exists():
        return {"state": "planned"}
    return read_json(path)


def _write_state(batch_dir: Path, state: str) -> None:
    current = _load_state(batch_dir)["state"]
    allowed = {
        "planned": {"planned", "validated", "failed", "quarantined"},
        "validated": {"validated", "committed", "failed", "quarantined"},
        "committed": {"committed"},
        "failed": {"failed", "validated"},
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
