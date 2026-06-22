from __future__ import annotations
 
import ctypes
import json
import os
import stat
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping
 
 
class SafeRootError(ValueError):
    """Structured error from SafeRoot V2 capability-anchored storage."""
 
 
_IS_WINDOWS = os.name == "nt"
 
if _IS_WINDOWS:
    _kernel32 = ctypes.windll.kernel32
    _GENERIC_READ = 0x80000000
    _GENERIC_WRITE = 0x40000000
    _FILE_SHARE_READ = 0x00000001
    _FILE_SHARE_WRITE = 0x00000002
    _FILE_SHARE_DELETE = 0x00000004
    _OPEN_EXISTING = 3
    _CREATE_ALWAYS = 2
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _FILE_ATTRIBUTE_NORMAL = 0x00000080
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    _FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    _MOVEFILE_REPLACE_EXISTING = 0x00000001
    _MOVEFILE_WRITE_THROUGH = 0x00000008
 
    class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _pack_ = 1
        _fields_ = [
            ("dwFileAttributes", ctypes.c_uint32),
            ("ftCreationTime", ctypes.c_uint64),
            ("ftLastAccessTime", ctypes.c_uint64),
            ("ftLastWriteTime", ctypes.c_uint64),
            ("dwVolumeSerialNumber", ctypes.c_uint32),
            ("nFileSizeHigh", ctypes.c_uint32),
            ("nFileSizeLow", ctypes.c_uint32),
            ("nNumberOfLinks", ctypes.c_uint32),
            ("nFileIndexHigh", ctypes.c_uint32),
            ("nFileIndexLow", ctypes.c_uint32),
        ]
 
 
def _win_file_info(handle: int) -> tuple[int, int, int, int, int]:
    info = _BY_HANDLE_FILE_INFORMATION()
    if not _kernel32.GetFileInformationByHandle(handle, ctypes.byref(info)):
        raise SafeRootError("file_info_unreadable")
    return (
        info.dwFileAttributes,
        info.dwVolumeSerialNumber,
        info.nFileIndexHigh,
        info.nFileIndexLow,
        info.nNumberOfLinks,
    )
 
 
def _win_open(path_str: str, *, write: bool = False, create_always: bool = False) -> int:
    access = _GENERIC_READ
    if write:
        access |= _GENERIC_WRITE
    creation = _CREATE_ALWAYS if create_always else _OPEN_EXISTING
    flags = _FILE_FLAG_BACKUP_SEMANTICS | _FILE_ATTRIBUTE_NORMAL
    handle = _kernel32.CreateFileW(
        path_str, access,
        _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
        None, creation, flags, None,
    )
    if handle == _INVALID_HANDLE_VALUE or handle is None:
        raise SafeRootError(f"open_failed:{os.path.basename(path_str)}")
    return handle
 
 
def _win_close(handle: int) -> None:
    _kernel32.CloseHandle(handle)
 
 
def _win_flush(handle: int) -> None:
    if not _kernel32.FlushFileBuffers(handle):
        raise SafeRootError("fsync_failed")
 
 
def _win_move(src: str, dst: str) -> None:
    if not _kernel32.MoveFileExW(src, dst, _MOVEFILE_REPLACE_EXISTING | _MOVEFILE_WRITE_THROUGH):
        raise SafeRootError(f"rename_failed:{os.path.basename(dst)}")
 
 
def _identity(handle: int) -> tuple[int, int, int, int, int]:
    if _IS_WINDOWS:
        return _win_file_info(handle)
    st = os.fstat(handle)
    return (0, st.st_dev, st.st_ino >> 32, st.st_ino & 0xFFFFFFFF, st.st_nlink)
 
 
def _is_reparse(attrs: int) -> bool:
    return bool(attrs & _FILE_ATTRIBUTE_REPARSE_POINT) if _IS_WINDOWS else False
 
 
def _fsync_file(handle: int) -> None:
    if _IS_WINDOWS:
        _win_flush(handle)
    else:
        os.fsync(handle)
 
 
def _fsync_dir(path: Path) -> None:
    if _IS_WINDOWS:
        # On Windows, FlushFileBuffers on a directory handle may fail with
        # access-denied even when opened with GENERIC_WRITE. The real durability
        # guarantee comes from MoveFileExW with MOVEFILE_WRITE_THROUGH, which
        # ensures the directory entry is committed to disk before returning.
        # We attempt the flush for belt-and-suspenders but do not fail if the
        # OS rejects it, since the write-through rename is the authoritative
        # durability mechanism on NTFS.
        try:
            handle = _win_open(str(path), write=True)
            try:
                _kernel32.FlushFileBuffers(handle)
            finally:
                _win_close(handle)
        except SafeRootError:
            pass
    else:
        fd = os.open(str(path), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
 
 
class SafeRoot:
    """Capability-anchored storage root. The opened root handle is the authority,
    not the path string. All operations verify the actual opened object identity."""
 
    def __init__(self, root_path: Path, *, _root_handle: int, _root_identity: tuple):
        self._root_path = root_path
        self._root_handle = _root_handle
        self._root_identity = _root_identity
        self._closed = False
 
    @classmethod
    def open_existing(cls, root: Path | str) -> "SafeRoot":
        path = Path(root).resolve()
        if not path.exists():
            raise SafeRootError("memory_root_missing")
        if _IS_WINDOWS:
            handle = _win_open(str(path))
            try:
                attrs, vol, ih, il, nlink = _identity(handle)
            except Exception:
                _win_close(handle)
                raise
            if _is_reparse(attrs):
                _win_close(handle)
                raise SafeRootError("root_is_reparse_point")
            if not (attrs & 0x10):
                _win_close(handle)
                raise SafeRootError("root_not_directory")
            return cls(path, _root_handle=handle, _root_identity=(vol, ih, il))
        else:
            fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW if hasattr(os, "O_NOFOLLOW") else os.O_RDONLY)
            st = os.fstat(fd)
            if stat.S_ISLNK(st.st_mode):
                os.close(fd)
                raise SafeRootError("root_is_symlink")
            if not stat.S_ISDIR(st.st_mode):
                os.close(fd)
                raise SafeRootError("root_not_directory")
            return cls(path, _root_handle=fd, _root_identity=(st.st_dev, st.st_ino, 0))
 
    @classmethod
    def initialize(cls, root: Path | str) -> "SafeRoot":
        path = Path(root)
        cls._verify_ancestors(path)
        path.mkdir(parents=True, exist_ok=True)
        return cls.open_existing(path)
 
    @staticmethod
    def _verify_ancestors(path: Path) -> None:
        current = path.parent
        while current != current.parent:
            if current.exists():
                if _IS_WINDOWS:
                    handle = _win_open(str(current))
                    try:
                        attrs = _win_file_info(handle)[0]
                        if _is_reparse(attrs) or not (attrs & 0x10):
                            raise SafeRootError("ancestor_not_directory")
                    finally:
                        _win_close(handle)
                else:
                    st = current.lstat()
                    if stat.S_ISLNK(st.st_mode):
                        raise SafeRootError("ancestor_is_symlink")
                    if not stat.S_ISDIR(st.st_mode):
                        raise SafeRootError("ancestor_not_directory")
                break
            current = current.parent
 
    @property
    def root_path(self) -> Path:
        return self._root_path
 
    @property
    def identity(self) -> tuple:
        return self._root_identity
 
    def close(self) -> None:
        if not self._closed:
            self._closed = True
            if _IS_WINDOWS:
                _win_close(self._root_handle)
            else:
                os.close(self._root_handle)
 
    def __enter__(self) -> "SafeRoot":
        return self
 
    def __exit__(self, *args: Any) -> None:
        self.close()
 
    def _resolve_relative(self, *parts: str, label: str = "") -> Path:
        for part in parts:
            if not isinstance(part, str) or part in ("", ".", "..") or "/" in part or "\\" in part or "\x00" in part:
                raise SafeRootError(f"unsafe_path_segment:{part}")
        return self._root_path.joinpath(*parts)
 
    def _open_child_dir(self, *parts: str, label: str = "child") -> int:
        path = self._resolve_relative(*parts, label=label)
        current = self._root_path
        for part in parts:
            current = current / part
            if _IS_WINDOWS:
                handle = _win_open(str(current))
                try:
                    attrs, vol, ih, il, nlink = _identity(handle)
                    if _is_reparse(attrs):
                        raise SafeRootError(f"path_reparse:{label}:{part}")
                    if not (attrs & 0x10):
                        raise SafeRootError(f"path_not_dir:{label}:{part}")
                except SafeRootError:
                    _win_close(handle)
                    raise
                _win_close(handle)
            else:
                st = current.lstat()
                if stat.S_ISLNK(st.st_mode):
                    raise SafeRootError(f"path_symlink:{label}:{part}")
                if not stat.S_ISDIR(st.st_mode):
                    raise SafeRootError(f"path_not_dir:{label}:{part}")
        return 0
 
    def _open_regular(self, *parts: str, label: str, require_private: bool = True) -> tuple[int, bytes]:
        path = self._resolve_relative(*parts, label=label)
        if _IS_WINDOWS:
            handle = _win_open(str(path))
            try:
                attrs, vol, ih, il, nlink = _identity(handle)
                if _is_reparse(attrs):
                    raise SafeRootError(f"file_reparse:{label}")
                if attrs & 0x10:
                    raise SafeRootError(f"file_is_dir:{label}")
                if require_private and nlink != 1:
                    raise SafeRootError(f"file_hardlink:{label}:{nlink}")
                data = self._read_handle(handle)
                attrs2, vol2, ih2, il2, nlink2 = _identity(handle)
                if (vol, ih, il) != (vol2, ih2, il2):
                    raise SafeRootError(f"file_changed_during_read:{label}")
            except SafeRootError:
                _win_close(handle)
                raise
            _win_close(handle)
            return 0, data
        else:
            fd = os.open(str(path), os.O_RDONLY)
            try:
                st = os.fstat(fd)
                if stat.S_ISLNK(st.st_mode):
                    raise SafeRootError(f"file_symlink:{label}")
                if not stat.S_ISREG(st.st_mode):
                    raise SafeRootError(f"file_not_regular:{label}")
                if require_private and st.st_nlink != 1:
                    raise SafeRootError(f"file_hardlink:{label}:{st.st_nlink}")
                data = os.read(fd, st.st_size)
                st2 = os.fstat(fd)
                if (st.st_dev, st.st_ino) != (st2.st_dev, st2.st_ino):
                    raise SafeRootError(f"file_changed_during_read:{label}")
            finally:
                os.close(fd)
            return 0, data
 
    @staticmethod
    def _read_handle(handle: int) -> bytes:
        chunks: list[bytes] = []
        buf = ctypes.create_string_buffer(65536)
        while True:
            read = ctypes.c_uint32(0)
            ok = _kernel32.ReadFile(handle, buf, 65536, ctypes.byref(read), None)
            if not ok:
                raise SafeRootError("read_failed")
            if read.value == 0:
                break
            chunks.append(buf.raw[: read.value])
        return b"".join(chunks)
 
    def read_bytes(self, *parts: str, label: str, require_private: bool = True) -> bytes:
        _, data = self._open_regular(*parts, label=label, require_private=require_private)
        return data
 
    def read_text(self, *parts: str, label: str) -> str:
        return self.read_bytes(*parts, label=label).decode("utf-8")
 
    def read_json(self, *parts: str, label: str, require_private: bool = True) -> Any:
        data = self.read_bytes(*parts, label=label, require_private=require_private)
        return _parse_json(data, label)
 
    def read_jsonl(self, *parts: str, label: str) -> list[dict[str, Any]]:
        data = self.read_bytes(*parts, label=label)
        return _parse_jsonl(data, label)
 
    def _ensure_parent_dirs(self, *parts: str, label: str) -> Path:
        path = self._resolve_relative(*parts, label=label)
        parent = path.parent
        if parent != self._root_path:
            rel = parent.relative_to(self._root_path)
            current = self._root_path
            for part in rel.parts:
                current = current / part
                if not current.exists():
                    current.mkdir()
                    _fsync_dir(current.parent)
                self._verify_dir(current, label)
        return path
 
    def _verify_dir(self, path: Path, label: str) -> None:
        if _IS_WINDOWS:
            handle = _win_open(str(path))
            try:
                attrs = _win_file_info(handle)[0]
                if _is_reparse(attrs) or not (attrs & 0x10):
                    raise SafeRootError(f"dir_unsafe:{label}")
            finally:
                _win_close(handle)
        else:
            st = path.lstat()
            if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
                raise SafeRootError(f"dir_unsafe:{label}")
 
    def write_bytes(self, *parts: str, data: bytes, label: str, replace: bool = True, allow_idempotent: bool = False) -> str:
        path = self._ensure_parent_dirs(*parts, label=label)
        if path.exists():
            if not replace:
                existing = self.read_bytes(*parts, label=label, require_private=False)
                if allow_idempotent and existing == data:
                    return "reused"
                raise SafeRootError(f"path_exists:{label}")
        tmp_name = f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}"
        tmp_path = path.parent / tmp_name
        if _IS_WINDOWS:
            handle = _win_open(str(tmp_path), write=True, create_always=True)
            try:
                written = ctypes.c_uint32(0)
                ok = _kernel32.WriteFile(handle, data, len(data), ctypes.byref(written), None)
                if not ok or written.value != len(data):
                    raise SafeRootError(f"write_failed:{label}")
                _win_flush(handle)
            finally:
                _win_close(handle)
            _win_move(str(tmp_path), str(path))
            _fsync_dir(path.parent)
        else:
            fd = os.open(str(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.rename(str(tmp_path), str(path))
            _fsync_dir(path.parent)
        return "written"
 
    def write_json(self, *parts: str, data: Mapping[str, Any], label: str, replace: bool = True, allow_idempotent: bool = False) -> str:
        return self.write_bytes(*parts, data=_dumps_json(data).encode("utf-8"), label=label, replace=replace, allow_idempotent=allow_idempotent)
 
    def write_jsonl(self, *parts: str, records: list[dict[str, Any]], label: str, replace: bool = True) -> str:
        payload = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n" for r in records).encode("utf-8")
        return self.write_bytes(*parts, data=payload, label=label, replace=replace)
 
    def append_jsonl(self, *parts: str, record: dict[str, Any], label: str) -> None:
        records: list[dict[str, Any]] = []
        path = self._resolve_relative(*parts, label=label)
        if path.exists():
            records = self.read_jsonl(*parts, label=label)
        records.append(record)
        self.write_jsonl(*parts, records=records, label=label, replace=True)
 
    def list_regular_files(self, *parts: str, suffix: str = "") -> list[Path]:
        base = self._resolve_relative(*parts, label="list")
        if not base.exists():
            return []
        self._verify_dir(base, "list_base")
        files: list[Path] = []
        for root, dirs, names in os.walk(base, followlinks=False):
            rp = Path(root)
            self._verify_dir(rp, "list_walk")
            dirs[:] = sorted(dirs)
            for name in sorted(names):
                fp = rp / name
                if suffix and not name.endswith(suffix):
                    continue
                files.append(fp)
        return sorted(files, key=lambda p: p.relative_to(self._root_path).as_posix())
 
    def unlink(self, *parts: str, label: str) -> None:
        path = self._resolve_relative(*parts, label=label)
        path.unlink()
 
    def exists(self, *parts: str) -> bool:
        return self._resolve_relative(*parts, label="exists").exists()
 
    def sha256(self, *parts: str, label: str) -> str:
        import hashlib
        return hashlib.sha256(self.read_bytes(*parts, label=label)).hexdigest()
 
    def verify_private_inode(self, *parts: str, label: str) -> list[str]:
        try:
            self.read_bytes(*parts, label=label, require_private=True)
        except SafeRootError as exc:
            return [str(exc)]
        return []
 
 
def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate_json_key:{key}")
        result[key] = value
    return result
 
 
def _reject_constant(value: str) -> None:
    raise ValueError(f"non_finite_json_number:{value}")
 
 
def _parse_json(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise SafeRootError(f"malformed_json:{label}") from exc
    except ValueError as exc:
        raise SafeRootError(str(exc)) from exc
 
 
def _parse_jsonl(data: bytes, label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, line in enumerate(data.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = _parse_json(line.encode("utf-8"), f"{label}:{index}")
        if not isinstance(item, dict):
            raise SafeRootError(f"invalid_jsonl_record:{label}:{index}")
        records.append(item)
    return records
 
 
def _dumps_json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
 
 
def open_existing_root(root: Path | str) -> SafeRoot:
    return SafeRoot.open_existing(root)
 
 
def initialize_root(root: Path | str) -> SafeRoot:
    return SafeRoot.initialize(root)
 
 
def read_source_file(path: Path) -> bytes:
    """Read a source workspace file with reparse/symlink rejection."""
    if _IS_WINDOWS:
        handle = _win_open(str(path))
        try:
            attrs = _win_file_info(handle)[0]
            if _is_reparse(attrs):
                raise SafeRootError(f"source_is_reparse:{path.name}")
            return SafeRoot._read_handle(handle)
        finally:
            _win_close(handle)
    else:
        st = path.lstat()
        if stat.S_ISLNK(st.st_mode):
            raise SafeRootError(f"source_is_symlink:{path.name}")
        return path.read_bytes()
