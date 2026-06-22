from __future__ import annotations

import json
import os
import stat
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping


class SafeStorageError(ValueError):
    pass


def open_existing_memory_root(root: Path | str) -> Path:
    path = Path(root)
    if not path.exists():
        raise SafeStorageError("memory_root_missing")
    return _controlled_directory(path, "memory_root")


def initialize_memory_root(root: Path | str) -> Path:
    path = Path(root)
    _verify_existing_ancestors(path)
    path.mkdir(parents=True, exist_ok=True)
    return _controlled_directory(path, "memory_root")


def open_existing_source_root(root: Path | str) -> Path:
    path = Path(root)
    if not path.exists():
        raise SafeStorageError("source_root_missing")
    return _controlled_directory(path, "source_root")


def safe_mkdirs(root: Path, parts: Iterable[str], *, label: str) -> Path:
    target = contained_child(root, *parts, label=label, must_exist=False)
    current = root
    for part in parts:
        current = current / part
        _ensure_child_contained(root, current, label)
        if current.exists():
            _controlled_directory(current, label)
            continue
        current.mkdir()
        _controlled_directory(current, label)
    return target


def safe_read_regular(root: Path, *parts: str, label: str, require_private_inode: bool = True) -> bytes:
    path = contained_child(root, *parts, label=label, must_exist=True)
    before = _regular_lstat(path, label, require_private_inode=require_private_inode)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise SafeStorageError(f"unreadable:{label}") from exc
    after = _regular_lstat(path, label, require_private_inode=require_private_inode)
    if _identity(before) != _identity(after):
        raise SafeStorageError(f"file_changed:{label}")
    _ensure_child_contained(root, path, label)
    return data


def safe_read_text(root: Path, *parts: str, label: str) -> str:
    return safe_read_regular(root, *parts, label=label).decode("utf-8")


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
    target = contained_child(root, *parts_tuple, label=label, must_exist=False)
    parent_parts = parts_tuple[:-1]
    parent = safe_mkdirs(root, parent_parts, label=f"{label}_parent") if parent_parts else root
    _controlled_directory(parent, f"{label}_parent")
    if target.exists():
        if not replace:
            existing = safe_read_regular(root, *parts_tuple, label=label)
            if allow_idempotent and existing == data:
                return "reused"
            raise SafeStorageError(f"path_exists:{label}")
        _regular_lstat(target, label, require_private_inode=False)
    tmp_name = f".{target.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}"
    tmp = parent / tmp_name
    _ensure_child_contained(root, tmp, f"{label}_tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(tmp, flags, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        _regular_lstat(tmp, f"{label}_tmp", require_private_inode=True)
        if os.environ.get(_env_hook(label, "BEFORE_REPLACE")) == "1":
            raise OSError(f"forced_before_replace:{label}")
        os.replace(tmp, target)
        _regular_lstat(target, label, require_private_inode=True)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    return "written"


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


def safe_atomic_jsonl(root: Path, parts: Iterable[str], records: list[dict[str, Any]], *, label: str, replace: bool = True) -> str:
    payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n" for record in records).encode("utf-8")
    return safe_atomic_write(root, parts, payload, label=label, replace=replace)


def safe_append_jsonl(root: Path, parts: Iterable[str], record: dict[str, Any], *, label: str) -> None:
    parts_tuple = tuple(parts)
    records: list[dict[str, Any]]
    target = contained_child(root, *parts_tuple, label=label, must_exist=False)
    if target.exists():
        records = read_jsonl_bytes(safe_read_regular(root, *parts_tuple, label=label), label)
    else:
        records = []
    records.append(record)
    safe_atomic_jsonl(root, parts_tuple, records, label=label, replace=True)


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
    root_abs = _controlled_directory(root, "memory_root")
    current = root_abs
    for part in parts:
        if not isinstance(part, str) or part in {"", ".", ".."} or "/" in part or "\\" in part or "\x00" in part:
            raise SafeStorageError(f"unsafe_path_segment:{label}")
        current = current / part
        if current.exists() or current.is_symlink():
            _reject_unsafe_lstat(current, label, allow_file=True, allow_dir=True)
    _ensure_child_contained(root_abs, current, label)
    if must_exist and not current.exists():
        raise SafeStorageError(f"path_missing:{label}")
    return current


def safe_list_regular_files(root: Path, *parts: str, suffix: str) -> list[Path]:
    base = contained_child(root, *parts, label="source_tree", must_exist=False)
    if not base.exists():
        return []
    _controlled_directory(base, "source_tree")
    files: list[Path] = []
    for current_root, dirs, names in os.walk(base, followlinks=False):
        current = Path(current_root)
        _controlled_directory(current, "source_tree")
        kept_dirs: list[str] = []
        for name in sorted(dirs):
            child = current / name
            _controlled_directory(child, "source_tree")
            kept_dirs.append(name)
        dirs[:] = kept_dirs
        for name in sorted(names):
            path = current / name
            if suffix and not name.endswith(suffix):
                continue
            _regular_lstat(path, "source_file", require_private_inode=False)
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def path_has_private_regular_inode(path: Path, label: str) -> list[str]:
    try:
        _regular_lstat(path, label, require_private_inode=True)
    except SafeStorageError as exc:
        return [str(exc)]
    return []


def _controlled_directory(path: Path, label: str) -> Path:
    try:
        st = path.lstat()
    except OSError as exc:
        raise SafeStorageError(f"path_unreadable:{label}:{exc.__class__.__name__}") from exc
    if _is_reparse_or_symlink(st):
        raise SafeStorageError(f"path_symlink:{label}")
    if not stat.S_ISDIR(st.st_mode):
        raise SafeStorageError(f"path_not_directory:{label}")
    if getattr(st, "st_nlink", 1) < 1:
        raise SafeStorageError(f"path_invalid_link_count:{label}")
    return path.resolve()


def _regular_lstat(path: Path, label: str, *, require_private_inode: bool) -> os.stat_result:
    try:
        st = path.lstat()
    except OSError as exc:
        raise SafeStorageError(f"path_unreadable:{label}:{exc.__class__.__name__}") from exc
    if _is_reparse_or_symlink(st):
        raise SafeStorageError(f"path_symlink:{label}")
    if not stat.S_ISREG(st.st_mode):
        raise SafeStorageError(f"path_not_file:{label}")
    if require_private_inode and getattr(st, "st_nlink", 1) != 1:
        raise SafeStorageError(f"path_hardlink:{label}")
    return st


def _reject_unsafe_lstat(path: Path, label: str, *, allow_file: bool, allow_dir: bool) -> None:
    try:
        st = path.lstat()
    except OSError as exc:
        raise SafeStorageError(f"path_unreadable:{label}:{exc.__class__.__name__}") from exc
    if _is_reparse_or_symlink(st):
        raise SafeStorageError(f"path_symlink:{label}")
    if stat.S_ISDIR(st.st_mode):
        if not allow_dir:
            raise SafeStorageError(f"path_not_file:{label}")
        return
    if stat.S_ISREG(st.st_mode):
        if not allow_file:
            raise SafeStorageError(f"path_not_directory:{label}")
        return
    raise SafeStorageError(f"path_not_regular:{label}")


def _verify_existing_ancestors(path: Path) -> None:
    ancestors = [path]
    current = path
    while not current.exists():
        parent = current.parent
        if parent == current:
            break
        ancestors.append(parent)
        current = parent
    if current.exists():
        _controlled_directory(current, "memory_root_parent")
    for ancestor in reversed(ancestors[1:]):
        if ancestor.exists() or ancestor.is_symlink():
            _controlled_directory(ancestor, "memory_root_parent")


def _ensure_child_contained(root: Path, child: Path, label: str) -> None:
    root_abs = root.resolve()
    try:
        child.resolve(strict=False).relative_to(root_abs)
    except ValueError as exc:
        raise SafeStorageError(f"path_escape:{label}") from exc
    current = root_abs
    rel = child.resolve(strict=False).relative_to(root_abs)
    for part in rel.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            _reject_unsafe_lstat(current, label, allow_file=True, allow_dir=True)


def _identity(st: os.stat_result) -> tuple[int, int, int, int]:
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)


def _is_reparse_or_symlink(st: os.stat_result) -> bool:
    if stat.S_ISLNK(st.st_mode):
        return True
    attrs = getattr(st, "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


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
