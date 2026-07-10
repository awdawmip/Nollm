"""GRF7 incremental update and repartition equivalence validation."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .cell_address import CellAddress
from .fixed_point import Q16_ONE
from .global_field import CrossPartitionBridgeKernel, CrossPartitionStitchProposal, GRFPartition, GlobalRecallBudget, GlobalRecallQuery, GlobalShardedField, partition_descriptor
from .gate_evidence import GatePredicate, GateResult
from .placement import GeometryMark, PlacementRecord


@dataclass(frozen=True)
class IncrementalRepartitionResult:
    add_changed_state: bool
    remove_changed_state: bool
    move_changed_state: bool
    cross_partition_move_replayed: bool
    profile_change_replayed: bool
    stitch_add_remove_replayed: bool
    split_merge_replayed: bool
    incremental_equals_full_rebuild: bool
    evidence_identity_preserved: bool
    placement_identity_preserved: bool
    admission_identity_preserved: bool
    source_fallback_preserved: bool
    identity_collision_count: int
    status: str

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


def run_incremental_repartition_validation() -> IncrementalRepartitionResult:
    field = GlobalShardedField()
    left = GRFPartition(partition_descriptor("partition:inc:left", 0, 9, 0, 99))
    right = GRFPartition(partition_descriptor("partition:inc:right", 10, 19, 100, 199))
    dream_descriptor = replace(partition_descriptor("partition:inc:dream", 20, 29, 200, 299, "profile_partitioning"), profile_id="dream_quasi_v1")
    dream = GRFPartition(dream_descriptor, ("dream_quasi_v1",))
    for partition in (left, right, dream):
        field.add_partition(partition)
    first, second, removed = _placement("first", 2), _placement("second", 12), _placement("removed", 3)
    field.insert("partition:inc:left", first, "admission:inc:first")
    field.insert("partition:inc:right", second, "admission:inc:second")
    field.insert("partition:inc:left", removed, "admission:inc:removed")
    add_changed = sum(item.placement_count for item in field.directory.entries()) == 3
    field._load("partition:inc:left").remove(removed.placement_id)
    field.directory.replace(field._load("partition:inc:left").descriptor)
    remove_changed = sum(item.placement_count for item in field.directory.entries()) == 2
    moved_local = _move(first, 4, "eisenstein_exact_v1")
    field._load("partition:inc:left").move(moved_local)
    move_changed = field._load("partition:inc:left").engine.placements._placements[first.placement_id].geometry_mark.cell.q == 4
    moved_cross = _move(moved_local, 14, "eisenstein_exact_v1")
    field.move_across_partition("partition:inc:left", "partition:inc:right", moved_cross)
    budget = GlobalRecallBudget(1, 1, 2, 1, 0)
    cross_ok = field.recall(GlobalRecallQuery("query:inc:cross", "admission_id", "admission:inc:first", budget, False)).selected_shards == (first.shard_id,)
    profiled = _move(moved_cross, 24, "dream_quasi_v1")
    field.move_across_partition("partition:inc:right", "partition:inc:dream", profiled)
    profile_ok = field.recall(GlobalRecallQuery("query:inc:profile", "placement_id", first.placement_id, budget, False)).selected_shards == (first.shard_id,)
    bridge = CrossPartitionBridgeKernel("bridge:inc", "partition:inc:right", "partition:inc:dream", second.placement_id, profiled.placement_id, Q16_ONE, Q16_ONE, 1, (second.shard_id, first.shard_id))
    field.accept_stitch(CrossPartitionStitchProposal("proposal:inc", bridge, ("manual_bridge",)), "stitch:inc", "2026-07-10T00:00:00Z")
    used = len(field.recall(GlobalRecallQuery("query:inc:bridge", "shard_id", second.shard_id, GlobalRecallBudget(1, 1, 2, 2, 0), True)).path.bridges_used) == 1
    field.rollback_stitch(bridge.bridge_id, "fixture", "2026-07-10T00:00:01Z")
    removed_bridge = field.recall(GlobalRecallQuery("query:inc:no-bridge", "shard_id", second.shard_id, budget, True)).path.bridges_used == ()
    disposable = GlobalShardedField()
    disposable.add_partition(GRFPartition(partition_descriptor("partition:inc:whole", 0, 19, 0, 199)))
    disposable.insert("partition:inc:whole", _placement("split-left", 2), "admission:split:left")
    disposable.insert("partition:inc:whole", _placement("split-right", 12), "admission:split:right")
    disposable.split_partition("partition:inc:whole", GRFPartition(partition_descriptor("partition:inc:split-left", 0, 9, 0, 99)), GRFPartition(partition_descriptor("partition:inc:split-right", 10, 19, 100, 199)), 9)
    disposable.merge_partitions("partition:inc:split-left", "partition:inc:split-right", GRFPartition(partition_descriptor("partition:inc:merged", 0, 19, 0, 199)))
    split_merge = disposable.recall(GlobalRecallQuery("query:inc:split-merge", "admission_id", "admission:split:right", budget, False)).selected_shards == ("shard:inc:split-right",)
    rebuilt = _full_rebuild(profiled, second)
    refs = (("admission_id", "admission:inc:first"), ("admission_id", "admission:inc:second"))
    equal = all(field.recall(GlobalRecallQuery(f"query:inc:left:{ref}", mode, ref, budget, False)).selected_shards == rebuilt.recall(GlobalRecallQuery(f"query:inc:right:{ref}", mode, ref, budget, False)).selected_shards for mode, ref in refs)
    identities = {profiled.shard_id, profiled.placement_id, "admission:inc:first", second.shard_id, second.placement_id, "admission:inc:second"}
    passed = all((add_changed, remove_changed, move_changed, cross_ok, profile_ok, used, removed_bridge, split_merge, equal)) and len(identities) == 6
    status = GateResult("F", (GatePredicate("incremental equivalence", passed, True, "eq"),)).status
    return IncrementalRepartitionResult(add_changed, remove_changed, move_changed, cross_ok, profile_ok, used and removed_bridge, split_merge, equal, profiled.shard_id == first.shard_id, profiled.placement_id == first.placement_id, cross_ok and profile_ok, profiled.source_fallback_refs == first.source_fallback_refs, 6 - len(identities), status)


def _full_rebuild(first: PlacementRecord, second: PlacementRecord) -> GlobalShardedField:
    field = GlobalShardedField()
    right = GRFPartition(partition_descriptor("partition:inc:right", 10, 19, 100, 199))
    dream_descriptor = replace(partition_descriptor("partition:inc:dream", 20, 29, 200, 299, "profile_partitioning"), profile_id="dream_quasi_v1")
    field.add_partition(right)
    field.add_partition(GRFPartition(dream_descriptor, ("dream_quasi_v1",)))
    field.insert("partition:inc:dream", first, "admission:inc:first")
    field.insert("partition:inc:right", second, "admission:inc:second")
    return field


def _placement(name: str, q: int) -> PlacementRecord:
    shard = f"shard:inc:{name}"
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    mark = GeometryMark(f"mark:inc:{name}", shard, cell.profile_id, cell.chart_id, cell, "incremental", "high", 0, "field:inc")
    return PlacementRecord(f"placement:inc:{name}", shard, f"candidate:inc:{name}", f"decision:inc:{name}", mark, f"island:inc:{name}", f"patch:inc:{name}", (shard,), cell.profile_id, "grf7_inc_v1")


def _move(placement: PlacementRecord, q: int, profile_id: str) -> PlacementRecord:
    cell = CellAddress(profile_id, "chart:grf7", 0, q, 0)
    mark = GeometryMark(placement.geometry_mark.mark_id, placement.shard_id, profile_id, cell.chart_id, cell, placement.geometry_mark.placement_method, "high", 0, placement.geometry_mark.relation_field_ref)
    return PlacementRecord(placement.placement_id, placement.shard_id, placement.candidate_id, placement.decision_id, mark, placement.island_id, placement.patch_id, placement.source_fallback_refs, profile_id, placement.replay_template_version)
