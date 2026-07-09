"""Bridge kernels created by accepted stitch records."""

from __future__ import annotations

from dataclasses import dataclass

from .fixed_point import Q16_ONE

BRIDGE_CLASSES = frozenset({"weak", "normal", "strong"})


@dataclass(frozen=True)
class BridgeKernel:
    bridge_id: str
    from_patch: str
    to_patch: str
    weight_q16: int
    bridge_class: str
    max_steps: int
    max_fanout: int
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for label, value in (("bridge_id", self.bridge_id), ("from_patch", self.from_patch), ("to_patch", self.to_patch)):
            if not isinstance(value, str) or value == "":
                raise ValueError(f"{label} must be non-empty text")
        if type(self.weight_q16) is not int or self.weight_q16 <= 0 or self.weight_q16 > Q16_ONE:
            raise ValueError("weight_q16 must be in 1..Q16_ONE")
        if self.bridge_class not in BRIDGE_CLASSES:
            raise ValueError("unknown bridge_class")
        if type(self.max_steps) is not int or self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        if type(self.max_fanout) is not int or self.max_fanout < 1:
            raise ValueError("max_fanout must be positive")
        if not self.evidence_refs or any(not isinstance(ref, str) or ref == "" for ref in self.evidence_refs):
            raise ValueError("evidence_refs must be non-empty text")

    def fanout_allowed(self, requested: int) -> bool:
        if type(requested) is not int or requested < 0:
            raise ValueError("requested fanout must be a non-negative integer")
        return requested <= self.max_fanout

    def to_mapping(self) -> dict[str, object]:
        return {
            "bridge_id": self.bridge_id,
            "from_patch": self.from_patch,
            "to_patch": self.to_patch,
            "weight_q16": self.weight_q16,
            "bridge_class": self.bridge_class,
            "max_steps": self.max_steps,
            "max_fanout": self.max_fanout,
            "evidence_refs": tuple(sorted(self.evidence_refs)),
            "not_fact_merge": True,
            "not_parent_child": True,
            "no_global_traversal": True,
        }
