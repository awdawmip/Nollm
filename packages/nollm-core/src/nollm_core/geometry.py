from __future__ import annotations

from dataclasses import dataclass

from .profiles import runtime_profile
from .validation import exact_int, exact_mapping, exact_str


@dataclass(frozen=True)
class GeometryAddress:
    profile_id: str
    chart_id: str
    layer: int
    q: int
    r: int
    phase: str | None = None

    def __post_init__(self) -> None:
        runtime_profile(self.profile_id)
        exact_str(self.chart_id, "chart_id")
        for name, value in (("layer", self.layer), ("q", self.q), ("r", self.r)):
            exact_int(value, name)
        if self.phase is not None:
            exact_str(self.phase, "phase")

    def stable_key(self) -> tuple[str, str, int, int, int, str]:
        return self.profile_id, self.chart_id, self.layer, self.q, self.r, self.phase or ""

    def to_mapping(self) -> dict[str, object]:
        return {"profile_id": self.profile_id, "chart_id": self.chart_id, "layer": self.layer, "q": self.q, "r": self.r, "phase": self.phase}

    @classmethod
    def from_mapping(cls, value: object) -> "GeometryAddress":
        item = exact_mapping(value, frozenset({"profile_id", "chart_id", "layer", "q", "r", "phase"}), "GeometryAddress")
        phase = item["phase"]
        if phase is not None and type(phase) is not str:
            raise TypeError("phase must be null or a string")
        return cls(exact_str(item["profile_id"], "profile_id"), exact_str(item["chart_id"], "chart_id"), exact_int(item["layer"], "layer"), exact_int(item["q"], "q"), exact_int(item["r"], "r"), phase)

    def partition_id(self, width: int = 64) -> tuple[int, int]:
        if type(width) is not int or width <= 0:
            raise ValueError("partition width must be positive")
        return self.q // width, self.r // width

    def lateral(self, ring: int = 1) -> tuple["GeometryAddress", ...]:
        from .axial import AxialCoord, hex_ring

        return tuple(GeometryAddress(self.profile_id, self.chart_id, self.layer, coord.q, coord.r, self.phase) for coord in hex_ring(AxialCoord(self.q, self.r), ring))
