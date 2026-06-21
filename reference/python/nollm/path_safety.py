from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


SNAPSHOT_ID_RE = re.compile(r"^snap_[0-9]{8}_[0-9]{6}_[0-9a-f]{12}$")
BATCH_ID_RE = re.compile(r"^batch_[0-9a-f]{20}(?:_recovery)?$")
FIELD_REVISION_ID_RE = re.compile(r"^fieldrev_[0-9a-f]{20}$")
SOURCE_OBJECT_ID_RE = re.compile(r"^src_[0-9a-f]{24}$")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_RELATIVE_ARTIFACT_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


def validate_snapshot_id(value: object) -> list[str]:
    return _validate_id(value, SNAPSHOT_ID_RE, "snapshot_id")


def validate_batch_id(value: object) -> list[str]:
    return _validate_id(value, BATCH_ID_RE, "batch_id")


def validate_field_revision_id(value: object) -> list[str]:
    return _validate_id(value, FIELD_REVISION_ID_RE, "field_revision_id")


def validate_source_object_id(value: object) -> list[str]:
    return _validate_id(value, SOURCE_OBJECT_ID_RE, "source_object_id")


def validate_sha256_hex(value: object) -> list[str]:
    return _validate_id(value, SHA256_HEX_RE, "sha256")


def require_snapshot_id(value: object) -> str:
    return _require_id(value, validate_snapshot_id)


def require_batch_id(value: object) -> str:
    return _require_id(value, validate_batch_id)


def require_field_revision_id(value: object) -> str:
    return _require_id(value, validate_field_revision_id)


def require_source_object_id(value: object) -> str:
    return _require_id(value, validate_source_object_id)


def validate_relative_artifact_path(value: object) -> list[str]:
    if not isinstance(value, str) or not value:
        return ["invalid_artifact_path"]
    if "\x00" in value or "\\" in value or value.startswith("/") or value in {".", ".."}:
        return [f"unsafe_artifact_path:{value}"]
    if not SAFE_RELATIVE_ARTIFACT_RE.match(value):
        return [f"unsafe_artifact_path:{value}"]
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return [f"unsafe_artifact_path:{value}"]
    return []


def contained_path(root: Path, *parts: str, label: str, must_exist: bool = True, require_file: bool | None = None) -> tuple[Path, list[str]]:
    errors: list[str] = []
    root_abs = root.resolve()
    path = root_abs.joinpath(*parts)
    try:
        path.resolve(strict=False).relative_to(root_abs)
    except ValueError:
        errors.append(f"path_escape:{label}")
        return path, errors
    errors.extend(no_symlink_segments(root_abs, path, label))
    if errors:
        return path, errors
    if must_exist:
        if not path.exists():
            errors.append(f"path_missing:{label}")
            return path, errors
        if path.is_symlink():
            errors.append(f"path_symlink:{label}")
            return path, errors
        if require_file is True and not path.is_file():
            errors.append(f"path_not_file:{label}")
        if require_file is False and not path.is_dir():
            errors.append(f"path_not_directory:{label}")
    return path, errors


def no_symlink_segments(root: Path, path: Path, label: str) -> list[str]:
    errors: list[str] = []
    root_abs = root.resolve()
    target_abs = path.absolute()
    try:
        rel = target_abs.relative_to(root_abs)
    except ValueError:
        return [f"path_escape:{label}"]
    current = root_abs
    for part in rel.parts:
        current = current / part
        try:
            if current.exists() and current.is_symlink():
                errors.append(f"path_symlink:{label}:{current.relative_to(root_abs).as_posix()}")
                return errors
        except OSError as exc:
            errors.append(f"path_unreadable:{label}:{exc.__class__.__name__}")
            return errors
    return errors


def ensure_contained_parent(root: Path, path: Path, label: str) -> list[str]:
    parent = path.parent
    try:
        parent.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        return [f"path_escape:{label}"]
    return no_symlink_segments(root, parent, label)


def first_error(errors: Iterable[str]) -> str | None:
    for error in errors:
        return error
    return None


def _validate_id(value: object, pattern: re.Pattern[str], label: str) -> list[str]:
    if not isinstance(value, str) or not pattern.match(value):
        return [f"invalid_{label}"]
    if any(ch.isspace() or ord(ch) < 32 for ch in value):
        return [f"invalid_{label}"]
    return []


def _require_id(value: object, validator) -> str:
    errors = validator(value)
    if errors:
        raise ValueError(errors[0])
    assert isinstance(value, str)
    return value
