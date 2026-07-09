"""Large-scale GRF field engine indexes."""

from __future__ import annotations

from dataclasses import dataclass

from .axial import AxialCoord, hex_ring
from .cell_address import CellAddress
from .placement import PlacementRecord

DENSITY_STATES = ("normal", "dense", "overloaded", "migration_candidate")


@dataclass(frozen=True)
class CellState:
    cell: CellAddress
    placement_ids: tuple[str, ...]
    density_state: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "cell": self.cell.to_mapping(),
            "placement_ids": self.placement_ids,
            "density_state": self.density_state,
            "cell_stores_shard_content": False,
            "cell_stores_semantic_edge": False,
            "cell_copies_coverage_relation": False,
        }


class CellRegistry:
    def __init__(self, dense_threshold: int = 8, overloaded_threshold: int = 32, migration_threshold: int = 96) -> None:
        self.dense_threshold = dense_threshold
        self.overloaded_threshold = overloaded_threshold
        self.migration_threshold = migration_threshold
        self._placements: dict[tuple[str, str, int, int, int, str], set[str]] = {}
        self._cells: dict[tuple[str, str, int, int, int, str], CellAddress] = {}

    def bind_cell(self, cell: CellAddress) -> CellAddress:
        self._cells[cell.stable_key()] = cell
        self._placements.setdefault(cell.stable_key(), set())
        return cell

    def add_placement(self, placement_id: str, cell: CellAddress) -> None:
        self.bind_cell(cell)
        self._placements[cell.stable_key()].add(placement_id)

    def remove_placement(self, placement_id: str, cell: CellAddress) -> None:
        self._placements.setdefault(cell.stable_key(), set()).discard(placement_id)

    def density_pressure(self, cell: CellAddress) -> str:
        count = len(self._placements.get(cell.stable_key(), set()))
        if count >= self.migration_threshold:
            return "migration_candidate"
        if count >= self.overloaded_threshold:
            return "overloaded"
        if count >= self.dense_threshold:
            return "dense"
        return "normal"

    def cell_state(self, cell: CellAddress) -> CellState:
        return CellState(cell, tuple(sorted(self._placements.get(cell.stable_key(), set()))), self.density_pressure(cell))

    def cell_count(self) -> int:
        return len(self._cells)


class PlacementIndex:
    def __init__(self, registry: CellRegistry | None = None) -> None:
        self.registry = registry or CellRegistry()
        self._placements: dict[str, PlacementRecord] = {}
        self._by_cell: dict[tuple[str, str, int, int, int, str], set[str]] = {}
        self._by_shard: dict[str, str] = {}

    def insert(self, placement: PlacementRecord) -> None:
        self._placements[placement.placement_id] = placement
        key = placement.geometry_mark.cell.stable_key()
        self._by_cell.setdefault(key, set()).add(placement.placement_id)
        self._by_shard[placement.shard_id] = placement.placement_id
        self.registry.add_placement(placement.placement_id, placement.geometry_mark.cell)

    def remove(self, placement_id: str) -> PlacementRecord:
        placement = self._placements.pop(placement_id)
        key = placement.geometry_mark.cell.stable_key()
        self._by_cell.get(key, set()).discard(placement_id)
        self._by_shard.pop(placement.shard_id, None)
        self.registry.remove_placement(placement_id, placement.geometry_mark.cell)
        return placement

    def move(self, placement: PlacementRecord) -> None:
        if placement.placement_id in self._placements:
            self.remove(placement.placement_id)
        self.insert(placement)

    def query_by_cell(self, cell: CellAddress) -> tuple[PlacementRecord, ...]:
        ids = self._by_cell.get(cell.stable_key(), set())
        return tuple(self._placements[item] for item in sorted(ids))

    def query_neighbors(self, cell: CellAddress, ring: int = 1) -> tuple[PlacementRecord, ...]:
        out: list[PlacementRecord] = []
        for coord in hex_ring(AxialCoord(cell.q, cell.r), ring):
            neighbor = CellAddress(cell.profile_id, cell.chart_id, cell.layer, coord.q, coord.r, cell.phase)
            out.extend(self.query_by_cell(neighbor))
        return tuple(sorted(out, key=lambda item: item.placement_id))

    def placement_count(self) -> int:
        return len(self._placements)

    def placements(self) -> tuple[PlacementRecord, ...]:
        return tuple(self._placements[key] for key in sorted(self._placements))

    def placement_id_for_shard(self, shard_id: str) -> str | None:
        return self._by_shard.get(shard_id)
