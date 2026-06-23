from __future__ import annotations

import re
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .archive import archive_sources, existing_memory_root_path, load_manifest, verify_archive_snapshot
from .archive_manifest import read_json, sha256_bytes
from .coverage import validate_source_coverage
from .legacy_extract import idempotence_key
from .legacy_text import NORMALIZATION_ID, normalize_legacy_text, source_range_hash, text_hash
from .native_field import (
    admit_current_publication,
    current_publication,
    LEGACY_IMPORT_ALLOWED_SHARD_FIELDS,
    load_field_head,
    shard_id_for,
    validate_legacy_import_shard_profile,
    validate_publication_activation,
    validate_publication_manifest_closure,
    validate_publication_semantics,
)
from .path_safety import contained_path, no_symlink_segments, validate_batch_id, validate_field_revision_id, validate_snapshot_id
from .safe_storage import SafeStorageError, read_jsonl_bytes, safe_read_regular
from .source_spans import SPAN_SCHEMA, _classify_span, _line_locator, _paragraph_ranges, load_source_spans, validate_source_span_record


SOURCE_REF_RE = re.compile(r"^archive://snapshot/(snap_[0-9]{8}_[0-9]{6}_[0-9a-f]{12})/source/(src_[0-9a-f]{24})/blob/sha256:([0-9a-f]{64})#B([0-9]+)-B([0-9]+)$")
LINK_SCHEMA = "nollm.source_span_link.v1"
SOURCE_SPAN_FIELDS = {
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
LINK_FIELDS = {
    "batch_id",
    "field_revision_id",
    "schema",
    "shard_id",
    "snapshot_id",
    "source_range_hash",
    "source_ref",
    "span_id",
    "text_hash",
}


def parse_source_ref(source_ref: str) -> tuple[str, str, str, int, int]:
    match = SOURCE_REF_RE.match(source_ref)
    if not match:
        raise ValueError(f"invalid_source_ref:{source_ref}")
    snapshot_id, source_object_id, digest, start, end = match.groups()
    return snapshot_id, source_object_id, digest, int(start), int(end)


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
    root = existing_memory_root_path(memory_root)
    archive = verify_archive_snapshot(root, snapshot_id)
    if not archive.get("ok"):
        raise ValueError(",".join(str(error) for error in archive.get("errors", [])))
    manifest = load_manifest(root, snapshot_id)
    records: list[dict[str, Any]] = []
    for obj in archive_sources(manifest):
        digest = str(obj["content_hash"]).removeprefix("sha256:")
        object_path, object_errors = contained_path(root, "archive", "objects", "sha256", digest, label="archive_object", must_exist=True, require_file=True)
        if object_errors:
            raise ValueError(",".join(object_errors))
        data = safe_read_regular(root, "archive", "objects", "sha256", digest, label="archive_object")
        source_object_id = str(obj["source_object_id"])
        for index, (start, end) in enumerate(_paragraph_ranges(data)):
            chunk = data[start:end]
            disposition, reason = _classify_span(chunk, obj.get("encoding"))
            records.append(
                {
                    "schema": SPAN_SCHEMA,
                    "snapshot_id": snapshot_id,
                    "source_object_id": source_object_id,
                    "original_relative_path": obj["original_relative_path"],
                    "content_hash": obj["content_hash"],
                    "span_id": f"span_{source_object_id.removeprefix('src_')}_{index:04d}",
                    "start_byte": start,
                    "end_byte_exclusive": end,
                    "locator": _line_locator(data, start, end),
                    "text_hash": "sha256:" + sha256_bytes(chunk),
                    "origin_kind": obj.get("origin_kind"),
                    "epistemic_state": obj.get("epistemic_state"),
                    "operational_state": obj.get("operational_state"),
                    "disposition": disposition,
                    "related_shard_ids": [],
                    "reason": reason,
                    "lifecycle": "classified",
                }
            )
    return records


def validate_staged_publication(memory_root: Path | str, batch_id: str, snapshot_id: str, field_revision_id: str) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return _result(snapshot_id, field_revision_id, [str(exc)])
    id_errors = validate_batch_id(batch_id) + validate_snapshot_id(snapshot_id) + validate_field_revision_id(field_revision_id)
    if id_errors:
        return _result(snapshot_id, field_revision_id, id_errors)
    publication, path_errors = contained_path(root, "field", ".staging", batch_id, "publication", label="field_staging", must_exist=True, require_file=False)
    if path_errors:
        return _result(snapshot_id, field_revision_id, path_errors)
    errors = _validate_publication_package(root, snapshot_id, field_revision_id, publication, require_head=False)
    return _result(snapshot_id, field_revision_id, errors)


def validate_active_publication_package(
    memory_root: Path | str,
    publication: Path,
    *,
    head: dict[str, Any] | None = None,
    expected_revision_id: str | None = None,
    expected_field_id: str | None = None,
    require_head: bool = True,
) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return _result("", expected_revision_id or publication.name, [str(exc)])
    revision_id = expected_revision_id or publication.name
    activation = _safe_read_json(root, publication / "activation.json", f"publication_activation:{revision_id}", [])
    snapshot_id = str(activation.get("snapshot_id")) if isinstance(activation, dict) else ""
    id_errors = validate_field_revision_id(revision_id) + validate_snapshot_id(snapshot_id)
    if id_errors:
        return _result(snapshot_id, revision_id, id_errors)
    errors = _validate_publication_package(root, snapshot_id, revision_id, publication, require_head=require_head)
    if expected_field_id is not None:
        revision = _safe_read_json(root, publication / "revision.json", f"publication_revision:{revision_id}", errors)
        if isinstance(revision, dict) and revision.get("field_id") != expected_field_id:
            errors.append(f"head_revision_field_id_mismatch:{revision_id}")
    return _result(snapshot_id, revision_id, errors)


def validate_deep_provenance(memory_root: Path | str, snapshot_id: str, field_revision_id: str) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return _result(snapshot_id, field_revision_id, [str(exc)])
    errors: list[str] = []
    id_errors = validate_snapshot_id(snapshot_id) + validate_field_revision_id(field_revision_id)
    if id_errors:
        return _result(snapshot_id, field_revision_id, id_errors)
    admission = admit_current_publication(root)
    head = admission.get("head")
    if not head or head.get("field_revision_id") != field_revision_id:
        admission_errors = [str(error) for error in admission.get("errors", [])]
        if admission_errors == ["active_path_missing:field_head"]:
            admission_errors = []
        return _result(snapshot_id, field_revision_id, admission_errors + [f"unpublished_revision:{field_revision_id}"])
    publication = admission.get("publication")
    if not publication or publication.name != field_revision_id:
        admission_errors = [str(error) for error in admission.get("errors", [])]
        return _result(snapshot_id, field_revision_id, admission_errors + [f"unpublished_revision:{field_revision_id}"])
    errors.extend(_validate_publication_package(root, snapshot_id, field_revision_id, publication, require_head=True))
    if errors:
        return _result(snapshot_id, field_revision_id, errors)
    archive = verify_archive_snapshot(root, snapshot_id)
    errors.extend(archive.get("errors", []))
    manifest = load_manifest(root, snapshot_id)
    source_policy_id = str(manifest.get("source_policy_id"))
    objects_by_source_id = {str(obj["source_object_id"]): obj for obj in archive_sources(manifest)}
    receipt_path = publication / "receipt.json"
    if not receipt_path.exists():
        errors.append(f"missing_publication_receipt:{field_revision_id}")
        return _result(snapshot_id, field_revision_id, errors)
    receipt = _safe_read_json(root, receipt_path, "publication_receipt", [])
    if receipt.get("snapshot_id") != snapshot_id:
        errors.append(f"receipt_snapshot_mismatch:{field_revision_id}")
    spans = _load_publication_jsonl(root, publication / "source-span-projection.jsonl")
    spans_by_id = {str(span["span_id"]): span for span in spans}
    spans_by_ref = {_span_source_ref(objects_by_source_id, span): span for span in spans if _span_source_ref(objects_by_source_id, span)}
    revision_path = publication / "revision.json"
    if not revision_path.exists():
        errors.append(f"missing_field_revision:{field_revision_id}")
        return _result(snapshot_id, field_revision_id, errors)
    revision = _safe_read_json(root, revision_path, "publication_revision", [])
    revision_shards = set(str(item) for item in revision.get("shard_ids", []))
    links = _load_publication_jsonl(root, publication / "source-span-links.jsonl")
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
        shard = _safe_read_json(root, shard_path, f"publication_shard:{shard_id}", [])
        key = str(shard.get("idempotence_key"))
        if key in seen_keys and seen_keys[key] != shard:
            errors.append(f"idempotence_collision:{key}")
        seen_keys[key] = shard
        shard_links = links_by_shard.get(shard_id, [])
        if not shard_links:
            errors.append(f"missing_source_span_link:{shard_id}")
        for source_ref in shard.get("source_refs", []):
            try:
                ref_snapshot_id, source_object_id, digest, start, end = parse_source_ref(str(source_ref))
            except ValueError as exc:
                errors.append(str(exc))
                continue
            obj = objects_by_source_id.get(source_object_id)
            if not obj:
                errors.append(f"source_ref_source_not_in_manifest:{shard_id}")
                continue
            if ref_snapshot_id != snapshot_id:
                errors.append(f"source_ref_snapshot_mismatch:{shard_id}")
            if str(obj.get("content_hash", "")).removeprefix("sha256:") != digest:
                errors.append(f"source_ref_digest_mismatch:{shard_id}")
            object_path, object_errors = contained_path(root, "archive", "objects", "sha256", digest, label="archive_object", must_exist=True, require_file=True)
            if object_errors:
                errors.extend(object_errors)
                continue
            from .safe_storage import safe_read_regular
            data = safe_read_regular(root, "archive", "objects", "sha256", digest, label="archive_object")
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
            _validate_legacy_shard_identity(errors, shard, receipt, source_policy_id, source_ref, span, obj, canonical, canonical_hash, raw_hash)
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
    errors.extend(_validate_exact_relation_closure(root, snapshot_id, publication, field_revision_id, receipt, objects_by_source_id, revision_shards, spans, links))
    coverage = validate_source_coverage(root, snapshot_id, require_linked=True)
    errors.extend(coverage.get("errors", []))
    return _result(snapshot_id, field_revision_id, errors, coverage=coverage)


def _validate_publication_package(root: Path, snapshot_id: str, field_revision_id: str, publication: Path, *, require_head: bool) -> list[str]:
    errors: list[str] = []
    try:
        publication.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        return [f"path_escape:publication:{field_revision_id}"]
    segment_errors = no_symlink_segments(root, publication, f"publication:{field_revision_id}")
    if segment_errors:
        return segment_errors
    if not publication.exists():
        return [f"missing_publication:{field_revision_id}"]
    manifest_path = publication / "publication-manifest.json"
    if not manifest_path.exists():
        return [f"missing_publication_manifest:{field_revision_id}"]
    if require_head:
        head = load_field_head(root)
        try:
            actual_manifest_hash = "sha256:" + sha256_bytes(safe_read_regular(root, *_rel_parts(root, manifest_path), label="publication_manifest", require_private_inode=False))
        except Exception as exc:
            return [f"unreadable_publication_manifest:{exc.__class__.__name__}"]
        if not head or head.get("field_revision_id") != field_revision_id:
            errors.append(f"unpublished_revision:{field_revision_id}")
        elif head.get("publication_manifest_hash") != actual_manifest_hash:
            errors.append(f"publication_manifest_hash_mismatch:{field_revision_id}")
        try:
            actual_activation_hash = "sha256:" + sha256_bytes(safe_read_regular(root, *_rel_parts(root, publication / "activation.json"), label="publication_activation", require_private_inode=False))
        except Exception as exc:
            return [f"unreadable_publication_activation:{exc.__class__.__name__}"]
        if head and head.get("field_revision_id") == field_revision_id and head.get("activation_hash") != actual_activation_hash:
            errors.append(f"activation_hash_mismatch:{field_revision_id}")
    manifest = _safe_read_json(root, manifest_path, f"publication_manifest:{field_revision_id}", errors)
    if not isinstance(manifest, dict):
        return errors
    if manifest.get("schema") != "nollm.publication_manifest.v1":
        errors.append(f"invalid_publication_manifest_schema:{field_revision_id}")
    if manifest.get("field_revision_id") != field_revision_id:
        errors.append(f"publication_manifest_revision_mismatch:{field_revision_id}")
    if manifest.get("snapshot_id") != snapshot_id:
        errors.append(f"publication_manifest_snapshot_mismatch:{field_revision_id}")
    errors.extend(validate_publication_manifest_closure(root, publication))
    errors.extend(validate_publication_semantics(root, publication, expected_revision_id=field_revision_id))
    manifest = _safe_read_json(root, manifest_path, f"publication_manifest:{field_revision_id}", errors)
    if isinstance(manifest, dict):
        errors.extend(validate_publication_activation(root, publication, head=load_field_head(root) if require_head else None, manifest=manifest))
    if errors:
        return errors
    artifact_hashes = manifest.get("artifact_hashes", {})
    required_paths = {"activation.json", "revision.json", "receipt.json", "source-span-links.jsonl", "source-span-projection.jsonl"}
    if isinstance(artifact_hashes, dict):
        for required in sorted(required_paths):
            if required not in artifact_hashes:
                errors.append(f"publication_artifact_hash_missing:{required}")
    errors.extend(_validate_inventory_and_projection(root, snapshot_id, publication))
    activation = _safe_read_json(root, publication / "activation.json", f"publication_activation:{field_revision_id}", errors)
    if isinstance(activation, dict):
        errors.extend(validate_legacy_import_shard_profile(root, publication, activation))
    return errors


def _validate_inventory_and_projection(root: Path, snapshot_id: str, publication: Path) -> list[str]:
    errors: list[str] = []
    try:
        canonical = canonical_source_spans(root, snapshot_id)
        persisted = load_source_spans(root, snapshot_id)
        projection = _load_publication_jsonl(root, publication / "source-span-projection.jsonl")
    except JSONDecodeError:
        return ["malformed_json:source_span_inventory_or_projection"]
    except Exception as exc:
        return [f"invalid_source_span_inventory_or_projection:{exc.__class__.__name__}"]
    canonical_by_id = {str(span["span_id"]): span for span in canonical}
    projection_ids = [str(span.get("span_id")) for span in projection]
    duplicate_projection_ids = sorted({span_id for span_id in projection_ids if projection_ids.count(span_id) > 1})
    errors.extend(f"duplicate_projection_span:{span_id}" for span_id in duplicate_projection_ids)
    missing_projection_ids = sorted(set(canonical_by_id) - set(projection_ids))
    extra_projection_ids = sorted(set(projection_ids) - set(canonical_by_id))
    errors.extend(f"projection_missing_span:{span_id}" for span_id in missing_projection_ids)
    errors.extend(f"projection_unknown_span:{span_id}" for span_id in extra_projection_ids)
    persisted_core = [_span_core(span) for span in persisted]
    canonical_core = [_span_core(span) for span in canonical]
    if persisted_core != canonical_core:
        errors.append("canonical_inventory_mismatch")
    if len(projection) != len(canonical):
        errors.append("projection_span_count_mismatch")
    revision = _safe_read_json(root, publication / "revision.json", "publication_revision", []) if (publication / "revision.json").exists() else {"shard_ids": []}
    revision_shards = set(str(item) for item in revision.get("shard_ids", []))
    links = _load_publication_jsonl(root, publication / "source-span-links.jsonl")
    link_counts: dict[tuple[str, str, str], int] = {}
    for link in links:
        key = (str(link.get("shard_id")), str(link.get("source_ref")), str(link.get("span_id")))
        link_counts[key] = link_counts.get(key, 0) + 1
    for key, count in link_counts.items():
        if count != 1:
            errors.append(f"duplicate_source_span_link:{key[0]}:{key[2]}")
    links_by_span: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        links_by_span.setdefault(str(link.get("span_id")), []).append(link)
    for span in projection:
        span_id = str(span.get("span_id"))
        expected = canonical_by_id.get(span_id)
        if not expected:
            errors.append(f"projection_unknown_span:{span_id}")
            continue
        errors.extend(_unknown_fields(span, SOURCE_SPAN_FIELDS, f"projection:{span_id}"))
        for key in [
            "schema",
            "snapshot_id",
            "source_object_id",
            "original_relative_path",
            "content_hash",
            "span_id",
            "start_byte",
            "end_byte_exclusive",
            "locator",
            "text_hash",
            "origin_kind",
            "epistemic_state",
            "operational_state",
        ]:
            if span.get(key) != expected.get(key):
                errors.append(f"projection_{key}_mismatch:{span_id}")
        expected_disposition = expected.get("disposition")
        if expected_disposition == "non_memory":
            if span.get("disposition") != "non_memory" or span.get("reason") != expected.get("reason") or span.get("related_shard_ids"):
                errors.append(f"projection_non_memory_changed:{span_id}")
            if links_by_span.get(span_id):
                errors.append(f"projection_non_memory_has_link:{span_id}")
        elif expected_disposition == "classified_pending":
            if span.get("disposition") != "sharded":
                errors.append(f"projection_candidate_not_sharded:{span_id}")
            related = [str(item) for item in span.get("related_shard_ids", [])]
            if len(related) != len(set(related)):
                errors.append(f"projection_duplicate_related_shard:{span_id}")
            if not related:
                errors.append(f"projection_sharded_without_related:{span_id}")
            for shard_id in related:
                if shard_id not in revision_shards:
                    errors.append(f"projection_related_shard_not_in_revision:{span_id}:{shard_id}")
            if not links_by_span.get(span_id):
                errors.append(f"projection_missing_link:{span_id}")
            linked = sorted(str(link.get("shard_id")) for link in links_by_span.get(span_id, []))
            if sorted(related) != linked:
                errors.append(f"projection_link_relation_mismatch:{span_id}")
        else:
            if span.get("disposition") != expected_disposition:
                errors.append(f"projection_disposition_mismatch:{span_id}")
    return errors


def _validate_exact_relation_closure(
    root: Path,
    snapshot_id: str,
    publication: Path,
    field_revision_id: str,
    receipt: dict[str, Any],
    objects_by_source_id: dict[str, dict[str, Any]],
    revision_shards: set[str],
    projection: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    canonical = canonical_source_spans(root, snapshot_id)
    canonical_by_id = {str(span["span_id"]): span for span in canonical}
    canonical_by_ref = {str(_span_source_ref(objects_by_source_id, span)): span for span in canonical if _span_source_ref(objects_by_source_id, span)}
    projection_by_id = {str(span.get("span_id")): span for span in projection}
    shards: dict[str, dict[str, Any]] = {}
    for shard_id in revision_shards:
        path = publication / "shards" / f"{shard_id}.json"
        if path.exists():
            shards[shard_id] = _safe_read_json(root, path, f"publication_shard:{shard_id}", [])

    expected_counts: dict[tuple[str, str, str], int] = {}
    for shard_id, shard in shards.items():
        for source_ref in [str(item) for item in shard.get("source_refs", [])]:
            span = canonical_by_ref.get(source_ref)
            if not span:
                continue
            span_id = str(span["span_id"])
            if span_id not in [str(item) for item in shard.get("continuity_refs", [])]:
                errors.append(f"relation_continuity_missing:{shard_id}:{span_id}")
            key = (shard_id, source_ref, span_id)
            expected_counts[key] = expected_counts.get(key, 0) + 1

    actual_counts: dict[tuple[str, str, str], int] = {}
    for link in links:
        key = (str(link.get("shard_id")), str(link.get("source_ref")), str(link.get("span_id")))
        actual_counts[key] = actual_counts.get(key, 0) + 1
    for key, count in actual_counts.items():
        if count != 1:
            errors.append(f"duplicate_source_span_link:{key[0]}:{key[2]}")

    for key in sorted(set(expected_counts) - set(actual_counts)):
        errors.append(f"missing_relation_link:{key[0]}:{key[2]}")
    for key in sorted(set(actual_counts) - set(expected_counts)):
        errors.append(f"extra_relation_link:{key[0]}:{key[2]}")

    for link in links:
        errors.extend(_unknown_fields(link, LINK_FIELDS, f"link:{link.get('shard_id')}:{link.get('span_id')}"))
        shard_id = str(link.get("shard_id"))
        source_ref = str(link.get("source_ref"))
        span_id = str(link.get("span_id"))
        shard = shards.get(shard_id)
        span = canonical_by_id.get(span_id)
        projected = projection_by_id.get(span_id)
        if shard_id not in revision_shards or not shard:
            errors.append(f"link_unknown_shard:{shard_id}")
            continue
        if source_ref not in [str(item) for item in shard.get("source_refs", [])]:
            errors.append(f"link_source_ref_not_in_shard:{shard_id}:{span_id}")
        if span_id not in [str(item) for item in shard.get("continuity_refs", [])]:
            errors.append(f"link_span_not_in_shard_continuity:{shard_id}:{span_id}")
        if not span:
            errors.append(f"link_unknown_span:{span_id}")
            continue
        if span.get("disposition") != "classified_pending":
            errors.append(f"link_non_importable_span:{span_id}")
        if not projected:
            errors.append(f"link_span_absent_from_projection:{span_id}")
            continue
        if projected.get("disposition") != "sharded":
            errors.append(f"link_span_not_projected_sharded:{span_id}")
        related = [str(item) for item in projected.get("related_shard_ids", [])]
        if related.count(shard_id) != 1:
            errors.append(f"link_projection_related_count_mismatch:{shard_id}:{span_id}")
        _validate_link_record(errors, link, snapshot_id, str(receipt.get("batch_id")), field_revision_id, shard, projected, source_ref)
    return errors


def _span_core(span: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": span.get("schema"),
        "snapshot_id": span.get("snapshot_id"),
        "source_object_id": span.get("source_object_id"),
        "original_relative_path": span.get("original_relative_path"),
        "content_hash": span.get("content_hash"),
        "span_id": span.get("span_id"),
        "start_byte": span.get("start_byte"),
        "end_byte_exclusive": span.get("end_byte_exclusive"),
        "locator": span.get("locator"),
        "text_hash": span.get("text_hash"),
        "origin_kind": span.get("origin_kind"),
        "epistemic_state": span.get("epistemic_state"),
        "operational_state": span.get("operational_state"),
        "disposition": span.get("disposition"),
        "related_shard_ids": span.get("related_shard_ids"),
        "reason": span.get("reason"),
        "lifecycle": span.get("lifecycle"),
    }


def _span_source_ref(objects_by_source_id: dict[str, dict[str, Any]], span: dict[str, Any]) -> str | None:
    source_object_id = str(span.get("source_object_id"))
    obj = objects_by_source_id.get(source_object_id)
    if obj:
        digest = str(obj.get("content_hash", "")).removeprefix("sha256:")
        return f"archive://snapshot/{span['snapshot_id']}/source/{source_object_id}/blob/sha256:{digest}#B{span['start_byte']}-B{span['end_byte_exclusive']}"
    return None


def _load_links(root: Path, snapshot_id: str, field_revision_id: str) -> list[dict[str, Any]]:
    path = root / "archive" / "source-span-links" / snapshot_id / f"{field_revision_id}.jsonl"
    if not path.exists():
        return []
    import json

    from .safe_storage import safe_read_regular, read_jsonl_bytes
    return read_jsonl_bytes(safe_read_regular(root, "archive", "source-span-links", snapshot_id, f"{field_revision_id}.jsonl", label=path.name, require_private_inode=False), path.name)


def _load_publication_jsonl(root: Path, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        from .safe_storage import safe_read_regular
        parts = _rel_parts(root, path)
        records = read_jsonl_bytes(safe_read_regular(root, *parts, label=path.name, require_private_inode=False), path.name)
    except SafeStorageError as exc:
        raise ValueError(str(exc)) from exc
    for index, record in enumerate(records, start=1):
        if path.name == "source-span-projection.jsonl":
            errors = validate_source_span_record(record, index=index)
            if errors:
                raise ValueError(",".join(errors))
    return records


def _unknown_fields(record: dict[str, Any], allowed: set[str], label: str) -> list[str]:
    return [f"unknown_{label}_field:{field}" for field in sorted(set(record) - allowed)]


def _rel_parts(root: Path, path: Path) -> tuple[str, ...]:
    """Compute relative path parts from root to path."""
    rel = Path(path).resolve().relative_to(Path(root).resolve())
    return tuple(rel.parts)


def _safe_read_json(root: Path, path: Path, label: str, errors: list[str]) -> Any | None:
    try:
        parts = _rel_parts(root, path)
        raw = safe_read_regular(root, *parts, label=label, require_private_inode=True)
        from .safe_storage import read_json_bytes
        return read_json_bytes(raw, label)
    except JSONDecodeError:
        errors.append(f"malformed_json:{label}")
    except OSError as exc:
        errors.append(f"unreadable_json:{label}:{exc.__class__.__name__}")
    except Exception as exc:
        errors.append(f"invalid_json:{label}:{exc.__class__.__name__}")
    return None


def _validate_legacy_shard_identity(
    errors: list[str],
    shard: dict[str, Any],
    receipt: dict[str, Any],
    source_policy_id: str,
    source_ref: str,
    span: dict[str, Any],
    source_object: dict[str, Any],
    canonical_text: str,
    canonical_hash: str,
    raw_hash: str,
) -> None:
    shard_id = str(shard.get("shard_id"))
    span_id = str(span.get("span_id"))
    for key in sorted(set(shard) - LEGACY_IMPORT_ALLOWED_SHARD_FIELDS):
        errors.append(f"legacy_shard_unknown_field:{shard_id}:{key}")
    if shard.get("schema") != "nollm.native_dream_shard.v1":
        errors.append(f"legacy_shard_schema_mismatch:{shard_id}")
    if shard.get("origin_kind") != source_object.get("origin_kind"):
        errors.append(f"legacy_shard_origin_kind_mismatch:{shard_id}")
    if shard.get("operational_state") != source_object.get("operational_state"):
        errors.append(f"legacy_shard_operational_state_mismatch:{shard_id}")
    if shard.get("epistemic_state") != source_object.get("epistemic_state"):
        errors.append(f"legacy_shard_epistemic_state_mismatch:{shard_id}")
    if shard.get("batch_id") != receipt.get("batch_id"):
        errors.append(f"legacy_shard_batch_mismatch:{shard_id}")
    if shard.get("source_policy_id") != source_policy_id:
        errors.append(f"legacy_shard_source_policy_mismatch:{shard_id}")
    if [str(item) for item in shard.get("source_refs", [])] != [source_ref]:
        errors.append(f"legacy_shard_source_refs_not_exact:{shard_id}")
    if [str(item) for item in shard.get("continuity_refs", [])] != [span_id]:
        errors.append(f"legacy_shard_continuity_not_exact:{shard_id}")
    if shard.get("source_range_hash") != raw_hash:
        errors.append(f"legacy_shard_source_range_hash_mismatch:{shard_id}")
    if shard.get("text") != canonical_text:
        errors.append(f"legacy_shard_text_mismatch:{shard_id}")
    if shard.get("text_hash") != canonical_hash:
        errors.append(f"legacy_shard_text_hash_mismatch:{shard_id}")
    recomputed_key = idempotence_key({"text": canonical_text, "source_ref": source_ref}, source_policy_id)
    if shard.get("idempotence_key") != recomputed_key:
        errors.append(f"legacy_shard_idempotence_key_mismatch:{shard_id}")
    expected_shard_id = shard_id_for(recomputed_key)
    if shard_id != expected_shard_id:
        errors.append(f"legacy_shard_id_mismatch:{shard_id}")
    if shard.get("geometry_intent") != {"mode": "archive_ingest_seed", "placement": "pending_cortex_orientation"}:
        errors.append(f"legacy_shard_geometry_intent_mismatch:{shard_id}")
    if shard.get("anchor_field_weights") != {}:
        errors.append(f"legacy_shard_anchor_field_weights_mismatch:{shard_id}")
    created_at = shard.get("created_at")
    if not isinstance(created_at, str) or not _is_utc_timestamp(created_at):
        errors.append(f"legacy_shard_created_at_invalid:{shard_id}")


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


def _is_utc_timestamp(value: str) -> bool:
    if not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def _result(snapshot_id: str, field_revision_id: str, errors: list[str], *, coverage: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": not errors,
        "snapshot_id": snapshot_id,
        "field_revision_id": field_revision_id,
        "provenance_verified": not errors,
        "coverage": coverage,
        "errors": errors,
    }
