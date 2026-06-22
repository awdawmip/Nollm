from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .archive import archive_sources, existing_memory_root_path, load_manifest, verify_archive_snapshot
from .archive_manifest import sha256_bytes
from .path_safety import contained_path, validate_snapshot_id
from .safe_storage import SafeStorageError, read_jsonl_bytes, safe_atomic_jsonl, safe_read_regular

SPAN_SCHEMA = "nollm.source_span_inventory.v1"
ALLOWED_DISPOSITIONS = {"classified_pending", "sharded", "non_memory", "manual_review", "unsupported"}
NON_MEMORY_REASONS = {"blank", "structural_heading"}
SPAN_FIELDS = {
    "content_hash",
    "disposition",
    "end_byte_exclusive",
    "epistemic_state",
    "lifecycle",
    "locator",
    "operational_state",
    "origin_kind",
    "original_relative_path",
    "reason",
    "related_shard_ids",
    "schema",
    "snapshot_id",
    "source_object_id",
    "span_id",
    "start_byte",
    "text_hash",
}


def build_source_span_inventory(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": [str(exc)]}
    id_errors = validate_snapshot_id(snapshot_id)
    if id_errors:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": id_errors}
    archive = verify_archive_snapshot(root, snapshot_id)
    if not archive.get("ok"):
        return {"ok": False, "snapshot_id": snapshot_id, "errors": archive.get("errors", [])}
    try:
        manifest = load_manifest(root, snapshot_id)
    except JSONDecodeError:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": ["malformed_json:archive_manifest"]}
    except Exception as exc:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": [f"invalid_archive_manifest:{exc.__class__.__name__}"]}
    records: list[dict[str, Any]] = []
    for source in archive_sources(manifest):
        digest = str(source["content_hash"]).removeprefix("sha256:")
        source_object_id = str(source["source_object_id"])
        object_path, object_errors = contained_path(root, "archive", "objects", "sha256", digest, label="archive_object", must_exist=True, require_file=True)
        if object_errors:
            return {"ok": False, "snapshot_id": snapshot_id, "errors": object_errors}
        try:
            data = safe_read_regular(root, "archive", "objects", "sha256", digest, label="archive_object")
        except SafeStorageError as exc:
            return {"ok": False, "snapshot_id": snapshot_id, "errors": [str(exc)]}
        for index, (start, end) in enumerate(_paragraph_ranges(data)):
            chunk = data[start:end]
            disposition, reason = _classify_span(chunk, source.get("encoding"))
            records.append(
                {
                    "schema": SPAN_SCHEMA,
                    "snapshot_id": snapshot_id,
                    "source_object_id": source_object_id,
                    "original_relative_path": source["original_relative_path"],
                    "content_hash": source["content_hash"],
                    "span_id": f"span_{source_object_id.removeprefix('src_')}_{index:04d}",
                    "start_byte": start,
                    "end_byte_exclusive": end,
                    "locator": _line_locator(data, start, end),
                    "text_hash": "sha256:" + sha256_bytes(chunk),
                    "origin_kind": source.get("origin_kind"),
                    "epistemic_state": source.get("epistemic_state"),
                    "operational_state": source.get("operational_state"),
                    "disposition": disposition,
                    "related_shard_ids": [],
                    "reason": reason,
                    "lifecycle": "classified",
                }
            )
    path, path_errors = contained_path(root, "archive", "source-spans", f"{snapshot_id}.jsonl", label="source_span_inventory", must_exist=False)
    if path_errors:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": path_errors}
    try:
        safe_atomic_jsonl(root, ("archive", "source-spans", f"{snapshot_id}.jsonl"), records, label="source_span_inventory")
    except SafeStorageError as exc:
        return {"ok": False, "snapshot_id": snapshot_id, "errors": [str(exc)]}
    return {"ok": True, "snapshot_id": snapshot_id, "span_count": len(records), "inventory_path": str(path)}


def load_source_spans(memory_root: Path | str, snapshot_id: str) -> list[dict[str, Any]]:
    root = existing_memory_root_path(memory_root)
    errors = validate_snapshot_id(snapshot_id)
    if errors:
        raise ValueError(errors[0])
    path, path_errors = contained_path(root, "archive", "source-spans", f"{snapshot_id}.jsonl", label="source_span_inventory", must_exist=True, require_file=True)
    if path_errors:
        raise ValueError(path_errors[0])
    try:
        records = read_jsonl_bytes(safe_read_regular(root, "archive", "source-spans", f"{snapshot_id}.jsonl", label="source_span_inventory"), "source_span_inventory")
    except SafeStorageError as exc:
        raise ValueError(str(exc)) from exc
    errors: list[str] = []
    for index, item in enumerate(records, start=1):
        errors.extend(validate_source_span_record(item, index=index))
    if errors:
        raise ValueError(",".join(errors))
    return records


def write_source_spans(memory_root: Path | str, snapshot_id: str, spans: list[dict[str, Any]]) -> None:
    root = existing_memory_root_path(memory_root)
    errors = validate_snapshot_id(snapshot_id)
    if errors:
        raise ValueError(errors[0])
    path, path_errors = contained_path(root, "archive", "source-spans", f"{snapshot_id}.jsonl", label="source_span_inventory", must_exist=False)
    if path_errors:
        raise ValueError(path_errors[0])
    for index, span in enumerate(spans, start=1):
        errors = validate_source_span_record(span, index=index)
        if errors:
            raise ValueError(",".join(errors))
    safe_atomic_jsonl(root, ("archive", "source-spans", f"{snapshot_id}.jsonl"), spans, label="source_span_inventory")


def mark_spans_linked(memory_root: Path | str, snapshot_id: str, links: list[dict[str, Any]]) -> None:
    by_span: dict[str, list[str]] = {}
    for link in links:
        by_span.setdefault(str(link["span_id"]), []).append(str(link["shard_id"]))
    spans = load_source_spans(memory_root, snapshot_id)
    for span in spans:
        related = sorted(set(by_span.get(str(span["span_id"]), [])))
        if related:
            span["disposition"] = "sharded"
            span["related_shard_ids"] = related
            span["lifecycle"] = "linked"
            span["reason"] = "linked_to_committed_shard"
    write_source_spans(memory_root, snapshot_id, spans)


def _paragraph_ranges(data: bytes) -> list[tuple[int, int]]:
    if not data:
        return [(0, 0)]
    ranges: list[tuple[int, int]] = []
    start = 0
    idx = 0
    while idx < len(data):
        if data.startswith(b"\r\n\r\n", idx):
            ranges.append((start, idx + 4))
            idx += 4
            start = idx
        elif data.startswith(b"\n\n", idx):
            ranges.append((start, idx + 2))
            idx += 2
            start = idx
        else:
            idx += 1
    if start < len(data):
        ranges.append((start, len(data)))
    return ranges or [(0, len(data))]


def _classify_span(chunk: bytes, encoding: object) -> tuple[str, str]:
    if encoding == "binary":
        return "unsupported", "binary_encoding"
    text = chunk.decode("utf-8")
    if not chunk.strip():
        return "non_memory", "blank"
    if _is_markdown_heading_only(text):
        return "non_memory", "structural_heading"
    return "classified_pending", "legacy_import_candidate"


def _is_markdown_heading_only(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return len(lines) == 1 and lines[0].startswith("#")


def _line_locator(data: bytes, start: int, end: int) -> dict[str, int | str]:
    start_line = data[:start].count(b"\n") + 1
    end_line = data[:end].count(b"\n") + (0 if end > start and data[end - 1 : end] == b"\n" else 1)
    return {"method": "byte_range_with_line_hint", "start_line": start_line, "end_line": max(start_line, end_line)}


def validate_source_span_record(item: dict[str, Any], *, index: int | None = None) -> list[str]:
    label = str(index) if index is not None else str(item.get("span_id", "unknown"))
    errors: list[str] = []
    unknown = sorted(set(item) - SPAN_FIELDS)
    for field in unknown:
        errors.append(f"unknown_source_span_field:{label}:{field}")
    if "archive_object_id" in item:
        errors.append(f"legacy_archive_object_id_forbidden:{label}")
    if item.get("schema") != SPAN_SCHEMA:
        errors.append(f"invalid_source_span_schema:{label}")
    for key in ("snapshot_id", "source_object_id", "original_relative_path", "content_hash", "span_id", "text_hash", "origin_kind", "epistemic_state", "operational_state", "disposition", "reason", "lifecycle"):
        if not isinstance(item.get(key), str):
            errors.append(f"invalid_source_span_{key}:{label}")
    for key in ("start_byte", "end_byte_exclusive"):
        if type(item.get(key)) is not int or int(item.get(key)) < 0:
            errors.append(f"invalid_source_span_{key}:{label}")
    if type(item.get("start_byte")) is int and type(item.get("end_byte_exclusive")) is int and item["end_byte_exclusive"] < item["start_byte"]:
        errors.append(f"invalid_source_span_range:{label}")
    locator = item.get("locator")
    if not isinstance(locator, dict):
        errors.append(f"invalid_source_span_locator:{label}")
    else:
        if locator.get("method") != "byte_range_with_line_hint":
            errors.append(f"invalid_source_span_locator_method:{label}")
        for key in ("start_line", "end_line"):
            if type(locator.get(key)) is not int or int(locator.get(key)) < 1:
                errors.append(f"invalid_source_span_locator_{key}:{label}")
    related = item.get("related_shard_ids")
    if not isinstance(related, list) or any(not isinstance(value, str) for value in related):
        errors.append(f"invalid_source_span_related_shard_ids:{label}")
    disposition = item.get("disposition")
    if disposition not in ALLOWED_DISPOSITIONS:
        errors.append(f"invalid_source_span_disposition:{label}")
    if disposition == "non_memory" and item.get("reason") not in NON_MEMORY_REASONS:
        errors.append(f"invalid_source_span_non_memory_reason:{label}")
    return errors
