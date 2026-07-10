from __future__ import annotations

from dataclasses import replace

from nollm.grf.cell_address import CellAddress
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.global_field import (
    CrossPartitionBridgeKernel,
    CrossPartitionStitchProposal,
    GRFPartition,
    GRFPartitionNeighbor,
    GlobalFieldDirectory,
    GlobalRecallBudget,
    GlobalRecallQuery,
    GlobalShardedField,
    partition_descriptor,
)
from nollm.grf.placement import GeometryMark, PlacementRecord


def _placement(index: int, q: int) -> PlacementRecord:
    shard = f"shard:grf7:{index}"
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    mark = GeometryMark(f"mark:grf7:{index}", shard, cell.profile_id, cell.chart_id, cell, "fixture", "high", 0, "field:grf7")
    return PlacementRecord(f"placement:grf7:{index}", shard, f"candidate:grf7:{index}", f"decision:grf7:{index}", mark, f"island:grf7:{index}", f"patch:grf7:{index}", (shard,), cell.profile_id, "grf7_v1")


def test_directory_is_metadata_only_linear_and_replay_deterministic() -> None:
    directory = GlobalFieldDirectory()
    sizes = []
    for index in range(4):
        directory.add(partition_descriptor(f"partition:{index}", index * 10, index * 10 + 9, index * 100, index * 100 + 99))
        sizes.append(len(directory.canonical_bytes()))
    directory.connect(GRFPartitionNeighbor("partition:0", "partition:1", "spatial_boundary"))
    payload = directory.canonical_bytes()
    replayed = GlobalFieldDirectory.from_bytes(payload)
    assert replayed.canonical_bytes() == payload
    assert b'"content":' not in payload and b'"semantic_edge":' not in payload
    increments = [right - left for left, right in zip(sizes, sizes[1:])]
    assert max(increments) - min(increments) < 32
    directory.remove("partition:3")
    assert len(directory.entries()) == 3


def test_cross_partition_recall_is_bounded_and_rollback_removes_path() -> None:
    global_field = GlobalShardedField()
    left = GRFPartition(partition_descriptor("partition:left", 0, 9, 0, 99))
    right = GRFPartition(partition_descriptor("partition:right", 10, 19, 100, 199))
    global_field.add_partition(left)
    global_field.add_partition(right)
    first, second = _placement(1, 1), _placement(2, 11)
    global_field.insert("partition:left", first, "admission:grf7:1")
    global_field.insert("partition:right", second, "admission:grf7:2")
    bridge = CrossPartitionBridgeKernel("bridge:grf7:1", "partition:left", "partition:right", first.placement_id, second.placement_id, Q16_ONE, Q16_ONE, 1, (first.shard_id, second.shard_id))
    proposal = CrossPartitionStitchProposal("proposal:grf7:1", bridge, ("source_backed_ref",))
    global_field.accept_stitch(proposal, "stitch:grf7:1", "2026-07-10T00:00:00Z")
    budget = GlobalRecallBudget(1, 1, 2, 2, Q16_ONE // 2)
    result = global_field.recall(GlobalRecallQuery("query:grf7:cross", "shard_id", first.shard_id, budget))
    assert result.selected_shards == (first.shard_id, second.shard_id)
    assert result.path.visited_partitions == ("partition:left", "partition:right")
    assert result.path.boundary_crossings == (("partition:left", "partition:right"),)
    assert result.visited_partition_count == 2 and result.exact_identity_match is True
    assert set(result.path.source_fallback_refs) == {first.shard_id, second.shard_id}
    global_field.rollback_stitch(bridge.bridge_id, "false_friend", "2026-07-10T00:00:01Z")
    after = global_field.recall(GlobalRecallQuery("query:grf7:rollback", "shard_id", first.shard_id, budget))
    assert after.selected_shards == (first.shard_id,)
    assert after.path.bridges_used == ()


def test_typed_entry_modes_and_repartition_preserve_identity_and_fallback() -> None:
    global_field = GlobalShardedField()
    original = GRFPartition(partition_descriptor("partition:original", 0, 19, 0, 199))
    global_field.add_partition(original)
    placements = (_placement(3, 3), _placement(4, 14))
    for index, placement in enumerate(placements, start=3):
        global_field.insert("partition:original", placement, f"admission:grf7:{index}")
    budget = GlobalRecallBudget(1, 1, 2, 1, 0)
    queries = (
        ("shard_id", placements[0].shard_id),
        ("placement_id", placements[0].placement_id),
        ("admission_id", "admission:grf7:3"),
        ("island_id", placements[0].island_id),
        ("patch_id", placements[0].patch_id),
        ("source_window", placements[0].source_fallback_refs[0]),
        ("explicit_cell", placements[0].geometry_mark.cell),
    )
    assert all(global_field.recall(GlobalRecallQuery(f"query:{mode}", mode, ref, budget, False)).selected_shards == (placements[0].shard_id,) for mode, ref in queries)
    left = GRFPartition(partition_descriptor("partition:left", 0, 9, 0, 99))
    right = GRFPartition(partition_descriptor("partition:right", 10, 19, 100, 199))
    global_field.split_partition("partition:original", left, right, 9)
    assert global_field.recall(GlobalRecallQuery("query:after-split", "admission_id", "admission:grf7:3", budget, False)).selected_shards == (placements[0].shard_id,)
    merged = GRFPartition(partition_descriptor("partition:merged", 0, 19, 0, 199))
    global_field.merge_partitions("partition:left", "partition:right", merged)
    result = global_field.recall(GlobalRecallQuery("query:after-merge", "placement_id", placements[1].placement_id, budget, False))
    assert result.selected_shards == (placements[1].shard_id,)
    assert result.path.source_fallback_refs == (placements[1].shard_id,)


def test_false_friend_stitch_is_rejected_without_bridge_storage() -> None:
    field = GlobalShardedField()
    field.add_partition(GRFPartition(partition_descriptor("partition:a", 0, 9, 0, 99)))
    field.add_partition(GRFPartition(partition_descriptor("partition:b", 10, 19, 100, 199)))
    bridge = CrossPartitionBridgeKernel("bridge:false", "partition:a", "partition:b", "placement:a", "placement:b", Q16_ONE // 4, Q16_ONE // 4, 1, ("shard:a", "shard:b"))
    rejected = field.reject_stitch(CrossPartitionStitchProposal("proposal:false", bridge, ("lexical_hint",)))
    assert rejected.state == "rejected"
    assert all(not descriptor.bridge_summary for descriptor in field.directory.entries())


def test_partition_lifecycle_load_snapshot_rebuild_and_empty_retirement() -> None:
    field = GlobalShardedField()
    active = GRFPartition(partition_descriptor("partition:lifecycle:active", 0, 9, 0, 99))
    empty = GRFPartition(partition_descriptor("partition:lifecycle:empty", 10, 19, 100, 199))
    field.add_partition(active)
    field.add_partition(empty)
    field.insert(active.descriptor.partition_id, _placement(10, 1), "admission:grf7:10")
    assert field.load_partition(active.descriptor.partition_id) is active
    assert field.snapshot_partition(active.descriptor.partition_id).partition_id == active.descriptor.partition_id
    digest = field.rebuild_directory()
    assert digest == field.directory.digest()
    assert field.retire_partition(empty.descriptor.partition_id).partition_id == empty.descriptor.partition_id
    try:
        field.retire_partition(active.descriptor.partition_id)
    except ValueError as error:
        assert "placements" in str(error)
    else:
        raise AssertionError("retirement must refuse non-empty partitions")
