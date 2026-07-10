from __future__ import annotations

from dataclasses import replace
from time import perf_counter_ns

import pytest

from nollm.grf.cell_address import CellAddress
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.global_field import (
    CrossPartitionBridgeKernel,
    CrossPartitionStitchProposal,
    GRFPartition,
    GlobalFieldDirectory,
    GlobalRecallBudget,
    GlobalRecallQuery,
    GlobalShardedField,
    partition_descriptor,
)
from nollm.grf.placement import GeometryMark, PlacementRecord


def _placement(name: str, q: int, *, shard: str | None = None, shared: str = "window:shared") -> PlacementRecord:
    shard_id = shard or f"shard:grf7r:{name}"
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    mark = GeometryMark(f"mark:grf7r:{name}", shard_id, cell.profile_id, cell.chart_id, cell, "integrity", "high", 0, "field:grf7r")
    return PlacementRecord(f"placement:grf7r:{name}", shard_id, f"candidate:grf7r:{name}", f"decision:grf7r:{name}", mark, "island:shared", "patch:shared", (shared,), cell.profile_id, "grf7r_v1")


def _field() -> tuple[GlobalShardedField, PlacementRecord, PlacementRecord]:
    field = GlobalShardedField()
    field.add_partition(GRFPartition(partition_descriptor("partition:left", 0, 9, 0, 99)))
    field.add_partition(GRFPartition(partition_descriptor("partition:right", 10, 19, 100, 199)))
    left, right = _placement("left", 2), _placement("right", 12)
    field.insert("partition:left", left, "admission:left")
    field.insert("partition:right", right, "admission:right")
    return field, left, right


def _bridge(name: str, left: PlacementRecord, right: PlacementRecord) -> CrossPartitionBridgeKernel:
    return CrossPartitionBridgeKernel(f"bridge:{name}", "partition:left", "partition:right", left.placement_id, right.placement_id, Q16_ONE, Q16_ONE, 1, (left.shard_id, right.shard_id))


def test_directory_uses_interval_indexes_and_replays_deterministically() -> None:
    directory = GlobalFieldDirectory()
    for index in range(100):
        directory.add(partition_descriptor(f"partition:{index:03d}", index * 10, index * 10 + 9, index * 100, index * 100 + 99))
    started = perf_counter_ns()
    assert directory.locate_cell(CellAddress("eisenstein_exact_v1", "chart:grf7", 0, 554, 0)) == ("partition:055",)
    cell_latency = perf_counter_ns() - started
    assert directory.last_descriptors_examined == 1
    assert directory.locate_source(5_554) == ("partition:055",)
    assert directory.last_descriptors_examined == 1
    assert cell_latency > 0
    assert GlobalFieldDirectory.from_bytes(directory.canonical_bytes()).canonical_bytes() == directory.canonical_bytes()


def test_directory_bulk_build_has_indexed_lookup() -> None:
    directory = GlobalFieldDirectory()
    directory.add_many(tuple(partition_descriptor(f"partition:bulk:{index:05d}", index, index, index * 10, index * 10 + 9) for index in range(10_000)))

    assert directory.locate_source(75_555) == ("partition:bulk:07555",)
    assert directory.last_descriptors_examined == 1


def test_unique_identity_conflicts_reject_and_shared_entries_accumulate() -> None:
    field, left, right = _field()
    duplicate = _placement("duplicate", 3, shard=left.shard_id)
    with pytest.raises(FileExistsError, match="unique identity"):
        field.insert("partition:left", duplicate)
    assert field._load("partition:left").engine.placements.placement_count() == 1
    budget = GlobalRecallBudget(1, 2, 2, 4, 0)
    result = field.recall(GlobalRecallQuery("query:shared", "source_window", "window:shared", budget, False))
    assert result.selected_shards == tuple(sorted((left.shard_id, right.shard_id)))
    assert result.visited_partition_count == 2


def test_loader_accounting_separates_resident_cache_visited_and_hydrated() -> None:
    records = {"partition:left": _placement("persisted", 2)}

    def loader(partition_id: str) -> GRFPartition:
        partition = GRFPartition(partition_descriptor(partition_id, 0, 9, 0, 99))
        partition.insert(records[partition_id])
        return partition

    field = GlobalShardedField(loader)
    descriptor = partition_descriptor("partition:left", 0, 9, 0, 99)
    field.add_descriptor(replace(descriptor, placement_count=1))
    placement = records["partition:left"]
    field.register_persisted_route("shard_id", placement.shard_id, "partition:left", placement.placement_id)
    result = field.recall(GlobalRecallQuery("query:hydrate", "shard_id", placement.shard_id, GlobalRecallBudget(1, 1, 1, 1, 0), False))
    assert result.resident_partition_count == 0
    assert result.cache_loaded_partition_count == 1
    assert result.visited_partition_count == 1
    assert result.disk_hydration_count == 1


def test_cross_partition_recall_preserves_entry_before_bridge_target() -> None:
    field, left, right = _field()
    proposal = CrossPartitionStitchProposal("proposal:ordered", _bridge("ordered", left, right), ("identity_order",))
    field.accept_stitch(proposal, "stitch:ordered", "2026-07-10T00:00:00Z")

    result = field.recall(GlobalRecallQuery("query:ordered", "placement_id", left.placement_id, GlobalRecallBudget(1, 1, 2, 2, 0), True))

    assert result.selected_shards == (left.shard_id, right.shard_id)
    assert result.exact_identity_match is True


def test_stitch_ledger_drives_counts_and_rollback_neighbor_cleanup() -> None:
    field, left, right = _field()
    deferred = field.defer_stitch(CrossPartitionStitchProposal("proposal:deferred", _bridge("deferred", left, right), ("boundary_overlap",)), "needs review")
    field.decay_stitch(deferred.proposal_id, "expired")
    field.reject_stitch(CrossPartitionStitchProposal("proposal:rejected", _bridge("rejected", left, right), ("lexical_hint",)))
    first = field.accept_stitch(CrossPartitionStitchProposal("proposal:first", _bridge("first", left, right), ("source_backed_ref",)), "stitch:first", "2026-07-10T00:00:00Z")
    second = field.accept_stitch(CrossPartitionStitchProposal("proposal:second", _bridge("second", left, right), ("manual_bridge",)), "stitch:second", "2026-07-10T00:00:00Z")
    field.rollback_stitch(first.bridge.bridge_id, "wrong relation", "2026-07-10T00:00:01Z")
    assert field.directory.neighbors("partition:left")
    field.rollback_stitch(second.bridge.bridge_id, "wrong relation", "2026-07-10T00:00:02Z")
    assert field.directory.neighbors("partition:left") == ()
    assert field.stitch_metrics() == {"proposal_count": 4, "accepted_count": 2, "rejected_count": 1, "deferred_count": 1, "decayed_count": 1, "rollback_count": 2}
    assert tuple(event.sequence for event in field.stitch_events()) == tuple(range(1, len(field.stitch_events()) + 1))


def test_bridge_endpoint_validation_and_transactional_move_failure() -> None:
    field, left, right = _field()
    invalid = replace(_bridge("invalid", left, right), from_placement_id="placement:missing")
    with pytest.raises(FileNotFoundError, match="placement endpoint"):
        field.accept_stitch(CrossPartitionStitchProposal("proposal:invalid", invalid, ("manual_bridge",)), "stitch:invalid", "2026-07-10T00:00:00Z")
    bad_cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, 99, 0)
    bad_mark = replace(left.geometry_mark, cell=bad_cell)
    bad_move = replace(left, geometry_mark=bad_mark)
    with pytest.raises(ValueError, match="outside partition"):
        field.move_across_partition("partition:left", "partition:right", bad_move)
    assert field._load("partition:left").engine.placements._placements[left.placement_id] == left
    assert field._load("partition:right").engine.placements._placements[right.placement_id] == right


def test_partition_move_rejects_profile_chart_change_atomically() -> None:
    field, left, _right = _field()
    changed = replace(left, geometry_mark=replace(left.geometry_mark, chart_id="chart:other", cell=CellAddress("eisenstein_exact_v1", "chart:other", 0, 2, 0)))

    with pytest.raises(ValueError, match="profile/chart"):
        field._load("partition:left").move(changed)

    assert field._load("partition:left").engine.placements._placements[left.placement_id] == left


def test_split_invalidates_bridges_without_dangling_directory_refs() -> None:
    field, left, right = _field()
    field.accept_stitch(CrossPartitionStitchProposal("proposal:split", _bridge("split", left, right), ("manual_bridge",)), "stitch:split", "2026-07-10T00:00:00Z")
    field.split_partition("partition:left", GRFPartition(partition_descriptor("partition:left:a", 0, 4, 0, 49)), GRFPartition(partition_descriptor("partition:left:b", 5, 9, 50, 99)), 4)
    assert field._bridges == {}
    assert all("partition:left" not in (item.partition_id, item.neighbor_partition_id) for descriptor in field.directory.entries() for item in field.directory.neighbors(descriptor.partition_id))
    assert any(event.event == "invalidated_for_repartition" for event in field.stitch_events())
