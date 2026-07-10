"""File-first source documents and deterministic original-text windows for GRF8."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path


SOURCE_TYPES = frozenset({"markdown", "text", "json", "jsonl", "code", "chat_log"})


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    source_path: str
    source_type: str
    content: str
    recorded_at: str
    revision: str

    def __post_init__(self) -> None:
        if self.source_type not in SOURCE_TYPES or not all(isinstance(value, str) and value for value in self.__dict__.values()):
            raise ValueError("invalid source document")


@dataclass(frozen=True)
class SourceWindow:
    window_id: str
    source_id: str
    ordinal: int
    content: str
    source_type: str
    recorded_at: str


class FileSourceConnector:
    """Read supported local files without summarization or token-sized splitting."""
    def load(self, path: Path, recorded_at: str) -> SourceDocument:
        path = Path(path)
        content = path.read_text(encoding="utf-8")
        source_type = _source_type(path)
        identity = sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:24]
        revision = sha256(content.encode("utf-8")).hexdigest()
        return SourceDocument(f"source:grf8:{identity}", str(path), source_type, content, recorded_at, revision)

    def windows(self, document: SourceDocument) -> tuple[SourceWindow, ...]:
        units = _units(document.content, document.source_type)
        return tuple(SourceWindow(f"window:grf8:{document.source_id.rsplit(':', 1)[-1]}:{index}", document.source_id, index, unit, document.source_type, document.recorded_at) for index, unit in enumerate(units) if unit.strip())


class MarkdownSource(FileSourceConnector): pass
class TextSource(FileSourceConnector): pass
class JsonSource(FileSourceConnector): pass
class JsonlSource(FileSourceConnector): pass
class CodeSource(FileSourceConnector): pass
class ChatLogSource(FileSourceConnector): pass


def connector_for(source_type: str) -> FileSourceConnector:
    mapping = {"markdown": MarkdownSource, "text": TextSource, "json": JsonSource, "jsonl": JsonlSource, "code": CodeSource, "chat_log": ChatLogSource}
    if source_type not in mapping:
        raise ValueError("unsupported source type")
    return mapping[source_type]()


def _source_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}: return "markdown"
    if suffix == ".json": return "json"
    if suffix == ".jsonl": return "jsonl"
    if suffix in {".py", ".ts", ".js", ".ps1", ".java", ".go", ".rs"}: return "code"
    if suffix in {".chat", ".log"}: return "chat_log"
    return "text"


def _units(content: str, source_type: str) -> tuple[str, ...]:
    if source_type == "json": return (json.dumps(json.loads(content), sort_keys=True, ensure_ascii=True),)
    if source_type == "jsonl": return tuple(line for line in content.splitlines() if line.strip())
    if source_type == "code": return tuple(block for block in content.split("\n\ndef ") if block.strip())
    if source_type == "markdown": return tuple(block.strip() for block in content.split("\n## ") if block.strip())
    return tuple(block for block in content.split("\n\n") if block.strip())
