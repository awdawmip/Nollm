"""GRF7R2 sustained mutation, durable ownership, and retry evidence runner."""

from __future__ import annotations

from collections import Counter, defaultdict
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
from nollm.grf.json_canonical import canonical_dumps
from nollm.grf.resource_sampler import sample_process_resources
from nollm.grf.placement import GeometryMark, PlacementRecord

from .grf7r_facade_runtime import FacadeRuntimeAdapter, HostRequestRegistry, LostHostResponse


def run_sustained_mutation(root: Path, *, operation_count: int = 1_000_000, checkpoint_interval: int = 100_000, mutation_count: int = 1_000) -> dict[str, object]:
    if operation_count < 1_000 or checkpoint_interval < 1 or mutation_count < 1:
        raise ValueError("invalid long-running workload dimensions")
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    registry_path = root / "host_request_registry.jsonl"
    workspaces = tuple(root / "workspaces" / f"workspace_{index:02d}" for index in range(10))
    adapters = [FacadeRuntimeAdapter(workspace, root / "runtime_attack_ledger.jsonl", registry_path=registry_path, compact_ledger=True) for workspace in workspaces]
    ledger_path = root / "long_running_event_ledger.jsonl"
    maintenance, maintenance_records = _maintenance_field()
    latency: dict[str, list[int]] = defaultdict(list)
    operations: Counter[str] = Counter()
    injected_failures = recoveries = real_post_commit_retries = 0
    identities: list[tuple[str, str, str]] = []
    snapshots = []
    tracemalloc.start()
    initial_resource = sample_process_resources()
    with ledger_path.open("w", encoding="utf-8", newline="\n") as ledger:
        # Interleave 1,000 mutation chains with bounded recall/replay observations.
        for index in range(mutation_count):
            workspace_index = index % len(workspaces)
            adapter = adapters[workspace_index]
            shard, placement, admission, adapter, retries = _mutation_chain(adapter, workspaces[workspace_index], registry_path, index, root / "runtime_attack_ledger.jsonl")
            adapters[workspace_index] = adapter
            identities.append((shard, placement, admission))
            real_post_commit_retries += retries
            injected_failures += retries
            recoveries += retries
            for retry_index in range(retries):
                operations["real_post_commit_retry"] += 1
                _write_event(ledger, "real_post_commit_retry", index, False, (shard, placement, admission), maintenance=True)
            for operation, request in (("capture", None), ("place", None), ("admit", None)):
                operations[operation] += 1
                _write_event(ledger, operation, index, False, (shard, placement, admission))
            for query_index in range(10):
                for operation in ("recall", "replay"):
                    started = perf_counter_ns()
                    response = adapter.handle("long", _query_request(f"host:long:{operation}:{index}:{query_index}", operation, admission))
                    elapsed = perf_counter_ns() - started
                    if response.get("ok") is not True:
                        raise AssertionError(f"{operation} failed")
                    operations[operation] += 1
                    latency[operation].append(elapsed)
                    _write_event(ledger, operation, index, False, (shard, placement, admission), response)
            if index < 1_000:
                _maintenance_event(maintenance, maintenance_records, "cross_partition_recall", index)
                operations["cross_partition_recall"] += 1
                _write_event(ledger, "cross_partition_recall", index, False, (), maintenance=True)
            if index < 500:
                bridge = _maintenance_bridge(maintenance_records, index)
                maintenance.accept_stitch(CrossPartitionStitchProposal(f"proposal:long:{index}", bridge, ("sustained_mutation",)), f"stitch:long:{index}", "2026-07-10T00:00:00Z")
                maintenance.rollback_stitch(bridge.bridge_id, "scheduled_revalidation", "2026-07-10T00:00:01Z")
                operations["stitch"] += 1
                operations["rollback"] += 1
                _write_event(ledger, "stitch", index, False, (), maintenance=True)
                _write_event(ledger, "rollback", index, False, (), maintenance=True)
            if index < 500:
                maintenance_records = (_moved(maintenance_records[0], 1 if maintenance_records[0].geometry_mark.cell.q == 2 else 2), maintenance_records[1])
                maintenance._load("partition:maintenance:left").move(maintenance_records[0])
                operations["move"] += 1
                _write_event(ledger, "move", index, False, (), maintenance=True)
            if index < 100:
                _split_merge(maintenance_records)
                operations["split_merge"] += 1
                _write_event(ledger, "split_merge", index, False, (), maintenance=True)
            if index < 100:
                adapter.close()
                adapter = FacadeRuntimeAdapter(workspaces[workspace_index], root / "runtime_attack_ledger.jsonl", registry_path=registry_path, compact_ledger=True)
                adapters[workspace_index] = adapter
                operations["restart"] += 1
                _write_event(ledger, "restart", index, False, (), maintenance=True)
                adapter.fail_before_dispatch = True
                try:
                    adapter.handle("long", _validate_request(f"host:long:failure:{index}"))
                except RuntimeError:
                    recovered = adapter.handle("long", _validate_request(f"host:long:failure:{index}"))
                    if recovered.get("ok") is not True:
                        raise AssertionError("adapter failure was not recoverable")
                    injected_failures += 1
                    recoveries += 1
                operations["adapter_failure"] += 1
                _write_event(ledger, "adapter_failure", index, False, (), maintenance=True)
            if (index + 1) % max(1, mutation_count // 10) == 0:
                adapter.flush_events()
                _snapshot(root, snapshots, workspaces, adapters, registry_path, operations, ledger_path, maintenance)
        # The remaining operations are actual Host retries, recorded as cache hits rather than fabricated class counts.
        adapter = adapters[0]
        cache_request = _validate_request("host:long:cached-operation")
        while sum(operations.values()) < operation_count:
            started = perf_counter_ns()
            response = adapter.handle("long", cache_request)
            elapsed = perf_counter_ns() - started
            if response.get("ok") is not True:
                raise AssertionError("cached host operation failed")
            operations["idempotent_host_retry"] += 1
            latency["idempotent_host_retry"].append(elapsed)
            _write_event(ledger, "idempotent_host_retry", sum(operations.values()), True, (), response)
        adapter.flush_events()
        if not snapshots or snapshots[-1]["operation_counts"] != dict(operations):
            _snapshot(root, snapshots, workspaces, adapters, registry_path, operations, ledger_path, maintenance)
    for item in adapters:
        item.flush_events()
    final_reports = tuple(item.service._facade.validate_workspace() for item in adapters)
    final_resource = sample_process_resources()
    current_trace, peak_trace = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    event_rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    measured_counts = Counter(str(item["operation"]) for item in event_rows)
    duplicate_evidence, duplicate_placement, duplicate_admission, orphan_count = _identity_integrity(final_reports, identities)
    registry_snapshot = HostRequestRegistry(registry_path).snapshot()
    last_workspace = workspaces[(len(identities) - 1) % len(workspaces)]
    snapshot_report = _snapshot_replay_report(root, last_workspace, registry_path, identities[-1], len(identities) - 1, registry_snapshot, maintenance)
    result = {
        "operation_count": len(event_rows),
        "operation_counts": dict(measured_counts),
        "injected_failure_count": injected_failures,
        "recovery_count": recoveries,
        "real_post_commit_retry_count": real_post_commit_retries,
        "duplicate_evidence_count": duplicate_evidence,
        "duplicate_placement_count": duplicate_placement,
        "duplicate_admission_count": duplicate_admission,
        "identity_collision_count": _identity_collision_count(identities),
        "orphan_count": orphan_count,
        "registry_state": registry_snapshot,
        "resource_backend": final_resource.backend_name,
        "current_rss_bytes": final_resource.current_rss_bytes,
        "peak_rss_bytes": final_resource.peak_rss_bytes,
        "rss_growth_bytes": max(0, final_resource.current_rss_bytes - initial_resource.current_rss_bytes),
        "tracemalloc_current_bytes": current_trace,
        "tracemalloc_peak_bytes": peak_trace,
        "object_count": len(gc.get_objects()),
        "ledger_bytes": ledger_path.stat().st_size,
        "snapshot_bytes": sum((root / "snapshots" / item["path"]).stat().st_size for item in snapshots),
        "latency_by_operation": {name: _quantiles(values) for name, values in latency.items()},
        "snapshots": snapshots,
        "snapshot_replay_equals_final_state": snapshot_report["passed"],
        "event_ledger_sha256": sha256(ledger_path.read_bytes()).hexdigest(),
        "runtime_attack_ledger_sha256": sha256((root / "runtime_attack_ledger.jsonl").read_bytes()).hexdigest(),
    }
    (root / "long_running_metrics.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    return result


def _mutation_chain(adapter: FacadeRuntimeAdapter, workspace: Path, registry: Path, index: int, event_path: Path) -> tuple[str, str, str, FacadeRuntimeAdapter, int]:
    retries = 0
    capture = _capture_request(index)
    capture_response, adapter, retried = _post_commit(adapter, workspace, registry, event_path, capture, index < 334)
    retries += retried
    shard = str(capture_response["evidence_identity"])
    place = _place_request(index, shard)
    place_response, adapter, retried = _post_commit(adapter, workspace, registry, event_path, place, 334 <= index < 667)
    retries += retried
    placement = str(place_response["placement_identity"])
    admit = _admit_request(index, shard, placement)
    admit_response, adapter, retried = _post_commit(adapter, workspace, registry, event_path, admit, 667 <= index < 1_000)
    retries += retried
    return shard, placement, str(admit_response["admission_identity"]), adapter, retries


def _post_commit(adapter: FacadeRuntimeAdapter, workspace: Path, registry: Path, event_path: Path, request: dict[str, object], lose: bool) -> tuple[dict[str, object], FacadeRuntimeAdapter, int]:
    if not lose:
        response = adapter.handle("long", request)
        if response.get("ok") is not True:
            raise AssertionError("mutation failed")
        return response, adapter, 0
    try:
        adapter.handle("long", request, lose_response_after_commit=True)
    except LostHostResponse:
        adapter.close()
        adapter = FacadeRuntimeAdapter(workspace, event_path, registry_path=registry, compact_ledger=True)
        response = adapter.handle("long", request)
        if response.get("ok") is not True:
            raise AssertionError("post-commit retry failed")
        return response, adapter, 1
    raise AssertionError("post-commit response was not lost")


def _capture_request(index: int) -> dict[str, object]:
    return _request(f"host:long:capture:{index}", "capture", {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": f"capture:long:{index}", "content": f"long mutation evidence {index}", "origin_kind": "validation_fixture", "source_window_refs": (f"window:long:{index}",), "recorded_at": "2026-07-10T00:00:00Z"})


def _place_request(index: int, shard: str) -> dict[str, object]:
    return _request(f"host:long:place:{index}", "place", {"kind": "nollm_grf_admit_request", "version": "1", "shard_id": shard, "source_window_id": f"window:long:{index}", "policy_hint": {"policy_id": "grf_deterministic_policy_v1", "chart_id": "chart:long"}, "recorded_at": "2026-07-10T00:00:01Z"}, evidence=shard)


def _admit_request(index: int, shard: str, placement: str) -> dict[str, object]:
    return _request(f"host:long:admit:{index}", "admit", {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": shard, "placement_id": placement, "recorded_at": "2026-07-10T00:00:02Z", "admitted_by": "host_rule"}, evidence=shard, placement=placement)


def _query_request(request_id: str, capability: str, admission: str) -> dict[str, object]:
    return _request(request_id, capability, {"kind": "nollm_grf_recall_request", "version": "1", "query_id": f"query:{request_id}", "entry_mode": "admission_id", "entry_ref": admission, "allowed_kernels": ("lateral",), "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1}}, admission=admission)


def _validate_request(request_id: str) -> dict[str, object]:
    return _request(request_id, "validate", {})


def _request(request_id: str, capability: str, payload: dict[str, object], *, evidence: str | None = None, placement: str | None = None, admission: str | None = None) -> dict[str, object]:
    return {"contract_version": "grf_host_v2", "host_request_id": request_id, "capability": capability, "payload": payload, "evidence_identity": evidence, "placement_identity": placement, "admission_identity": admission}


def _write_event(stream, operation: str, sequence: int, cache_hit: bool, identities: tuple[str, ...], response: dict[str, object] | None = None, maintenance: bool = False) -> None:
    stream.write(json.dumps({"operation": operation, "sequence": sequence, "cache_hit": cache_hit, "identities": identities, "maintenance": maintenance, "response_ok": None if response is None else response.get("ok")}, sort_keys=True, separators=(",", ":")) + "\n")


def _snapshot(root: Path, snapshots: list[dict[str, object]], workspaces: tuple[Path, ...], adapters: list[FacadeRuntimeAdapter], registry_path: Path, operations: Counter[str], ledger_path: Path, maintenance: GlobalShardedField) -> None:
    reports = tuple(item.service._facade.validate_workspace().__dict__ for item in adapters)
    payload = {"workspace_reports": reports, "registry_state": HostRequestRegistry(registry_path).snapshot(), "operation_counts": dict(operations), "ledger_position": ledger_path.stat().st_size, "directory_digest": maintenance.directory.digest(), "bridge_digest": sha256(canonical_dumps(tuple(item.bridge.to_mapping() for item in maintenance._bridges.values()))).hexdigest()}
    path = root / "snapshots" / f"snapshot_{len(snapshots) + 1:04d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_dumps(payload))
    snapshots.append({"path": path.name, "sha256": sha256(path.read_bytes()).hexdigest(), **payload})


def _snapshot_replay_report(root: Path, workspace: Path, registry: Path, identity: tuple[str, str, str], mutation_index: int, expected_registry: dict[str, object], maintenance: GlobalShardedField) -> dict[str, object]:
    adapter = FacadeRuntimeAdapter(workspace, root / "runtime_attack_ledger.jsonl", registry_path=registry, compact_ledger=True)
    replay = adapter.handle("long", _query_request(f"host:long:replay:{mutation_index}:0", "replay", identity[2]))
    report = adapter.service._facade.validate_workspace()
    payload = {"core_object_counts": report.__dict__, "host_ownership_index": adapter.registry.snapshot(), "recall_result_digest": sha256(canonical_dumps(replay.get("result"))).hexdigest(), "evidence_fallback_digest": sha256(identity[0].encode("utf-8")).hexdigest(), "directory_digest": maintenance.directory.digest(), "bridge_digest": sha256(canonical_dumps(tuple(item.bridge.to_mapping() for item in maintenance._bridges.values()))).hexdigest(), "passed": adapter.registry.snapshot() == expected_registry and replay.get("ok") is True}
    (root / "snapshot_replay_report.json").write_bytes(canonical_dumps(payload))
    return payload


def _identity_integrity(reports, identities: list[tuple[str, str, str]]) -> tuple[int, int, int, int]:
    shards, placements, admissions = zip(*identities)
    duplicates = (len(shards) - len(set(shards)), len(placements) - len(set(placements)), len(admissions) - len(set(admissions)))
    evidence = sum(item.evidence_shard_count for item in reports)
    placement = sum(item.placement_record_count for item in reports)
    admission = sum(item.admission_record_count for item in reports)
    orphan = int(evidence != len(shards) or placement != len(placements) or admission != len(admissions))
    return (*duplicates, orphan)


def _identity_collision_count(identities: list[tuple[str, str, str]]) -> int:
    return sum(len(set(group)) != len(group) for group in zip(*identities))


def _quantiles(values: list[int]) -> dict[str, int]:
    if not values:
        return {"p50": 0, "p95": 0, "p99": 0}
    ordered = sorted(values)
    return {name: ordered[min(len(ordered) - 1, (len(ordered) * pct + 99) // 100 - 1)] for name, pct in (("p50", 50), ("p95", 95), ("p99", 99))}


def _maintenance_field() -> tuple[GlobalShardedField, tuple[PlacementRecord, PlacementRecord]]:
    field = GlobalShardedField()
    field.add_partition(GRFPartition(partition_descriptor("partition:maintenance:left", 0, 9, 0, 99)))
    field.add_partition(GRFPartition(partition_descriptor("partition:maintenance:right", 10, 19, 100, 199)))
    left, right = _maintenance_record("left", 2), _maintenance_record("right", 12)
    field.insert("partition:maintenance:left", left, "admission:maintenance:left")
    field.insert("partition:maintenance:right", right, "admission:maintenance:right")
    return field, (left, right)


def _maintenance_record(name: str, q: int) -> PlacementRecord:
    shard = f"shard:maintenance:{name}"
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    mark = GeometryMark(f"mark:maintenance:{name}", shard, cell.profile_id, cell.chart_id, cell, "maintenance", "high", 0, "field:maintenance")
    return PlacementRecord(f"placement:maintenance:{name}", shard, f"candidate:maintenance:{name}", f"decision:maintenance:{name}", mark, f"island:maintenance:{name}", f"patch:maintenance:{name}", (shard,), cell.profile_id, "grf7r2_long_v1")


def _maintenance_bridge(records: tuple[PlacementRecord, PlacementRecord], sequence: int) -> CrossPartitionBridgeKernel:
    return CrossPartitionBridgeKernel(f"bridge:long:{sequence}", "partition:maintenance:left", "partition:maintenance:right", records[0].placement_id, records[1].placement_id, Q16_ONE, Q16_ONE, 1, (records[0].shard_id, records[1].shard_id))


def _maintenance_event(field: GlobalShardedField, records: tuple[PlacementRecord, PlacementRecord], operation: str, sequence: int) -> None:
    field.recall(GlobalRecallQuery(f"query:long:cross:{sequence}", "placement_id", records[0].placement_id, GlobalRecallBudget(1, 1, 2, 2, 0), True))


def _moved(record: PlacementRecord, q: int) -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    mark = GeometryMark(record.geometry_mark.mark_id, record.shard_id, cell.profile_id, cell.chart_id, cell, record.geometry_mark.placement_method, "high", 0, record.geometry_mark.relation_field_ref)
    return PlacementRecord(record.placement_id, record.shard_id, record.candidate_id, record.decision_id, mark, record.island_id, record.patch_id, record.source_fallback_refs, record.replay_profile_id, record.replay_template_version)


def _split_merge(records: tuple[PlacementRecord, PlacementRecord]) -> None:
    field = GlobalShardedField()
    field.add_partition(GRFPartition(partition_descriptor("partition:temp", 0, 19, 0, 199)))
    field.insert("partition:temp", records[0])
    field.insert("partition:temp", records[1])
    field.split_partition("partition:temp", GRFPartition(partition_descriptor("partition:temp:left", 0, 9, 0, 99)), GRFPartition(partition_descriptor("partition:temp:right", 10, 19, 100, 199)), 9)
    field.merge_partitions("partition:temp:left", "partition:temp:right", GRFPartition(partition_descriptor("partition:temp:merged", 0, 19, 0, 199)))
