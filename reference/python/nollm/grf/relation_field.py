"""Sparse GRF relation field runtime."""

from __future__ import annotations

from dataclasses import dataclass

from .bridge_kernel import BridgeKernel
from .cell_address import CellAddress
from .coverage_template import COVERAGE_DOWN, COVERAGE_UP, LATERAL, CoverageTemplate, expand_lateral, expand_template
from .placement import PlacementRecord
from .propagation import ActivationFrontier, SparseActivation, propagate_score
from .recall_digest import RecallPath


@dataclass(frozen=True)
class RelationField:
    coverage_templates: tuple[CoverageTemplate, ...]
    bridge_kernels: tuple[BridgeKernel, ...]
    placements: tuple[PlacementRecord, ...]

    def __post_init__(self) -> None:
        self._template_index()
        self._cell_index()

    def step(self, activation: SparseActivation, allowed_kernels: tuple[str, ...], max_lateral_ring: int, max_bridge_steps: int) -> tuple[tuple[SparseActivation, RecallPath], ...]:
        results: list[tuple[SparseActivation, RecallPath]] = []
        if COVERAGE_UP in allowed_kernels:
            results.extend(self._coverage_step(activation, COVERAGE_UP))
        if COVERAGE_DOWN in allowed_kernels:
            results.extend(self._coverage_step(activation, COVERAGE_DOWN))
        if LATERAL in allowed_kernels:
            results.extend(self._lateral_step(activation, max_lateral_ring))
        if "bridge" in allowed_kernels and max_bridge_steps > 0:
            results.extend(self._bridge_step(activation))
        return tuple(sorted(results, key=lambda item: (-item[0].score_q16, item[0].cell.stable_key(), item[1].kernel_type)))

    def shards_at(self, cell: CellAddress) -> tuple[PlacementRecord, ...]:
        return self._cell_index().get(cell.stable_key(), ())

    def frontier(self, activations: tuple[SparseActivation, ...], beam: int, step: int) -> ActivationFrontier:
        return ActivationFrontier(step, activations).merged(beam)

    def _coverage_step(self, activation: SparseActivation, direction: str) -> tuple[tuple[SparseActivation, RecallPath], ...]:
        template = self._template_index().get((activation.cell.profile_id, direction))
        if template is None:
            return ()
        expanded = expand_template(activation.cell, template)
        return tuple(_activation_path(activation, cell, weight, direction, direction, ()) for cell, weight in expanded)

    def _lateral_step(self, activation: SparseActivation, ring: int) -> tuple[tuple[SparseActivation, RecallPath], ...]:
        expanded = expand_lateral(activation.cell, ring)
        return tuple(_activation_path(activation, cell, weight, LATERAL, LATERAL, ()) for cell, weight in expanded)

    def _bridge_step(self, activation: SparseActivation) -> tuple[tuple[SparseActivation, RecallPath], ...]:
        placements = self.shards_at(activation.cell)
        patch_ids = {record.patch_id for record in placements}
        out = []
        for bridge in self.bridge_kernels:
            if bridge.from_patch not in patch_ids:
                continue
            targets = [record for record in self.placements if record.patch_id == bridge.to_patch]
            if not bridge.fanout_allowed(len(targets)):
                targets = targets[: bridge.max_fanout]
            for target in targets:
                out.append(_activation_path(activation, target.geometry_mark.cell, bridge.weight_q16, "bridge", bridge.bridge_class, ("bridge",)))
        return tuple(out)

    def _template_index(self) -> dict[tuple[str, str], CoverageTemplate]:
        return {(template.profile_id, template.direction): template for template in self.coverage_templates}

    def _cell_index(self) -> dict[tuple[str, str, int, int, int, str], tuple[PlacementRecord, ...]]:
        index: dict[tuple[str, str, int, int, int, str], list[PlacementRecord]] = {}
        for record in self.placements:
            index.setdefault(record.geometry_mark.cell.stable_key(), []).append(record)
        return {key: tuple(sorted(value, key=lambda item: item.shard_id)) for key, value in index.items()}


def _activation_path(source: SparseActivation, to_cell: CellAddress, weight_q16: int, kernel_type: str, path_kind: str, flags: tuple[str, ...]) -> tuple[SparseActivation, RecallPath]:
    score = propagate_score(source.score_q16, weight_q16)
    path_id = f"{source.path_id}/{path_kind}:{to_cell.layer}:{to_cell.q}:{to_cell.r}"
    activation = SparseActivation(to_cell, score, path_id)
    path = RecallPath(source.cell, to_cell, kernel_type, weight_q16, score, 0, flags)
    return activation, path
