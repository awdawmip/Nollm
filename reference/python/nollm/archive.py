from __future__ import annotations

from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .archive_manifest import canonical_json, detect_encoding, manifest_hash, newline_profile, read_json, sha256_bytes, write_json
from .path_safety import contained_path, ensure_contained_parent, validate_sha256_hex, validate_snapshot_id, validate_source_object_id
from .source_policy import POLICY_ID, enumerate_legacy_sources, resolve_source_path, state_for_path, validate_relative_source_path


ARCHIVE_SCHEMA = "nollm.archive_manifest.v3"
LEGACY_ARCHIVE_V2_ERROR = "legacy_mt1_archive_v2_requires_rearchive"
SOURCE_FIELDS = {
    "archived_path",
    "byte_length",
    "content_hash",
    "encoding",
    "epistemic_state",
    "line_count",
    "newline_profile",
    "operational_state",
    "origin_kind",
    "original_relative_path",
    "source_object_id",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def memory_root_path(memory_root: Path | str) -> Path:
    raw = Path(memory_root)
    if raw.exists() and raw.is_symlink():
        raise ValueError("unsafe_storage_root")
    root = raw.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_archive_snapshot(workspace: Path | str, memory_root: Path | str, *, policy_id: str = POLICY_ID) -> dict[str, Any]:
    try:
        workspace_path = Path(workspace).resolve()
        root = memory_root_path(memory_root)
        assert_memory_root_outside_workspace(workspace_path, root)
        if policy_id != POLICY_ID:
            return {"ok": False, "errors": [f"unsupported_source_policy:{policy_id}"]}
        archive_errors = ensure_contained_parent(root, root / "archive" / "objects" / "sha256" / "placeholder", "archive_objects")
        archive_errors.extend(ensure_contained_parent(root, root / "archive" / "manifests" / "placeholder.json", "archive_manifests"))
        if archive_errors:
            return {"ok": False, "errors": archive_errors}
        created_at = utc_now()
        sources = enumerate_legacy_sources(workspace_path, policy_id)
        source_bytes: dict[str, bytes] = {}
        content_digests: dict[str, str] = {}
        for source in sources:
            try:
                path = resolve_source_path(workspace_path, source.relative_path)
                before = path.read_bytes()
            except ValueError as exc:
                return {"ok": False, "errors": [str(exc)]}
            except OSError as exc:
                return {"ok": False, "errors": [f"source_unreadable:{source.relative_path}:{exc.__class__.__name__}"]}
            digest = sha256_bytes(before)
            source_bytes[source.relative_path] = before
            content_digests[source.relative_path] = digest
            if path.read_bytes() != before:
                return {"ok": False, "errors": [f"source_changed_during_snapshot:{source.relative_path}"]}
        seed_digest = snapshot_seed_digest(policy_id, content_digests)
        snapshot_id = f"snap_{created_at.replace('-', '').replace(':', '').replace('T', '_').replace('Z', '')}_{seed_digest[:12]}"
        source_records: list[dict[str, Any]] = []
        for source in sources:
            before = source_bytes[source.relative_path]
            digest = content_digests[source.relative_path]
            _, object_errors = contained_path(root, "archive", "objects", "sha256", digest, label="archive_object", must_exist=False)
            object_errors.extend(validate_sha256_hex(digest))
            if object_errors:
                return {"ok": False, "snapshot_id": snapshot_id, "errors": object_errors}
            object_path = root / "archive" / "objects" / "sha256" / digest
            object_path.parent.mkdir(parents=True, exist_ok=True)
            if object_path.exists():
                if object_path.is_symlink() or not object_path.is_file():
                    return {"ok": False, "snapshot_id": snapshot_id, "errors": [f"archive_object_not_regular:{digest}"]}
                existing = object_path.read_bytes()
                if sha256_bytes(existing) != digest:
                    return {"ok": False, "snapshot_id": snapshot_id, "errors": [f"archive_object_hash_mismatch_existing:{digest}"]}
            else:
                object_path.write_bytes(before)
            source_records.append(canonical_source_entry(snapshot_id, policy_id, source.relative_path, before))
        pre_manifest = {
            "schema": ARCHIVE_SCHEMA,
            "snapshot_id": snapshot_id,
            "created_at": created_at,
            "workspace_identity": workspace_path.name,
            "source_policy_id": policy_id,
            "sources": source_records,
            "snapshot_seed_hash": "sha256:" + seed_digest,
            "manifest_hash": None,
            "archive_manifest_hash": None,
        }
        pre_manifest["archive_manifest_hash"] = manifest_hash(pre_manifest)
        pre_manifest["manifest_hash"] = pre_manifest["archive_manifest_hash"]
        path = root / "archive" / "manifests" / f"{pre_manifest['snapshot_id']}.json"
        manifest_errors = ensure_contained_parent(root, path, "archive_manifest")
        if manifest_errors:
            return {"ok": False, "snapshot_id": snapshot_id, "errors": manifest_errors}
        write_json(path, pre_manifest)
        return {
            "ok": True,
            "snapshot_id": pre_manifest["snapshot_id"],
            "manifest_path": str(path),
            "source_count": len(source_records),
            "object_count": len(source_records),
            "manifest_hash": pre_manifest["manifest_hash"],
            "archive_manifest_hash": pre_manifest["archive_manifest_hash"],
        }
    except ValueError as exc:
        return {"ok": False, "errors": [str(exc)]}


def assert_memory_root_outside_workspace(workspace: Path | str, memory_root: Path | str) -> None:
    workspace_path = Path(workspace).resolve()
    root = Path(memory_root).resolve()
    if workspace_path == root:
        raise ValueError("memory root must not equal workspace")
    if _is_relative_to(root, workspace_path):
        raise ValueError("memory root must not be inside workspace")
    if _is_relative_to(workspace_path, root):
        raise ValueError("workspace must not be inside memory root")


def load_manifest(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    errors = validate_snapshot_id(snapshot_id)
    if errors:
        raise ValueError(errors[0])
    root = memory_root_path(memory_root)
    path, path_errors = contained_path(root, "archive", "manifests", f"{snapshot_id}.json", label="archive_manifest", must_exist=True, require_file=True)
    if path_errors:
        raise ValueError(path_errors[0])
    return read_json(path)


def archive_sources(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    sources = manifest.get("sources")
    return sources if isinstance(sources, list) else []


def canonical_source_entry(snapshot_id: str, policy_id: str, relative_path: str, data: bytes) -> dict[str, Any]:
    digest = sha256_bytes(data)
    content_hash = "sha256:" + digest
    states = state_for_path(relative_path)
    source_object_id = canonical_source_object_id(snapshot_id, policy_id, relative_path, content_hash)
    return {
        "source_object_id": source_object_id,
        "original_relative_path": relative_path,
        "content_hash": content_hash,
        "byte_length": len(data),
        "line_count": data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0),
        "encoding": detect_encoding(data),
        "newline_profile": newline_profile(data),
        "archived_path": canonical_archived_path(snapshot_id, source_object_id, digest),
        "origin_kind": states["origin_kind"],
        "epistemic_state": states["epistemic_state"],
        "operational_state": states["operational_state"],
    }


def canonical_source_object_id(snapshot_id: str, policy_id: str, relative_path: str, content_hash: str) -> str:
    payload = f"{snapshot_id}\0{policy_id}\0{relative_path}\0{content_hash}".encode("utf-8")
    return "src_" + sha256_bytes(payload)[:24]


def canonical_archived_path(snapshot_id: str, source_object_id: str, digest: str) -> str:
    return f"archive://snapshot/{snapshot_id}/source/{source_object_id}/blob/sha256:{digest}"


def snapshot_seed_digest(policy_id: str, content_digests: dict[str, str]) -> str:
    return sha256_bytes(
        canonical_json(
            {
                "schema": ARCHIVE_SCHEMA,
                "source_policy_id": policy_id,
                "sources": [(path, "sha256:" + content_digests[path]) for path in sorted(content_digests)],
            }
        )
    )


def verify_archive_snapshot(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    try:
        root = memory_root_path(memory_root)
    except ValueError as exc:
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": [str(exc)], "source_count": 0, "object_count": 0}
    errors: list[str] = []
    errors.extend(validate_snapshot_id(snapshot_id))
    if errors:
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": errors, "source_count": 0, "object_count": 0}
    manifest_path, path_errors = contained_path(root, "archive", "manifests", f"{snapshot_id}.json", label="archive_manifest", must_exist=True, require_file=True)
    errors.extend(path_errors)
    if errors:
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": errors, "source_count": 0, "object_count": 0}
    try:
        manifest = read_json(manifest_path)
    except JSONDecodeError:
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": ["malformed_json:archive_manifest"], "source_count": 0, "object_count": 0}
    except OSError as exc:
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": [f"unreadable_json:archive_manifest:{exc.__class__.__name__}"], "source_count": 0, "object_count": 0}
    if not isinstance(manifest, dict):
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": ["invalid_archive_manifest"], "source_count": 0, "object_count": 0}
    errors.extend(validate_archive_manifest_schema(manifest, expected_snapshot_id=snapshot_id, memory_root=root))
    if manifest.get("archive_manifest_hash", manifest.get("manifest_hash")) != manifest_hash(manifest):
        errors.append("manifest_hash_mismatch")
    sources = archive_sources(manifest)
    report = {
        "ok": not errors,
        "snapshot_id": snapshot_id,
        "archive_verified": not errors,
        "errors": errors,
        "source_count": len(sources),
        "object_count": len(sources),
    }
    return report


def inspect_archive_snapshot(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    verify = verify_archive_snapshot(memory_root, snapshot_id)
    if not verify.get("ok"):
        return verify
    manifest = load_manifest(memory_root, snapshot_id)
    return {
        "ok": True,
        "snapshot_id": snapshot_id,
        "source_policy_id": manifest.get("source_policy_id"),
        "sources": archive_sources(manifest),
        "manifest_hash": manifest.get("manifest_hash"),
        "archive_manifest_hash": manifest.get("archive_manifest_hash"),
    }


def validate_archive_manifest_schema(manifest: dict[str, Any], *, expected_snapshot_id: str | None = None, memory_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    schema = manifest.get("schema")
    if schema == "nollm.archive_manifest.v2":
        return [LEGACY_ARCHIVE_V2_ERROR]
    if schema != ARCHIVE_SCHEMA:
        errors.append("invalid_archive_manifest_schema")
    if "objects" in manifest:
        errors.append("legacy_objects_field_forbidden")
    if "source_entries" in manifest:
        errors.append("legacy_source_entries_field_forbidden")
    snapshot_id = manifest.get("snapshot_id")
    if expected_snapshot_id is not None and snapshot_id != expected_snapshot_id:
        errors.append("archive_snapshot_id_mismatch")
    if not isinstance(snapshot_id, str) or validate_snapshot_id(snapshot_id):
        errors.append("invalid_snapshot_id")
    if manifest.get("source_policy_id") != POLICY_ID:
        errors.append("invalid_source_policy_id")
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        return errors + ["invalid_archive_sources"]
    seed_items: dict[str, str] = {}
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    if isinstance(snapshot_id, str) and not validate_snapshot_id(snapshot_id):
        snapshot_for_id = snapshot_id
    else:
        snapshot_for_id = ""
    for source in sources:
        if not isinstance(source, dict):
            errors.append("invalid_archive_source")
            continue
        unknown = sorted(set(source) - SOURCE_FIELDS)
        for field in unknown:
            errors.append(f"unknown_archive_source_field:{field}")
        if "archive_object_id" in source:
            errors.append("legacy_archive_object_id_forbidden")
        rel = source.get("original_relative_path")
        rel_valid = False
        if not isinstance(rel, str) or not rel:
            errors.append("invalid_original_relative_path")
            rel = ""
        else:
            try:
                validate_relative_source_path(rel)
                rel_valid = True
            except ValueError:
                errors.append(f"source_path_not_allowed:{rel}")
            if rel in seen_paths:
                errors.append(f"duplicate_original_relative_path:{rel}")
            seen_paths.add(rel)
        digest = str(source.get("content_hash", "")).removeprefix("sha256:")
        if validate_sha256_hex(digest):
            errors.append(f"invalid_content_hash:{rel}")
            data = b""
        else:
            data = b""
            if memory_root is not None:
                object_path, object_errors = contained_path(memory_root, "archive", "objects", "sha256", digest, label="archive_object", must_exist=True, require_file=True)
                errors.extend(object_errors)
                if not object_errors:
                    try:
                        data = object_path.read_bytes()
                    except OSError as exc:
                        errors.append(f"unreadable_archive_object:{rel}:{exc.__class__.__name__}")
                    else:
                        if sha256_bytes(data) != digest:
                            errors.append(f"archive_object_hash_mismatch:{rel}")
            seed_items[rel] = digest
        if rel_valid and rel and snapshot_for_id and not validate_sha256_hex(digest):
            expected = canonical_source_entry(snapshot_for_id, POLICY_ID, rel, data)
            for key, expected_value in expected.items():
                if source.get(key) != expected_value:
                    errors.append(f"archive_source_{key}_mismatch:{rel}")
        source_object_id = source.get("source_object_id")
        if validate_source_object_id(source_object_id):
            errors.append(f"invalid_source_object_id:{rel}")
        elif source_object_id in seen_ids:
            errors.append(f"duplicate_source_object_id:{source_object_id}")
        else:
            seen_ids.add(str(source_object_id))
        if not isinstance(source.get("byte_length"), int) or int(source.get("byte_length")) < 0:
            errors.append(f"invalid_byte_length:{rel}")
    if snapshot_for_id:
        seed_digest = snapshot_seed_digest(str(manifest.get("source_policy_id")), seed_items)
        if manifest.get("snapshot_seed_hash") != "sha256:" + seed_digest:
            errors.append("snapshot_seed_hash_mismatch")
        if not snapshot_for_id.endswith(seed_digest[:12]):
            errors.append("snapshot_id_seed_mismatch")
    return errors


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
