from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from stat import S_ISREG

from .safe_storage import open_existing_source_root, safe_list_regular_files, safe_read_regular


POLICY_ID = "openclaw_legacy_v1"
ALLOWED_LEGACY_FILES = ("MEMORY.md", "DREAMS.md")
EXCLUDED_DIRS = {".git", "archive", "field", "ingress", "quarantine", "locks", "__pycache__"}


@dataclass(frozen=True)
class SourcePolicyEntry:
    relative_path: str
    origin_kind: str
    epistemic_state: str
    operational_state: str


def enumerate_legacy_sources(workspace: Path, policy_id: str = POLICY_ID) -> list[SourcePolicyEntry]:
    if policy_id != POLICY_ID:
        raise ValueError(f"unsupported source policy: {policy_id}")
    root = open_existing_source_root(workspace)
    entries: list[SourcePolicyEntry] = []
    for name in ALLOWED_LEGACY_FILES:
        path = root / name
        if path.exists():
            entries.append(_entry(root, path))
    memory_dir = root / "memory"
    if memory_dir.exists():
        for path in safe_list_regular_files(root, "memory", suffix=".md"):
            if _is_excluded(path.relative_to(root)):
                continue
            entries.append(_entry(root, path))
    return sorted(entries, key=lambda item: item.relative_path)


def validate_relative_source_path(relative_path: str) -> None:
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError("source path must be relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("source path must not contain empty, dot, or parent segments")
    if _is_excluded(path):
        raise ValueError(f"source path is excluded by policy: {relative_path}")
    allowed = relative_path in ALLOWED_LEGACY_FILES or (path.parts[:1] == ("memory",) and path.suffix == ".md")
    if not allowed:
        raise ValueError(f"source path is not allowed by policy: {relative_path}")


def resolve_source_path(workspace: Path, relative_path: str) -> Path:
    validate_relative_source_path(relative_path)
    root = workspace.resolve()
    raw_target = root / relative_path
    if raw_target.is_symlink():
        raise ValueError(f"source path is a symlink: {relative_path}")
    if raw_target.exists() and not raw_target.is_file():
        raise ValueError(f"source_not_regular:{relative_path}")
    target = raw_target.resolve()
    if not _is_relative_to(target, root):
        raise ValueError(f"source path escapes workspace: {relative_path}")
    if target.is_symlink():
        raise ValueError(f"source path is a symlink: {relative_path}")
    return target


def read_stable_source_bytes(workspace: Path, relative_path: str) -> bytes:
    try:
        validate_relative_source_path(relative_path)
        root = open_existing_source_root(workspace)
        return safe_read_regular(root, *Path(relative_path).parts, label=f"source:{relative_path}", require_private_inode=False)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("path_symlink"):
            raise ValueError(f"source path is a symlink: {relative_path}") from exc
        if message.startswith("path_not_file"):
            raise ValueError(f"source_not_regular:{relative_path}") from exc
        if message.startswith("file_changed"):
            raise ValueError(f"source_changed_during_snapshot:{relative_path}") from exc
        raise ValueError(f"source_unreadable:{relative_path}:{message}") from exc


def state_for_path(relative_path: str) -> dict[str, str]:
    validate_relative_source_path(relative_path)
    if relative_path == "DREAMS.md":
        epistemic = "tentative"
    else:
        epistemic = "legacy_recorded"
    return {
        "origin_kind": "legacy_import",
        "epistemic_state": epistemic,
        "operational_state": "loose",
    }


def _entry(root: Path, path: Path) -> SourcePolicyEntry:
    if path.is_symlink():
        raise ValueError(f"source path is a symlink: {path}")
    if not path.is_file():
        raise ValueError(f"source_not_regular:{path.relative_to(root).as_posix()}")
    resolved = path.resolve()
    if not _is_relative_to(resolved, root):
        raise ValueError(f"source path escapes workspace: {path}")
    relative = resolved.relative_to(root).as_posix()
    states = state_for_path(relative)
    return SourcePolicyEntry(relative_path=relative, **states)


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
