from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .archive import archive_sources, load_manifest, memory_root_path, verify_archive_snapshot
from .archive_manifest import sha256_bytes
from .path_safety import contained_path, validate_snapshot_id

SPAN_SCHEMA = "nollm.source_span_inventory.v1"
ALLOWED_DISPOSITIONS = {"classified_pending", "sharded", "non_memory", "manual_review", "unsupported"}
NON_MEMORY_REASONS = {"blank", "structural_heading"}


def build_source_span_inventory(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    try:
        root = memory_root_path(memory_root)
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
        data = object_path.read_bytes()
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
    return {"ok": True, "snapshot_id": snapshot_id, "span_count": len(records), "inventory_path": str(path)}


def load_source_spans(memory_root: Path | str, snapshot_id: str) -> list[dict[str, Any]]:
    root = memory_root_path(memory_root)
    errors = validate_snapshot_id(snapshot_id)
    if errors:
        raise ValueError(errors[0])
    path, path_errors = contained_path(root, "archive", "source-spans", f"{snapshot_id}.jsonl", label="source_span_inventory", must_exist=True, require_file=True)
    if path_errors:
        raise ValueError(path_errors[0])
    records: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"invalid_source_span_record:{index}")
        if "archive_object_id" in item:
            raise ValueError(f"legacy_archive_object_id_forbidden:{index}")
        records.append(item)
    return records


def write_source_spans(memory_root: Path | str, snapshot_id: str, spans: list[dict[str, Any]]) -> None:
    root = memory_root_path(memory_root)
    errors = validate_snapshot_id(snapshot_id)
    if errors:
        raise ValueError(errors[0])
    path, path_errors = contained_path(root, "archive", "source-spans", f"{snapshot_id}.jsonl", label="source_span_inventory", must_exist=False)
    if path_errors:
        raise ValueError(path_errors[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(span, ensure_ascii=False, sort_keys=True) + "\n" for span in spans), encoding="utf-8")


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
