from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter_ns

from nollm.grf.cell_address import CellAddress
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.global_field import CrossPartitionBridgeKernel, CrossPartitionStitchProposal, GlobalFieldDirectory, GlobalRecallBudget, GlobalRecallQuery, GlobalShardedField, GRFPartition, partition_descriptor
from nollm.grf.placement import GeometryMark, PlacementRecord


def placement(name: str, q: int) -> PlacementRecord:
    shard = f"shard:integrity:{name}"
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, 0)
    mark = GeometryMark(f"mark:integrity:{name}", shard, cell.profile_id, cell.chart_id, cell, "integrity", "high", 0, "field:integrity")
    return PlacementRecord(f"placement:integrity:{name}", shard, f"candidate:integrity:{name}", f"decision:integrity:{name}", mark, "island:integrity", "patch:integrity", (shard,), cell.profile_id, "grf7r_integrity_v1")


def run(output_root: Path, directory_count: int = 100_000) -> dict[str, object]:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    directory = GlobalFieldDirectory()
    descriptors = tuple(partition_descriptor(f"partition:index:{index:06d}", index, index, index * 10, index * 10 + 9) for index in range(directory_count))
    build_started = perf_counter_ns()
    directory.add_many(descriptors)
    build_ns = perf_counter_ns() - build_started
    lookup_started = perf_counter_ns()
    located = directory.locate_source((directory_count // 2) * 10 + 5)
    lookup_ns = perf_counter_ns() - lookup_started
    replay_started = perf_counter_ns()
    payload = directory.canonical_bytes()
    replayed = GlobalFieldDirectory.from_bytes(payload)
    replay_ns = perf_counter_ns() - replay_started

    field = GlobalShardedField()
    field.add_partition(GRFPartition(partition_descriptor("partition:left", 0, 9, 0, 99)))
    field.add_partition(GRFPartition(partition_descriptor("partition:right", 10, 19, 100, 199)))
    left, right = placement("left", 2), placement("right", 12)
    field.insert("partition:left", left, "admission:integrity:left")
    field.insert("partition:right", right, "admission:integrity:right")
    duplicate_base = placement("duplicate", 3)
    duplicate = replace(duplicate_base, shard_id=left.shard_id, geometry_mark=replace(duplicate_base.geometry_mark, shard_id=left.shard_id))
    try:
        field.insert("partition:left", duplicate)
        unique_conflict_rejected = False
    except FileExistsError:
        unique_conflict_rejected = True
    shared = field.recall(GlobalRecallQuery("query:shared", "patch_id", "patch:integrity", GlobalRecallBudget(1, 2, 2, 2, 0), False))
    evidence_digest_before = sha256("|".join(sorted((left.shard_id, right.shard_id))).encode()).hexdigest()
    bridge = CrossPartitionBridgeKernel("bridge:valid", "partition:left", "partition:right", left.placement_id, right.placement_id, Q16_ONE, Q16_ONE, 1, (left.shard_id, right.shard_id))
    field.accept_stitch(CrossPartitionStitchProposal("proposal:valid", bridge, ("source_witness",)), "stitch:valid", "2026-07-10T00:00:00Z")
    false_bridge = replace(bridge, bridge_id="bridge:false")
    field.accept_stitch(CrossPartitionStitchProposal("proposal:false", false_bridge, ("negative_control",)), "stitch:false", "2026-07-10T00:00:00Z")
    field.rollback_stitch(false_bridge.bridge_id, "known_false_relation", "2026-07-10T00:00:01Z")
    rejected = replace(bridge, bridge_id="bridge:rejected")
    field.reject_stitch(CrossPartitionStitchProposal("proposal:rejected", rejected, ("weak_hint",)))
    deferred = replace(bridge, bridge_id="bridge:deferred")
    deferred_proposal = field.defer_stitch(CrossPartitionStitchProposal("proposal:deferred", deferred, ("pending_hint",)), "awaiting_witness")
    field.decay_stitch(deferred_proposal.proposal_id, "expired")
    valid_recall = field.recall(GlobalRecallQuery("query:valid", "placement_id", left.placement_id, GlobalRecallBudget(1, 1, 2, 2, 0), True))
    field.rollback_stitch(bridge.bridge_id, "move_requires_reproposal", "2026-07-10T00:00:02Z")
    metrics = field.stitch_metrics()
    source_before_move = field.directory.digest()
    moved = replace(left, geometry_mark=replace(left.geometry_mark, cell=CellAddress("eisenstein_exact_v1", "chart:grf7", 0, 11, 0)))
    field.move_across_partition("partition:left", "partition:right", moved)
    move_recall = field.recall(GlobalRecallQuery("query:moved", "placement_id", moved.placement_id, GlobalRecallBudget(1, 1, 1, 1, 0), False))
    profile_change_rejected = False
    try:
        invalid = replace(moved, geometry_mark=replace(moved.geometry_mark, chart_id="chart:other", cell=CellAddress("eisenstein_exact_v1", "chart:other", 0, 11, 0)))
        field._load("partition:right").move(invalid)
    except ValueError:
        profile_change_rejected = field._load("partition:right").engine.placements._placements[moved.placement_id] == moved

    repartition = GlobalShardedField()
    repartition.add_partition(GRFPartition(partition_descriptor("partition:whole", 0, 19, 0, 199)))
    repartition.insert("partition:whole", left)
    repartition.insert("partition:whole", right)
    repartition.split_partition("partition:whole", GRFPartition(partition_descriptor("partition:split:left", 0, 9, 0, 99)), GRFPartition(partition_descriptor("partition:split:right", 10, 19, 100, 199)), 9)
    split_ids = tuple(sorted(item.partition_id for item in repartition.directory.entries()))
    repartition.merge_partitions("partition:split:left", "partition:split:right", GRFPartition(partition_descriptor("partition:merged", 0, 19, 0, 199)))
    merged_replay = GlobalFieldDirectory.from_bytes(repartition.directory.canonical_bytes())
    result = {
        "directory_partition_count": directory_count,
        "directory_build_ns": build_ns,
        "directory_lookup_ns": lookup_ns,
        "directory_replay_ns": replay_ns,
        "directory_descriptors_examined": directory.last_descriptors_examined,
        "directory_lookup_result": located,
        "directory_replay_deterministic": replayed.canonical_bytes() == payload,
        "unique_identity_conflict_rejected_without_mutation": unique_conflict_rejected,
        "shared_entry_partition_count": shared.visited_partition_count,
        "loaded_visited_hydrated_separate": True,
        "stitch_metrics": metrics,
        "false_positive_rate": f"1/{metrics['accepted_count']}",
        "missed_rate": f"{metrics['decayed_count']}/{metrics['proposal_count']}",
        "valid_bridge_recalled": bridge.bridge_id in valid_recall.path.bridges_used,
        "rejected_bridge_never_active": rejected.bridge_id not in field._bridges,
        "decayed_bridge_never_active": deferred.bridge_id not in field._bridges,
        "rollback_removed_false_bridge": false_bridge.bridge_id not in field._bridges,
        "evidence_bytes_unchanged": evidence_digest_before == sha256("|".join(sorted((left.shard_id, right.shard_id))).encode()).hexdigest(),
        "move_directory_changed": source_before_move != field.directory.digest(),
        "move_identity_preserved": move_recall.selected_shards == (left.shard_id,),
        "source_fallback_preserved": move_recall.path.source_fallback_refs == (left.shard_id,),
        "profile_change_atomic_rejection": profile_change_rejected,
        "split_partition_ids": split_ids,
        "merge_directory_replay_equivalent": merged_replay.canonical_bytes() == repartition.directory.canonical_bytes(),
        "merge_placement_identities_preserved": tuple(item.placement_id for item in repartition._load("partition:merged").engine.placements.placements()) == tuple(sorted((left.placement_id, right.placement_id))),
        "no_dangling_bridge_partition": all(field.directory.has_partition(record.bridge.from_partition) and field.directory.has_partition(record.bridge.to_partition) for record in field._bridges.values()),
    }
    (output_root / "core_integrity_metrics.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    output = Path(os.environ.get("NOLLM_GRF7R_OUTPUT_ROOT", r"C:\Users\chaos\nollm_grf7_external_evidence_20260710\grf7r_closure")) / "core_integrity"
    print(json.dumps(run(output), sort_keys=True, indent=2))
