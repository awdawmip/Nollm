from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .archive import load_manifest, memory_root_path
from .archive_manifest import sha256_bytes

SPAN_SCHEMA = "nollm.source_span_inventory.v1"
ALLOWED_DISPOSITIONS = {"sharded", "non_memory", "manual_review", "unsupported"}


def build_source_span_inventory(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    manifest = load_manifest(root, snapshot_id)
    records: list[dict[str, Any]] = []
    for obj in manifest.get("objects", []):
        digest = str(obj["content_hash"]).removeprefix("sha256:")
        data = (root / "archive" / "objects" / "sha256" / digest).read_bytes()
        for index, (start, end) in enumerate(_paragraph_ranges(data)):
            chunk = data[start:end]
            disposition = "non_memory" if not chunk.strip() else ("unsupported" if obj.get("encoding") == "binary" else "sharded")
            records.append(
                {
                    "schema": SPAN_SCHEMA,
                    "snapshot_id": snapshot_id,
                    "archive_object_id": obj["archive_object_id"],
                    "original_relative_path": obj["original_relative_path"],
                    "span_id": f"span_{obj['archive_object_id'].removeprefix('arc_')}_{index:04d}",
                    "start_byte": start,
                    "end_byte_exclusive": end,
                    "locator": _line_locator(data, start, end),
                    "text_hash": "sha256:" + sha256_bytes(chunk),
                    "disposition": disposition,
                    "related_shard_ids": [],
                    "reason": "deterministic paragraph coverage",
                }
            )
    path = root / "archive" / "source-spans" / f"{snapshot_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
    return {"ok": True, "snapshot_id": snapshot_id, "span_count": len(records), "inventory_path": str(path)}


def load_source_spans(memory_root: Path | str, snapshot_id: str) -> list[dict[str, Any]]:
    path = memory_root_path(memory_root) / "archive" / "source-spans" / f"{snapshot_id}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def _line_locator(data: bytes, start: int, end: int) -> dict[str, int | str]:
    start_line = data[:start].count(b"\n") + 1
    end_line = data[:end].count(b"\n") + (0 if end > start and data[end - 1 : end] == b"\n" else 1)
    return {"method": "byte_range_with_line_hint", "start_line": start_line, "end_line": max(start_line, end_line)}
