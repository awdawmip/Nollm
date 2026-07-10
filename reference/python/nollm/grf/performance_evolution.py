"""Measured GRF5 indexed recall lookup benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from sys import getsizeof
from time import perf_counter_ns

from .field_engine import FieldEngine
from .kernel_registry import KernelRegistry
from .real_scale_benchmark import RealSyntheticDataset


@dataclass(frozen=True)
class RecallIndexMetrics:
    placement_count: int
    query_count: int
    indexed_lookup_ns: int
    linear_lookup_ns: int
    index_storage_bytes: int
    equivalent: bool


def run_recall_index_benchmark(placement_count: int = 100_000, query_count: int = 1_000) -> RecallIndexMetrics:
    registry = KernelRegistry()
    registry.compile_profiles(("eisenstein_exact_v1",))
    engine = FieldEngine(registry)
    for _shard, _window, _island, placement in RealSyntheticDataset(placement_count).records():
        engine.insert(placement)
    field = engine.build_relation_field()
    probes = tuple(field.placements[(index * 7919) % placement_count].shard_id for index in range(query_count))
    indexed_started = perf_counter_ns()
    indexed = tuple(field.placements_for_entry("shard_id", shard_id) for shard_id in probes)
    indexed_ns = perf_counter_ns() - indexed_started
    linear_started = perf_counter_ns()
    linear = tuple(tuple(item for item in field.placements if item.shard_id == shard_id) for shard_id in probes)
    linear_ns = perf_counter_ns() - linear_started
    index_storage = getsizeof(field._entry_lookup_cache) + sum(getsizeof(index) for index in field._entry_lookup_cache.values())
    return RecallIndexMetrics(placement_count, query_count, indexed_ns, linear_ns, index_storage, indexed == linear)
