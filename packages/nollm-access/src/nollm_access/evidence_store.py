from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from .statement import MemoryStatement
from .workspace_lock import workspace_lock


class EvidenceStore(Protocol):
    def put_original(self, statement: MemoryStatement) -> None: ...

    def get_original(self, statement_id: str) -> MemoryStatement: ...

    def exists(self, statement_id: str) -> bool: ...


class FileEvidenceStore:
    """File-first original Evidence store with no semantic or relation index."""

    def __init__(self, root: Path) -> None:
        self.workspace = Path(root)
        self.root = self.workspace / "access" / "evidence"
        self._lock = workspace_lock(self.workspace)

    def put_original(self, statement: MemoryStatement) -> None:
        if type(statement) is not MemoryStatement:
            raise TypeError("statement must be MemoryStatement")
        with self._lock:
            path = self._path(statement.statement_id)
            payload = _canonical({"schema_version": "nollm_access_evidence_v1", "statement": statement.to_mapping()})
            if path.exists():
                if path.read_bytes() != payload:
                    raise FileExistsError("statement evidence already exists with different content")
                return
            _atomic_write(path, payload)

    def get_original(self, statement_id: str) -> MemoryStatement:
        path = self._path(statement_id)
        payload = path.read_bytes()
        value = json.loads(payload.decode("utf-8"))
        if type(value) is not dict or set(value) != {"schema_version", "statement"} or value["schema_version"] != "nollm_access_evidence_v1":
            raise ValueError("unsupported or noncanonical Evidence schema")
        statement = MemoryStatement.from_mapping(value["statement"])
        if _canonical(value) != payload:
            raise ValueError("Evidence bytes must be canonical")
        if statement.statement_id != statement_id:
            raise ValueError("Evidence statement identity mismatch")
        return statement

    def exists(self, statement_id: str) -> bool:
        return self._path(statement_id).is_file()

    def _path(self, statement_id: str) -> Path:
        if type(statement_id) is not str or not statement_id:
            raise TypeError("statement_id must be a non-empty string")
        digest = sha256(statement_id.encode("utf-8")).hexdigest()
        return self.root / digest[:2] / f"{digest}.json"


def _canonical(value: dict[str, object]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
