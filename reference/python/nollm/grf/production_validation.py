"""Production-like in-memory GRF4 field benchmark without terminal imports."""

from __future__ import annotations

from dataclasses import dataclass, replace
from sys import getsizeof
from time import perf_counter_ns

from .cell_address import CellAddress
from .field_engine import CellRegistry, FieldEngine
from .kernel_registry import KernelRegistry
from .placement import GeometryMark, PlacementRecord
from .real_scale_benchmark import RealSyntheticDataset, inject_failure_boundaries
from .recall import QueryProbe, RecallBudget, resolve_grf_recall


@dataclass(frozen=True)
class GRF4ProductionMetrics:
    evidence_count: int
    placement_count: int
    profile_ids: tuple[str, ...]
    capture_throughput: str
    capture_latency_ns: int
    placement_latency_ns: int
    recall_latency_ns: int
    rebuild_latency_ns: int
    kernel_loading_ns: int
    cached_kernel_loading_ns: int
    memory_usage_bytes: int
    source_fallback_preserved: bool
    incremental_update_preserved: bool
    failure_recovery: dict[str, object]

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


def run_production_like_benchmark(dataset_size: int = 1_000_001) -> GRF4ProductionMetrics:
    if type(dataset_size) is not int or dataset_size < 1:
        raise ValueError("dataset_size must be a positive integer")
    profiles = ("eisenstein_exact_v1", "dream_quasi_v1", "aligned_baseline_v1")
    registry = KernelRegistry()
    registry.compile_profiles(profiles)
    kernel_started = perf_counter_ns()
    registry.coverage_templates()
    kernel_loading_ns = perf_counter_ns() - kernel_started
    cached_kernel_started = perf_counter_ns()
    registry.coverage_templates()
    cached_kernel_loading_ns = perf_counter_ns() - cached_kernel_started

    engine = FieldEngine(registry, CellRegistry())
    dataset = RealSyntheticDataset(dataset_size)
    started = perf_counter_ns()
    source_fallback_preserved = True
    first: PlacementRecord | None = None
    for index, (shard, _window, _island, placement) in enumerate(dataset.records()):
        mixed = _mixed_profile_placement(placement, profiles[index % len(profiles)])
        source_fallback_preserved = source_fallback_preserved and mixed.source_fallback_refs == shard.source_window_refs
        engine.insert(mixed)
        if first is None:
            first = mixed
    capture_latency_ns = perf_counter_ns() - started
    if first is None:
        raise AssertionError("production dataset unexpectedly empty")

    rebuild_started = perf_counter_ns()
    field = engine.build_relation_field()
    rebuild_latency_ns = perf_counter_ns() - rebuild_started
    recall_started = perf_counter_ns()
    digest = resolve_grf_recall(QueryProbe("query:grf4:production", "explicit_cell", first.geometry_mark.cell, ("lateral",), RecallBudget(0, 1, 0, 0, 0, 1)), field)
    recall_latency_ns = perf_counter_ns() - recall_started
    source_fallback_preserved = source_fallback_preserved and digest.coverage_reports[0].source_fallback_ref == first.source_fallback_refs[0]

    moved = _moved(first, first.geometry_mark.cell.q + 1, first.geometry_mark.cell.r + 1)
    engine.move(moved)
    incremental_field = engine.build_relation_field()
    rebuilt = FieldEngine(registry, CellRegistry())
    for placement in engine.placements.placements():
        rebuilt.insert(placement)
    full_field = rebuilt.build_relation_field()
    incremental_update_preserved = incremental_field.placements == full_field.placements and incremental_field.shards_at(moved.geometry_mark.cell) == full_field.shards_at(moved.geometry_mark.cell)
    memory_usage = _engine_memory_usage(engine)
    return GRF4ProductionMetrics(
        dataset_size,
        engine.placements.placement_count(),
        profiles,
        f"{dataset_size}/{capture_latency_ns}",
        capture_latency_ns,
        capture_latency_ns,
        recall_latency_ns,
        rebuild_latency_ns,
        kernel_loading_ns,
        cached_kernel_loading_ns,
        memory_usage,
        source_fallback_preserved,
        incremental_update_preserved,
        inject_failure_boundaries(),
    )


def _mixed_profile_placement(placement: PlacementRecord, profile_id: str) -> PlacementRecord:
    if placement.geometry_mark.profile_id == profile_id:
        return placement
    original = placement.geometry_mark
    cell = CellAddress(profile_id, original.chart_id, original.cell.layer, original.cell.q, original.cell.r, original.cell.phase)
    mark = GeometryMark(original.mark_id, placement.shard_id, profile_id, original.chart_id, cell, original.placement_method, original.confidence_band, original.uncertainty_q16, original.relation_field_ref)
    return replace(placement, geometry_mark=mark, replay_profile_id=profile_id)


def _moved(placement: PlacementRecord, q: int, r: int) -> PlacementRecord:
    mark = placement.geometry_mark
    cell = CellAddress(mark.profile_id, mark.chart_id, mark.cell.layer, q, r, mark.cell.phase)
    return replace(placement, geometry_mark=GeometryMark(mark.mark_id, placement.shard_id, mark.profile_id, mark.chart_id, cell, mark.placement_method, mark.confidence_band, mark.uncertainty_q16, mark.relation_field_ref))


def _engine_memory_usage(engine: FieldEngine) -> int:
    registry = engine.registry
    index = engine.placements
    return (
        getsizeof(registry._cells)
        + getsizeof(registry._placements)
        + getsizeof(index._placements)
        + getsizeof(index._by_cell)
        + getsizeof(index._by_shard)
        + sum(getsizeof(record) + getsizeof(record.geometry_mark) + getsizeof(record.geometry_mark.cell) for record in index._placements.values())
    )
