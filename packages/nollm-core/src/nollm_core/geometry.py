from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class GeometryAddress:
    profile_id: str
    chart_id: str
    layer: int
    q: int
    r: int
    phase: str | None = None

    def __post_init__(self) -> None:
        if not self.profile_id or not self.chart_id:
            raise ValueError("profile_id and chart_id are required")
        for value in (self.layer, self.q, self.r):
            if type(value) is not int:
                raise TypeError("geometry coordinates must be integers")
        if self.phase is not None and not self.phase:
            raise ValueError("phase must be non-empty when provided")

    def stable_key(self) -> tuple[str, str, int, int, int, str]:
        return self.profile_id, self.chart_id, self.layer, self.q, self.r, self.phase or ""

    def to_mapping(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "chart_id": self.chart_id,
            "layer": self.layer,
            "q": self.q,
            "r": self.r,
            "phase": self.phase,
        }

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "GeometryAddress":
        return cls(
            str(value["profile_id"]),
            str(value["chart_id"]),
            int(value["layer"]),
            int(value["q"]),
            int(value["r"]),
            None if value.get("phase") is None else str(value["phase"]),
        )

    def partition_id(self, width: int = 64) -> tuple[int, int]:
        if type(width) is not int or width <= 0:
            raise ValueError("partition width must be positive")
        return self.q // width, self.r // width

    def lateral(self, ring: int = 1) -> tuple["GeometryAddress", ...]:
        if type(ring) is not int or ring < 1:
            raise ValueError("lateral ring must be a positive integer")
        directions = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
        q = self.q + directions[4][0] * ring
        r = self.r + directions[4][1] * ring
        output = []
        for direction in range(6):
            dq, dr = directions[direction]
            for _ in range(ring):
                output.append(GeometryAddress(self.profile_id, self.chart_id, self.layer, q, r, self.phase))
                q += dq
                r += dr
        return tuple(output)

    def coverage_up(self) -> tuple["GeometryAddress", ...]:
        return (
            GeometryAddress(
                self.profile_id,
                self.chart_id,
                self.layer + 1,
                self.q // 2,
                self.r // 2,
                self.phase,
            ),
        )

    def coverage_down(self) -> tuple["GeometryAddress", ...]:
        center = GeometryAddress(
            self.profile_id,
            self.chart_id,
            self.layer - 1,
            self.q * 2,
            self.r * 2,
            self.phase,
        )
        return (center, *center.lateral(1))
