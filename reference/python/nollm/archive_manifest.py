from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .safe_storage import json_dumps, read_json_bytes, safe_read_file


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: Mapping[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def manifest_hash(manifest: Mapping[str, Any]) -> str:
    clone = dict(manifest)
    if "manifest_hash" in clone:
        clone["manifest_hash"] = None
    if "archive_manifest_hash" in clone:
        clone["archive_manifest_hash"] = None
    return "sha256:" + sha256_bytes(canonical_json(clone))


def write_json(path: Path, data: Mapping[str, Any]) -> None:
    from .safe_storage import safe_write_file
    safe_write_file(path, json_dumps(data).encode("utf-8"), label=path.name)


def read_json(path: Path) -> dict[str, Any]:
    from .safe_storage import safe_read_file
    data = read_json_bytes(safe_read_file(path, label=path.name, require_private=False), path.name)
    if not isinstance(data, dict):
        raise ValueError("invalid_json:not_object")
    return data


def newline_profile(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    cr = data.count(b"\r") - crlf
    kinds = [name for name, count in (("crlf", crlf), ("lf", lf), ("cr", cr)) if count]
    if not kinds:
        return "none"
    if len(kinds) == 1:
        return kinds[0]
    return "mixed"


def detect_encoding(data: bytes) -> str:
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "binary"

def read_json_root(sr, *parts: str, label: str, require_private: bool = True) -> dict[str, Any]:
    """Root-relative JSON read through SafeRoot V3."""
    data = read_json_bytes(sr.read_bytes(*parts, label=label, require_private=require_private), label)
    if not isinstance(data, dict):
        raise ValueError("invalid_json:not_object")
    return data


def write_json_root(sr, *parts: str, data: Mapping[str, Any], label: str, replace: bool = True, allow_idempotent: bool = False) -> str:
    """Root-relative JSON write through SafeRoot V3."""
    from .safe_storage import safe_atomic_write
    return safe_atomic_write(sr.root_path, parts, json_dumps(data).encode("utf-8"), label=label, replace=replace, allow_idempotent=allow_idempotent)
