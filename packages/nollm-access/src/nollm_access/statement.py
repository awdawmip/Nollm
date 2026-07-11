from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryStatement:
    statement_id: str
    content_utf8: str
    source_handle: str | None = None
    context_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.statement_id) is not str or not self.statement_id or type(self.content_utf8) is not str or not self.content_utf8:
            raise TypeError("statement_id and content_utf8 must be non-empty strings")
        if self.source_handle is not None and (type(self.source_handle) is not str or not self.source_handle):
            raise TypeError("source_handle must be null or a non-empty string")
        if type(self.context_refs) is not tuple or any(type(ref) is not str or not ref for ref in self.context_refs):
            raise TypeError("context_refs must be a tuple of non-empty strings")

    def to_mapping(self) -> dict[str, object]:
        return {"statement_id": self.statement_id, "content_utf8": self.content_utf8, "source_handle": self.source_handle, "context_refs": list(self.context_refs)}

    @classmethod
    def from_mapping(cls, value: object) -> "MemoryStatement":
        keys = {"statement_id", "content_utf8", "source_handle", "context_refs"}
        if type(value) is not dict or set(value) != keys or type(value["context_refs"]) is not list:
            raise ValueError("MemoryStatement mapping must have exact canonical fields")
        if any(type(item) is not str for item in value["context_refs"]):
            raise TypeError("context_refs entries must be strings")
        return cls(value["statement_id"], value["content_utf8"], value["source_handle"], tuple(value["context_refs"]))
