from __future__ import annotations

import json
import os
import stat
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping

from .safe_root import SafeRoot, SafeRootError


class SafeStorageError(ValueError):
    """Structured error from safe storage operations."""


def open_existing_memory_root(root: Path | str) -> Path:
    try:
        sr = SafeRoot.open_existing(root)
        sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc
    return Path(root).resolve()


def initialize_memory_root(root: Path | str) -> Path:
    try:
        sr = SafeRoot.initialize(root)
        sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc
    return Path(root).resolve()


def open_existing_source_root(root: Path | str) -> Path:
    return open_existing_memory_root(root)


def safe_mkdirs(root: Path, parts: Iterable[str], *, label: str) -> Path:
    parts_tuple = tuple(parts)
    try:
        sr = SafeRoot.open_existing(root)
        try:
            return sr._ensure_parent_dirs(*parts_tuple, label=label)
        finally:
            sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc


def safe_read_regular(root: Path, *parts: str, label: str, require_private_inode: bool = True) -> bytes:
    try:
        sr = SafeRoot.open_existing(root)
        try:
            return sr.read_bytes(*parts, label=label, require_private=require_private_inode)
        finally:
            sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc


def safe_read_text(root: Path, *parts: str, label: str) -> str:
    return safe_read_regular(root, *parts, label=label).decode("utf-8")


def safe_read_file(path: Path, *, label: str, require_private: bool = True) -> bytes:
    """Deprecated: use safe_read_regular(root, *parts) for authoritative MT1 reads."""
    try:
        sr = SafeRoot.open_existing(path.parent)
        try:
            return sr.read_bytes(path.name, label=label, require_private=require_private)
        finally:
            sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc


def safe_write_file(path: Path, data: bytes, *, label: str, replace: bool = True) -> None:
    """Deprecated: use safe_atomic_write(root, parts, ...) for authoritative MT1 writes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        sr = SafeRoot.open_existing(path.parent)
        try:
            sr.write_bytes(path.name, data=data, label=label, replace=replace, allow_idempotent=False)
        finally:
            sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc


def safe_atomic_write(
    root: Path,
    parts: Iterable[str],
    data: bytes,
    *,
    label: str,
    replace: bool = True,
    allow_idempotent: bool = False,
) -> str:
    parts_tuple = tuple(parts)
    if os.environ.get(_env_hook(label, "BEFORE_REPLACE")) == "1":
        raise OSError(f"forced_before_replace:{label}")
    try:
        sr = SafeRoot.open_existing(root)
        try:
            return sr.write_bytes(*parts_tuple, data=data, label=label, replace=replace, allow_idempotent=allow_idempotent)
        finally:
            sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc


def safe_atomic_json(
    root: Path,
    parts: Iterable[str],
    data: Mapping[str, Any],
    *,
    label: str,
    replace: bool = True,
    allow_idempotent: bool = False,
) -> str:
    return safe_atomic_write(
        root,
        parts,
        json_dumps(data).encode("utf-8"),
        label=label,
        replace=replace,
        allow_idempotent=allow_idempotent,
    )


def safe_atomic_jsonl(root: Path, parts: Iterable[str], records: list[dict[str, Any]], *, label: str, replace: bool = True, allow_idempotent: bool = False) -> str:
    payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n" for record in records).encode("utf-8")
    return safe_atomic_write(root, parts, payload, label=label, replace=replace, allow_idempotent=allow_idempotent)


def safe_append_jsonl(root: Path, parts: Iterable[str], record: dict[str, Any], *, label: str) -> None:
    parts_tuple = tuple(parts)
    try:
        sr = SafeRoot.open_existing(root)
        try:
            sr.append_jsonl(*parts_tuple, record=record, label=label)
        finally:
            sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc


def read_json_bytes(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise SafeStorageError(f"malformed_json:{label}") from exc
    except ValueError as exc:
        raise SafeStorageError(str(exc)) from exc


def read_jsonl_bytes(data: bytes, label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, line in enumerate(data.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = read_json_bytes(line.encode("utf-8"), f"{label}:{index}")
        if not isinstance(item, dict):
            raise SafeStorageError(f"invalid_jsonl_record:{label}:{index}")
        records.append(item)
    return records


def json_dumps(data: Mapping[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"


def contained_child(root: Path, *parts: str, label: str, must_exist: bool) -> Path:
    root_abs = Path(root).resolve()
    current = root_abs
    for part in parts:
        if not isinstance(part, str) or part in {"", ".", ".."} or "/" in part or "\\" in part or "\x00" in part:
            raise SafeStorageError(f"unsafe_path_segment:{label}")
        current = current / part
    if must_exist and not current.exists():
        raise SafeStorageError(f"path_missing:{label}")
    return current


def safe_list_regular_files(root: Path, *parts: str, suffix: str) -> list[Path]:
    try:
        sr = SafeRoot.open_existing(root)
        try:
            return sr.list_regular_files(*parts, suffix=suffix)
        finally:
            sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc


def path_has_private_regular_inode(path: Path, label: str) -> list[str]:
    try:
        sr = SafeRoot.open_existing(path.parent)
        try:
            return sr.verify_private_inode(path.name, label=label)
        finally:
            sr.close()
    except SafeRootError as exc:
        return [str(exc)]


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non_finite_json_number:{value}")


def _env_hook(label: str, suffix: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in label.upper())
    return f"NOLLM_SAFE_STORAGE_{normalized}_{suffix}"


def safe_append_jsonl_serialized(root: Path, parts: Iterable[str], record_line: bytes, *, label: str) -> None:
    """Atomically append a pre-serialized record line to a JSONL file."""
    parts_tuple = tuple(parts)
    try:
        sr = SafeRoot.open_existing(root)
        try:
            sr.append_jsonl_serialized(*parts_tuple, record_line=record_line, label=label)
        finally:
            sr.close()
    except SafeRootError as exc:
        raise SafeStorageError(str(exc)) from exc
