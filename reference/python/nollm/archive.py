from __future__ import annotations

from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .archive_manifest import detect_encoding, manifest_hash, newline_profile, read_json, sha256_bytes, write_json
from .path_safety import contained_path, ensure_contained_parent, validate_sha256_hex, validate_snapshot_id
from .source_policy import POLICY_ID, enumerate_legacy_sources, resolve_source_path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def memory_root_path(memory_root: Path | str) -> Path:
    root = Path(memory_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_archive_snapshot(workspace: Path | str, memory_root: Path | str, *, policy_id: str = POLICY_ID) -> dict[str, Any]:
    workspace_path = Path(workspace).resolve()
    root = memory_root_path(memory_root)
    assert_memory_root_outside_workspace(workspace_path, root)
    archive_errors = ensure_contained_parent(root, root / "archive" / "objects" / "sha256" / "placeholder", "archive_objects")
    archive_errors.extend(ensure_contained_parent(root, root / "archive" / "manifests" / "placeholder.json", "archive_manifests"))
    if archive_errors:
        return {"ok": False, "errors": archive_errors}
    created_at = utc_now()
    source_entries: list[dict[str, Any]] = []
    sources = enumerate_legacy_sources(workspace_path, policy_id)
    source_bytes: dict[str, bytes] = {}
    content_digests: dict[str, str] = {}
    for source in sources:
        path = resolve_source_path(workspace_path, source.relative_path)
        before = path.read_bytes()
        digest = sha256_bytes(before)
        source_bytes[source.relative_path] = before
        content_digests[source.relative_path] = digest
        if path.read_bytes() != before:
            raise ValueError(f"source changed during snapshot: {source.relative_path}")
    seed_digest = sha256_bytes(str([(path, content_digests[path]) for path in sorted(content_digests)]).encode("utf-8"))
    snapshot_id = f"snap_{created_at.replace('-', '').replace(':', '').replace('T', '_').replace('Z', '')}_{seed_digest[:12]}"
    objects: list[dict[str, Any]] = []
    for source in sources:
        before = source_bytes[source.relative_path]
        digest = content_digests[source.relative_path]
        object_dir = root / "archive" / "objects" / "sha256"
        object_path = object_dir / digest
        _, object_errors = contained_path(root, "archive", "objects", "sha256", digest, label="archive_object", must_exist=False)
        object_errors.extend(validate_sha256_hex(digest))
        if object_errors:
            return {"ok": False, "snapshot_id": snapshot_id, "errors": object_errors}
        object_path.parent.mkdir(parents=True, exist_ok=True)
        if object_path.exists():
            if object_path.is_symlink() or not object_path.is_file():
                return {"ok": False, "snapshot_id": snapshot_id, "errors": [f"archive_object_not_regular:{digest}"]}
            existing = object_path.read_bytes()
            if sha256_bytes(existing) != digest:
                return {"ok": False, "snapshot_id": snapshot_id, "errors": [f"archive_object_hash_mismatch_existing:{digest}"]}
        else:
            object_path.write_bytes(before)
        source_object_id = "src_" + sha256_bytes(f"{snapshot_id}\0{source.relative_path}\0sha256:{digest}".encode("utf-8"))[:24]
        entry = {
            "source_object_id": source_object_id,
            "archive_object_id": source_object_id,
            "original_relative_path": source.relative_path,
            "content_hash": f"sha256:{digest}",
            "byte_length": len(before),
            "line_count": before.count(b"\n") + (1 if before and not before.endswith(b"\n") else 0),
            "encoding": detect_encoding(before),
            "newline_profile": newline_profile(before),
            "archived_path": f"archive://snapshot/{snapshot_id}/source/{source_object_id}/blob/sha256:{digest}",
            "origin_kind": source.origin_kind,
            "epistemic_state": source.epistemic_state,
            "operational_state": source.operational_state,
        }
        source_entries.append(entry)
        objects.append(
            entry
        )
    pre_manifest = {
        "schema": "nollm.archive_manifest.v2",
        "snapshot_id": snapshot_id,
        "created_at": created_at,
        "workspace_identity": workspace_path.name,
        "source_policy_id": policy_id,
        "objects": objects,
        "source_entries": source_entries,
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
    return {"ok": True, "snapshot_id": pre_manifest["snapshot_id"], "manifest_path": str(path), "object_count": len(objects), "manifest_hash": pre_manifest["manifest_hash"], "archive_manifest_hash": pre_manifest["archive_manifest_hash"]}


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


def verify_archive_snapshot(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    errors: list[str] = []
    errors.extend(validate_snapshot_id(snapshot_id))
    if errors:
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": errors, "object_count": 0}
    manifest_path, path_errors = contained_path(root, "archive", "manifests", f"{snapshot_id}.json", label="archive_manifest", must_exist=True, require_file=True)
    errors.extend(path_errors)
    if errors:
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": errors, "object_count": 0}
    try:
        manifest = read_json(manifest_path)
    except JSONDecodeError:
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": ["malformed_json:archive_manifest"], "object_count": 0}
    except OSError as exc:
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": [f"unreadable_json:archive_manifest:{exc.__class__.__name__}"], "object_count": 0}
    if not isinstance(manifest, dict):
        return {"ok": False, "snapshot_id": snapshot_id, "archive_verified": False, "errors": ["invalid_archive_manifest"], "object_count": 0}
    errors.extend(validate_archive_manifest_schema(manifest, expected_snapshot_id=snapshot_id))
    if manifest.get("archive_manifest_hash", manifest.get("manifest_hash")) != manifest_hash(manifest):
        errors.append("manifest_hash_mismatch")
    objects = manifest.get("objects", [])
    if not isinstance(objects, list):
        errors.append("invalid_archive_objects")
        objects = []
    for obj in objects:
        if not isinstance(obj, dict):
            errors.append("invalid_archive_object")
            continue
        digest = str(obj.get("content_hash", "")).removeprefix("sha256:")
        object_path, object_errors = contained_path(root, "archive", "objects", "sha256", digest, label="archive_object", must_exist=True, require_file=True)
        errors.extend(object_errors)
        if object_errors:
            continue
        try:
            data = object_path.read_bytes()
        except OSError as exc:
            errors.append(f"unreadable_archive_object:{obj.get('original_relative_path')}:{exc.__class__.__name__}")
            continue
        if sha256_bytes(data) != digest:
            errors.append(f"archive_object_hash_mismatch:{obj.get('original_relative_path')}")
        if len(data) != obj.get("byte_length"):
            errors.append(f"archive_object_length_mismatch:{obj.get('original_relative_path')}")
    report = {"ok": not errors, "snapshot_id": snapshot_id, "archive_verified": not errors, "errors": errors, "object_count": len(objects)}
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
        "objects": manifest.get("objects", []),
        "manifest_hash": manifest.get("manifest_hash"),
        "archive_manifest_hash": manifest.get("archive_manifest_hash"),
    }


def validate_archive_manifest_schema(manifest: dict[str, Any], *, expected_snapshot_id: str | None = None) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema") != "nollm.archive_manifest.v2":
        errors.append("legacy_mt1_package_requires_reimport")
    snapshot_id = manifest.get("snapshot_id")
    if expected_snapshot_id is not None and snapshot_id != expected_snapshot_id:
        errors.append("archive_snapshot_id_mismatch")
    if not isinstance(snapshot_id, str) or validate_snapshot_id(snapshot_id):
        errors.append("invalid_snapshot_id")
    objects = manifest.get("objects")
    if not isinstance(objects, list):
        return errors + ["invalid_archive_objects"]
    seed_items: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for obj in objects:
        if not isinstance(obj, dict):
            errors.append("invalid_archive_object")
            continue
        source_object_id = obj.get("source_object_id", obj.get("archive_object_id"))
        if not isinstance(source_object_id, str) or not source_object_id.startswith("src_"):
            errors.append("invalid_source_object_id")
        elif source_object_id in seen_ids:
            errors.append(f"duplicate_source_object_id:{source_object_id}")
        else:
            seen_ids.add(source_object_id)
        rel = obj.get("original_relative_path")
        if not isinstance(rel, str) or not rel:
            errors.append("invalid_original_relative_path")
        elif rel in seen_paths:
            errors.append(f"duplicate_original_relative_path:{rel}")
        else:
            seen_paths.add(rel)
        digest = str(obj.get("content_hash", "")).removeprefix("sha256:")
        if validate_sha256_hex(digest):
            errors.append(f"invalid_content_hash:{rel}")
        elif isinstance(rel, str):
            seed_items.append((rel, digest))
        if not isinstance(obj.get("byte_length"), int) or int(obj.get("byte_length")) < 0:
            errors.append(f"invalid_byte_length:{rel}")
    if isinstance(snapshot_id, str) and not validate_snapshot_id(snapshot_id):
        seed_digest = sha256_bytes(str([(path, digest) for path, digest in sorted(seed_items)]).encode("utf-8"))
        if manifest.get("snapshot_seed_hash") != "sha256:" + seed_digest:
            errors.append("snapshot_seed_hash_mismatch")
        if not snapshot_id.endswith(seed_digest[:12]):
            errors.append("snapshot_id_seed_mismatch")
    return errors


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
