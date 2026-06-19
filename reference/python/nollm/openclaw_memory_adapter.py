from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


SCHEMA = "nollm.openclaw_memory_fixture_index.v1"
FORBIDDEN_SEMANTICS = {
    "real_openclaw_plugin": False,
    "real_llm_call": False,
    "memory_slot_replacement": False,
    "auto_memory_write": False,
    "drift_class_trust_mapping": False,
}


@dataclass(frozen=True)
class OpenClawMemoryChunk:
    memory_id: str
    source_path: str
    line_range: tuple[int, int]
    text: str
    source_role: str
    heading_path: tuple[str, ...]
    source_sha256: str
    chunk_sha256: str

    def to_record(self) -> dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "source_path": self.source_path,
            "line_range": list(self.line_range),
            "text": self.text,
            "source_role": self.source_role,
            "heading_path": list(self.heading_path),
            "source_sha256": self.source_sha256,
            "chunk_sha256": self.chunk_sha256,
        }


@dataclass(frozen=True)
class OpenClawMemoryIndex:
    workspace_root: str
    chunk_count: int
    chunks: tuple[OpenClawMemoryChunk, ...]
    warnings: tuple[str, ...]
    source_files: tuple[str, ...]

    def to_record(self) -> dict[str, object]:
        return {
            "workspace_root": self.workspace_root,
            "chunk_count": self.chunk_count,
            "source_files": list(self.source_files),
            "chunks": [chunk.to_record() for chunk in self.chunks],
            "warnings": list(self.warnings),
        }


def parse_openclaw_memory_workspace(workspace_root: Path | str) -> OpenClawMemoryIndex:
    root = Path(workspace_root).resolve()
    warnings: list[str] = []
    chunks: list[OpenClawMemoryChunk] = []
    source_files: list[str] = []

    if not root.exists():
        warnings.append("workspace_missing")
        return OpenClawMemoryIndex(str(root), 0, (), tuple(warnings), ())

    for path in _memory_source_files(root):
        relative = _relative_posix(root, path)
        source_files.append(relative)
        chunks.extend(_parse_markdown_file(path, source_path=relative, source_role=_source_role(relative)))

    return OpenClawMemoryIndex(
        workspace_root=str(root),
        chunk_count=len(chunks),
        chunks=tuple(chunks),
        warnings=tuple(warnings),
        source_files=tuple(source_files),
    )


def build_openclaw_memory_fixture_report(repo_root: Path | str, workspace: Path | str) -> dict[str, object]:
    repo = Path(repo_root).resolve()
    workspace_path = Path(workspace).resolve()
    index = parse_openclaw_memory_workspace(workspace_path)
    record = index.to_record()
    report = {
        "schema": SCHEMA,
        "ok": not any(FORBIDDEN_SEMANTICS.values()),
        "workspace": _relative_posix(repo, workspace_path) if _is_relative_to(workspace_path, repo) else str(workspace_path),
        "chunk_count": record["chunk_count"],
        "source_files": record["source_files"],
        "chunks": record["chunks"],
        "warnings": record["warnings"],
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }
    _assert_json_primitive(report)
    return report


def write_openclaw_memory_fixture_report(report: Mapping[str, object], output: Path | str) -> None:
    _assert_json_primitive(report)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _memory_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    memory = root / "MEMORY.md"
    dreams = root / "DREAMS.md"
    if memory.exists():
        files.append(memory)
    memory_dir = root / "memory"
    if memory_dir.exists():
        files.extend(sorted(path for path in memory_dir.glob("*.md") if path.is_file()))
    if dreams.exists():
        files.append(dreams)
    return files


def _parse_markdown_file(path: Path, *, source_path: str, source_role: str) -> list[OpenClawMemoryChunk]:
    data = path.read_bytes()
    source_sha256 = _sha256_bytes(data)
    lines = data.decode("utf-8", errors="replace").splitlines()
    chunks: list[OpenClawMemoryChunk] = []
    headings: list[str] = []
    block: list[tuple[int, str]] = []

    def flush_block() -> None:
        if not block:
            return
        text = "\n".join(line.strip() for _, line in block).strip()
        start = block[0][0]
        end = block[-1][0]
        block.clear()
        if not text:
            return
        chunk_sha256 = _sha256_text(text)
        memory_id = _memory_id(source_path, (start, end), chunk_sha256)
        chunks.append(
            OpenClawMemoryChunk(
                memory_id=memory_id,
                source_path=source_path,
                line_range=(start, end),
                text=text,
                source_role=source_role,
                heading_path=tuple(headings),
                source_sha256=source_sha256,
                chunk_sha256=chunk_sha256,
            )
        )

    for line_number, line in enumerate(lines, start=1):
        heading = _parse_heading(line)
        if heading is not None:
            flush_block()
            level, title = heading
            headings = headings[: max(0, level - 1)]
            headings.append(title)
            continue
        if line.strip() == "":
            flush_block()
            continue
        block.append((line_number, line))
    flush_block()
    return chunks


def _parse_heading(line: str) -> tuple[int, str] | None:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return None
    marks = len(stripped) - len(stripped.lstrip("#"))
    if marks == 0 or marks > 6:
        return None
    if len(stripped) <= marks or stripped[marks] != " ":
        return None
    title = stripped[marks:].strip()
    if not title:
        return None
    return marks, title


def _source_role(source_path: str) -> str:
    if source_path == "MEMORY.md":
        return "durable_memory"
    if source_path == "DREAMS.md":
        return "dreams"
    if source_path.startswith("memory/") and source_path.endswith(".md"):
        return "daily_memory"
    return "unknown"


def _memory_id(source_path: str, line_range: tuple[int, int], chunk_sha256: str) -> str:
    raw = f"{source_path}:{line_range[0]}-{line_range[1]}:{chunk_sha256}"
    return f"mem_{_sha256_text(raw)[:16]}"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _relative_posix(base: Path, target: Path) -> str:
    return target.resolve().relative_to(base.resolve()).as_posix()


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _assert_json_primitive(value: object) -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        for item in value:
            _assert_json_primitive(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("report keys must be strings")
            _assert_json_primitive(item)
        return
    raise TypeError(f"report value is not JSON primitive: {type(value).__name__}")


__all__ = [
    "FORBIDDEN_SEMANTICS",
    "SCHEMA",
    "OpenClawMemoryChunk",
    "OpenClawMemoryIndex",
    "build_openclaw_memory_fixture_report",
    "parse_openclaw_memory_workspace",
    "write_openclaw_memory_fixture_report",
]
