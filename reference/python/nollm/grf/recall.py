"""Minimal structured GRF recall runtime."""

from __future__ import annotations

from dataclasses import dataclass

from .cell_address import CellAddress
from .fixed_point import Q16_ONE
from .propagation import SparseActivation
from .recall_digest import CoverageReport, RecallDigest, RecallPath
from .relation_field import RelationField

ENTRY_MODES = frozenset({"explicit_cell", "shard_id", "island_id", "patch_id", "source_window", "admission_id", "placement_id"})


@dataclass(frozen=True)
class RecallBudget:
    max_steps: int
    beam: int
    max_layer_delta: int
    max_lateral_ring: int
    max_bridge_steps: int
    max_results: int

    def __post_init__(self) -> None:
        for value in (self.max_steps, self.beam, self.max_layer_delta, self.max_lateral_ring, self.max_bridge_steps, self.max_results):
            if type(value) is not int or value < 0:
                raise ValueError("budget values must be non-negative integers")
        if self.beam < 1 or self.max_results < 1:
            raise ValueError("beam and max_results must be positive")


@dataclass(frozen=True)
class QueryProbe:
    query_id: str
    entry_mode: str
    entry_ref: object
    allowed_kernels: tuple[str, ...]
    budget: RecallBudget

    def __post_init__(self) -> None:
        if not isinstance(self.query_id, str) or self.query_id == "":
            raise ValueError("query_id must be non-empty text")
        if self.entry_mode not in ENTRY_MODES:
            raise ValueError("unknown entry_mode")
        if not self.allowed_kernels:
            raise ValueError("allowed_kernels cannot be empty")
        if not isinstance(self.budget, RecallBudget):
            raise TypeError("budget must be RecallBudget")


def resolve_grf_recall(query: QueryProbe, field: RelationField, *, collect_rejected: bool = True) -> RecallDigest:
    starts = _entry_activations(query, field)
    entry_shards = {placement.shard_id for placement in field.explicit_entries(query.entry_mode, query.entry_ref)}
    frontier = field.frontier(starts, query.budget.beam, 0)
    paths: dict[tuple[str, str, int, int, int, str], tuple[RecallPath, ...]] = {activation.cell.stable_key(): () for activation in frontier.activations}
    selected: dict[str, CoverageReport] = {}
    rejected: list[str] = []
    exhausted = False
    for step in range(query.budget.max_steps + 1):
        for activation in frontier.activations:
            placements = tuple(sorted(field.shards_at(activation.cell), key=lambda item: (item.shard_id not in entry_shards, item.shard_id)))
            for placement in placements:
                if placement.shard_id in selected:
                    continue
                selected[placement.shard_id] = _report(query, placement.shard_id, paths.get(activation.cell.stable_key(), ()), activation.score_q16, placement.source_fallback_refs[0])
                if len(selected) >= query.budget.max_results:
                    exhausted = True
                    break
            if exhausted:
                break
        if exhausted or step == query.budget.max_steps:
            break
        next_items = field.step(tuple(frontier.activations)[0], query.allowed_kernels, query.budget.max_lateral_ring, query.budget.max_bridge_steps) if len(frontier.activations) == 1 else tuple(
            item for activation in frontier.activations for item in field.step(activation, query.allowed_kernels, query.budget.max_lateral_ring, query.budget.max_bridge_steps)
        )
        next_activations = tuple(item[0] for item in next_items)
        for activation, path in next_items:
            prior = paths.get(path.from_cell.stable_key(), ())
            paths[activation.cell.stable_key()] = (*prior, path)
        frontier = field.frontier(next_activations, query.budget.beam, step + 1)
        if not frontier.activations:
            break
    if collect_rejected:
        for placement in field.placements:
            if placement.shard_id not in selected:
                rejected.append(placement.shard_id)
    return RecallDigest(query.query_id, tuple(sorted(selected)), tuple(selected[key] for key in sorted(selected)), tuple(sorted(rejected)), exhausted, ("no_global_capture_pool_claim",))


def _entry_activations(query: QueryProbe, field: RelationField) -> tuple[SparseActivation, ...]:
    if query.entry_mode == "explicit_cell":
        if not isinstance(query.entry_ref, CellAddress):
            raise TypeError("explicit_cell entry_ref must be CellAddress")
        return (SparseActivation(query.entry_ref, Q16_ONE, query.query_id),)
    matches = field.explicit_entries(query.entry_mode, query.entry_ref)
    return tuple(SparseActivation(record.geometry_mark.cell, Q16_ONE, query.query_id) for record in sorted(matches, key=lambda item: item.shard_id))


def _report(query: QueryProbe, shard_id: str, path: tuple[RecallPath, ...], score: int, fallback: str) -> CoverageReport:
    bridge_count = sum(1 for item in path if item.kernel_type == "bridge")
    drift = {"steps": len(path), "bridge_count": bridge_count}
    return CoverageReport(str(query.entry_ref), shard_id, path, score, drift, "direct" if not path else "propagated", bridge_count, fallback)
