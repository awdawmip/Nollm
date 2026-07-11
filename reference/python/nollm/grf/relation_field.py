"""Sparse relation propagation derived from placement geometry, without routes."""

from __future__ import annotations

from dataclasses import dataclass, field

from nollm_core import NullTraceSink, TraceEvent, TraceSink, safe_emit

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
    trace_sink: TraceSink = field(default_factory=NullTraceSink, compare=False, repr=False)

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
        output = tuple(sorted(results, key=lambda item: (-item[0].score_q16, item[0].cell.stable_key(), item[1].kernel_type)))
        safe_emit(
            self.trace_sink,
            TraceEvent(
                "relation.step",
                {
                    "source_cell": activation.cell.stable_key(),
                    "allowed_kernels": allowed_kernels,
                    "result_count": len(output),
                },
                "stable",
            ),
        )
        return output

    def shards_at(self, cell: CellAddress) -> tuple[PlacementRecord, ...]:
        return tuple(sorted((item for item in self.placements if item.geometry_mark.cell == cell), key=lambda item: item.shard_id))

    def frontier(self, activations: tuple[SparseActivation, ...], beam: int, step: int) -> ActivationFrontier:
        return ActivationFrontier(step, activations).merged(beam)

    def explicit_entries(self, entry_mode: str, entry_ref: object) -> tuple[PlacementRecord, ...]:
        if entry_mode == "placement_id" and isinstance(entry_ref, str):
            return tuple(item for item in self.placements if item.placement_id == entry_ref)
        if entry_mode == "explicit_cell" and isinstance(entry_ref, CellAddress):
            return self.shards_at(entry_ref)
        return ()

    def _coverage_step(self, activation: SparseActivation, direction: str) -> tuple[tuple[SparseActivation, RecallPath], ...]:
        template = next((item for item in self.coverage_templates if item.profile_id == activation.cell.profile_id and item.direction == direction), None)
        if template is None:
            return ()
        return tuple(_activation_path(activation, cell, weight, direction, direction, ()) for cell, weight in expand_template(activation.cell, template))

    def _lateral_step(self, activation: SparseActivation, ring: int) -> tuple[tuple[SparseActivation, RecallPath], ...]:
        return tuple(_activation_path(activation, cell, weight, LATERAL, LATERAL, ()) for cell, weight in expand_lateral(activation.cell, ring))

    def _bridge_step(self, activation: SparseActivation) -> tuple[tuple[SparseActivation, RecallPath], ...]:
        patch_ids = {record.patch_id for record in self.shards_at(activation.cell)}
        output = []
        for bridge in self.bridge_kernels:
            if bridge.from_patch not in patch_ids:
                continue
            targets = tuple(item for item in self.placements if item.patch_id == bridge.to_patch)
            for target in targets[: bridge.max_fanout]:
                output.append(_activation_path(activation, target.geometry_mark.cell, bridge.weight_q16, "bridge", bridge.bridge_class, ("bridge",)))
        return tuple(output)


def _activation_path(source: SparseActivation, to_cell: CellAddress, weight_q16: int, kernel_type: str, path_kind: str, flags: tuple[str, ...]) -> tuple[SparseActivation, RecallPath]:
    score = propagate_score(source.score_q16, weight_q16)
    activation = SparseActivation(to_cell, score, f"{source.path_id}/{path_kind}:{to_cell.layer}:{to_cell.q}:{to_cell.r}")
    return activation, RecallPath(source.cell, to_cell, kernel_type, weight_q16, score, 0, flags)
