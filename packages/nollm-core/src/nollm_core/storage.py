from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4


SCHEMA_VERSION = "nollm_core_state_v1"


def canonical_state_bytes(document: dict[str, object]) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


class _FileCoreStateStore:
    """Private canonical current-state persistence owned by CoreRuntime."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace).resolve()
        self.path = self.workspace / "core" / "current_state.json"

    def exists(self) -> bool:
        return self.path.is_file()

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()

    def write_document(self, document: dict[str, object]) -> bytes:
        payload = canonical_state_bytes(document)
        self.write_bytes(payload)
        return payload

    def write_bytes(self, payload: bytes) -> None:
        _atomic_write(self.path, payload)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _atomic_replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_replace(source: Path, target: Path) -> None:
    os.replace(source, target)
