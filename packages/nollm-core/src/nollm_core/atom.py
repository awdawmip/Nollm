from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryAtom:
    atom_id: str
    payload_utf8: str

    def __post_init__(self) -> None:
        if not self.atom_id or not self.payload_utf8:
            raise ValueError("atom_id and payload_utf8 are required")

    def to_mapping(self) -> dict[str, str]:
        return {"atom_id": self.atom_id, "payload_utf8": self.payload_utf8}

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "MemoryAtom":
        return cls(str(value["atom_id"]), str(value["payload_utf8"]))
