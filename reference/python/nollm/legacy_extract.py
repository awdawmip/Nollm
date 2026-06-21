from __future__ import annotations

from pathlib import Path
from typing import Any

from .archive import load_manifest, memory_root_path
from .archive_manifest import sha256_bytes
from .source_spans import load_source_spans


EXTRACTION_SCHEMA = "nollm.legacy_extraction.v1"


def extract_legacy_spans(memory_root: Path | str, snapshot_id: str) -> list[dict[str, Any]]:
    root = memory_root_path(memory_root)
    manifest = load_manifest(root, snapshot_id)
    by_object = {obj["archive_object_id"]: obj for obj in manifest.get("objects", [])}
    extracted: list[dict[str, Any]] = []
    for span in load_source_spans(root, snapshot_id):
        if span.get("disposition") not in {"classified_pending", "sharded"}:
            continue
        obj = by_object[str(span["archive_object_id"])]
        digest = str(obj["content_hash"]).removeprefix("sha256:")
        data = (root / "archive" / "objects" / "sha256" / digest).read_bytes()
        start = int(span["start_byte"])
        end = int(span["end_byte_exclusive"])
        chunk = data[start:end]
        text = chunk.decode("utf-8").strip()
        if not text or _is_markdown_heading_only(text):
            continue
        source_ref = f"archive://object/sha256:{digest}#B{start}-B{end}"
        extracted.append(
            {
                "schema": EXTRACTION_SCHEMA,
                "snapshot_id": snapshot_id,
                "span_id": span["span_id"],
                "archive_object_id": span["archive_object_id"],
                "original_relative_path": span["original_relative_path"],
                "source_ref": source_ref,
                "text": text,
                "text_hash": "sha256:" + sha256_bytes(chunk),
                "origin_kind": obj.get("origin_kind", "legacy_import"),
                "epistemic_state": obj.get("epistemic_state", "legacy_recorded"),
                "operational_state": obj.get("operational_state", "loose"),
            }
        )
    return extracted


def _is_markdown_heading_only(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return len(lines) == 1 and lines[0].startswith("#")


def idempotence_key(record: dict[str, Any], source_policy_id: str) -> str:
    text = " ".join(str(record["text"]).split())
    refs = "\n".join(sorted([str(record["source_ref"])]))
    payload = f"nollm.legacy_import.idempotence.v1\0{text}\0{refs}\0{source_policy_id}".encode("utf-8")
    return "sha256:" + sha256_bytes(payload)
