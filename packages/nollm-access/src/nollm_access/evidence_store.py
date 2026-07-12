from __future__ import annotations

from pathlib import Path
from typing import Protocol
from warnings import warn

from .statement import MemoryStatement
from .statement_store import FileStatementStore


class EvidenceStore(Protocol):
    def put_original(self, statement: MemoryStatement) -> None: ...
    def get_original(self, statement_id: str) -> MemoryStatement: ...
    def exists(self, statement_id: str) -> bool: ...


class FileEvidenceStore(FileStatementStore):
    """Deprecated compatibility facade; new writes use StatementStore bytes."""

    def __init__(self, root: Path) -> None:
        super().__init__(root)

    def put_original(self, statement: MemoryStatement) -> None:
        warn("FileEvidenceStore.put_original is deprecated; use FileStatementStore.put", DeprecationWarning, stacklevel=2)
        self.put(statement)

    def get_original(self, statement_id: str) -> MemoryStatement:
        warn("FileEvidenceStore.get_original is deprecated; use FileStatementStore.get", DeprecationWarning, stacklevel=2)
        return self.get(statement_id)
