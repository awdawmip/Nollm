"""Incremental GRF relation field builder."""

from __future__ import annotations

from dataclasses import dataclass

from .bridge_kernel import BridgeKernel
from .cell_address import CellAddress
from .field_engine import CellRegistry, PlacementIndex
from .kernel_registry import KernelRegistry
from .placement import PlacementRecord
from .relation_field import RelationField


@dataclass(frozen=True)
class IncrementalUpdateReport:
    invalidated_regions: tuple[tuple[str, str, int, int, int, str], ...]
    local_impact_only: bool
    deterministic: bool


class IncrementalFieldBuilder:
    def __init__(self, kernel_registry: KernelRegistry | None = None) -> None:
        self.kernel_registry = kernel_registry or KernelRegistry()
        if not self.kernel_registry.templates():
            self.kernel_registry.compile_profiles(("eisenstein_exact_v1",))
        self.placement_index = PlacementIndex(CellRegistry())
        self._bridges: dict[str, BridgeKernel] = {}
        self._invalidated: set[tuple[str, str, int, int, int, str]] = set()

    def add_placement(self, placement: PlacementRecord) -> IncrementalUpdateReport:
        self.placement_index.insert(placement)
        return self.invalidate_region(placement.geometry_mark.cell)

    def remove_placement(self, placement_id: str) -> IncrementalUpdateReport:
        placement = self.placement_index.remove(placement_id)
        return self.invalidate_region(placement.geometry_mark.cell)

    def move_placement(self, placement: PlacementRecord) -> IncrementalUpdateReport:
        prior = self.placement_index.remove(placement.placement_id) if self.placement_index.placement_id_for_shard(placement.shard_id) else None
        self.placement_index.insert(placement)
        cells = [placement.geometry_mark.cell]
        if prior is not None:
            cells.append(prior.geometry_mark.cell)
        for cell in cells:
            self._invalidated.add(cell.stable_key())
        return self._report()

    def add_stitch_bridge(self, bridge: BridgeKernel) -> IncrementalUpdateReport:
        self._bridges[bridge.bridge_id] = bridge
        return self._report()

    def invalidate_region(self, cell: CellAddress) -> IncrementalUpdateReport:
        self._invalidated.add(cell.stable_key())
        return self._report()

    def rebuild_region(self, cell: CellAddress) -> IncrementalUpdateReport:
        self._invalidated.discard(cell.stable_key())
        return self._report()

    def relation_field(self) -> RelationField:
        return RelationField(self.kernel_registry.coverage_templates(), tuple(self._bridges[key] for key in sorted(self._bridges)), self.placement_index.placements())

    def full_rebuild(self) -> RelationField:
        return self.relation_field()

    def _report(self) -> IncrementalUpdateReport:
        return IncrementalUpdateReport(tuple(sorted(self._invalidated)), True, True)
