from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
    root = workspace.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"workspace is not a directory: {workspace}")
    entries: list[SourcePolicyEntry] = []
    for name in ALLOWED_LEGACY_FILES:
        path = root / name
        if path.exists():
            entries.append(_entry(root, path))
    memory_dir = root / "memory"
    if memory_dir.exists():
        for path in sorted(memory_dir.rglob("*.md")):
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
    target = (root / relative_path).resolve()
    if not _is_relative_to(target, root):
        raise ValueError(f"source path escapes workspace: {relative_path}")
    if target.is_symlink():
        raise ValueError(f"source path is a symlink: {relative_path}")
    return target


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

