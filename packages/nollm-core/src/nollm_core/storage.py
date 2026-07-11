from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable
from uuid import uuid4


SCHEMA_VERSION = "nollm_core_state_v1"


def canonical_state_bytes(document: dict[str, object]) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


class FileCoreStateStore:
    """Canonical current-state file; it is not an identity or relation index."""

    def __init__(self, workspace: Path, before_replace: Callable[[Path], None] | None = None) -> None:
        self._workspace = Path(workspace).resolve()
        self._path = self._workspace / "core" / "current_state.json"
        self._before_replace = before_replace
        self._callback_runner: Callable[..., object] | None = None
        self._bound = False
        self._semantic_validator: Callable[[bytes], None] | None = None
        self._owner_token: object | None = None

    @property
    def workspace(self) -> Path:
        return self._workspace

    @property
    def path(self) -> Path:
        return self._path

    @property
    def before_replace(self) -> Callable[[Path], None] | None:
        return self._before_replace

    @before_replace.setter
    def before_replace(self, callback: Callable[[Path], None] | None) -> None:
        if self._bound:
            raise RuntimeError("Core state Store hook is frozen after Runtime binding")
        self._before_replace = callback

    def bind_semantic_validator(
        self,
        validator: Callable[[bytes], None],
        callback_runner: Callable[..., object] | None = None,
    ) -> object:
        if self._owner_token is not None:
            raise RuntimeError("Core state store is already bound")
        self._semantic_validator = validator
        self._callback_runner = callback_runner
        self._owner_token = object()
        self._bound = True
        return self._owner_token

    def exists(self) -> bool:
        return self.path.is_file()

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()

    def read_document(self) -> dict[str, object]:
        payload = self.read_bytes()
        value = json.loads(payload.decode("utf-8"))
        if type(value) is not dict or canonical_state_bytes(value) != payload:
            raise ValueError("Core state bytes must be canonical")
        if self._semantic_validator is None:
            raise RuntimeError("Core state store requires a bound semantic validator")
        self._semantic_validator(payload)
        if value.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported Core state schema")
        return value

    def write_document(self, document: dict[str, object], owner_token: object | None = None) -> bytes:
        payload = canonical_state_bytes(document)
        self.write_bytes(payload, owner_token)
        return payload

    def write_bytes(self, payload: bytes, owner_token: object | None = None) -> None:
        if owner_token is not self._owner_token:
            raise RuntimeError("Core state writes require the live Runtime owner capability")
        value = json.loads(payload.decode("utf-8"))
        if value.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported Core state schema")
        if canonical_state_bytes(value) != payload:
            raise ValueError("Core state bytes must be canonical")
        if self._semantic_validator is None:
            raise RuntimeError("Core state store requires a bound semantic validator")
        self._semantic_validator(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.parent / f".{self.path.name}.{uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            if self._before_replace is not None:
                if self._callback_runner is None:
                    self._before_replace(temporary)
                else:
                    self._callback_runner(self._before_replace, temporary)
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()
