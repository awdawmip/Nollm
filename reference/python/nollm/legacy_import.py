from __future__ import annotations

import json
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
    move_staged_shards,
    publish_field_revision,
    shard_id_for,
    stage_shards,
)
from .source_spans import build_source_span_inventory


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
    request = {
        "schema": IMPORT_SCHEMA,
        "batch_id": batch_id,
        "snapshot_id": snapshot_id,
        "target_field_id": target_field_id,
        "source_policy_id": manifest.get("source_policy_id"),
        "created_at": utc_now(),
        "extraction_count": len(extracted),
        "commit_state": "planned",
    }
    write_json(batch_dir / "import-request.json", request)
    _write_jsonl(batch_dir / "extraction.jsonl", extracted)
    write_json(batch_dir / "migration-report.json", _migration_report(root, batch_id, request, dry_run=True))
    return {"ok": True, "batch_id": batch_id, "snapshot_id": snapshot_id, "extraction_count": len(extracted), "batch_dir": str(batch_dir)}


def run_legacy_import(memory_root: Path | str, batch_id: str, *, dry_run: bool = False, commit: bool = False) -> dict[str, Any]:
    if dry_run == commit:
        return {"ok": False, "batch_id": batch_id, "errors": ["choose exactly one of dry_run or commit"]}
    root = memory_root_path(memory_root)
    batch_dir = _batch_dir(root, batch_id)
    request = read_json(batch_dir / "import-request.json")
    archive = verify_archive_snapshot(root, str(request["snapshot_id"]))
    coverage = validate_source_coverage(root, str(request["snapshot_id"]))
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
    stage_shards(root, batch_id, shards)
    shard_ids = move_staged_shards(root, batch_id)
    revision = publish_field_revision(root, batch_id=batch_id, target_field_id=str(request["target_field_id"]), shard_ids=shard_ids)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "batch_id": batch_id,
        "snapshot_id": request["snapshot_id"],
        "target_field_id": request["target_field_id"],
        "committed_at": utc_now(),
        "created_shard_ids": shard_ids,
        "created_shard_count": len(shard_ids),
        "duplicate_count": duplicate_count,
        "field_revision_id": revision["field_revision_id"],
    }
    write_json(batch_dir / "import-receipt.json", receipt)
    request["commit_state"] = "committed"
    write_json(batch_dir / "import-request.json", request)
    write_json(batch_dir / "migration-report.json", _migration_report(root, batch_id, request, receipt=receipt, duplicate_count=duplicate_count))
    append_jsonl(root / "ledger" / "events.jsonl", {"op": "legacy_import_commit", "batch_id": batch_id, "timestamp": utc_now(), "receipt": receipt})
    return {"ok": True, "batch_id": batch_id, "committed": True, "created_shard_count": len(shard_ids), "duplicate_count": duplicate_count, "field_revision_id": revision["field_revision_id"]}


def validate_legacy_import(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    errors: list[str] = []
    batch_dir = _batch_dir(root, batch_id)
    request = read_json(batch_dir / "import-request.json")
    archive = verify_archive_snapshot(root, str(request["snapshot_id"]))
    coverage = validate_source_coverage(root, str(request["snapshot_id"]))
    errors.extend(archive.get("errors", []))
    errors.extend(coverage.get("errors", []))
    receipt_path = batch_dir / "import-receipt.json"
    if receipt_path.exists():
        receipt = read_json(receipt_path)
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
    return {"ok": not errors, "batch_id": batch_id, "errors": errors}


def legacy_import_report(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    request = read_json(_batch_dir(root, batch_id) / "import-request.json")
    report_path = _batch_dir(root, batch_id) / "migration-report.json"
    report = read_json(report_path) if report_path.exists() else _migration_report(root, batch_id, request)
    report["validation"] = validate_legacy_import(root, batch_id) if (_batch_dir(root, batch_id) / "import-receipt.json").exists() else {"ok": False, "errors": ["not_committed"]}
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
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
