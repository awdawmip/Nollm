"""Exact file-source windows for the geometry-native ingestion path."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re


SOURCE_TYPES = frozenset({"markdown", "text", "json", "jsonl", "code", "chat_log"})


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    source_path: str
    source_type: str
    content: str
    recorded_at: str
    revision: str
    encoding: str = "utf-8"
    newline_style: str = "none"

    def __post_init__(self) -> None:
        if self.source_type not in SOURCE_TYPES or not all(isinstance(value, str) and value for value in (self.source_id, self.source_path, self.content, self.recorded_at, self.revision, self.encoding, self.newline_style)):
            raise ValueError("invalid source document")


@dataclass(frozen=True)
class SourceWindow:
    window_id: str
    source_id: str
    source_path: str
    source_type: str
    encoding: str
    newline_style: str
    start_offset: int
    end_offset: int
    ordinal: int
    content: str
    recorded_at: str

    def __post_init__(self) -> None:
        if self.start_offset < 0 or self.end_offset <= self.start_offset or self.ordinal < 0:
            raise ValueError("invalid source window span")
        if not self.content:
            raise ValueError("source window content is required")

    @property
    def fingerprint(self) -> str:
        return sha256(self.content.encode("utf-8")).hexdigest()


class FileSourceConnector:
    """Read local UTF-8 files without normalizing, parsing, or summarizing."""
    def load(self, path: Path, recorded_at: str) -> SourceDocument:
        path = Path(path)
        raw = path.read_bytes()
        content = raw.decode("utf-8")
        source_type = _source_type(path)
        identity = sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:24]
        revision = sha256(raw).hexdigest()
        return SourceDocument(f"source:grf:{identity}", str(path), source_type, content, recorded_at, revision, "utf-8", _newline_style(content))

    def windows(self, document: SourceDocument) -> tuple[SourceWindow, ...]:
        spans = _spans(document.content, document.source_type)
        return tuple(
            SourceWindow(
                f"window:grf:{document.source_id.rsplit(':', 1)[-1]}:{ordinal}:{sha256(document.content[start:end].encode('utf-8')).hexdigest()[:16]}",
                document.source_id, document.source_path, document.source_type,
                document.encoding, document.newline_style, start, end, ordinal,
                document.content[start:end], document.recorded_at,
            )
            for ordinal, (start, end) in enumerate(spans)
            if document.content[start:end]
        )


class MarkdownSource(FileSourceConnector):
    pass


class TextSource(FileSourceConnector):
    pass


class JsonSource(FileSourceConnector):
    pass


class JsonlSource(FileSourceConnector):
    pass


class CodeSource(FileSourceConnector):
    pass


class ChatLogSource(FileSourceConnector):
    pass


def connector_for(source_type: str) -> FileSourceConnector:
    mapping = {"markdown": MarkdownSource, "text": TextSource, "json": JsonSource, "jsonl": JsonlSource, "code": CodeSource, "chat_log": ChatLogSource}
    if source_type not in mapping:
        raise ValueError("unsupported source type")
    return mapping[source_type]()


def _source_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".json":
        return "json"
    if suffix == ".jsonl":
        return "jsonl"
    if suffix in {".py", ".ts", ".js", ".ps1", ".java", ".go", ".rs"}:
        return "code"
    if suffix in {".chat", ".log"}:
        return "chat_log"
    return "text"


def _newline_style(content: str) -> str:
    if "\r\n" in content:
        return "crlf" if "\n" not in content.replace("\r\n", "") else "mixed"
    return "lf" if "\n" in content else "none"


def _spans(content: str, source_type: str) -> tuple[tuple[int, int], ...]:
    if source_type == "json":
        return ((0, len(content)),)
    if source_type == "jsonl":
        return _line_spans(content)
    if source_type == "markdown":
        return _markdown_spans(content)
    if source_type == "code":
        return _code_spans(content)
    return _paragraph_spans(content)


def _line_spans(content: str) -> tuple[tuple[int, int], ...]:
    spans, offset = [], 0
    for line in content.splitlines(keepends=True):
        end = offset + len(line)
        if line.strip():
            spans.append((offset, end))
        offset = end
    if offset < len(content) and content[offset:].strip():
        spans.append((offset, len(content)))
    return tuple(spans) or ((0, len(content)),)


def _markdown_spans(content: str) -> tuple[tuple[int, int], ...]:
    starts, offset, fenced = [0], 0, False
    for line in content.splitlines(keepends=True):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and re.match(r"^[ \t]{0,3}#{1,6}[ \t]", line) and offset != 0:
            starts.append(offset)
        offset += len(line)
    return _ranges(starts, len(content))


def _code_spans(content: str) -> tuple[tuple[int, int], ...]:
    starts, offset = [0], 0
    for line in content.splitlines(keepends=True):
        if offset != 0 and re.match(r"^(?:async[ \t]+def|def|class)[ \t]", line):
            starts.append(offset)
        offset += len(line)
    return _ranges(starts, len(content))


def _paragraph_spans(content: str) -> tuple[tuple[int, int], ...]:
    starts = [0]
    for match in re.finditer(r"(?:\r?\n)[ \t]*(?:\r?\n)+", content):
        if match.end() < len(content):
            starts.append(match.end())
    return _ranges(starts, len(content))


def _ranges(starts: list[int], length: int) -> tuple[tuple[int, int], ...]:
    unique = sorted(set(starts))
    return tuple((start, end) for start, end in zip(unique, (*unique[1:], length)) if end > start)
