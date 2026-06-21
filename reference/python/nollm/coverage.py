from __future__ import annotations

from pathlib import Path
from typing import Any

from .archive import load_manifest, memory_root_path
from .source_spans import ALLOWED_DISPOSITIONS, load_source_spans


def validate_source_coverage(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    manifest = load_manifest(root, snapshot_id)
    spans = load_source_spans(root, snapshot_id)
    by_object: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for span in spans:
        by_object.setdefault((str(span["archive_object_id"]), str(span["original_relative_path"])), []).append(span)
    errors: list[str] = []
    total = 0
    covered = 0
    unsupported = 0
    manual_review = 0
    for obj in manifest.get("objects", []):
        key = (str(obj["archive_object_id"]), str(obj["original_relative_path"]))
        current = 0
        object_spans = sorted(by_object.get(key, []), key=lambda item: int(item["start_byte"]))
        if not object_spans and obj.get("byte_length", 0) != 0:
            errors.append(f"missing_spans:{key[1]}")
        for span in object_spans:
            total += 1
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
        "errors": errors,
    }
