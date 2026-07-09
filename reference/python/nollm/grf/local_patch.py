"""Local GRF patch placement records."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .cell_address import CellAddress
from .fixed_point import Q16_ONE
from .profiles import get_profile

PATCH_STATES = frozenset({"floating", "placed", "stitch_candidate", "stitched", "retired"})
_PATCH_TRANSITIONS = {
    "floating": frozenset({"placed", "retired"}),
    "placed": frozenset({"stitch_candidate", "retired"}),
    "stitch_candidate": frozenset({"stitched", "retired"}),
    "stitched": frozenset({"retired"}),
    "retired": frozenset(),
}


@dataclass(frozen=True)
class LocalPatch:
    patch_id: str
    island_id: str
    chart_id: str
    profile_id: str
    center_cell: CellAddress
    occupied_cells: tuple[CellAddress, ...]
    boundary_cells: tuple[CellAddress, ...]
    state: str
    density_pressure_q16: int
    ambiguity_q16: int

    def __post_init__(self) -> None:
        for label, value in (("patch_id", self.patch_id), ("island_id", self.island_id), ("chart_id", self.chart_id)):
            if not isinstance(value, str) or value == "":
                raise ValueError(f"{label} must be non-empty text")
        get_profile(self.profile_id)
        if self.state not in PATCH_STATES:
            raise ValueError("unknown patch state")
        if not self.occupied_cells:
            raise ValueError("occupied_cells cannot be empty")
        for cell in (self.center_cell, *self.occupied_cells, *self.boundary_cells):
            if not isinstance(cell, CellAddress):
                raise TypeError("patch cells must be CellAddress")
            if cell.profile_id != self.profile_id or cell.chart_id != self.chart_id:
                raise ValueError("patch cells must share profile_id and chart_id")
        _require_q16(self.density_pressure_q16, "density_pressure_q16")
        _require_q16(self.ambiguity_q16, "ambiguity_q16")

    def transition(self, next_state: str) -> "LocalPatch":
        if next_state not in _PATCH_TRANSITIONS[self.state]:
            raise ValueError("invalid patch state transition")
        return replace(self, state=next_state)

    def to_mapping(self) -> dict[str, object]:
        return {
            "patch_id": self.patch_id,
            "island_id": self.island_id,
            "chart_id": self.chart_id,
            "profile_id": self.profile_id,
            "center_cell": self.center_cell.to_mapping(),
            "occupied_cells": tuple(cell.to_mapping() for cell in sorted(self.occupied_cells, key=lambda item: item.stable_key())),
            "boundary_cells": tuple(cell.to_mapping() for cell in sorted(self.boundary_cells, key=lambda item: item.stable_key())),
            "state": self.state,
            "density_pressure_q16": self.density_pressure_q16,
            "ambiguity_q16": self.ambiguity_q16,
            "not_folder": True,
            "not_fact_merge": True,
        }


def _require_q16(value: int, label: str) -> None:
    if type(value) is not int or value < 0 or value > Q16_ONE:
        raise ValueError(f"{label} must be an integer in Q16 range")
