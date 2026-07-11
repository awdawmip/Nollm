from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryStatement:
    statement_id: str
    content_utf8: str
    source_handle: str | None = None
    context_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement_id or not self.content_utf8:
            raise ValueError("statement_id and content_utf8 are required")
        if self.source_handle is not None and not self.source_handle:
            raise ValueError("source_handle must be non-empty when provided")
        if any(not ref for ref in self.context_refs):
            raise ValueError("context_refs must be non-empty strings")

    def to_mapping(self) -> dict[str, object]:
        return {
            "statement_id": self.statement_id,
            "content_utf8": self.content_utf8,
            "source_handle": self.source_handle,
            "context_refs": list(self.context_refs),
        }

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "MemoryStatement":
        return cls(
            str(value["statement_id"]),
            str(value["content_utf8"]),
            None if value.get("source_handle") is None else str(value["source_handle"]),
            tuple(str(item) for item in value.get("context_refs", [])),
        )
