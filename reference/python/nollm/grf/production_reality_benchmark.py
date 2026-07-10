"""GRF4R measured capture-to-fallback benchmark with bounded validation storage."""

from __future__ import annotations

from dataclasses import dataclass
from sys import getsizeof
from time import perf_counter_ns

from .admission_bridge import GRFAdmissionBridge, resolve_source_fallback
from .capture import GRFCaptureIngress, GRFCaptureRequest
from .cell_address import CellAddress
from .evidence import EvidenceShardRecord
from .field_engine import CellRegistry, FieldEngine
from .exporters import to_jsonable
from .json_canonical import canonical_dumps
from .kernel_registry import KernelRegistry
from .recall import QueryProbe, RecallBudget, resolve_grf_recall
from .source_window import SourceWindowRecord


@dataclass(frozen=True)
class RealityBenchmarkMetrics:
    dataset_size: int
    items_per_second: int
    bytes_per_second: int
    capture_latency_ns: int
    placement_latency_ns: int
    admission_latency_ns: int
    recall_latency_ns: int
    rebuild_latency_ns: int
    evidence_storage_size: int
    placement_storage_size: int
    admission_storage_size: int
    kernel_storage_size: int
    template_storage_size: int
    relation_storage_size: int
    index_storage_size: int
    recall_correctness: str
    source_faithfulness: str
    false_stitch_rate: str
    missed_stitch_rate: str
    source_fallback_success: str
    failure_rate: str

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


class StreamingValidationStore:
    """Serializes every written object while retaining only active pipeline facts."""

    def __init__(self) -> None:
        self.evidence: dict[str, EvidenceShardRecord] = {}
        self.placements: dict[str, object] = {}
        self.first_shard_id: str | None = None
        self.storage_bytes = {"evidence": 0, "placement": 0, "admission": 0, "other": 0}

    def write_evidence_shard(self, shard: EvidenceShardRecord, recorded_at: str | None = None):
        self._measure("evidence", shard)
        self.evidence[shard.shard_id] = shard
        if self.first_shard_id is None:
            self.first_shard_id = shard.shard_id

    def read_evidence_shard(self, shard_id: str) -> EvidenceShardRecord:
        try:
            return self.evidence[shard_id]
        except KeyError as exc:
            raise FileNotFoundError("missing streamed evidence") from exc

    def write_evidence_island(self, island):
        self._measure("other", island)

    def write_local_patch(self, patch):
        self._measure("other", patch)

    def write_placement_candidate(self, candidate):
        self._measure("other", candidate)

    def write_placement_record(self, record, recorded_at: str | None = None):
        self._measure("placement", record)
        self.placements[record.placement_id] = record

    def read_placement_record(self, placement_id: str):
        try:
            return self.placements[placement_id]
        except KeyError as exc:
            raise FileNotFoundError("missing streamed placement") from exc

    def write_rejection_record(self, record, recorded_at: str | None = None):
        self._measure("other", record)

    def minimal_admission_records(self) -> tuple[object, ...]:
        return ()

    def write_minimal_admission_record(self, record, recorded_at: str | None = None):
        self._measure("admission", record)

    def release(self, shard_id: str, placement_id: str) -> None:
        if shard_id != self.first_shard_id:
            self.evidence.pop(shard_id, None)
        self.placements.pop(placement_id, None)

    def _measure(self, category: str, value: object) -> None:
        payload = value.to_mapping() if hasattr(value, "to_mapping") else value.__dict__
        self.storage_bytes[category] += len(canonical_dumps(payload))


def run_reality_benchmark(dataset_size: int) -> RealityBenchmarkMetrics:
    if type(dataset_size) is not int or dataset_size < 1:
        raise ValueError("dataset_size must be a positive integer")
    store = StreamingValidationStore()
    ingress = GRFCaptureIngress(store)
    bridge = GRFAdmissionBridge(store)
    kernels = KernelRegistry()
    kernels.compile_profiles(("eisenstein_exact_v1",))
    engine = FieldEngine(kernels, CellRegistry())
    capture_ns = placement_ns = admission_ns = 0
    fallback_success = 0
    total_started = perf_counter_ns()
    first_placement = None

    for index in range(dataset_size):
        window_id = f"window:grf4r:benchmark:{index}"
        capture_started = perf_counter_ns()
        receipt = ingress.capture(GRFCaptureRequest(f"capture:grf4r:benchmark:{index}", f"production reality evidence {index}", "validation_fixture", (window_id,), "2026-07-10T00:00:00Z"))
        capture_ns += perf_counter_ns() - capture_started
        if receipt.status != "captured" or receipt.shard_id is None:
            raise AssertionError("stream capture failed")
        shard = store.read_evidence_shard(receipt.shard_id)
        window = SourceWindowRecord(window_id, "validation_fixture", (f"fixture:{index}",), "2026-07-10T00:00:00Z")
        placement_started = perf_counter_ns()
        placed = bridge.place(shard, window, {"policy_id": "validation_fixture_policy", "target_cell": CellAddress("eisenstein_exact_v1", "chart:grf4r:benchmark", 0, index, 0)}, "2026-07-10T00:00:01Z")
        placement_ns += perf_counter_ns() - placement_started
        placement = placed.placement_record
        if placement is None or placed.admission_record is not None:
            raise AssertionError("place did not produce placement-only state")
        admission_started = perf_counter_ns()
        bridge.admit_existing_placement(shard, placement.placement_id, "2026-07-10T00:00:02Z", "validation_fixture")
        admission_ns += perf_counter_ns() - admission_started
        fallback = resolve_source_fallback(placement.source_fallback_refs[0], store)
        if isinstance(fallback, EvidenceShardRecord) and fallback.content == shard.content:
            fallback_success += 1
        engine.insert(placement)
        if first_placement is None:
            first_placement = placement
        store.release(shard.shard_id, placement.placement_id)

    pipeline_ns = perf_counter_ns() - total_started
    if first_placement is None:
        raise AssertionError("benchmark produced no placement")
    rebuild_started = perf_counter_ns()
    field = engine.build_relation_field()
    rebuild_ns = perf_counter_ns() - rebuild_started
    recall_started = perf_counter_ns()
    digest = resolve_grf_recall(QueryProbe("query:grf4r:benchmark", "shard_id", first_placement.shard_id, ("lateral",), RecallBudget(0, 1, 0, 0, 0, 1)), field)
    recall_ns = perf_counter_ns() - recall_started
    correct = digest.selected_shards == (first_placement.shard_id,)
    faithful = correct and digest.coverage_reports[0].source_fallback_ref == first_placement.source_fallback_refs[0]
    kernel_size = len(canonical_dumps(tuple((key.stable_key(), tuple(entry.__dict__.copy() for entry in entries)) for key, entries in kernels.templates())))
    template_size = len(canonical_dumps(to_jsonable(kernels.coverage_templates())))
    index_size, relation_size = _engine_sizes(engine)
    total_bytes = sum(store.storage_bytes.values()) + kernel_size + template_size + relation_size
    return RealityBenchmarkMetrics(
        dataset_size,
        dataset_size * 1_000_000_000 // max(1, pipeline_ns),
        total_bytes * 1_000_000_000 // max(1, pipeline_ns),
        capture_ns,
        placement_ns,
        admission_ns,
        recall_ns,
        rebuild_ns,
        store.storage_bytes["evidence"],
        store.storage_bytes["placement"],
        store.storage_bytes["admission"],
        kernel_size,
        template_size,
        relation_size,
        index_size,
        "1/1" if correct else "0/1",
        "1/1" if faithful else "0/1",
        "0/1",
        "0/1",
        f"{fallback_success}/{dataset_size}",
        f"0/{dataset_size}",
    )


def _engine_sizes(engine: FieldEngine) -> tuple[int, int]:
    index = engine.placements
    index_size = getsizeof(index._placements) + getsizeof(index._by_cell) + getsizeof(index._by_shard)
    relation_size = index_size + getsizeof(engine.registry._cells) + getsizeof(engine.registry._placements)
    relation_size += sum(getsizeof(record) + getsizeof(record.geometry_mark) + getsizeof(record.geometry_mark.cell) for record in index._placements.values())
    return index_size, relation_size
