from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .archive_manifest import detect_encoding, manifest_hash, newline_profile, read_json, sha256_bytes, write_json
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
    objects: list[dict[str, Any]] = []
    for source in enumerate_legacy_sources(workspace_path, policy_id):
        path = resolve_source_path(workspace_path, source.relative_path)
        before = path.read_bytes()
        digest = sha256_bytes(before)
        object_dir = root / "archive" / "objects" / "sha256"
        object_path = object_dir / digest
        object_path.parent.mkdir(parents=True, exist_ok=True)
        if not object_path.exists():
            object_path.write_bytes(before)
        if path.read_bytes() != before:
            raise ValueError(f"source changed during snapshot: {source.relative_path}")
        objects.append(
            {
                "archive_object_id": f"arc_{digest[:16]}",
                "original_relative_path": source.relative_path,
                "content_hash": f"sha256:{digest}",
                "byte_length": len(before),
                "line_count": before.count(b"\n") + (1 if before and not before.endswith(b"\n") else 0),
                "encoding": detect_encoding(before),
                "newline_profile": newline_profile(before),
                "archived_path": f"archive://object/sha256:{digest}",
                "origin_kind": source.origin_kind,
                "epistemic_state": source.epistemic_state,
                "operational_state": source.operational_state,
            }
        )
    pre_manifest = {
        "schema": "nollm.archive_manifest.v1",
        "snapshot_id": "",
        "created_at": utc_now(),
        "workspace_identity": workspace_path.name,
        "source_policy_id": policy_id,
        "objects": objects,
        "manifest_hash": None,
    }
    digest = sha256_bytes(str([(obj["original_relative_path"], obj["content_hash"]) for obj in objects]).encode("utf-8"))
    pre_manifest["snapshot_id"] = f"snap_{pre_manifest['created_at'].replace('-', '').replace(':', '').replace('T', '_').replace('Z', '')}_{digest[:12]}"
    pre_manifest["manifest_hash"] = manifest_hash(pre_manifest)
    path = root / "archive" / "manifests" / f"{pre_manifest['snapshot_id']}.json"
    write_json(path, pre_manifest)
    return {"ok": True, "snapshot_id": pre_manifest["snapshot_id"], "manifest_path": str(path), "object_count": len(objects), "manifest_hash": pre_manifest["manifest_hash"]}


def load_manifest(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    path = memory_root_path(memory_root) / "archive" / "manifests" / f"{snapshot_id}.json"
    return read_json(path)


def verify_archive_snapshot(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    manifest = load_manifest(root, snapshot_id)
    errors: list[str] = []
    if manifest.get("manifest_hash") != manifest_hash(manifest):
        errors.append("manifest_hash_mismatch")
    for obj in manifest.get("objects", []):
        digest = str(obj.get("content_hash", "")).removeprefix("sha256:")
        object_path = root / "archive" / "objects" / "sha256" / digest
        if not object_path.exists():
            errors.append(f"missing_archive_object:{obj.get('original_relative_path')}")
            continue
        data = object_path.read_bytes()
        if sha256_bytes(data) != digest:
            errors.append(f"archive_object_hash_mismatch:{obj.get('original_relative_path')}")
        if len(data) != obj.get("byte_length"):
            errors.append(f"archive_object_length_mismatch:{obj.get('original_relative_path')}")
    report = {"ok": not errors, "snapshot_id": snapshot_id, "archive_verified": not errors, "errors": errors, "object_count": len(manifest.get("objects", []))}
    return report


def inspect_archive_snapshot(memory_root: Path | str, snapshot_id: str) -> dict[str, Any]:
    manifest = load_manifest(memory_root, snapshot_id)
    return {
        "ok": True,
        "snapshot_id": snapshot_id,
        "source_policy_id": manifest.get("source_policy_id"),
        "objects": manifest.get("objects", []),
        "manifest_hash": manifest.get("manifest_hash"),
    }

