"""Geometry-native in-memory cell occupancy for bounded GRF validation."""

from __future__ import annotations

from dataclasses import dataclass

from .axial import AxialCoord, hex_ring
from .cell_address import CellAddress
from .placement import PlacementRecord
from .bridge_kernel import BridgeKernel
from .kernel_registry import KernelRegistry
from .relation_field import RelationField


@dataclass(frozen=True)
class CellState:
    cell: CellAddress
    placements: tuple[PlacementRecord, ...]
    density_state: str


class CellStore:
    """Occupancy is stored by actual geometry cell, never by semantic identity."""
    def __init__(self, dense_threshold: int = 8, overloaded_threshold: int = 32, migration_threshold: int = 96) -> None:
        self.dense_threshold = dense_threshold
        self.overloaded_threshold = overloaded_threshold
        self.migration_threshold = migration_threshold
        self._cells: dict[tuple[str, str, int, int, int, str], list[PlacementRecord]] = {}

    def insert(self, placement: PlacementRecord) -> None:
        cell = placement.geometry_mark.cell
        values = self._cells.setdefault(cell.stable_key(), [])
        if any(item.placement_id == placement.placement_id for item in values):
            raise FileExistsError("placement already occupies cell")
        values.append(placement)

    def remove(self, placement_id: str) -> PlacementRecord:
        for key, values in tuple(self._cells.items()):
            for index, placement in enumerate(values):
                if placement.placement_id == placement_id:
                    values.pop(index)
                    if not values:
                        del self._cells[key]
                    return placement
        raise FileNotFoundError("placement does not occupy any cell")

    def move(self, placement: PlacementRecord) -> None:
        try:
            self.remove(placement.placement_id)
        except FileNotFoundError:
            pass
        self.insert(placement)

    def at(self, cell: CellAddress) -> tuple[PlacementRecord, ...]:
        return tuple(sorted(self._cells.get(cell.stable_key(), ()), key=lambda item: item.placement_id))

    def neighbors(self, cell: CellAddress, ring: int = 1) -> tuple[PlacementRecord, ...]:
        values: list[PlacementRecord] = []
        for coord in hex_ring(AxialCoord(cell.q, cell.r), ring):
            values.extend(self.at(CellAddress(cell.profile_id, cell.chart_id, cell.layer, coord.q, coord.r, cell.phase)))
        return tuple(sorted(values, key=lambda item: item.placement_id))

    def all(self) -> tuple[PlacementRecord, ...]:
        return tuple(sorted((item for values in self._cells.values() for item in values), key=lambda item: item.placement_id))

    def find(self, placement_id: str) -> PlacementRecord | None:
        return next((item for item in self.all() if item.placement_id == placement_id), None)

    def placement_count(self) -> int:
        return sum(len(values) for values in self._cells.values())

    def cell_state(self, cell: CellAddress) -> CellState:
        values = self.at(cell)
        count = len(values)
        density = "migration_candidate" if count >= self.migration_threshold else "overloaded" if count >= self.overloaded_threshold else "dense" if count >= self.dense_threshold else "normal"
        return CellState(cell, values, density)


class FieldEngine:
    """Assembles a relation field directly from cell occupancy and bridges."""
    def __init__(self, kernel_registry: KernelRegistry | None = None, cell_store: CellStore | None = None) -> None:
        self.kernel_registry = kernel_registry or KernelRegistry()
        if not self.kernel_registry.templates():
            self.kernel_registry.compile_profiles(("eisenstein_exact_v1",))
        self.cells = cell_store or CellStore()
        self._bridges: dict[str, BridgeKernel] = {}

    def insert(self, placement: PlacementRecord) -> None:
        self.cells.insert(placement)

    def remove(self, placement_id: str) -> PlacementRecord:
        return self.cells.remove(placement_id)

    def move(self, placement: PlacementRecord) -> None:
        self.cells.move(placement)

    def add_bridge(self, bridge: BridgeKernel) -> None:
        self._bridges[bridge.bridge_id] = bridge

    def remove_bridge(self, bridge_id: str) -> BridgeKernel:
        return self._bridges.pop(bridge_id)

    def build_relation_field(self) -> RelationField:
        return RelationField(self.kernel_registry.coverage_templates(), tuple(self._bridges[key] for key in sorted(self._bridges)), self.cells.all())
