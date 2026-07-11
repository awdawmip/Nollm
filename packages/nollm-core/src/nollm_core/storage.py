from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable
from uuid import uuid4


SCHEMA_VERSION = "nollm_core_state_v1"


def canonical_state_bytes(document: dict[str, object]) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


class _FileCoreStateStore:
    """Private canonical current-state persistence owned by CoreRuntime."""

    def __init__(self, workspace: Path, validator: Callable[[bytes], None]) -> None:
        self.workspace = Path(workspace).resolve()
        self.path = self.workspace / "core" / "current_state.json"
        self._validator = validator

    def exists(self) -> bool:
        return self.path.is_file()

    def read_bytes(self) -> bytes:
        payload = self.path.read_bytes()
        self._validator(payload)
        return payload

    def write_document(self, document: dict[str, object]) -> bytes:
        payload = canonical_state_bytes(document)
        self.write_bytes(payload)
        return payload

    def write_bytes(self, payload: bytes) -> None:
        self._validator(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.parent / f".{self.path.name}.{uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            _atomic_replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()


def _atomic_replace(source: Path, target: Path) -> None:
    os.replace(source, target)
