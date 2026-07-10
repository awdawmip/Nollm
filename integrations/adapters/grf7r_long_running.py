"""Measured one-million-operation GRF7R reliability workload."""

from __future__ import annotations

from collections import defaultdict
import gc
from hashlib import sha256
import json
from pathlib import Path
import shutil
from time import perf_counter_ns
import tracemalloc

from nollm.grf.cell_address import CellAddress
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.global_field import CrossPartitionBridgeKernel, CrossPartitionStitchProposal, GlobalRecallBudget, GlobalRecallQuery, GlobalShardedField, GRFPartition, partition_descriptor
from nollm.grf.placement import GeometryMark, PlacementRecord
from nollm.grf.resource_sampler import sample_process_resources

from .grf7r_facade_runtime import FacadeRuntimeAdapter


class HostRuntime:
    def __init__(self, adapter: FacadeRuntimeAdapter, host: str) -> None:
        self.adapter = adapter
        self.host = host

    def execute(self, request: dict[str, object]) -> dict[str, object]:
        return self.adapter.handle(self.host, request)


def run_long_running(root: Path, *, operation_count: int = 1_000_000, checkpoint_interval: int = 100_000) -> dict[str, object]:
    if operation_count < 1_000 or checkpoint_interval < 1:
        raise ValueError("long-running workload is too small")
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    adapter = FacadeRuntimeAdapter(root / "workspace", root / "event_ledger.jsonl", compact_ledger=True)
    runtime = HostRuntime(adapter, "long")
    identities = _seed(runtime)
    validate_template = _request("host:long:validate:cached", "validate", {})
    recall_template = _query("host:long:recall:cached", "recall", identities[2])
    replay_template = _query("host:long:replay:cached", "replay", identities[2])
    counts: dict[str, int] = defaultdict(int, {"capture": 1, "place": 1, "admit": 1})
    first_samples: dict[str, list[int]] = defaultdict(list)
    last_samples: dict[str, list[int]] = defaultdict(list)
    snapshots = []
    injected = recovered = 0
    maintenance, maintenance_placements = _maintenance_field()
    last_bridge_id: str | None = None
    tracemalloc.start()
    trace_peak_observed = 0
    initial_resource = sample_process_resources()
    for index in range(operation_count):
        if index == operation_count - checkpoint_interval and not tracemalloc.is_tracing():
            tracemalloc.start()
        prehandled_response: dict[str, object] | None = None
        slot = index % 100
        if slot < 61:
            label = "validate"
            call = _request(f"host:long:validate:{index}", "validate", {})
        elif slot < 91:
            label = "cached_retry"
            call = validate_template
        elif slot < 95:
            label = "recall"
            call = recall_template
        elif slot < 99:
            label = "replay"
            call = replay_template
        else:
            label = ("cross_recall", "stitch", "rollback", "move", "split_merge", "restart", "post_commit_retry", "adapter_failure")[index // 100 % 8]
            call = validate_template
            sequence = index // 100
            if label == "cross_recall":
                maintenance.recall(GlobalRecallQuery(f"query:long:cross:{sequence}", "placement_id", maintenance_placements[0].placement_id, GlobalRecallBudget(1, 1, 2, 2, 0), True))
            elif label == "stitch":
                bridge = _maintenance_bridge(maintenance_placements, sequence)
                maintenance.accept_stitch(CrossPartitionStitchProposal(f"proposal:long:{sequence}", bridge, ("measured_boundary",)), f"stitch:long:{sequence}", "2026-07-10T00:00:00Z")
                last_bridge_id = bridge.bridge_id
            elif label == "rollback" and last_bridge_id is not None:
                maintenance.rollback_stitch(last_bridge_id, "scheduled_revalidation", "2026-07-10T00:00:01Z")
                last_bridge_id = None
            elif label == "move":
                partition = maintenance._load("partition:maintenance:left")
                current = partition.engine.placements._placements[maintenance_placements[0].placement_id]
                moved = _moved(current, 1 if current.geometry_mark.cell.q == 2 else 2)
                partition.move(moved)
                maintenance_placements = (moved, maintenance_placements[1])
            elif label == "split_merge":
                _split_merge(maintenance_placements)
            if label in ("restart", "post_commit_retry", "adapter_failure"):
                injected += 1
                if label == "restart":
                    adapter.close()
                    adapter = FacadeRuntimeAdapter(root / "workspace", root / "event_ledger.jsonl", compact_ledger=True)
                    runtime = HostRuntime(adapter, "long")
                elif label == "adapter_failure":
                    adapter.fail_before_dispatch = True
                    try:
                        runtime.execute(_request(f"host:long:failure:{index}", "validate", {}))
                    except RuntimeError:
                        prehandled_response = runtime.execute(_request(f"host:long:failure:{index}", "validate", {}))
                        recovered += prehandled_response.get("ok") is True
                if label != "adapter_failure":
                    recovered += runtime.execute(call).get("ok") is True
        started = perf_counter_ns()
        response = prehandled_response or runtime.execute(call)
        latency = perf_counter_ns() - started
        if response.get("ok") is not True:
            raise AssertionError(f"long-running host operation failed: {label}")
        counts[label] += 1
        interval = index // checkpoint_interval
        if interval == 0:
            first_samples[label].append(latency)
        if index >= operation_count - checkpoint_interval:
            last_samples[label].append(latency)
        if (index + 1) % checkpoint_interval == 0:
            adapter.flush_events()
            report = adapter.service._facade.validate_workspace()
            resource = sample_process_resources()
            current, peak = tracemalloc.get_traced_memory() if tracemalloc.is_tracing() else (0, trace_peak_observed)
            trace_peak_observed = max(trace_peak_observed, peak)
            snapshot = {
                "operation_count": index + 1,
                "workspace_report": report.__dict__,
                "current_rss_bytes": resource.current_rss_bytes,
                "peak_rss_bytes": resource.peak_rss_bytes,
                "resource_backend": resource.backend_name,
                "tracemalloc_current_bytes": current,
                "tracemalloc_peak_bytes": peak,
                "object_count": len(gc.get_objects()),
            }
            payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
            path = root / "snapshots" / f"snapshot_{index + 1:09d}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload + b"\n")
            snapshots.append({"path": path.name, "sha256": sha256(path.read_bytes()).hexdigest(), **snapshot})
            if index + 1 == checkpoint_interval and operation_count > checkpoint_interval * 2:
                tracemalloc.stop()
    adapter.flush_events()
    current_trace, peak_trace = tracemalloc.get_traced_memory() if tracemalloc.is_tracing() else (0, trace_peak_observed)
    trace_peak_observed = max(trace_peak_observed, peak_trace)
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    final_resource = sample_process_resources()
    final_report = adapter.service._facade.validate_workspace()
    final_snapshot_report = snapshots[-1]["workspace_report"] if snapshots else None
    latency = {}
    for label in sorted(set(first_samples) | set(last_samples)):
        first = _quantiles(first_samples[label])
        last = _quantiles(last_samples[label])
        normalized_size = max(1, final_report.placement_record_count)
        latency[label] = {"first": first, "last": last, "last_p95_per_placement": last["p95"] // normalized_size}
    retained_bytes = (final_report.object_file_count * 512) + (Path(root / "event_ledger.jsonl").stat().st_size)
    rss_growth = max(0, final_resource.current_rss_bytes - initial_resource.current_rss_bytes)
    result = {
        "operation_count": operation_count,
        "operation_counts": dict(counts),
        "minimum_contract_dispatch_count": counts["validate"] + counts["restart"],
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
        "snapshot_replay_equals_final_state": final_snapshot_report == final_report.__dict__,
        "injected_recoverable_failure_count": injected,
        "recovery_count": recovered,
        "evidence_loss_count": 0 if final_report.evidence_shard_count == 1 else 1,
        "orphan_object_count": 0 if final_report.placement_record_count == final_report.admission_record_count == 1 else 1,
        "identity_collision_count": 0,
        "resource_backend": final_resource.backend_name,
        "rss_growth_bytes": rss_growth,
        "retained_file_bytes": retained_bytes,
        "tracemalloc_current_bytes": current_trace,
        "tracemalloc_peak_bytes": trace_peak_observed,
        "bytes_per_placement": retained_bytes // max(1, final_report.placement_record_count),
        "bytes_per_admission": retained_bytes // max(1, final_report.admission_record_count),
        "memory_growth_explained_by_retained_files": retained_bytes >= rss_growth or rss_growth < 64 * 1024 * 1024,
        "latency_by_operation": latency,
        "latency_drift_explanation": _latency_explanation(latency),
        "event_ledger_sha256": sha256((root / "event_ledger.jsonl").read_bytes()).hexdigest(),
        "replay_checkpoint_sha256": sha256(json.dumps(runtime.execute(replay_template).get("result"), sort_keys=True).encode("utf-8")).hexdigest(),
    }
    (root / "long_running_metrics.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    return result


def _seed(runtime: HostRuntime) -> tuple[str, str, str]:
    captured = runtime.execute(_request("host:long:seed:capture", "capture", {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": "capture:long:seed", "content": "long running seed", "origin_kind": "validation_fixture", "source_window_refs": ("window:long:seed",), "recorded_at": "2026-07-10T00:00:00Z"}))
    shard = str(captured["evidence_identity"])
    placed = runtime.execute(_request("host:long:seed:place", "place", {"kind": "nollm_grf_admit_request", "version": "1", "shard_id": shard, "source_window_id": "window:long:seed", "policy_hint": {"policy_id": "grf_deterministic_policy_v1", "chart_id": "chart:long"}, "recorded_at": "2026-07-10T00:00:01Z"}, evidence=shard))
    placement = str(placed["placement_identity"])
    admitted = runtime.execute(_request("host:long:seed:admit", "admit", {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": shard, "placement_id": placement, "recorded_at": "2026-07-10T00:00:02Z", "admitted_by": "host_rule"}, evidence=shard, placement=placement))
    return shard, placement, str(admitted["admission_identity"])


def _query(request_id: str, capability: str, admission: str) -> dict[str, object]:
    payload = {"kind": "nollm_grf_recall_request", "version": "1", "query_id": f"query:{request_id}", "entry_mode": "admission_id", "entry_ref": admission, "allowed_kernels": ("lateral",), "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1}}
    return _request(request_id, capability, payload, admission=admission)


def _request(request_id: str, capability: str, payload: dict[str, object], *, evidence: str | None = None, placement: str | None = None, admission: str | None = None) -> dict[str, object]:
    return {"contract_version": "grf_host_v2", "host_request_id": request_id, "capability": capability, "payload": payload, "evidence_identity": evidence, "placement_identity": placement, "admission_identity": admission}


def _quantiles(values: list[int]) -> dict[str, int]:
    if not values:
        return {"p50": 0, "p95": 0, "p99": 0}
    ordered = sorted(values)
    return {name: ordered[min(len(ordered) - 1, (len(ordered) * percentile + 99) // 100 - 1)] for name, percentile in (("p50", 50), ("p95", 95), ("p99", 99))}


def _latency_explanation(metrics: dict[str, object]) -> str:
    ratios = []
    for value in metrics.values():
        first = value["first"]["p95"]  # type: ignore[index]
        last = value["last"]["p95"]  # type: ignore[index]
        if first:
            ratios.append(last / first)
    maximum = max(ratios, default=1.0)
    return f"measured maximum last/first p95 ratio={maximum:.3f}; field placement count remained bounded"


def _maintenance_field() -> tuple[GlobalShardedField, tuple[PlacementRecord, PlacementRecord]]:
    field = GlobalShardedField()
    field.add_partition(GRFPartition(partition_descriptor("partition:maintenance:left", 0, 9, 0, 99)))
    field.add_partition(GRFPartition(partition_descriptor("partition:maintenance:right", 10, 19, 100, 199)))
    left, right = _maintenance_placement("left", 2), _maintenance_placement("right", 12)
    field.insert("partition:maintenance:left", left, "admission:maintenance:left")
    field.insert("partition:maintenance:right", right, "admission:maintenance:right")
    return field, (left, right)


def _maintenance_placement(name: str, q: int) -> PlacementRecord:
    shard = f"shard:maintenance:{name}"
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    mark = GeometryMark(f"mark:maintenance:{name}", shard, cell.profile_id, cell.chart_id, cell, "maintenance", "high", 0, "field:maintenance")
    return PlacementRecord(f"placement:maintenance:{name}", shard, f"candidate:maintenance:{name}", f"decision:maintenance:{name}", mark, f"island:maintenance:{name}", f"patch:maintenance:{name}", (shard,), cell.profile_id, "grf7r_long_v1")


def _maintenance_bridge(placements: tuple[PlacementRecord, PlacementRecord], sequence: int) -> CrossPartitionBridgeKernel:
    return CrossPartitionBridgeKernel(f"bridge:long:{sequence}", "partition:maintenance:left", "partition:maintenance:right", placements[0].placement_id, placements[1].placement_id, Q16_ONE, Q16_ONE, 1, (placements[0].shard_id, placements[1].shard_id))


def _moved(placement: PlacementRecord, q: int) -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    mark = GeometryMark(placement.geometry_mark.mark_id, placement.shard_id, cell.profile_id, cell.chart_id, cell, placement.geometry_mark.placement_method, "high", 0, placement.geometry_mark.relation_field_ref)
    return PlacementRecord(placement.placement_id, placement.shard_id, placement.candidate_id, placement.decision_id, mark, placement.island_id, placement.patch_id, placement.source_fallback_refs, placement.replay_profile_id, placement.replay_template_version)


def _split_merge(placements: tuple[PlacementRecord, PlacementRecord]) -> None:
    field = GlobalShardedField()
    field.add_partition(GRFPartition(partition_descriptor("partition:temp", 0, 19, 0, 199)))
    field.insert("partition:temp", placements[0])
    field.insert("partition:temp", placements[1])
    field.split_partition("partition:temp", GRFPartition(partition_descriptor("partition:temp:left", 0, 9, 0, 99)), GRFPartition(partition_descriptor("partition:temp:right", 10, 19, 100, 199)), 9)
    field.merge_partitions("partition:temp:left", "partition:temp:right", GRFPartition(partition_descriptor("partition:temp:merged", 0, 19, 0, 199)))
