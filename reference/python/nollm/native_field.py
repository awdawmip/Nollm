from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from .archive import memory_root_path, utc_now
from .archive_manifest import canonical_json, read_json, sha256_bytes, write_json
from .legacy_text import NORMALIZATION_ID


FIELD_REVISION_SCHEMA = "nollm.native_field_revision.v1"
SHARD_SCHEMA = "nollm.native_dream_shard.v1"


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
    root = memory_root_path(memory_root)
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


def stage_shards(memory_root: Path | str, batch_id: str, shards: list[dict[str, Any]]) -> Path:
    root = memory_root_path(memory_root)
    staging = root / "field" / ".staging" / batch_id
    if staging.exists():
        for path in sorted(staging.glob("*.json")):
            path.unlink()
    staging.mkdir(parents=True, exist_ok=True)
    for shard in shards:
        write_json(staging / f"{shard['shard_id']}.json", shard)
    return staging


def publish_field_revision(memory_root: Path | str, *, batch_id: str, target_field_id: str, shard_ids: list[str]) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    existing_ids = _current_field_shards(root, target_field_id)
    merged_ids = sorted(set(existing_ids).union(shard_ids))
    revision_seed = canonical_json({"batch_id": batch_id, "field_id": target_field_id, "shard_ids": merged_ids})
    revision_id = "fieldrev_" + sha256_bytes(revision_seed)[:20]
    revision = {
        "schema": FIELD_REVISION_SCHEMA,
        "field_revision_id": revision_id,
        "field_id": target_field_id,
        "batch_id": batch_id,
        "created_at": utc_now(),
        "shard_ids": merged_ids,
        "shard_count": len(merged_ids),
    }
    write_json(root / "field" / "revisions" / f"{revision_id}.json", revision)
    write_json(root / "field" / "HEAD.json", {"field_id": target_field_id, "field_revision_id": revision_id})
    return revision


def move_staged_shards(memory_root: Path | str, batch_id: str) -> list[str]:
    root = memory_root_path(memory_root)
    staging = root / "field" / ".staging" / batch_id
    target = root / "field" / "shards"
    target.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for path in sorted(staging.glob("*.json")):
        data = read_json(path)
        out = target / path.name
        if not out.exists():
            out.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        moved.append(str(data["shard_id"]))
    return moved


def load_field_head(memory_root: Path | str) -> dict[str, Any] | None:
    path = memory_root_path(memory_root) / "field" / "HEAD.json"
    if not path.exists() or path.is_symlink():
        return None
    try:
        return read_json(path)
    except Exception:
        return None


def current_publication(memory_root: Path | str) -> Path | None:
    return admit_current_publication(memory_root)["publication"]


def admit_current_publication(memory_root: Path | str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
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
    field_id = head.get("field_id")
    revision_id = head.get("field_revision_id")
    expected = head.get("publication_manifest_hash")
    if not isinstance(field_id, str) or not field_id:
        errors.append("invalid_head_field_id")
    if not isinstance(revision_id, str) or not revision_id:
        errors.append("invalid_head_field_revision_id")
    if not isinstance(expected, str) or not expected.startswith("sha256:"):
        errors.append("invalid_head_publication_manifest_hash")
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
    return {"publication": publication if not errors else None, "head": head, "errors": errors}


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
    except Exception as exc:
        return [f"unreadable_publication_manifest:{exc}"]
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
    if not manifest_path.exists():
        errors.append(f"missing_publication_manifest:{revision_id}")
    if not revision_path.exists():
        errors.append(f"missing_publication_revision:{revision_id}")
    if not receipt_path.exists():
        errors.append(f"missing_publication_receipt:{revision_id}")
    if errors:
        return errors
    manifest = _safe_read_json(manifest_path, "publication_manifest", errors)
    revision = _safe_read_json(revision_path, "publication_revision", errors)
    receipt = _safe_read_json(receipt_path, "publication_receipt", errors)
    _safe_read_jsonl(publication / "source-span-links.jsonl", "source_span_links", errors)
    _safe_read_jsonl(publication / "source-span-projection.jsonl", "source_span_projection", errors)
    if errors:
        return errors
    assert isinstance(manifest, dict)
    assert isinstance(revision, dict)
    assert isinstance(receipt, dict)
    if manifest.get("schema") != "nollm.publication_manifest.v1":
        errors.append("invalid_publication_manifest_schema")
    if manifest.get("field_revision_id") != revision_id:
        errors.append(f"publication_manifest_revision_mismatch:{revision_id}")
    if revision.get("field_revision_id") != revision_id:
        errors.append(f"revision_id_mismatch:{revision_id}")
    if receipt.get("field_revision_id") != revision_id:
        errors.append(f"receipt_revision_mismatch:{revision_id}")
    if manifest.get("field_id") != revision.get("field_id"):
        errors.append(f"publication_manifest_field_mismatch:{revision_id}")
    if expected_field_id is not None and manifest.get("field_id") != expected_field_id:
        errors.append(f"head_field_id_mismatch:{revision_id}")
    if expected_field_id is not None and revision.get("field_id") != expected_field_id:
        errors.append(f"head_revision_field_id_mismatch:{revision_id}")
    if manifest.get("batch_id") != revision.get("batch_id") or manifest.get("batch_id") != receipt.get("batch_id"):
        errors.append(f"publication_batch_mismatch:{revision_id}")
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
