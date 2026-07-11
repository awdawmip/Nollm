from __future__ import annotations

from dataclasses import dataclass

from .geometry import GeometryAddress
from .validation import exact_int, exact_list, exact_mapping, exact_str


Q16_ONE = 1 << 16
BRIDGE_CLASSES = frozenset({"weak", "normal", "strong"})


@dataclass(frozen=True)
class GeometryAnchor:
    anchor_id: str
    cells: tuple[GeometryAddress, ...]

    def __post_init__(self) -> None:
        if type(self.anchor_id) is not str or not self.anchor_id:
            raise TypeError("anchor_id must be a non-empty string")
        if type(self.cells) is not tuple or not self.cells or any(type(cell) is not GeometryAddress for cell in self.cells):
            raise TypeError("cells must be a non-empty GeometryAddress tuple")
        if len(set(self.cells)) != len(self.cells):
            raise ValueError("anchor cells must be unique")

    def to_mapping(self) -> dict[str, object]:
        return {"anchor_id": self.anchor_id, "cells": [cell.to_mapping() for cell in self.cells]}

    @classmethod
    def from_mapping(cls, value: object) -> "GeometryAnchor":
        item = exact_mapping(value, frozenset({"anchor_id", "cells"}), "GeometryAnchor")
        return cls(exact_str(item["anchor_id"], "anchor_id"), tuple(GeometryAddress.from_mapping(cell) for cell in exact_list(item["cells"], "cells")))


@dataclass(frozen=True)
class BridgeSpec:
    bridge_id: str
    from_anchor: GeometryAnchor
    to_anchor: GeometryAnchor
    weight_q16: int
    bridge_class: str
    max_steps: int
    max_fanout: int

    def __post_init__(self) -> None:
        if type(self.bridge_id) is not str or not self.bridge_id:
            raise TypeError("bridge_id must be a non-empty string")
        if type(self.from_anchor) is not GeometryAnchor or type(self.to_anchor) is not GeometryAnchor:
            raise TypeError("bridge anchors must be GeometryAnchor values")
        if type(self.bridge_class) is not str:
            raise TypeError("bridge_class must be a string")
        if type(self.weight_q16) is not int or not 0 < self.weight_q16 <= Q16_ONE:
            raise ValueError("weight_q16 must be in (0, Q16_ONE]")
        if self.bridge_class not in BRIDGE_CLASSES:
            raise ValueError("invalid bridge_class")
        if type(self.max_steps) is not int or self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        if type(self.max_fanout) is not int or not 1 <= self.max_fanout <= 64:
            raise ValueError("max_fanout must be in [1, 64]")

    def to_mapping(self) -> dict[str, object]:
        return {
            "bridge_id": self.bridge_id,
            "from_anchor": self.from_anchor.to_mapping(),
            "to_anchor": self.to_anchor.to_mapping(),
            "weight_q16": self.weight_q16,
            "bridge_class": self.bridge_class,
            "max_steps": self.max_steps,
            "max_fanout": self.max_fanout,
        }

    @classmethod
    def from_mapping(cls, value: object) -> "BridgeSpec":
        item = exact_mapping(value, frozenset({"bridge_id", "from_anchor", "to_anchor", "weight_q16", "bridge_class", "max_steps", "max_fanout"}), "BridgeSpec")
        return cls(
            exact_str(item["bridge_id"], "bridge_id"),
            GeometryAnchor.from_mapping(item["from_anchor"]),
            GeometryAnchor.from_mapping(item["to_anchor"]),
            exact_int(item["weight_q16"], "weight_q16"),
            exact_str(item["bridge_class"], "bridge_class"),
            exact_int(item["max_steps"], "max_steps"),
            exact_int(item["max_fanout"], "max_fanout"),
        )
