from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .archive import load_manifest, memory_root_path, verify_archive_snapshot
from .archive_manifest import read_json, sha256_bytes
from .coverage import validate_source_coverage
from .source_spans import load_source_spans


SOURCE_REF_RE = re.compile(r"^archive://object/sha256:([0-9a-f]{64})#B([0-9]+)-B([0-9]+)$")
LINK_SCHEMA = "nollm.source_span_link.v1"


def parse_source_ref(source_ref: str) -> tuple[str, int, int]:
    match = SOURCE_REF_RE.match(source_ref)
    if not match:
        raise ValueError(f"invalid_source_ref:{source_ref}")
    digest, start, end = match.groups()
    return digest, int(start), int(end)


def build_source_span_links(
    *,
    snapshot_id: str,
    batch_id: str,
    field_revision_id: str,
    shards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for shard in shards:
        for source_ref in shard.get("source_refs", []):
            links.append(
                {
                    "schema": LINK_SCHEMA,
                    "snapshot_id": snapshot_id,
                    "batch_id": batch_id,
                    "field_revision_id": field_revision_id,
                    "span_id": shard["continuity_refs"][0],
                    "shard_id": shard["shard_id"],
                    "source_ref": source_ref,
                    "text_hash": shard["text_hash"],
                }
            )
    return links


def validate_deep_provenance(memory_root: Path | str, snapshot_id: str, field_revision_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    errors: list[str] = []
    archive = verify_archive_snapshot(root, snapshot_id)
    errors.extend(archive.get("errors", []))
    manifest = load_manifest(root, snapshot_id)
    objects_by_digest = {str(obj["content_hash"]).removeprefix("sha256:"): obj for obj in manifest.get("objects", [])}
    spans = load_source_spans(root, snapshot_id)
    spans_by_id = {str(span["span_id"]): span for span in spans}
    spans_by_ref = {_span_source_ref(objects_by_digest, span): span for span in spans if _span_source_ref(objects_by_digest, span)}
    revision_path = root / "field" / "revisions" / f"{field_revision_id}.json"
    if not revision_path.exists():
        errors.append(f"missing_field_revision:{field_revision_id}")
        return _result(snapshot_id, field_revision_id, errors)
    revision = read_json(revision_path)
    revision_shards = set(str(item) for item in revision.get("shard_ids", []))
    links = _load_links(root, snapshot_id, field_revision_id)
    links_by_shard: dict[str, list[dict[str, Any]]] = {}
    links_by_span: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        links_by_shard.setdefault(str(link.get("shard_id")), []).append(link)
        links_by_span.setdefault(str(link.get("span_id")), []).append(link)
    seen_keys: dict[str, dict[str, Any]] = {}
    for shard_id in revision_shards:
        shard_path = root / "field" / "shards" / f"{shard_id}.json"
        if not shard_path.exists():
            errors.append(f"missing_shard:{shard_id}")
            continue
        shard = read_json(shard_path)
        key = str(shard.get("idempotence_key"))
        if key in seen_keys and seen_keys[key] != shard:
            errors.append(f"idempotence_collision:{key}")
        seen_keys[key] = shard
        shard_links = links_by_shard.get(shard_id, [])
        if not shard_links:
            errors.append(f"missing_source_span_link:{shard_id}")
        for source_ref in shard.get("source_refs", []):
            try:
                digest, start, end = parse_source_ref(str(source_ref))
            except ValueError as exc:
                errors.append(str(exc))
                continue
            obj = objects_by_digest.get(digest)
            if not obj:
                errors.append(f"source_ref_digest_not_in_manifest:{shard_id}")
                continue
            object_path = root / "archive" / "objects" / "sha256" / digest
            if not object_path.exists():
                errors.append(f"missing_archive_object:{digest}")
                continue
            data = object_path.read_bytes()
            if sha256_bytes(data) != digest:
                errors.append(f"archive_object_hash_mismatch:{digest}")
            if not (0 <= start < end <= int(obj.get("byte_length", 0))):
                errors.append(f"source_ref_range_out_of_bounds:{shard_id}:{start}-{end}")
                continue
            span = spans_by_ref.get(str(source_ref))
            if not span:
                errors.append(f"source_ref_has_no_exact_span:{shard_id}:{source_ref}")
                continue
            chunk = data[start:end]
            chunk_hash = "sha256:" + sha256_bytes(chunk)
            if span.get("text_hash") != chunk_hash:
                errors.append(f"span_text_hash_mismatch:{span.get('span_id')}")
            if shard.get("text_hash") != chunk_hash:
                errors.append(f"shard_text_hash_mismatch:{shard_id}")
            if span.get("span_id") not in shard.get("continuity_refs", []):
                errors.append(f"missing_continuity_ref:{shard_id}:{span.get('span_id')}")
            if shard_id not in span.get("related_shard_ids", []):
                errors.append(f"missing_reverse_span_link:{span.get('span_id')}:{shard_id}")
            if not any(link.get("span_id") == span.get("span_id") and link.get("source_ref") == source_ref for link in shard_links):
                errors.append(f"missing_exact_relation:{shard_id}:{span.get('span_id')}")
    for span in spans:
        if span.get("disposition") == "sharded":
            related = set(str(item) for item in span.get("related_shard_ids", []))
            if not related:
                errors.append(f"sharded_span_without_related_shards:{span.get('span_id')}")
            for shard_id in related:
                if shard_id not in revision_shards:
                    errors.append(f"span_related_shard_not_in_revision:{span.get('span_id')}:{shard_id}")
                if not links_by_span.get(str(span.get("span_id"))):
                    errors.append(f"sharded_span_without_link_record:{span.get('span_id')}")
    coverage = validate_source_coverage(root, snapshot_id, require_linked=True)
    errors.extend(coverage.get("errors", []))
    return _result(snapshot_id, field_revision_id, errors, coverage=coverage)


def _span_source_ref(objects_by_digest: dict[str, dict[str, Any]], span: dict[str, Any]) -> str | None:
    for digest, obj in objects_by_digest.items():
        if obj.get("archive_object_id") == span.get("archive_object_id"):
            return f"archive://object/sha256:{digest}#B{span['start_byte']}-B{span['end_byte_exclusive']}"
    return None


def _load_links(root: Path, snapshot_id: str, field_revision_id: str) -> list[dict[str, Any]]:
    path = root / "archive" / "source-span-links" / snapshot_id / f"{field_revision_id}.jsonl"
    if not path.exists():
        return []
    import json

    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _result(snapshot_id: str, field_revision_id: str, errors: list[str], *, coverage: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": not errors,
        "snapshot_id": snapshot_id,
        "field_revision_id": field_revision_id,
        "provenance_verified": not errors,
        "coverage": coverage,
        "errors": errors,
    }
