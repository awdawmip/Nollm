"""Stable GRF cell addresses."""

from __future__ import annotations

from dataclasses import dataclass

from .profiles import get_profile


@dataclass(frozen=True, order=True)
class CellAddress:
    profile_id: str
    chart_id: str
    layer: int
    q: int
    r: int
    phase: str | None = None

    def __post_init__(self) -> None:
        get_profile(self.profile_id)
        if not isinstance(self.chart_id, str) or self.chart_id == "":
            raise ValueError("chart_id cannot be empty")
        if type(self.layer) is not int or type(self.q) is not int or type(self.r) is not int:
            raise TypeError("layer, q, and r must be integers")
        if self.phase is not None and not isinstance(self.phase, str):
            raise TypeError("phase must be text or None")

    def to_mapping(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "chart_id": self.chart_id,
            "layer": self.layer,
            "q": self.q,
            "r": self.r,
            "phase": self.phase,
        }

    def stable_key(self) -> tuple[str, str, int, int, int, str]:
        return (self.profile_id, self.chart_id, self.layer, self.q, self.r, self.phase or "")
