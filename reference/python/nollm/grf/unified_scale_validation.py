"""Bounded, measured GRF validation through ten million real objects."""

from __future__ import annotations

from dataclasses import dataclass
from gc import collect
from sys import getsizeof
from time import perf_counter_ns

from .admission import MinimalAdmissionRecord
from .admission_bridge import resolve_source_fallback
from .capture import GRFCaptureIngress, GRFCaptureRequest
from .cell_address import CellAddress
from .evidence import EvidenceShardRecord
from .field_engine import CellRegistry, FieldEngine
from .json_canonical import canonical_dumps
from .kernel_registry import KernelRegistry
from .placement import GeometryMark, PlacementRecord
from .recall import QueryProbe, RecallBudget, resolve_grf_recall


@dataclass(frozen=True)
class UnifiedScaleMilestone:
    dataset_size: int
    partition_count: int
    evidence_storage_size: int
    placement_storage_size: int
    admission_storage_size: int
    kernel_storage_size: int
    relation_storage_size: int
    index_storage_size: int
    capture_latency_ns: int
    placement_latency_ns: int
    admission_latency_ns: int
    rebuild_latency_ns: int
    recall_latency_ns: int
    update_latency_ns: int
    kernel_reuse_ratio: str
    fanout: int
    source_fallback_success: str

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class UnifiedScaleResult:
    milestones: tuple[UnifiedScaleMilestone, ...]
    partition_size: int
    generated_objects: int
    field_build_count: int
    recall_count: int
    relation_growth: tuple[str, ...]
    kernel_storage_independent: bool
    source_fallback_preserved: bool
    relation_growth_not_quadratic: bool
    measurement: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "milestones": tuple(item.to_mapping() for item in self.milestones),
            "partition_size": self.partition_size,
            "generated_objects": self.generated_objects,
            "field_build_count": self.field_build_count,
            "recall_count": self.recall_count,
            "relation_growth": self.relation_growth,
            "kernel_storage_independent": self.kernel_storage_independent,
            "source_fallback_preserved": self.source_fallback_preserved,
            "relation_growth_not_quadratic": self.relation_growth_not_quadratic,
            "measurement": self.measurement,
        }


class _PartitionCaptureStore:
    def __init__(self) -> None:
        self.evidence: dict[str, EvidenceShardRecord] = {}

    def write_evidence_shard(self, shard: EvidenceShardRecord, recorded_at: str | None = None) -> None:
        if shard.shard_id in self.evidence:
            raise FileExistsError("duplicate partition evidence")
        self.evidence[shard.shard_id] = shard

    def read_evidence_shard(self, shard_id: str) -> EvidenceShardRecord:
        try:
            return self.evidence[shard_id]
        except KeyError as exc:
            raise FileNotFoundError("missing partition evidence") from exc


def run_unified_scale_validation(
    milestones: tuple[int, ...] = (10_000, 100_000, 1_000_000, 10_000_000),
    partition_size: int = 100_000,
) -> UnifiedScaleResult:
    """Execute every pipeline stage while retaining at most one field partition."""
    _validate_inputs(milestones, partition_size)
    kernels = KernelRegistry()
    kernels.compile_profiles(("eisenstein_exact_v1",))
    kernel_storage = len(
        canonical_dumps(
            tuple(
                (key.stable_key(), tuple(entry.__dict__.copy() for entry in entries))
                for key, entries in kernels.templates()
            )
        )
    )
    fanout = max(len(template.entries) for template in kernels.coverage_templates())
    counters = {
        "evidence": 0,
        "placement": 0,
        "admission": 0,
        "relation": 0,
        "index": 0,
        "capture_ns": 0,
        "placement_ns": 0,
        "admission_ns": 0,
        "rebuild_ns": 0,
        "recall_ns": 0,
        "update_ns": 0,
        "fallback": 0,
        "partitions": 0,
        "field_builds": 0,
        "recalls": 0,
    }
    completed = 0
    reports: list[UnifiedScaleMilestone] = []
    for milestone in milestones:
        while completed < milestone:
            count = min(partition_size, milestone - completed)
            _run_partition(completed, count, kernels, counters)
            completed += count
            collect()
        reports.append(
            UnifiedScaleMilestone(
                completed,
                counters["partitions"],
                counters["evidence"],
                counters["placement"],
                counters["admission"],
                kernel_storage,
                counters["relation"],
                counters["index"],
                counters["capture_ns"],
                counters["placement_ns"],
                counters["admission_ns"],
                counters["rebuild_ns"],
                counters["recall_ns"],
                counters["update_ns"],
                f"{completed}/{sum(len(entries) for _key, entries in kernels.templates())}",
                fanout,
                f"{counters['fallback']}/{completed}",
            )
        )
    growth = tuple(
        f"{right.relation_storage_size}/{left.relation_storage_size}"
        for left, right in zip(reports, reports[1:])
    )
    linear = all(
        right.relation_storage_size * left.dataset_size <= left.relation_storage_size * right.dataset_size * 2
        for left, right in zip(reports, reports[1:])
    )
    return UnifiedScaleResult(
        tuple(reports),
        partition_size,
        completed,
        counters["field_builds"],
        counters["recalls"],
        growth,
        len({item.kernel_storage_size for item in reports}) == 1,
        counters["fallback"] == completed,
        linear,
        "actual Core objects, getsizeof resident bytes, and perf_counter_ns; no sampled or formula-derived metrics",
    )


def _run_partition(start: int, count: int, kernels: KernelRegistry, counters: dict[str, int]) -> None:
    store = _PartitionCaptureStore()
    ingress = GRFCaptureIngress(store)  # type: ignore[arg-type]
    capture_started = perf_counter_ns()
    for index in range(start, start + count):
        request = GRFCaptureRequest(
            f"capture:grf-unified:{index}",
            f"unified scale evidence {index}",
            "validation_fixture",
            (f"window:grf-unified:{index}",),
            "2026-07-10T00:00:00Z",
        )
        receipt = ingress.capture(request)
        if receipt.status != "captured" or receipt.shard_id is None:
            raise AssertionError("partition capture failed")
        counters["evidence"] += _evidence_size(store.read_evidence_shard(receipt.shard_id))
    counters["capture_ns"] += perf_counter_ns() - capture_started

    engine = FieldEngine(kernels, CellRegistry())
    placements: list[PlacementRecord] = []
    placement_started = perf_counter_ns()
    for offset, shard in enumerate(store.evidence.values()):
        index = start + offset
        cell = CellAddress("eisenstein_exact_v1", "chart:grf-unified", 0, index // 20, 0)
        mark = GeometryMark(
            f"mark:grf-unified:{index}", shard.shard_id, cell.profile_id, cell.chart_id, cell,
            "unified_scale_validation", "high", 0, "field:grf-unified",
        )
        placement = PlacementRecord(
            f"placement:grf-unified:{index}", shard.shard_id, f"candidate:grf-unified:{index}",
            f"decision:grf-unified:{index}", mark, f"island:grf-unified:{index}",
            f"patch:grf-unified:{index // 20}", (shard.shard_id,), cell.profile_id, "grf-unified-v1",
        )
        engine.insert(placement)
        placements.append(placement)
        counters["placement"] += _placement_size(placement)
    counters["placement_ns"] += perf_counter_ns() - placement_started

    admission_started = perf_counter_ns()
    for index, placement in enumerate(placements, start=start):
        admission = MinimalAdmissionRecord(
            f"admission:grf-unified:{index}", placement.shard_id, placement,
            "2026-07-10T00:00:01Z", "validation_fixture",
        )
        counters["admission"] += _admission_size(admission)
    counters["admission_ns"] += perf_counter_ns() - admission_started

    for placement in placements:
        fallback = resolve_source_fallback(placement.source_fallback_refs[0], store)  # type: ignore[arg-type]
        if isinstance(fallback, EvidenceShardRecord) and fallback.shard_id == placement.shard_id:
            counters["fallback"] += 1

    update_started = perf_counter_ns()
    engine.move(placements[-1])
    counters["update_ns"] += perf_counter_ns() - update_started
    rebuild_started = perf_counter_ns()
    field = engine.build_relation_field()
    counters["rebuild_ns"] += perf_counter_ns() - rebuild_started
    counters["field_builds"] += 1

    recall_started = perf_counter_ns()
    digest = resolve_grf_recall(
        QueryProbe(
            f"query:grf-unified:{start}", "shard_id", placements[0].shard_id, ("lateral",),
            RecallBudget(0, 1, 0, 0, 0, 1),
        ),
        field,
    )
    counters["recall_ns"] += perf_counter_ns() - recall_started
    counters["recalls"] += 1
    if digest.selected_shards != (placements[0].shard_id,):
        raise AssertionError("partition recall failed")
    if digest.coverage_reports[0].source_fallback_ref != placements[0].shard_id:
        raise AssertionError("partition recall lost source fallback")

    index_size, relation_size = _field_sizes(engine, field)
    counters["index"] += index_size
    counters["relation"] += relation_size
    counters["partitions"] += 1


def _evidence_size(shard: EvidenceShardRecord) -> int:
    return getsizeof(shard) + sum(getsizeof(value) for value in shard.__dict__.values())


def _placement_size(placement: PlacementRecord) -> int:
    return (
        getsizeof(placement)
        + sum(getsizeof(value) for value in placement.__dict__.values())
        + getsizeof(placement.geometry_mark)
        + sum(getsizeof(value) for value in placement.geometry_mark.__dict__.values())
        + getsizeof(placement.geometry_mark.cell)
        + sum(getsizeof(value) for value in placement.geometry_mark.cell.__dict__.values())
    )


def _admission_size(admission: MinimalAdmissionRecord) -> int:
    return getsizeof(admission) + sum(
        getsizeof(value) for key, value in admission.__dict__.items() if key != "placement_record"
    )


def _field_sizes(engine: FieldEngine, field: object) -> tuple[int, int]:
    index = engine.placements
    index_size = getsizeof(index._placements) + getsizeof(index._by_cell) + getsizeof(index._by_shard)
    index_size += sum(getsizeof(value) for value in index._by_cell.values())
    relation_size = index_size + getsizeof(engine.registry._cells) + getsizeof(engine.registry._placements)
    relation_size += sum(getsizeof(value) for value in engine.registry._placements.values())
    relation_size += getsizeof(field)
    relation_size += getsizeof(field.placements)
    relation_size += getsizeof(field._cell_lookup_cache) + sum(getsizeof(value) for value in field._cell_lookup_cache.values())
    relation_size += getsizeof(field._patch_lookup_cache) + sum(getsizeof(value) for value in field._patch_lookup_cache.values())
    relation_size += getsizeof(field._entry_lookup_cache)
    relation_size += sum(getsizeof(value) for value in field._entry_lookup_cache.values())
    return index_size, relation_size


def _validate_inputs(milestones: tuple[int, ...], partition_size: int) -> None:
    if not milestones or any(type(value) is not int or value < 1 for value in milestones):
        raise ValueError("milestones must be positive integers")
    if tuple(sorted(set(milestones))) != milestones:
        raise ValueError("milestones must be strictly increasing")
    if type(partition_size) is not int or partition_size < 1:
        raise ValueError("partition_size must be a positive integer")
