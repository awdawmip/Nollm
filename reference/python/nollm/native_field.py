from __future__ import annotations

import json
import re
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from .archive import ARCHIVE_SCHEMA, LEGACY_ARCHIVE_V2_ERROR, archive_sources, existing_memory_root_path, load_manifest, memory_root_path, utc_now
from .archive import verify_archive_snapshot
from .archive_manifest import canonical_json, read_json, sha256_bytes, write_json
from .legacy_extract import idempotence_key
from .legacy_text import NORMALIZATION_ID
from .legacy_text import normalize_legacy_text, source_range_hash, text_hash
from .path_safety import contained_path, validate_batch_id, validate_field_id, validate_field_revision_id
from .safe_storage import SafeStorageError, safe_read_regular


FIELD_REVISION_SCHEMA = "nollm.native_field_revision.v1"
SHARD_SCHEMA = "nollm.native_dream_shard.v1"
ACTIVATION_SCHEMA = "nollm.field_activation.v1"
LEGACY_IMPORT_PROFILE = "nollm.legacy_import_shard_profile.v1"
SOURCE_REF_RE = re.compile(r"^archive://snapshot/(snap_[0-9]{8}_[0-9]{6}_[0-9a-f]{12})/source/(src_[0-9a-f]{24})/blob/sha256:([0-9a-f]{64})#B([0-9]+)-B([0-9]+)$")
LEGACY_IMPORT_GEOMETRY_INTENT = {
    "mode": "archive_ingest_seed",
    "placement": "pending_cortex_orientation",
}
LEGACY_IMPORT_ALLOWED_SHARD_FIELDS = {
    "anchor_field_weights",
    "batch_id",
    "continuity_refs",
    "created_at",
    "epistemic_state",
    "geometry_intent",
    "idempotence_key",
    "normalization_id",
    "operational_state",
    "origin_kind",
    "schema",
    "shard_id",
    "source_policy_id",
    "source_range_hash",
    "source_refs",
    "text",
    "text_hash",
}
HEAD_FIELDS = {"activation_hash", "field_id", "field_revision_id", "publication_manifest_hash"}
PUBLICATION_MANIFEST_FIELDS = {"artifact_hashes", "batch_id", "field_id", "field_revision_id", "schema", "snapshot_id"}
REVISION_FIELDS = {"batch_id", "created_at", "field_id", "field_revision_id", "schema", "shard_count", "shard_ids"}
RECEIPT_FIELDS = {
    "batch_id",
    "committed_at",
    "created_shard_count",
    "created_shard_ids",
    "duplicate_count",
    "field_revision_id",
    "schema",
    "snapshot_id",
    "source_policy_id",
    "target_field_id",
}
ACTIVATION_FIELDS = {
    "archive_manifest_hash",
    "archive_manifest_schema",
    "batch_id",
    "field_id",
    "field_revision_id",
    "legacy_import_profile",
    "receipt_hash",
    "revision_hash",
    "schema",
    "snapshot_id",
    "source_policy_id",
    "source_span_links_hash",
    "source_span_projection_hash",
}


def shard_id_for(idempotence_key: str) -> str:
    return "shard_" + idempotence_key.removeprefix("sha256:")[:24]


def build_shard(record: dict[str, Any], *, batch_id: str, source_policy_id: str, idempotence_key: str) -> dict[str, Any]:
    return {
        "schema": SHARD_SCHEMA,
        "shard_id": shard_id_for(idempotence_key),
        "batch_id": batch_id,
        "origin_kind": record.get("origin_kind", "legacy_import"),
        "operational_state": record.get("operational_state", "loose"),
        "epistemic_state": record.get("epistemic_state", "legacy_recorded"),
        "source_policy_id": source_policy_id,
        "source_refs": [record["source_ref"]],
        "source_range_hash": record.get("source_range_hash", record["text_hash"]),
        "continuity_refs": [record["span_id"]],
        "geometry_intent": {
            "mode": "archive_ingest_seed",
            "placement": "pending_cortex_orientation",
        },
        "anchor_field_weights": {},
        "text": record["text"],
        "text_hash": record["text_hash"],
        "normalization_id": record.get("normalization_id", NORMALIZATION_ID),
        "idempotence_key": idempotence_key,
        "created_at": utc_now(),
    }


def existing_shards_by_key(memory_root: Path | str) -> dict[str, dict[str, Any]]:
    root = existing_memory_root_path(memory_root)
    shards: dict[str, dict[str, Any]] = {}
    publication = current_publication(root)
    if not publication:
        return shards
    revision_path = publication / "revision.json"
    if not revision_path.exists():
        return {}
    try:
        revision = read_json(revision_path)
    except Exception:
        return {}
    shard_ids = [str(item) for item in revision.get("shard_ids", [])]
    if len(shard_ids) != len(set(shard_ids)):
        return {}
    for shard_id in shard_ids:
        path = publication / "shards" / f"{shard_id}.json"
        if not path.exists():
            return {}
        try:
            data = read_json(path)
        except Exception:
            return {}
        if data.get("shard_id") != shard_id or path.stem != shard_id:
            return {}
        key = data.get("idempotence_key")
        if isinstance(key, str) and shard_id_for(key) != shard_id:
            return {}
        if isinstance(key, str):
            shards[key] = data
    return shards


def stage_shards(memory_root: Path | str, batch_id: str, shards: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ok": False,
        "errors": ["unsupported_legacy_flat_writer"],
        "batch_id": batch_id,
        "shard_count": len(shards),
    }


def publish_field_revision(memory_root: Path | str, *, batch_id: str, target_field_id: str, shard_ids: list[str]) -> dict[str, Any]:
    return {
        "ok": False,
        "errors": ["unsupported_legacy_flat_writer"],
        "batch_id": batch_id,
        "target_field_id": target_field_id,
        "shard_ids": shard_ids,
    }


def move_staged_shards(memory_root: Path | str, batch_id: str) -> dict[str, Any]:
    return {"ok": False, "errors": ["unsupported_legacy_flat_writer"], "batch_id": batch_id}


def load_field_head(memory_root: Path | str) -> dict[str, Any] | None:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError:
        return None
    path, errors = contained_path(root, "field", "HEAD.json", label="field_head", must_exist=True, require_file=True)
    if errors:
        return None
    try:
        data = safe_read_regular(root, "field", "HEAD.json", label="field_head")
        loaded = json.loads(data.decode("utf-8"))
        return loaded if isinstance(loaded, dict) else None
    except Exception:
        return None


def current_publication(memory_root: Path | str) -> Path | None:
    return admit_current_publication(memory_root)["publication"]


def admit_current_publication(memory_root: Path | str) -> dict[str, Any]:
    try:
        root = existing_memory_root_path(memory_root)
    except ValueError as exc:
        return {"publication": None, "head": None, "errors": [str(exc)]}
    errors: list[str] = []
    field_dir = root / "field"
    head_path = field_dir / "HEAD.json"
    _validate_contained_regular_path(root, field_dir, "field_dir", errors, must_exist=False, require_file=False)
    _validate_contained_regular_path(root, head_path, "field_head", errors)
    if errors:
        return {"publication": None, "head": None, "errors": errors}
    head = _safe_read_json(head_path, "field_head", errors)
    if not isinstance(head, dict):
        errors.append("invalid_field_head")
        return {"publication": None, "head": None, "errors": errors}
    errors.extend(_unknown_fields(head, HEAD_FIELDS, "field_head"))
    field_id = head.get("field_id")
    revision_id = head.get("field_revision_id")
    expected = head.get("publication_manifest_hash")
    expected_activation = head.get("activation_hash")
    field_errors = validate_field_id(field_id)
    if field_errors:
        errors.extend("invalid_head_" + error.removeprefix("invalid_") for error in field_errors)
    revision_errors = validate_field_revision_id(revision_id)
    if revision_errors:
        errors.extend("invalid_head_" + error.removeprefix("invalid_") for error in revision_errors)
    if not isinstance(expected, str) or not expected.startswith("sha256:"):
        errors.append("invalid_head_publication_manifest_hash")
    if not isinstance(expected_activation, str) or not expected_activation.startswith("sha256:"):
        errors.append("invalid_head_activation_hash")
    if errors:
        return {"publication": None, "head": head, "errors": errors}
    publications_dir = field_dir / "publications"
    publication = publications_dir / revision_id
    manifest_path = publication / "publication-manifest.json"
    _validate_contained_regular_path(root, publications_dir, "publications_dir", errors, require_file=False)
    _validate_contained_regular_path(root, publication, "publication_dir", errors, require_file=False)
    _validate_contained_regular_path(root, manifest_path, "publication_manifest", errors)
    if errors:
        return {"publication": None, "head": head, "errors": errors}
    activation_path = publication / "activation.json"
    _validate_contained_regular_path(root, activation_path, "publication_activation", errors)
    if errors:
        return {"publication": None, "head": head, "errors": errors}
    activation_digest = _safe_sha256_file(activation_path, "publication_activation", errors)
    if activation_digest is None:
        return {"publication": None, "head": head, "errors": errors}
    if "sha256:" + activation_digest != expected_activation:
        errors.append(f"activation_hash_mismatch:{revision_id}")
        return {"publication": None, "head": head, "errors": errors}
    manifest_digest = _safe_sha256_file(manifest_path, "publication_manifest", errors)
    if manifest_digest is None:
        return {"publication": None, "head": head, "errors": errors}
    if "sha256:" + manifest_digest != expected:
        errors.append(f"publication_manifest_hash_mismatch:{revision_id}")
        return {"publication": None, "head": head, "errors": errors}
    manifest = _safe_read_json(manifest_path, "publication_manifest", errors)
    if not isinstance(manifest, dict):
        errors.append(f"invalid_publication_manifest:{revision_id}")
        return {"publication": None, "head": head, "errors": errors}
    if manifest.get("field_id") != field_id:
        errors.append(f"head_field_id_mismatch:{revision_id}")
    if manifest.get("field_revision_id") != revision_id:
        errors.append(f"head_revision_id_mismatch:{revision_id}")
    if errors:
        return {"publication": None, "head": head, "errors": errors}
    errors.extend(validate_publication_manifest_closure(publication))
    errors.extend(validate_publication_semantics(publication, expected_revision_id=revision_id, expected_field_id=field_id))
    errors.extend(validate_publication_activation(publication, head=head, manifest=manifest))
    activation = _safe_read_json(activation_path, "publication_activation", errors) if not errors else None
    if isinstance(activation, dict):
        errors.extend(validate_legacy_import_shard_profile(root, publication, activation))
    if not errors:
        from .provenance import validate_active_publication_package

        package = validate_active_publication_package(root, publication, head=head, expected_revision_id=revision_id, expected_field_id=field_id, require_head=True)
        errors.extend(str(error) for error in package.get("errors", []))
    return {"publication": publication if not errors else None, "head": head, "errors": errors}


def validate_publication_activation(publication: Path, *, head: dict[str, Any] | None = None, manifest: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    revision_id = publication.name
    activation_path = publication / "activation.json"
    if not activation_path.exists() or activation_path.is_symlink():
        return [f"missing_publication_activation:{revision_id}"]
    activation = _safe_read_json(activation_path, "publication_activation", errors)
    revision = _safe_read_json(publication / "revision.json", "publication_revision", errors)
    receipt = _safe_read_json(publication / "receipt.json", "publication_receipt", errors)
    if manifest is None:
        manifest = _safe_read_json(publication / "publication-manifest.json", "publication_manifest", errors)
    if not isinstance(activation, dict) or not isinstance(revision, dict) or not isinstance(receipt, dict) or not isinstance(manifest, dict):
        return errors or [f"invalid_publication_activation:{revision_id}"]
    if activation.get("schema") != ACTIVATION_SCHEMA:
        errors.append(f"invalid_activation_schema:{revision_id}")
    errors.extend(_unknown_fields(activation, ACTIVATION_FIELDS, f"activation:{revision_id}"))
    errors.extend(_unknown_fields(revision, REVISION_FIELDS, f"revision:{revision_id}"))
    errors.extend(_unknown_fields(receipt, RECEIPT_FIELDS, f"receipt:{revision_id}"))
    errors.extend(_unknown_fields(manifest, PUBLICATION_MANIFEST_FIELDS, f"publication_manifest:{revision_id}"))
    expected_pairs = {
        "field_id": manifest.get("field_id"),
        "field_revision_id": revision.get("field_revision_id"),
        "batch_id": receipt.get("batch_id"),
        "snapshot_id": receipt.get("snapshot_id"),
        "source_policy_id": receipt.get("source_policy_id"),
    }
    for key, expected in expected_pairs.items():
        if activation.get(key) != expected:
            errors.append(f"activation_{key}_mismatch:{revision_id}")
    if receipt.get("target_field_id") != activation.get("field_id"):
        errors.append(f"receipt_target_field_mismatch:{revision_id}")
    if head is not None:
        if head.get("field_id") != activation.get("field_id"):
            errors.append(f"activation_head_field_mismatch:{revision_id}")
        if head.get("field_revision_id") != activation.get("field_revision_id"):
            errors.append(f"activation_head_revision_mismatch:{revision_id}")
        activation_digest = _safe_sha256_file(activation_path, "publication_activation", errors)
        if activation_digest is not None and head.get("activation_hash") != "sha256:" + activation_digest:
            errors.append(f"activation_head_hash_mismatch:{revision_id}")
    if activation.get("legacy_import_profile") != LEGACY_IMPORT_PROFILE:
        errors.append(f"invalid_legacy_import_profile:{revision_id}")
    snapshot_id = activation.get("snapshot_id")
    if isinstance(snapshot_id, str):
        memory_root = _memory_root_for_publication(publication)
        archive = verify_archive_snapshot(memory_root, snapshot_id)
        errors.extend(str(error) for error in archive.get("errors", []))
        try:
            archive_manifest = load_manifest(memory_root, snapshot_id)
        except Exception as exc:
            archive_manifest = {}
            errors.append(f"invalid_archive_manifest:{exc.__class__.__name__}")
        if archive_manifest:
            if activation.get("archive_manifest_schema") != archive_manifest.get("schema"):
                errors.append(f"activation_archive_manifest_schema_mismatch:{revision_id}")
            if activation.get("archive_manifest_hash") != archive_manifest.get("archive_manifest_hash", archive_manifest.get("manifest_hash")):
                errors.append(f"activation_archive_manifest_hash_mismatch:{revision_id}")
    hash_paths = {
        "receipt_hash": publication / "receipt.json",
        "revision_hash": publication / "revision.json",
        "source_span_links_hash": publication / "source-span-links.jsonl",
        "source_span_projection_hash": publication / "source-span-projection.jsonl",
    }
    for field, path in hash_paths.items():
        digest = _safe_sha256_file(path, field, errors)
        if digest is not None and activation.get(field) != "sha256:" + digest:
            errors.append(f"activation_{field}_mismatch:{revision_id}")
    artifact_hashes = manifest.get("artifact_hashes")
    if isinstance(artifact_hashes, dict):
        activation_digest = _safe_sha256_file(activation_path, "publication_activation", errors)
        if activation_digest is not None and artifact_hashes.get("activation.json") != "sha256:" + activation_digest:
            errors.append(f"activation_manifest_hash_mismatch:{revision_id}")
    else:
        errors.append(f"invalid_publication_artifact_hashes:{revision_id}")
    return errors


def _memory_root_for_publication(publication: Path) -> Path:
    for parent in publication.parents:
        if (parent / "archive").exists() and (parent / "field").exists():
            return parent
    return publication.parents[2]


def validate_legacy_import_shard_profile(root: Path, publication: Path, activation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    snapshot_id = activation.get("snapshot_id")
    source_policy_id = activation.get("source_policy_id")
    revision_id = activation.get("field_revision_id")
    batch_id = activation.get("batch_id")
    if not all(isinstance(item, str) and item for item in (snapshot_id, source_policy_id, revision_id, batch_id)):
        return [f"invalid_activation_legacy_profile_identity:{publication.name}"]
    try:
        manifest = load_manifest(root, str(snapshot_id))
    except JSONDecodeError:
        return [f"malformed_json:archive_manifest:{snapshot_id}"]
    except OSError as exc:
        return [f"unreadable_json:archive_manifest:{exc.__class__.__name__}"]
    except Exception as exc:
        return [f"invalid_json:archive_manifest:{exc.__class__.__name__}"]
    if manifest.get("source_policy_id") != source_policy_id:
        errors.append(f"activation_source_policy_mismatch:{revision_id}")
    if manifest.get("schema") == "nollm.archive_manifest.v2":
        errors.append(f"{LEGACY_ARCHIVE_V2_ERROR}:{revision_id}")
    elif manifest.get("schema") != ARCHIVE_SCHEMA:
        errors.append(f"legacy_mt1_archive_requires_rearchive:{revision_id}")
    objects_by_source_id = {str(obj["source_object_id"]): obj for obj in archive_sources(manifest)}
    revision = _safe_read_json(publication / "revision.json", "publication_revision", errors)
    links = _safe_read_jsonl(publication / "source-span-links.jsonl", "source_span_links", errors)
    if not isinstance(revision, dict) or links is None:
        return errors
    links_by_shard: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        links_by_shard.setdefault(str(link.get("shard_id")), []).append(link)
    for shard_id in [str(item) for item in revision.get("shard_ids", [])]:
        shard_path = publication / "shards" / f"{shard_id}.json"
        shard = _safe_read_json(shard_path, f"publication_shard:{shard_id}", errors)
        if not isinstance(shard, dict):
            continue
        shard_links = links_by_shard.get(shard_id, [])
        if not shard_links:
            errors.append(f"legacy_profile_missing_source_span_link:{shard_id}")
            continue
        for link in shard_links:
            _validate_legacy_import_shard_profile(
                errors,
                root,
                shard,
                link,
                objects_by_source_id,
                snapshot_id=str(snapshot_id),
                source_policy_id=str(source_policy_id),
                batch_id=str(batch_id),
                field_revision_id=str(revision_id),
            )
    return errors


def _validate_legacy_import_shard_profile(
    errors: list[str],
    root: Path,
    shard: dict[str, Any],
    link: dict[str, Any],
    objects_by_source_id: dict[str, dict[str, Any]],
    *,
    snapshot_id: str,
    source_policy_id: str,
    batch_id: str,
    field_revision_id: str,
) -> None:
    shard_id = str(shard.get("shard_id"))
    source_ref = str(link.get("source_ref"))
    span_id = str(link.get("span_id"))
    unknown = sorted(set(shard) - LEGACY_IMPORT_ALLOWED_SHARD_FIELDS)
    for key in unknown:
        errors.append(f"legacy_shard_unknown_field:{shard_id}:{key}")
    match = SOURCE_REF_RE.match(source_ref)
    if not match:
        errors.append(f"legacy_shard_invalid_source_ref:{shard_id}")
        return
    ref_snapshot_id, source_object_id, digest, start_text, end_text = match.groups()
    obj = objects_by_source_id.get(source_object_id)
    if not obj:
        errors.append(f"legacy_shard_source_ref_source_not_in_manifest:{shard_id}")
        return
    if ref_snapshot_id != snapshot_id:
        errors.append(f"legacy_shard_source_ref_snapshot_mismatch:{shard_id}")
    if str(obj.get("content_hash", "")).removeprefix("sha256:") != digest:
        errors.append(f"legacy_shard_source_ref_digest_mismatch:{shard_id}")
    expected_static = {
        "schema": SHARD_SCHEMA,
        "origin_kind": obj.get("origin_kind"),
        "operational_state": obj.get("operational_state"),
        "epistemic_state": obj.get("epistemic_state"),
        "source_policy_id": source_policy_id,
        "batch_id": batch_id,
        "normalization_id": NORMALIZATION_ID,
    }
    for key, expected in expected_static.items():
        if shard.get(key) != expected:
            errors.append(f"legacy_shard_{key}_mismatch:{shard_id}")
    if shard.get("geometry_intent") != LEGACY_IMPORT_GEOMETRY_INTENT:
        errors.append(f"legacy_shard_geometry_intent_mismatch:{shard_id}")
    if shard.get("anchor_field_weights") != {}:
        errors.append(f"legacy_shard_anchor_field_weights_mismatch:{shard_id}")
    created_at = shard.get("created_at")
    if not isinstance(created_at, str) or not _is_utc_timestamp(created_at):
        errors.append(f"legacy_shard_created_at_invalid:{shard_id}")
    start = int(start_text)
    end = int(end_text)
    if not (0 <= start < end <= int(obj.get("byte_length", 0))):
        errors.append(f"legacy_shard_source_ref_range_out_of_bounds:{shard_id}")
        return
    object_path, object_errors = contained_path(root, "archive", "objects", "sha256", digest, label="archive_object", must_exist=True, require_file=True)
    if object_errors:
        errors.extend(f"legacy_shard_archive_path_error:{shard_id}:{error}" for error in object_errors)
        return
    try:
        data = object_path.read_bytes()
    except OSError as exc:
        errors.append(f"legacy_shard_archive_unreadable:{shard_id}:{exc.__class__.__name__}")
        return
    if sha256_bytes(data) != digest:
        errors.append(f"legacy_shard_archive_object_hash_mismatch:{shard_id}")
        return
    chunk = data[start:end]
    canonical_text = normalize_legacy_text(chunk)
    canonical_text_hash = text_hash(canonical_text)
    canonical_range_hash = source_range_hash(chunk)
    recomputed_key = idempotence_key({"text": canonical_text, "source_ref": source_ref}, source_policy_id)
    expected_shard_id = shard_id_for(recomputed_key)
    exact_lists = {
        "source_refs": [source_ref],
        "continuity_refs": [span_id],
    }
    for key, expected in exact_lists.items():
        if [str(item) for item in shard.get(key, [])] != expected:
            errors.append(f"legacy_shard_{key}_mismatch:{shard_id}")
    expected_dynamic = {
        "source_range_hash": canonical_range_hash,
        "text": canonical_text,
        "text_hash": canonical_text_hash,
        "idempotence_key": recomputed_key,
        "shard_id": expected_shard_id,
    }
    for key, expected in expected_dynamic.items():
        if shard.get(key) != expected:
            errors.append(f"legacy_shard_{key}_mismatch:{shard_id}")
    expected_link = {
        "schema": "nollm.source_span_link.v1",
        "snapshot_id": snapshot_id,
        "batch_id": batch_id,
        "field_revision_id": field_revision_id,
        "span_id": span_id,
        "shard_id": expected_shard_id,
        "source_ref": source_ref,
        "source_range_hash": canonical_range_hash,
        "text_hash": canonical_text_hash,
    }
    for key, expected in expected_link.items():
        if link.get(key) != expected:
            errors.append(f"legacy_link_{key}_mismatch:{shard_id}")


def _is_utc_timestamp(value: str) -> bool:
    if not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def _validate_contained_regular_path(
    root: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    must_exist: bool = True,
    require_file: bool = True,
) -> None:
    root_abs = root.absolute()
    path_abs = path.absolute()
    try:
        rel = path_abs.relative_to(root_abs)
    except ValueError:
        errors.append(f"active_path_escape:{label}")
        return
    current = root_abs
    for part in rel.parts:
        current = current / part
        try:
            if current.is_symlink():
                errors.append(f"active_path_symlink:{label}:{current.relative_to(root_abs).as_posix()}")
                return
        except OSError as exc:
            errors.append(f"active_path_unreadable:{label}:{exc.__class__.__name__}")
            return
    if must_exist and not path.exists():
        errors.append(f"active_path_missing:{label}")
        return
    if must_exist and require_file and not path.is_file():
        errors.append(f"active_path_not_file:{label}")
    if must_exist and not require_file and not path.is_dir():
        errors.append(f"active_path_not_directory:{label}")


def _safe_read_json(path: Path, label: str, errors: list[str]) -> Any | None:
    try:
        return read_json(path)
    except JSONDecodeError:
        errors.append(f"malformed_json:{label}")
    except OSError as exc:
        errors.append(f"unreadable_json:{label}:{exc.__class__.__name__}")
    except Exception as exc:
        errors.append(f"invalid_json:{label}:{exc.__class__.__name__}")
    return None


def _safe_read_jsonl(path: Path, label: str, errors: list[str]) -> list[dict[str, Any]] | None:
    records: list[dict[str, Any]] = []
    try:
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                errors.append(f"invalid_jsonl_record:{label}:{index}")
                return None
            records.append(item)
        return records
    except JSONDecodeError:
        errors.append(f"malformed_jsonl:{label}")
    except OSError as exc:
        errors.append(f"unreadable_jsonl:{label}:{exc.__class__.__name__}")
    return None


def _safe_sha256_file(path: Path, label: str, errors: list[str]) -> str | None:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        errors.append(f"unreadable_file:{label}:{exc.__class__.__name__}")
    return None


def validate_publication_manifest_closure(publication: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = publication / "publication-manifest.json"
    if not manifest_path.exists() or manifest_path.is_symlink():
        return ["missing_publication_manifest"]
    try:
        manifest = read_json(manifest_path)
    except JSONDecodeError:
        return ["malformed_json:publication_manifest"]
    except OSError as exc:
        return [f"unreadable_publication_manifest:{exc.__class__.__name__}"]
    except Exception as exc:
        return [f"invalid_publication_manifest:{exc.__class__.__name__}"]
    artifact_hashes = manifest.get("artifact_hashes")
    if not isinstance(artifact_hashes, dict):
        return ["invalid_publication_artifact_hashes"]
    actual_files: set[str] = set()
    for path in publication.rglob("*"):
        if path.is_symlink():
            errors.append(f"publication_symlink:{path.relative_to(publication).as_posix()}")
            continue
        if path.is_file() and path.name != "publication-manifest.json":
            actual_files.add(path.relative_to(publication).as_posix())
    listed_files: set[str] = set()
    for rel, digest in artifact_hashes.items():
        rel_text = str(rel)
        rel_path = PurePosixPath(rel_text)
        if "\\" in rel_text or rel_path.is_absolute() or ".." in rel_path.parts or rel_text in {"", "."}:
            errors.append(f"unsafe_manifest_path:{rel_text}")
            continue
        path = publication.joinpath(*rel_path.parts)
        try:
            path.relative_to(publication)
        except ValueError:
            errors.append(f"manifest_path_escape:{rel_text}")
            continue
        if not path.exists() or not path.is_file() or path.is_symlink():
            errors.append(f"manifest_path_not_regular:{rel_text}")
            continue
        actual_digest = _safe_sha256_file(path, f"publication_artifact:{rel_text}", errors)
        if actual_digest is None:
            continue
        if "sha256:" + actual_digest != digest:
            errors.append(f"publication_artifact_hash_mismatch:{rel_text}")
        listed_files.add(rel_text)
    for rel in sorted(actual_files - listed_files):
        errors.append(f"unmanifested_publication_artifact:{rel}")
    for rel in sorted(listed_files - actual_files):
        errors.append(f"manifested_artifact_missing:{rel}")
    return errors


def validate_publication_semantics(publication: Path, *, expected_revision_id: str | None = None, expected_field_id: str | None = None) -> list[str]:
    errors: list[str] = []
    revision_id = expected_revision_id or publication.name
    manifest_path = publication / "publication-manifest.json"
    revision_path = publication / "revision.json"
    receipt_path = publication / "receipt.json"
    activation_path = publication / "activation.json"
    if not manifest_path.exists():
        errors.append(f"missing_publication_manifest:{revision_id}")
    if not revision_path.exists():
        errors.append(f"missing_publication_revision:{revision_id}")
    if not receipt_path.exists():
        errors.append(f"missing_publication_receipt:{revision_id}")
    if not activation_path.exists():
        errors.append(f"missing_publication_activation:{revision_id}")
    if errors:
        return errors
    manifest = _safe_read_json(manifest_path, "publication_manifest", errors)
    revision = _safe_read_json(revision_path, "publication_revision", errors)
    receipt = _safe_read_json(receipt_path, "publication_receipt", errors)
    activation = _safe_read_json(activation_path, "publication_activation", errors)
    _safe_read_jsonl(publication / "source-span-links.jsonl", "source_span_links", errors)
    _safe_read_jsonl(publication / "source-span-projection.jsonl", "source_span_projection", errors)
    if errors:
        return errors
    if not isinstance(manifest, dict):
        errors.append("invalid_publication_manifest")
    if not isinstance(revision, dict):
        errors.append(f"invalid_publication_revision:{revision_id}")
    if not isinstance(receipt, dict):
        errors.append(f"invalid_publication_receipt:{revision_id}")
    if not isinstance(activation, dict):
        errors.append(f"invalid_publication_activation:{revision_id}")
    if errors:
        return errors
    if manifest.get("schema") != "nollm.publication_manifest.v1":
        errors.append("invalid_publication_manifest_schema")
    errors.extend(_unknown_fields(manifest, PUBLICATION_MANIFEST_FIELDS, f"publication_manifest:{revision_id}"))
    errors.extend(_unknown_fields(revision, REVISION_FIELDS, f"revision:{revision_id}"))
    errors.extend(_unknown_fields(receipt, RECEIPT_FIELDS, f"receipt:{revision_id}"))
    errors.extend(_unknown_fields(activation, ACTIVATION_FIELDS, f"activation:{revision_id}"))
    if activation.get("schema") != ACTIVATION_SCHEMA:
        errors.append(f"invalid_activation_schema:{revision_id}")
    for label, value in (
        ("manifest", manifest.get("field_id")),
        ("revision", revision.get("field_id")),
        ("activation", activation.get("field_id")),
        ("receipt_target", receipt.get("target_field_id")),
    ):
        for error in validate_field_id(value):
            errors.append(f"{label}_{error}:{revision_id}")
    if manifest.get("field_revision_id") != revision_id:
        errors.append(f"publication_manifest_revision_mismatch:{revision_id}")
    if revision.get("field_revision_id") != revision_id:
        errors.append(f"revision_id_mismatch:{revision_id}")
    if receipt.get("field_revision_id") != revision_id:
        errors.append(f"receipt_revision_mismatch:{revision_id}")
    if activation.get("field_revision_id") != revision_id:
        errors.append(f"activation_revision_mismatch:{revision_id}")
    if manifest.get("field_id") != revision.get("field_id"):
        errors.append(f"publication_manifest_field_mismatch:{revision_id}")
    if receipt.get("target_field_id") != revision.get("field_id"):
        errors.append(f"receipt_target_field_mismatch:{revision_id}")
    if activation.get("field_id") != revision.get("field_id"):
        errors.append(f"activation_field_mismatch:{revision_id}")
    if expected_field_id is not None and manifest.get("field_id") != expected_field_id:
        errors.append(f"head_field_id_mismatch:{revision_id}")
    if expected_field_id is not None and revision.get("field_id") != expected_field_id:
        errors.append(f"head_revision_field_id_mismatch:{revision_id}")
    if manifest.get("batch_id") != revision.get("batch_id") or manifest.get("batch_id") != receipt.get("batch_id"):
        errors.append(f"publication_batch_mismatch:{revision_id}")
    for label, value in (
        ("manifest", manifest.get("batch_id")),
        ("revision", revision.get("batch_id")),
        ("receipt", receipt.get("batch_id")),
        ("activation", activation.get("batch_id")),
    ):
        for error in validate_batch_id(value):
            errors.append(f"{label}_{error}:{revision_id}")
    shard_ids = [str(item) for item in revision.get("shard_ids", [])]
    if len(shard_ids) != len(set(shard_ids)):
        errors.append(f"duplicate_revision_shard_ids:{revision_id}")
    if revision.get("shard_count") != len(shard_ids):
        errors.append(f"revision_shard_count_mismatch:{revision_id}")
    created_shard_ids = [str(item) for item in receipt.get("created_shard_ids", [])]
    if len(created_shard_ids) != len(set(created_shard_ids)):
        errors.append(f"duplicate_receipt_created_shard_ids:{revision_id}")
    if receipt.get("created_shard_count") != len(created_shard_ids):
        errors.append(f"receipt_created_shard_count_mismatch:{revision_id}")
    revision_set = set(shard_ids)
    for shard_id in created_shard_ids:
        if shard_id not in revision_set:
            errors.append(f"receipt_created_shard_not_in_revision:{shard_id}")
    for path in sorted((publication / "shards").glob("*.json")):
        if path.stem not in revision_set:
            errors.append(f"unlisted_shard_file:{path.name}")
    for shard_id in shard_ids:
        path = publication / "shards" / f"{shard_id}.json"
        if not path.exists() or not path.is_file() or path.is_symlink():
            errors.append(f"missing_revision_shard:{shard_id}")
            continue
        shard = _safe_read_json(path, f"publication_shard:{shard_id}", errors)
        if not isinstance(shard, dict):
            continue
        if shard.get("shard_id") != shard_id:
            errors.append(f"shard_payload_id_mismatch:{shard_id}")
        if not isinstance(shard.get("idempotence_key"), str):
            errors.append(f"shard_missing_idempotence_key:{shard_id}")
    return errors


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _unknown_fields(record: dict[str, Any], allowed: set[str], label: str) -> list[str]:
    return [f"unknown_{label}_field:{field}" for field in sorted(set(record) - allowed)]


def _current_field_shards(root: Path, target_field_id: str) -> list[str]:
    head = root / "field" / "HEAD.json"
    if not head.exists():
        return []
    current = read_json(head)
    if current.get("field_id") != target_field_id:
        return []
    revision_path = root / "field" / "revisions" / f"{current['field_revision_id']}.json"
    if not revision_path.exists():
        return []
    return [str(item) for item in read_json(revision_path).get("shard_ids", [])]


def _current_head_shards(root: Path) -> list[str]:
    head = root / "field" / "HEAD.json"
    if not head.exists():
        return []
    current = read_json(head)
    revision_path = root / "field" / "revisions" / f"{current['field_revision_id']}.json"
    if not revision_path.exists():
        return []
    return [str(item) for item in read_json(revision_path).get("shard_ids", [])]
