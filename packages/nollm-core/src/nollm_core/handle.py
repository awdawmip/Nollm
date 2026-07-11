from __future__ import annotations

from dataclasses import dataclass

from .geometry import GeometryAddress
from .validation import exact_mapping, exact_str


@dataclass(frozen=True)
class AtomHandle:
    geometry_address: GeometryAddress
    local_atom_id: str

    def __post_init__(self) -> None:
        if type(self.geometry_address) is not GeometryAddress:
            raise TypeError("geometry_address must be GeometryAddress")
        exact_str(self.local_atom_id, "local_atom_id")

    def to_mapping(self) -> dict[str, object]:
        return {
            "geometry_address": self.geometry_address.to_mapping(),
            "local_atom_id": self.local_atom_id,
        }

    @classmethod
    def from_mapping(cls, value: object) -> "AtomHandle":
        item = exact_mapping(value, frozenset({"geometry_address", "local_atom_id"}), "AtomHandle")
        return cls(
            GeometryAddress.from_mapping(item["geometry_address"]),
            exact_str(item["local_atom_id"], "local_atom_id"),
        )
