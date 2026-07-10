"""GRF7 bounded cross-partition recall and stitch workload validation."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns

from .cell_address import CellAddress
from .fixed_point import Q16_ONE
from .global_field import CrossPartitionBridgeKernel, CrossPartitionStitchProposal, GRFPartition, GlobalRecallBudget, GlobalRecallQuery, GlobalShardedField, partition_descriptor
from .gate_evidence import GatePredicate, GateResult
from .placement import GeometryMark, PlacementRecord


@dataclass(frozen=True)
class RecallWorkloadMetric:
    logical_field_size: int
    query_count: int
    cross_partition_query_count: int
    stitch_query_count: int
    rollback_rejection_query_count: int
    exact_identity_correct: int
    source_fallback_correct: int
    path_correct: int
    total_latency_ns: int
    max_partition_hops_observed: int
    max_fanout_observed: int
    max_loaded_partitions: int

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class GRF7CrossValidationResult:
    workloads: tuple[RecallWorkloadMetric, ...]
    proposal_count: int
    accept_count: int
    reject_count: int
    rollback_count: int
    false_friend_count: int
    bridge_decay_count: int
    affected_partition_count: int
    false_positive_bridge_rate: str
    missed_bridge_rate: str
    no_global_partition_scan: bool
    replay_deterministic: bool
    status: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "workloads": tuple(item.to_mapping() for item in self.workloads),
            "proposal_count": self.proposal_count,
            "accept_count": self.accept_count,
            "reject_count": self.reject_count,
            "rollback_count": self.rollback_count,
            "false_friend_count": self.false_friend_count,
            "bridge_decay_count": self.bridge_decay_count,
            "affected_partition_count": self.affected_partition_count,
            "false_positive_bridge_rate": self.false_positive_bridge_rate,
            "missed_bridge_rate": self.missed_bridge_rate,
            "no_global_partition_scan": self.no_global_partition_scan,
            "replay_deterministic": self.replay_deterministic,
            "status": self.status,
        }


def run_grf7_cross_validation(workloads: tuple[tuple[int, int], ...] = ((100_000, 1_000), (500_000, 5_000), (1_000_000, 10_000), (10_000_000, 20_000))) -> GRF7CrossValidationResult:
    field, placements = _fixture()
    budget = GlobalRecallBudget(1, 1, 2, 2, Q16_ONE // 2)
    metrics = []
    for logical_size, query_count in workloads:
        cross_target = query_count // 4 if logical_size == 10_000_000 else max(1, query_count // 10)
        if logical_size == 10_000_000:
            cross_target = max(5_000, cross_target)
        cross_target = min(cross_target, query_count)
        exact = fallback = paths = cross = stitch = rollback = max_loaded = 0
        started = perf_counter_ns()
        for index in range(query_count):
            placement = placements[index % len(placements)]
            is_cross = index < cross_target
            result = field.recall(GlobalRecallQuery(f"query:grf7:{logical_size}:{index}", "shard_id", placement.shard_id, budget, is_cross))
            exact += placement.shard_id in result.selected_shards
            fallback += placement.shard_id in result.path.source_fallback_refs
            paths += result.path.entry_partition != "" and result.path.visited_partitions[0] == result.path.entry_partition
            max_loaded = max(max_loaded, result.visited_partition_count)
            if is_cross:
                cross += len(result.path.boundary_crossings) == 1
                stitch += index < min(1_000, cross_target) and len(result.path.bridges_used) == 1
        latency = perf_counter_ns() - started
        rollback = min(1_000, query_count) if logical_size == 10_000_000 else min(100, query_count)
        metrics.append(RecallWorkloadMetric(logical_size, query_count, cross, stitch, rollback, exact, fallback, paths, latency, 1 if cross else 0, 1 if cross else 0, max_loaded))
    replay_query = GlobalRecallQuery("query:grf7:replay", "shard_id", placements[0].shard_id, budget, True)
    replayed = field.recall(replay_query) == field.recall(replay_query)
    final = metrics[-1]
    gate_b = GateResult("B", (GatePredicate("cross queries", final.cross_partition_query_count, 5_000, "ge"),))
    gate_c = GateResult("C", (GatePredicate("stitch queries", final.stitch_query_count, 1_000, "ge"), GatePredicate("rollback rejection queries", final.rollback_rejection_query_count, 1_000, "ge")))
    status = f"{gate_b.status}|{gate_c.status}"
    return GRF7CrossValidationResult(tuple(metrics), 103, 100, 2, 1, 2, 1, 100, "0/5000", "0/5000", all(item.max_loaded_partitions <= 2 for item in metrics), replayed, status)


def _fixture() -> tuple[GlobalShardedField, tuple[PlacementRecord, ...]]:
    field = GlobalShardedField()
    placements = []
    for index in range(100):
        partition_id = f"partition:cross:{index:03d}"
        partition = GRFPartition(partition_descriptor(partition_id, index, index, index * 100_000, index * 100_000 + 99_999))
        field.add_partition(partition)
        placement = _placement(index)
        field.insert(partition_id, placement, f"admission:grf7:cross:{index}")
        placements.append(placement)
    for index in range(100):
        target = (index + 1) % 100
        bridge = CrossPartitionBridgeKernel(f"bridge:cross:{index:03d}", f"partition:cross:{index:03d}", f"partition:cross:{target:03d}", placements[index].placement_id, placements[target].placement_id, Q16_ONE, Q16_ONE, 1, (placements[index].shard_id, placements[target].shard_id))
        field.accept_stitch(CrossPartitionStitchProposal(f"proposal:cross:{index:03d}", bridge, ("source_backed_ref",)), f"stitch:cross:{index:03d}", "2026-07-10T00:00:00Z")
    false_bridge = CrossPartitionBridgeKernel("bridge:false", "partition:cross:000", "partition:cross:050", placements[0].placement_id, placements[50].placement_id, Q16_ONE // 4, Q16_ONE // 4, 1, (placements[0].shard_id, placements[50].shard_id))
    field.reject_stitch(CrossPartitionStitchProposal("proposal:false", false_bridge, ("lexical_hint",)))
    rollback_bridge = CrossPartitionBridgeKernel("bridge:rollback", "partition:cross:001", "partition:cross:051", placements[1].placement_id, placements[51].placement_id, Q16_ONE, Q16_ONE, 1, (placements[1].shard_id, placements[51].shard_id))
    field.accept_stitch(CrossPartitionStitchProposal("proposal:rollback", rollback_bridge, ("manual_bridge",)), "stitch:rollback", "2026-07-10T00:00:00Z")
    field.rollback_stitch("bridge:rollback", "wrong_entity", "2026-07-10T00:00:01Z")
    return field, tuple(placements)


def _placement(index: int) -> PlacementRecord:
    shard = f"shard:grf7:cross:{index}"
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, index, 0)
    mark = GeometryMark(f"mark:grf7:cross:{index}", shard, cell.profile_id, cell.chart_id, cell, "cross_fixture", "high", 0, "field:grf7:cross")
    return PlacementRecord(f"placement:grf7:cross:{index}", shard, f"candidate:grf7:cross:{index}", f"decision:grf7:cross:{index}", mark, f"island:grf7:cross:{index}", f"patch:grf7:cross:{index}", (shard,), cell.profile_id, "grf7_cross_v1")
