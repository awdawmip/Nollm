from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from nollm_core import AtomHandle


class FileHandleStore:
    """Caller-owned physical handle registry; never a Recall relation entry."""

    def __init__(self, root: Path) -> None:
        self.path = Path(root) / "access" / "handles.json"

    def put(self, statement_id: str, handle: AtomHandle) -> None:
        values = self._load()
        values[statement_id] = handle
        self._write(values)

    def get(self, statement_id: str) -> AtomHandle:
        try:
            return self._load()[statement_id]
        except KeyError as error:
            raise KeyError("statement has no saved Core handle") from error

    def remove(self, statement_id: str) -> AtomHandle:
        values = self._load()
        try:
            handle = values.pop(statement_id)
        except KeyError as error:
            raise KeyError("statement has no saved Core handle") from error
        self._write(values)
        return handle

    def remove_handle(self, handle: AtomHandle) -> None:
        values = self._load()
        changed = False
        for statement_id in tuple(values):
            if values[statement_id] == handle:
                del values[statement_id]
                changed = True
        if changed:
            self._write(values)

    def exists(self, statement_id: str) -> bool:
        return statement_id in self._load()

    def statement_for_handle(self, handle: AtomHandle) -> str:
        matches = sorted(statement_id for statement_id, stored in self._load().items() if stored == handle)
        if not matches:
            raise KeyError("Core handle has no saved statement")
        return matches[0]

    def _load(self) -> dict[str, AtomHandle]:
        if not self.path.exists():
            return {}
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if value.get("schema_version") != "nollm_access_handles_v1":
            raise ValueError("unsupported HandleStore schema")
        return {key: AtomHandle.from_mapping(dict(item)) for key, item in value["handles"].items()}

    def _write(self, values: dict[str, AtomHandle]) -> None:
        document = {
            "schema_version": "nollm_access_handles_v1",
            "handles": {key: values[key].to_mapping() for key in sorted(values)},
        }
        payload = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.parent / f".{self.path.name}.{uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()
