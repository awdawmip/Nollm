from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .archive import load_manifest, memory_root_path, verify_archive_snapshot
from .archive_manifest import read_json, sha256_bytes
from .coverage import validate_source_coverage
from .legacy_text import NORMALIZATION_ID, normalize_legacy_text, source_range_hash, text_hash
from .native_field import current_publication, load_field_head
from .source_spans import _classify_span, _paragraph_ranges, load_source_spans


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
                    "source_range_hash": shard["source_range_hash"],
                    "text_hash": shard["text_hash"],
                }
            )
    return links


def canonical_source_spans(memory_root: Path | str, snapshot_id: str) -> list[dict[str, Any]]:
    root = memory_root_path(memory_root)
    manifest = load_manifest(root, snapshot_id)
    records: list[dict[str, Any]] = []
    for obj in manifest.get("objects", []):
        digest = str(obj["content_hash"]).removeprefix("sha256:")
        data = (root / "archive" / "objects" / "sha256" / digest).read_bytes()
        for index, (start, end) in enumerate(_paragraph_ranges(data)):
            chunk = data[start:end]
            disposition, reason = _classify_span(chunk, obj.get("encoding"))
            records.append(
                {
                    "snapshot_id": snapshot_id,
                    "archive_object_id": obj["archive_object_id"],
                    "original_relative_path": obj["original_relative_path"],
                    "span_id": f"span_{obj['archive_object_id'].removeprefix('arc_')}_{index:04d}",
                    "start_byte": start,
                    "end_byte_exclusive": end,
                    "text_hash": "sha256:" + sha256_bytes(chunk),
                    "disposition": disposition,
                    "reason": reason,
                }
            )
    return records


def validate_staged_publication(memory_root: Path | str, batch_id: str, snapshot_id: str, field_revision_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    publication = root / "field" / ".staging" / batch_id / "publication"
    errors = _validate_publication_package(root, snapshot_id, field_revision_id, publication, require_head=False)
    return _result(snapshot_id, field_revision_id, errors)


def validate_deep_provenance(memory_root: Path | str, snapshot_id: str, field_revision_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    errors: list[str] = []
    head = load_field_head(root)
    if not head or head.get("field_revision_id") != field_revision_id:
        return _result(snapshot_id, field_revision_id, [f"unpublished_revision:{field_revision_id}"])
    publication = current_publication(root)
    if not publication or publication.name != field_revision_id:
        return _result(snapshot_id, field_revision_id, [f"unpublished_revision:{field_revision_id}"])
    errors.extend(_validate_publication_package(root, snapshot_id, field_revision_id, publication, require_head=True))
    if errors:
        return _result(snapshot_id, field_revision_id, errors)
    archive = verify_archive_snapshot(root, snapshot_id)
    errors.extend(archive.get("errors", []))
    manifest = load_manifest(root, snapshot_id)
    objects_by_digest = {str(obj["content_hash"]).removeprefix("sha256:"): obj for obj in manifest.get("objects", [])}
    receipt_path = publication / "receipt.json"
    if not receipt_path.exists():
        errors.append(f"missing_publication_receipt:{field_revision_id}")
        return _result(snapshot_id, field_revision_id, errors)
    receipt = read_json(receipt_path)
    if receipt.get("snapshot_id") != snapshot_id:
        errors.append(f"receipt_snapshot_mismatch:{field_revision_id}")
    state_path = root / "ingress" / "legacy-import" / str(receipt.get("batch_id")) / "state.json"
    state = read_json(state_path).get("state") if state_path.exists() else None
    if state not in {"committed", "publishing"}:
        errors.append(f"batch_not_committed:{receipt.get('batch_id')}")
    spans = _load_publication_jsonl(publication / "source-span-projection.jsonl")
    spans_by_id = {str(span["span_id"]): span for span in spans}
    spans_by_ref = {_span_source_ref(objects_by_digest, span): span for span in spans if _span_source_ref(objects_by_digest, span)}
    revision_path = publication / "revision.json"
    if not revision_path.exists():
        errors.append(f"missing_field_revision:{field_revision_id}")
        return _result(snapshot_id, field_revision_id, errors)
    revision = read_json(revision_path)
    revision_shards = set(str(item) for item in revision.get("shard_ids", []))
    links = _load_publication_jsonl(publication / "source-span-links.jsonl")
    links_by_shard: dict[str, list[dict[str, Any]]] = {}
    links_by_span: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        links_by_shard.setdefault(str(link.get("shard_id")), []).append(link)
        links_by_span.setdefault(str(link.get("span_id")), []).append(link)
    seen_keys: dict[str, dict[str, Any]] = {}
    for shard_id in revision_shards:
        shard_path = publication / "shards" / f"{shard_id}.json"
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
            canonical = normalize_legacy_text(chunk)
            canonical_hash = text_hash(canonical)
            raw_hash = source_range_hash(chunk)
            if shard.get("source_range_hash") != raw_hash:
                errors.append(f"source_range_hash_mismatch:{shard_id}")
            if shard.get("normalization_id") != NORMALIZATION_ID:
                errors.append(f"normalization_id_mismatch:{shard_id}")
            if shard.get("text") != canonical:
                errors.append(f"shard_text_mismatch:{shard_id}")
            if shard.get("text_hash") != canonical_hash:
                errors.append(f"shard_text_hash_mismatch:{shard_id}")
            if span.get("span_id") not in shard.get("continuity_refs", []):
                errors.append(f"missing_continuity_ref:{shard_id}:{span.get('span_id')}")
            if shard_id not in span.get("related_shard_ids", []):
                errors.append(f"missing_reverse_span_link:{span.get('span_id')}:{shard_id}")
            matching_links = [link for link in shard_links if link.get("span_id") == span.get("span_id") and link.get("source_ref") == source_ref]
            if not matching_links:
                errors.append(f"missing_exact_relation:{shard_id}:{span.get('span_id')}")
            for link in matching_links:
                _validate_link_record(errors, link, snapshot_id, str(receipt.get("batch_id")), field_revision_id, shard, span, source_ref)
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


def _validate_publication_package(root: Path, snapshot_id: str, field_revision_id: str, publication: Path, *, require_head: bool) -> list[str]:
    errors: list[str] = []
    if not publication.exists():
        return [f"missing_publication:{field_revision_id}"]
    manifest_path = publication / "publication-manifest.json"
    if not manifest_path.exists():
        return [f"missing_publication_manifest:{field_revision_id}"]
    if require_head:
        head = load_field_head(root)
        actual_manifest_hash = "sha256:" + sha256_bytes(manifest_path.read_bytes())
        if not head or head.get("field_revision_id") != field_revision_id:
            errors.append(f"unpublished_revision:{field_revision_id}")
        elif head.get("publication_manifest_hash") != actual_manifest_hash:
            errors.append(f"publication_manifest_hash_mismatch:{field_revision_id}")
    manifest = read_json(manifest_path)
    if manifest.get("schema") != "nollm.publication_manifest.v1":
        errors.append(f"invalid_publication_manifest_schema:{field_revision_id}")
    if manifest.get("field_revision_id") != field_revision_id:
        errors.append(f"publication_manifest_revision_mismatch:{field_revision_id}")
    if manifest.get("snapshot_id") != snapshot_id:
        errors.append(f"publication_manifest_snapshot_mismatch:{field_revision_id}")
    artifact_hashes = manifest.get("artifact_hashes", {})
    if not isinstance(artifact_hashes, dict):
        errors.append(f"publication_manifest_artifact_hashes_invalid:{field_revision_id}")
        artifact_hashes = {}
    expected_paths = {"revision.json", "receipt.json", "source-span-links.jsonl", "source-span-projection.jsonl"}
    for path in sorted(publication.rglob("*")):
        if path.is_file() and path.name != "publication-manifest.json":
            rel = path.relative_to(publication).as_posix()
            expected_paths.add(rel)
            actual = "sha256:" + sha256_bytes(path.read_bytes())
            if artifact_hashes.get(rel) != actual:
                errors.append(f"publication_artifact_hash_mismatch:{rel}")
    missing = expected_paths - set(artifact_hashes)
    errors.extend(f"publication_artifact_hash_missing:{path}" for path in sorted(missing))
    errors.extend(_validate_inventory_and_projection(root, snapshot_id, publication))
    return errors


def _validate_inventory_and_projection(root: Path, snapshot_id: str, publication: Path) -> list[str]:
    errors: list[str] = []
    canonical = canonical_source_spans(root, snapshot_id)
    persisted = load_source_spans(root, snapshot_id)
    projection = _load_publication_jsonl(publication / "source-span-projection.jsonl")
    canonical_by_id = {str(span["span_id"]): span for span in canonical}
    persisted_core = [_span_core(span) for span in persisted]
    canonical_core = [_span_core(span) for span in canonical]
    if persisted_core != canonical_core:
        errors.append("canonical_inventory_mismatch")
    if len(projection) != len(canonical):
        errors.append("projection_span_count_mismatch")
    revision = read_json(publication / "revision.json") if (publication / "revision.json").exists() else {"shard_ids": []}
    revision_shards = set(str(item) for item in revision.get("shard_ids", []))
    links = _load_publication_jsonl(publication / "source-span-links.jsonl")
    links_by_span: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        links_by_span.setdefault(str(link.get("span_id")), []).append(link)
    for span in projection:
        span_id = str(span.get("span_id"))
        expected = canonical_by_id.get(span_id)
        if not expected:
            errors.append(f"projection_unknown_span:{span_id}")
            continue
        for key in ["snapshot_id", "archive_object_id", "original_relative_path", "span_id", "start_byte", "end_byte_exclusive", "text_hash"]:
            if span.get(key) != expected.get(key):
                errors.append(f"projection_{key}_mismatch:{span_id}")
        expected_disposition = expected.get("disposition")
        if expected_disposition == "non_memory":
            if span.get("disposition") != "non_memory" or span.get("reason") != expected.get("reason") or span.get("related_shard_ids"):
                errors.append(f"projection_non_memory_changed:{span_id}")
        elif expected_disposition == "classified_pending":
            if span.get("disposition") != "sharded":
                errors.append(f"projection_candidate_not_sharded:{span_id}")
            related = [str(item) for item in span.get("related_shard_ids", [])]
            if not related:
                errors.append(f"projection_sharded_without_related:{span_id}")
            for shard_id in related:
                if shard_id not in revision_shards:
                    errors.append(f"projection_related_shard_not_in_revision:{span_id}:{shard_id}")
            if not links_by_span.get(span_id):
                errors.append(f"projection_missing_link:{span_id}")
        else:
            if span.get("disposition") != expected_disposition:
                errors.append(f"projection_disposition_mismatch:{span_id}")
    return errors


def _span_core(span: dict[str, Any]) -> dict[str, Any]:
    return {
        "snapshot_id": span.get("snapshot_id"),
        "archive_object_id": span.get("archive_object_id"),
        "original_relative_path": span.get("original_relative_path"),
        "span_id": span.get("span_id"),
        "start_byte": span.get("start_byte"),
        "end_byte_exclusive": span.get("end_byte_exclusive"),
        "text_hash": span.get("text_hash"),
        "disposition": span.get("disposition"),
        "reason": span.get("reason"),
    }


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


def _load_publication_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    import json

    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _validate_link_record(
    errors: list[str],
    link: dict[str, Any],
    snapshot_id: str,
    batch_id: str,
    field_revision_id: str,
    shard: dict[str, Any],
    span: dict[str, Any],
    source_ref: str,
) -> None:
    expected = {
        "schema": LINK_SCHEMA,
        "snapshot_id": snapshot_id,
        "batch_id": batch_id,
        "field_revision_id": field_revision_id,
        "span_id": span.get("span_id"),
        "shard_id": shard.get("shard_id"),
        "source_ref": source_ref,
        "source_range_hash": shard.get("source_range_hash"),
        "text_hash": shard.get("text_hash"),
    }
    for key, value in expected.items():
        if link.get(key) != value:
            errors.append(f"link_{key}_mismatch:{shard.get('shard_id')}")


def _result(snapshot_id: str, field_revision_id: str, errors: list[str], *, coverage: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": not errors,
        "snapshot_id": snapshot_id,
        "field_revision_id": field_revision_id,
        "provenance_verified": not errors,
        "coverage": coverage,
        "errors": errors,
    }
