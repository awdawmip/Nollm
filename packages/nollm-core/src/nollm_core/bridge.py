from __future__ import annotations

from dataclasses import dataclass

from .geometry import GeometryAddress


Q16_ONE = 1 << 16
BRIDGE_CLASSES = frozenset({"weak", "normal", "strong"})


@dataclass(frozen=True)
class GeometryAnchor:
    anchor_id: str
    cells: tuple[GeometryAddress, ...]

    def __post_init__(self) -> None:
        if not self.anchor_id or not self.cells:
            raise ValueError("anchor_id and cells are required")
        if len(set(self.cells)) != len(self.cells):
            raise ValueError("anchor cells must be unique")

    def to_mapping(self) -> dict[str, object]:
        return {"anchor_id": self.anchor_id, "cells": [cell.to_mapping() for cell in self.cells]}

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "GeometryAnchor":
        return cls(str(value["anchor_id"]), tuple(GeometryAddress.from_mapping(dict(item)) for item in value["cells"]))


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
        if not self.bridge_id:
            raise ValueError("bridge_id is required")
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
    def from_mapping(cls, value: dict[str, object]) -> "BridgeSpec":
        return cls(
            str(value["bridge_id"]),
            GeometryAnchor.from_mapping(dict(value["from_anchor"])),
            GeometryAnchor.from_mapping(dict(value["to_anchor"])),
            int(value["weight_q16"]),
            str(value["bridge_class"]),
            int(value["max_steps"]),
            int(value["max_fanout"]),
        )
