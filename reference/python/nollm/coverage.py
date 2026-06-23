from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .archive import archive_sources, existing_memory_root_path, load_manifest
from .archive_manifest import read_json
from .native_field import current_publication
from .source_spans import ALLOWED_DISPOSITIONS, NON_MEMORY_REASONS, load_source_spans


def validate_source_coverage(memory_root: Path | str, snapshot_id: str, *, require_linked: bool = False) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return _coverage_error(snapshot_id, str(exc))
    try:
        manifest = load_manifest(root, snapshot_id)
        spans = _published_spans(root, snapshot_id) if require_linked else load_source_spans(root, snapshot_id)
    except JSONDecodeError:
        return _coverage_error(snapshot_id, "malformed_json:source_span_inventory" if not require_linked else "malformed_json:published_source_span_projection")
    except Exception as exc:
        return _coverage_error(snapshot_id, f"invalid_source_coverage_input:{exc.__class__.__name__}")
    by_object: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for span in spans:
        by_object.setdefault((str(span.get("source_object_id")), str(span["original_relative_path"])), []).append(span)
    errors: list[str] = []
    total = 0
    covered = 0
    unsupported = 0
    manual_review = 0
    pending = 0
    sharded_without_links = 0
    for obj in archive_sources(manifest):
        key = (str(obj.get("source_object_id")), str(obj["original_relative_path"]))
        current = 0
        object_spans = sorted(by_object.get(key, []), key=lambda item: int(item["start_byte"]))
        if not object_spans and obj.get("byte_length", 0) != 0:
            errors.append(f"missing_spans:{key[1]}")
        for span in object_spans:
            total += 1
            if type(span.get("start_byte")) is not int or type(span.get("end_byte_exclusive")) is not int:
                errors.append(f"invalid_span_integer:{key[1]}:{span.get('span_id')}")
                continue
            start = int(span["start_byte"])
            end = int(span["end_byte_exclusive"])
            if start != current:
                errors.append(f"coverage_gap_or_overlap:{key[1]}:{current}-{start}")
            if end < start:
                errors.append(f"negative_span:{key[1]}:{start}-{end}")
            current = end
            disposition = span.get("disposition")
            if disposition not in ALLOWED_DISPOSITIONS:
                errors.append(f"unknown_disposition:{key[1]}:{disposition}")
            elif disposition == "unsupported":
                unsupported += 1
            elif disposition == "manual_review":
                manual_review += 1
            elif disposition == "classified_pending":
                pending += 1
                if require_linked:
                    errors.append(f"pending_span_not_linked:{span.get('span_id')}")
                else:
                    covered += 1
            elif disposition == "non_memory":
                if span.get("reason") not in NON_MEMORY_REASONS:
                    errors.append(f"invalid_non_memory_reason:{span.get('span_id')}:{span.get('reason')}")
                covered += 1
            elif disposition == "sharded":
                if not span.get("related_shard_ids"):
                    sharded_without_links += 1
                    errors.append(f"sharded_span_without_related_shards:{span.get('span_id')}")
                covered += 1
            else:
                covered += 1
        if current != int(obj.get("byte_length", 0)):
            errors.append(f"coverage_does_not_reach_eof:{key[1]}:{current}!={obj.get('byte_length')}")
    ratio = 1.0 if total == 0 else covered / total
    return {
        "ok": not errors and unsupported == 0 and manual_review == 0,
        "snapshot_id": snapshot_id,
        "coverage_ratio": ratio,
        "total_source_spans": total,
        "covered_source_spans": covered,
        "uncovered_source_spans": len([error for error in errors if "coverage" in error or "missing" in error]),
        "unsupported": unsupported,
        "manual_review": manual_review,
        "classified_pending": pending,
        "sharded_without_links": sharded_without_links,
        "errors": errors,
    }


def _published_spans(root: Path, snapshot_id: str) -> list[dict[str, Any]]:
    publication = current_publication(root)
    if not publication:
        return []
    receipt_path = publication / "receipt.json"
    projection_path = publication / "source-span-projection.jsonl"
    if not receipt_path.exists() or not projection_path.exists():
        return []
    from .safe_storage import safe_read_regular, read_json_bytes
    rel_parts = tuple(receipt_path.resolve().relative_to(root.resolve()).parts)
    receipt = read_json_bytes(safe_read_regular(root, *rel_parts, label="publication_receipt", require_private_inode=False), "publication_receipt")
    if receipt.get("snapshot_id") != snapshot_id:
        return []
    proj_parts = tuple(projection_path.resolve().relative_to(root.resolve()).parts)
    return [json.loads(line) for line in safe_read_regular(root, *proj_parts, label="source_span_projection", require_private_inode=False).decode("utf-8").splitlines() if line.strip()]


def _coverage_error(snapshot_id: str, error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "snapshot_id": snapshot_id,
        "coverage_ratio": 0.0,
        "total_source_spans": 0,
        "covered_source_spans": 0,
        "uncovered_source_spans": 0,
        "unsupported": 0,
        "manual_review": 0,
        "classified_pending": 0,
        "sharded_without_links": 0,
        "errors": [error],
    }
