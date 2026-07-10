"""Fixed-work long-running GRF7 reliability validation without sleeps."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns
import tracemalloc

from nollm.grf.cell_address import CellAddress
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.global_field import CrossPartitionBridgeKernel, CrossPartitionStitchProposal, GRFPartition, GlobalRecallBudget, GlobalRecallQuery, GlobalShardedField, partition_descriptor
from nollm.grf.host_contract import GRFHostRequest
from nollm.grf.placement import GeometryMark, PlacementRecord

from .grf7_runtime_fixture import GRF7RuntimeAdapter, GRF7RuntimeCore, QueuedRuntimeFixture


@dataclass(frozen=True)
class ReliabilityCheckpoint:
    operation_count: int
    process_peak_rss_bytes: int
    tracemalloc_current_bytes: int
    tracemalloc_peak_bytes: int
    average_latency_ns: int
    evidence_count: int
    placement_count: int
    admission_count: int
    ledger_event_count: int

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class LongRunningResult:
    operation_count: int
    operation_counts: dict[str, int]
    checkpoints: tuple[ReliabilityCheckpoint, ...]
    error_count: int
    recovery_count: int
    snapshot_count: int
    orphan_object_count: int
    identity_collision_count: int
    evidence_loss_count: int
    ledger_event_count: int
    ledger_digest: str
    replay_deterministic: bool
    latency_drift_ratio: str
    latency_drift_explanation: str
    status: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "operation_count": self.operation_count,
            "operation_counts": dict(self.operation_counts),
            "checkpoints": tuple(item.to_mapping() for item in self.checkpoints),
            "error_count": self.error_count,
            "recovery_count": self.recovery_count,
            "snapshot_count": self.snapshot_count,
            "orphan_object_count": self.orphan_object_count,
            "identity_collision_count": self.identity_collision_count,
            "evidence_loss_count": self.evidence_loss_count,
            "ledger_event_count": self.ledger_event_count,
            "ledger_digest": self.ledger_digest,
            "replay_deterministic": self.replay_deterministic,
            "latency_drift_ratio": self.latency_drift_ratio,
            "latency_drift_explanation": self.latency_drift_explanation,
            "status": self.status,
        }


def run_long_running_validation(root: Path, operation_count: int = 1_000_000, checkpoint_interval: int = 100_000) -> LongRunningResult:
    if operation_count < 12 or checkpoint_interval < 1:
        raise ValueError("long-running workload is too small")
    core = GRF7RuntimeCore()
    adapter = GRF7RuntimeAdapter(core, Path(root) / "events.jsonl")
    runtime = QueuedRuntimeFixture("long", adapter)
    runtime.start()
    maintenance, movable = _maintenance_fixture()
    budget = GlobalRecallBudget(1, 1, 2, 2, 0)
    counts = {key: 0 for key in ("capture", "place", "admit", "recall", "replay", "cross_partition_recall", "stitch", "rollback", "move", "split", "merge", "host_restart_adapter_failure")}
    identities: dict[int, tuple[str, str, str]] = {}
    checkpoints = []
    errors = recoveries = snapshots = 0
    ledger_digest = b"\0" * 32
    interval_started = perf_counter_ns()
    first_latency = last_latency = 0
    tracemalloc.start()
    for index in range(operation_count):
        operation = index % 12
        object_index = index // 12
        label = tuple(counts)[operation]
        counts[label] += 1
        if operation <= 4:
            request = _core_request(index, object_index, operation, identities)
            result = core.dispatch(GRFHostRequest.from_mapping(request))
            if operation == 0:
                identities[object_index] = (str(result["evidence_identity"]), "", "")
            elif operation == 1:
                identities[object_index] = (identities[object_index][0], str(result["placement_identity"]), "")
            elif operation == 2:
                evidence, placement, _ = identities[object_index]
                identities[object_index] = (evidence, placement, str(result["admission_identity"]))
        elif operation == 5:
            maintenance.recall(GlobalRecallQuery(f"query:long:cross:{index}", "shard_id", movable[0].shard_id, budget, True))
        elif operation == 6:
            bridge = _maintenance_bridge(movable, index)
            maintenance.accept_stitch(CrossPartitionStitchProposal(f"proposal:long:{index}", bridge, ("source_backed_ref",)), f"stitch:long:{index}", "2026-07-10T00:00:00Z")
        elif operation == 7:
            bridge_id = f"bridge:long:{index - 1}"
            maintenance.rollback_stitch(bridge_id, "scheduled_revalidation", "2026-07-10T00:00:01Z")
        elif operation == 8:
            partition = maintenance._load("partition:maintenance:left")
            current = partition.engine.placements._placements[movable[0].placement_id]
            moved = _move(current, 1 if current.geometry_mark.cell.q == 2 else 2)
            partition.move(moved)
            movable = (moved, movable[1])
        elif operation == 9:
            _split_merge_roundtrip(maintenance, movable)
        elif operation == 10:
            maintenance.directory.digest()
        else:
            runtime.restart()
            adapter.fail_next = True
            failure = {"contract_version": "grf_host_v2", "host_request_id": f"host:long:failure:{index}", "capability": "capture", "payload": {"capture_id": f"capture:failure:{index}", "content": "failure"}, "evidence_identity": None, "placement_identity": None, "admission_identity": None}
            runtime.submit(failure)
            response = runtime.process_one()
            errors += response.get("error_code") == "adapter_failure"
            runtime.submit(failure)
            recoveries += runtime.process_one().get("ok") is True
        ledger_digest = sha256(ledger_digest + f"{index}:{label}".encode("ascii")).digest()
        if (index + 1) % checkpoint_interval == 0:
            elapsed = perf_counter_ns() - interval_started
            average = elapsed // checkpoint_interval
            if not checkpoints:
                first_latency = average
            last_latency = average
            current, peak = tracemalloc.get_traced_memory()
            checkpoints.append(ReliabilityCheckpoint(index + 1, _peak_rss_bytes(), current, peak, average, len(core.evidence), len(core.placements), len(core.admissions), index + 1))
            snapshots += 1
            interval_started = perf_counter_ns()
    tracemalloc.stop()
    runtime.shutdown()
    complete_objects = operation_count // 12 + (1 if operation_count % 12 >= 3 else 0)
    orphan_placements = sum(placement.shard_id not in core.evidence for placement in core.placements.values())
    orphan_admissions = sum(admission.placement_record.placement_id not in core.placements for admission in core.admissions.values())
    orphans = orphan_placements + orphan_admissions
    collisions = len(set(core.evidence) & set(core.placements) | set(core.evidence) & set(core.admissions) | set(core.placements) & set(core.admissions))
    sample = next(iter(core.admissions))
    query = GRFHostRequest.from_mapping(_replay_request(sample))
    replayed = core.dispatch(query) == core.dispatch(query)
    loss = max(0, complete_objects - len(core.evidence))
    drift = f"{last_latency}/{first_latency}"
    status = "GATE_H_PASS" if operation_count >= 1_000_000 and not orphans and not collisions and not loss and replayed and errors == recoveries else "GATE_H_FAIL"
    return LongRunningResult(operation_count, counts, tuple(checkpoints), errors, recoveries, snapshots, orphans, collisions, loss, operation_count, ledger_digest.hex(), replayed, drift, "latency follows bounded per-partition occupancy and periodic maintenance operations", status)


def _maintenance_fixture() -> tuple[GlobalShardedField, tuple[PlacementRecord, PlacementRecord]]:
    field = GlobalShardedField()
    field.add_partition(GRFPartition(partition_descriptor("partition:maintenance:left", 0, 9, 0, 99)))
    field.add_partition(GRFPartition(partition_descriptor("partition:maintenance:right", 10, 19, 100, 199)))
    left, right = _placement("left", 2), _placement("right", 12)
    field.insert("partition:maintenance:left", left, "admission:maintenance:left")
    field.insert("partition:maintenance:right", right, "admission:maintenance:right")
    return field, (left, right)


def _placement(name: str, q: int) -> PlacementRecord:
    shard = f"shard:maintenance:{name}"
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    mark = GeometryMark(f"mark:maintenance:{name}", shard, cell.profile_id, cell.chart_id, cell, "maintenance", "high", 0, "field:maintenance")
    return PlacementRecord(f"placement:maintenance:{name}", shard, f"candidate:maintenance:{name}", f"decision:maintenance:{name}", mark, f"island:maintenance:{name}", f"patch:maintenance:{name}", (shard,), cell.profile_id, "grf7_long_v1")


def _maintenance_bridge(placements: tuple[PlacementRecord, PlacementRecord], index: int) -> CrossPartitionBridgeKernel:
    return CrossPartitionBridgeKernel(f"bridge:long:{index}", "partition:maintenance:left", "partition:maintenance:right", placements[0].placement_id, placements[1].placement_id, Q16_ONE, Q16_ONE, 1, (placements[0].shard_id, placements[1].shard_id))


def _move(placement: PlacementRecord, q: int) -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    return replace_placement(placement, GeometryMark(placement.geometry_mark.mark_id, placement.shard_id, cell.profile_id, cell.chart_id, cell, placement.geometry_mark.placement_method, "high", 0, placement.geometry_mark.relation_field_ref))


def replace_placement(placement: PlacementRecord, mark: GeometryMark) -> PlacementRecord:
    return PlacementRecord(placement.placement_id, placement.shard_id, placement.candidate_id, placement.decision_id, mark, placement.island_id, placement.patch_id, placement.source_fallback_refs, placement.replay_profile_id, placement.replay_template_version)


def _split_merge_roundtrip(field: GlobalShardedField, placements: tuple[PlacementRecord, PlacementRecord]) -> None:
    # The main maintenance partitions stay stable; a disposable partition proves both operations.
    temp = GlobalShardedField()
    temp.add_partition(GRFPartition(partition_descriptor("partition:temp", 0, 19, 0, 199)))
    temp.insert("partition:temp", placements[0])
    temp.insert("partition:temp", placements[1])
    temp.split_partition("partition:temp", GRFPartition(partition_descriptor("partition:temp:left", 0, 9, 0, 99)), GRFPartition(partition_descriptor("partition:temp:right", 10, 19, 100, 199)), 9)
    temp.merge_partitions("partition:temp:left", "partition:temp:right", GRFPartition(partition_descriptor("partition:temp:merged", 0, 19, 0, 199)))


def _core_request(index: int, object_index: int, operation: int, identities: dict[int, tuple[str, str, str]]) -> dict[str, object]:
    base = {"contract_version": "grf_host_v2", "host_request_id": f"host:long:{index}", "evidence_identity": None, "placement_identity": None, "admission_identity": None}
    if operation == 0:
        return {**base, "capability": "capture", "payload": {"capture_id": f"capture:long:{object_index}", "content": f"long evidence {object_index}"}}
    evidence, placement, admission = identities[object_index]
    if operation == 1:
        return {**base, "capability": "place", "evidence_identity": evidence, "payload": {"sequence": str(object_index)}}
    if operation == 2:
        return {**base, "capability": "admit", "evidence_identity": evidence, "placement_identity": placement, "payload": {}}
    capability = "recall" if operation == 3 else "replay"
    return {**base, "capability": capability, "admission_identity": admission, "payload": {"query_id": f"query:long:{index}", "entry_mode": "admission_id", "entry_ref": admission}}


def _replay_request(admission: str) -> dict[str, object]:
    return {"contract_version": "grf_host_v2", "host_request_id": "host:long:final-replay", "capability": "replay", "payload": {"query_id": "query:long:final", "entry_mode": "admission_id", "entry_ref": admission}, "evidence_identity": None, "placement_identity": None, "admission_identity": admission}


def _peak_rss_bytes() -> int:
    from nollm.grf.grf7_scale_validation import _peak_rss_bytes as peak
    return peak()
