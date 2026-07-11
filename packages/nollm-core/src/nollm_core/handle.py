from __future__ import annotations

from dataclasses import dataclass

from .geometry import GeometryAddress


@dataclass(frozen=True)
class AtomHandle:
    geometry_address: GeometryAddress
    local_atom_id: str

    def __post_init__(self) -> None:
        if not self.local_atom_id:
            raise ValueError("local_atom_id is required")

    def to_mapping(self) -> dict[str, object]:
        return {
            "geometry_address": self.geometry_address.to_mapping(),
            "local_atom_id": self.local_atom_id,
        }

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "AtomHandle":
        return cls(
            GeometryAddress.from_mapping(dict(value["geometry_address"])),
            str(value["local_atom_id"]),
        )
