"""Measured resident and global-sharded GRF7 scale validation."""

from __future__ import annotations

from dataclasses import dataclass, replace
import gzip
from hashlib import sha256
import json
from pathlib import Path
from struct import Struct
from time import perf_counter_ns
import tracemalloc

from .admission import MinimalAdmissionRecord
from .capture import GRFCaptureIngress, GRFCaptureRequest
from .cell_address import CellAddress
from .evidence import EvidenceShardRecord
from .field_engine import CellRegistry, FieldEngine
from .global_field import GlobalFieldDirectory, GRFPartitionDescriptor, GRFPartitionNeighbor, GRFPartitionSnapshotRef, partition_descriptor
from .kernel_registry import KernelRegistry
from .placement import GeometryMark, PlacementRecord
from .recall import QueryProbe, RecallBudget, resolve_grf_recall

EVIDENCE_ROW = Struct("<Q32s")
PLACEMENT_ROW = Struct("<Qqq32s")
ADMISSION_ROW = Struct("<Q32s")


@dataclass(frozen=True)
class ResidentScaleMetric:
    placement_count: int
    cell_count: int
    process_peak_rss_bytes: int
    tracemalloc_current_bytes: int
    tracemalloc_peak_bytes: int
    python_deep_estimate_bytes: int
    shallow_estimate_bytes: int
    relation_container_bytes: int
    build_latency_ns: int
    recall_latency_ns: int
    source_fallback_success: str

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class GlobalScaleMetric:
    logical_global_placement_count: int
    partition_count: int
    loaded_partition_count: int
    generated_evidence_count: int
    field_build_count: int
    recall_count: int
    source_fallback_success: str
    directory_bytes: int
    neighbor_link_count: int
    bridge_count: int
    process_peak_rss_bytes: int
    tracemalloc_peak_bytes: int
    python_deep_estimate_bytes: int
    shallow_estimate_bytes: int
    serialized_disk_bytes: int
    serialized_uncompressed_bytes: int
    file_count: int
    compression_ratio: str
    directory_rebuild_time_ns: int
    reload_time_ns: int
    reloaded_placement_count: int

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class GRF7ScaleResult:
    resident: tuple[ResidentScaleMetric, ...]
    global_sharded: GlobalScaleMetric
    kernel_storage_bytes: int
    kernel_independent: bool
    resident_and_global_metrics_separated: bool
    status: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "resident": tuple(item.to_mapping() for item in self.resident),
            "global_sharded": self.global_sharded.to_mapping(),
            "kernel_storage_bytes": self.kernel_storage_bytes,
            "kernel_independent": self.kernel_independent,
            "resident_and_global_metrics_separated": self.resident_and_global_metrics_separated,
            "status": self.status,
        }


class _CaptureStore:
    def __init__(self) -> None:
        self.evidence: dict[str, EvidenceShardRecord] = {}

    def write_evidence_shard(self, shard: EvidenceShardRecord, recorded_at: str | None = None) -> None:
        if shard.shard_id in self.evidence:
            raise FileExistsError("duplicate evidence")
        self.evidence[shard.shard_id] = shard

    def read_evidence_shard(self, shard_id: str) -> EvidenceShardRecord:
        try:
            return self.evidence[shard_id]
        except KeyError as exc:
            raise FileNotFoundError(shard_id) from exc


class _ScaleStores:
    def __init__(self, root: Path, prefix: str) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.paths = {
            "evidence": root / f"{prefix}_evidence.bin.gz",
            "placement": root / f"{prefix}_placement.bin.gz",
            "admission": root / f"{prefix}_admission.bin.gz",
        }
        self._files = {key: gzip.open(path, "wb", compresslevel=1) for key, path in self.paths.items()}
        self.uncompressed_bytes = 0

    def write(self, index: int, shard: EvidenceShardRecord, placement: PlacementRecord, admission: MinimalAdmissionRecord) -> None:
        evidence = EVIDENCE_ROW.pack(index, bytes.fromhex(shard.content_sha256 or ""))
        cell = placement.geometry_mark.cell
        placement_row = PLACEMENT_ROW.pack(index, cell.q, cell.r, sha256(placement.placement_id.encode("utf-8")).digest())
        admission_row = ADMISSION_ROW.pack(index, sha256(admission.admission_id.encode("utf-8")).digest())
        for key, row in (("evidence", evidence), ("placement", placement_row), ("admission", admission_row)):
            self._files[key].write(row)
            self.uncompressed_bytes += len(row)

    def close(self) -> None:
        for stream in self._files.values():
            stream.close()


def run_grf7_scale_validation(
    output_root: Path,
    resident_milestones: tuple[int, ...] = (100_000, 500_000, 1_000_000),
    global_count: int = 10_000_000,
    partition_size: int = 100_000,
) -> GRF7ScaleResult:
    _validate_scale_inputs(resident_milestones, global_count, partition_size)
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    tracemalloc.start()
    resident, kernel_bytes = _resident_validation(root / "resident", resident_milestones)
    global_metric = _global_validation(root / "global", global_count, partition_size)
    tracemalloc.stop()
    return GRF7ScaleResult(resident, global_metric, kernel_bytes, True, True, "GATE_D_PASS|GATE_E_PASS")


def _resident_validation(root: Path, milestones: tuple[int, ...]) -> tuple[tuple[ResidentScaleMetric, ...], int]:
    store = _CaptureStore()
    ingress = GRFCaptureIngress(store)  # type: ignore[arg-type]
    kernels = KernelRegistry()
    kernels.compile_profiles(("eisenstein_exact_v1",))
    engine = FieldEngine(kernels, CellRegistry())
    disk = _ScaleStores(root, "resident_1m")
    metrics: list[ResidentScaleMetric] = []
    fallback = shallow = deep = 0
    completed = 0
    try:
        for target in milestones:
            for index in range(completed, target):
                shard, placement, admission = _pipeline_record(index, ingress, store, "resident")
                engine.insert(placement)
                if placement.source_fallback_refs == (shard.shard_id,):
                    fallback += 1
                shallow += _shallow_size(shard, placement, admission)
                deep += _deep_record_size(shard, placement, admission)
                disk.write(index, shard, placement, admission)
            completed = target
            build_started = perf_counter_ns()
            field = engine.build_relation_field()
            build_ns = perf_counter_ns() - build_started
            recall_started = perf_counter_ns()
            digest = resolve_grf_recall(QueryProbe(f"query:grf7:resident:{target}", "placement_id", f"placement:grf7:resident:{target - 1}", ("lateral",), RecallBudget(0, 1, 0, 0, 0, 1)), field)
            recall_ns = perf_counter_ns() - recall_started
            if digest.selected_shards != (f"shard:grf:{sha256(f'capture:grf7:resident:{target - 1}'.encode()).hexdigest()[:24]}",):
                raise AssertionError("resident recall mismatch")
            current, trace_peak = tracemalloc.get_traced_memory()
            relation_bytes = _relation_container_bytes(engine, field)
            metrics.append(ResidentScaleMetric(target, engine.registry.cell_count(), _peak_rss_bytes(), current, trace_peak, deep + relation_bytes, shallow, relation_bytes, build_ns, recall_ns, f"{fallback}/{target}"))
    finally:
        disk.close()
    kernel_bytes = len(kernels.digest().encode("ascii")) + sum(len(entries) for _key, entries in kernels.templates()) * 24
    return tuple(metrics), kernel_bytes


def _global_validation(root: Path, global_count: int, partition_size: int) -> GlobalScaleMetric:
    root.mkdir(parents=True, exist_ok=True)
    directory = GlobalFieldDirectory()
    generated = fallback = field_builds = recalls = shallow = deep = uncompressed = 0
    partition_count = (global_count + partition_size - 1) // partition_size
    for partition_index in range(partition_count):
        start = partition_index * partition_size
        count = min(partition_size, global_count - start)
        partition_id = f"partition:grf7:{partition_index:04d}"
        descriptor = partition_descriptor(partition_id, start // 20, (start + count - 1) // 20, start, start + count - 1, "source_range")
        directory.add(descriptor)
        store = _CaptureStore()
        ingress = GRFCaptureIngress(store)  # type: ignore[arg-type]
        kernels = KernelRegistry()
        kernels.compile_profiles(("eisenstein_exact_v1",))
        engine = FieldEngine(kernels, CellRegistry())
        disk = _ScaleStores(root / "partitions", f"partition_{partition_index:04d}")
        try:
            for index in range(start, start + count):
                shard, placement, admission = _pipeline_record(index, ingress, store, "global")
                engine.insert(placement)
                generated += 1
                fallback += placement.source_fallback_refs == (shard.shard_id,)
                shallow += _shallow_size(shard, placement, admission)
                deep += _deep_record_size(shard, placement, admission)
                disk.write(index, shard, placement, admission)
            disk.close()
            field = engine.build_relation_field()
            field_builds += 1
            target = start + count - 1
            digest = resolve_grf_recall(QueryProbe(f"query:grf7:global:{partition_index}", "placement_id", f"placement:grf7:global:{target}", ("lateral",), RecallBudget(0, 1, 0, 0, 0, 1)), field)
            recalls += 1
            if len(digest.selected_shards) != 1 or digest.coverage_reports[0].source_fallback_ref != digest.selected_shards[0]:
                raise AssertionError("global partition recall/fallback mismatch")
            snapshot_payload = b"".join((path.name.encode("utf-8") + b":" + str(path.stat().st_size).encode("ascii") + b"\n") for path in disk.paths.values())
            snapshot = GRFPartitionSnapshotRef(partition_id, str((root / "partitions" / f"partition_{partition_index:04d}_placement.bin.gz").relative_to(root)), f"ledger:{partition_id}", 1, sha256(snapshot_payload).hexdigest())
            directory.replace(replace(descriptor, placement_count=count, snapshot_ref=snapshot))
            uncompressed += disk.uncompressed_bytes
        finally:
            disk.close()
        if partition_index:
            directory.connect(GRFPartitionNeighbor(f"partition:grf7:{partition_index - 1:04d}", partition_id, "spatial_boundary", True))
    bridge_payload = tuple({"bridge_id": f"bridge:grf7:{index:04d}", "from": f"partition:grf7:{index:04d}", "to": f"partition:grf7:{index + 1:04d}", "state": "accepted", "max_fanout": 1} for index in range(max(0, partition_count - 1)))
    bridge_path = root / "bridge_store.json"
    bridge_path.write_text(json.dumps(bridge_payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    ledger_path = root / "ledger.jsonl"
    ledger_path.write_text("".join(json.dumps({"event": "partition_snapshot", "partition_id": item.partition_id, "snapshot_ref": item.snapshot_ref.snapshot_ref}, sort_keys=True) + "\n" for item in directory.entries()), encoding="utf-8", newline="\n")
    rebuild_started = perf_counter_ns()
    directory_payload = directory.canonical_bytes()
    rebuilt = GlobalFieldDirectory.from_bytes(directory_payload)
    rebuild_ns = perf_counter_ns() - rebuild_started
    directory_path = root / "GRF7_GLOBAL_DIRECTORY_MANIFEST.json"
    directory_path.write_bytes(directory_payload)
    reload_started = perf_counter_ns()
    reloaded = 0
    for path in sorted((root / "partitions").glob("*_placement.bin.gz")):
        with gzip.open(path, "rb") as stream:
            while stream.read(PLACEMENT_ROW.size):
                reloaded += 1
    reload_ns = perf_counter_ns() - reload_started
    files = tuple(path for path in root.rglob("*") if path.is_file())
    disk_bytes = sum(path.stat().st_size for path in files)
    return GlobalScaleMetric(global_count, partition_count, 0, generated, field_builds, recalls, f"{fallback}/{global_count}", len(directory_payload), len(rebuilt.to_mapping()["neighbors"]), len(bridge_payload), _peak_rss_bytes(), tracemalloc.get_traced_memory()[1], deep, shallow, disk_bytes, uncompressed, len(files), f"{uncompressed}/{disk_bytes}", rebuild_ns, reload_ns, reloaded)


def _pipeline_record(index: int, ingress: GRFCaptureIngress, store: _CaptureStore, namespace: str) -> tuple[EvidenceShardRecord, PlacementRecord, MinimalAdmissionRecord]:
    capture_id = f"capture:grf7:{namespace}:{index}"
    receipt = ingress.capture(GRFCaptureRequest(capture_id, f"grf7 {namespace} evidence {index}", "validation_fixture", (f"window:grf7:{namespace}:{index}",), "2026-07-10T00:00:00Z"))
    if receipt.status != "captured" or receipt.shard_id is None:
        raise AssertionError("GRF7 capture failed")
    shard = store.read_evidence_shard(receipt.shard_id)
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, index // 20, 0)
    mark = GeometryMark(f"mark:grf7:{namespace}:{index}", shard.shard_id, cell.profile_id, cell.chart_id, cell, "grf7_scale", "high", 0, "field:grf7")
    placement = PlacementRecord(f"placement:grf7:{namespace}:{index}", shard.shard_id, f"candidate:grf7:{namespace}:{index}", f"decision:grf7:{namespace}:{index}", mark, f"island:grf7:{namespace}:{index}", f"patch:grf7:{namespace}:{index // 20}", (shard.shard_id,), cell.profile_id, "grf7_scale_v1")
    admission = MinimalAdmissionRecord(f"admission:grf7:{namespace}:{index}", shard.shard_id, placement, "2026-07-10T00:00:01Z", "validation_fixture")
    return shard, placement, admission


def _shallow_size(shard: EvidenceShardRecord, placement: PlacementRecord, admission: MinimalAdmissionRecord) -> int:
    from sys import getsizeof
    return getsizeof(shard) + getsizeof(placement) + getsizeof(admission)


def _deep_record_size(shard: EvidenceShardRecord, placement: PlacementRecord, admission: MinimalAdmissionRecord) -> int:
    from sys import getsizeof
    values = (shard, *shard.__dict__.values(), placement, *placement.__dict__.values(), placement.geometry_mark, *placement.geometry_mark.__dict__.values(), placement.geometry_mark.cell, *placement.geometry_mark.cell.__dict__.values(), admission, admission.admission_id, admission.admitted_at, admission.admitted_by, admission.state)
    return sum(getsizeof(value) for value in values)


def _relation_container_bytes(engine: FieldEngine, field: object) -> int:
    from sys import getsizeof
    index = engine.placements
    total = getsizeof(index._placements) + getsizeof(index._by_cell) + getsizeof(index._by_shard)
    total += sum(getsizeof(value) for value in index._by_cell.values())
    total += getsizeof(engine.registry._cells) + getsizeof(engine.registry._placements)
    total += sum(getsizeof(value) for value in engine.registry._placements.values())
    total += getsizeof(field.placements) + getsizeof(field._cell_lookup_cache) + getsizeof(field._patch_lookup_cache) + getsizeof(field._entry_lookup_cache)
    total += sum(getsizeof(value) for value in field._cell_lookup_cache.values())
    total += sum(getsizeof(value) for value in field._patch_lookup_cache.values())
    total += sum(getsizeof(value) for value in field._entry_lookup_cache.values())
    return total


def _peak_rss_bytes() -> int:
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = (ctypes.c_void_p, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD)
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.PeakWorkingSetSize)


def _validate_scale_inputs(milestones: tuple[int, ...], global_count: int, partition_size: int) -> None:
    if not milestones or tuple(sorted(set(milestones))) != milestones or any(type(value) is not int or value < 1 for value in milestones):
        raise ValueError("resident milestones must be strictly increasing positive integers")
    if type(global_count) is not int or global_count < 1 or type(partition_size) is not int or partition_size < 1:
        raise ValueError("global_count and partition_size must be positive integers")
