from __future__ import annotations

from dataclasses import dataclass

from .validation import exact_mapping, exact_str


@dataclass(frozen=True)
class MemoryAtom:
    atom_id: str
    payload_utf8: str

    def __post_init__(self) -> None:
        exact_str(self.atom_id, "atom_id")
        exact_str(self.payload_utf8, "payload_utf8")

    def to_mapping(self) -> dict[str, str]:
        return {"atom_id": self.atom_id, "payload_utf8": self.payload_utf8}

    @classmethod
    def from_mapping(cls, value: object) -> "MemoryAtom":
        item = exact_mapping(value, frozenset({"atom_id", "payload_utf8"}), "MemoryAtom")
        return cls(exact_str(item["atom_id"], "atom_id"), exact_str(item["payload_utf8"], "payload_utf8"))
