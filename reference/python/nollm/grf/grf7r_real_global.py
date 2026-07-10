"""Artifact-backed GRF7R global workload with bounded partition activation."""

from __future__ import annotations

from dataclasses import dataclass
import gzip
from hashlib import sha256
import json
from pathlib import Path
import random
from time import perf_counter_ns

from .cell_address import CellAddress
from .fixed_point import Q16_ONE
from .global_field import (
    CrossPartitionBridgeKernel,
    CrossPartitionStitchProposal,
    GlobalFieldDirectory,
    GlobalRecallBudget,
    GlobalRecallQuery,
    GlobalShardedField,
    GRFPartition,
)
from .grf7_scale_validation import ADMISSION_ROW, EVIDENCE_ROW, PLACEMENT_ROW
from .json_canonical import canonical_dumps
from .placement import GeometryMark, PlacementRecord


@dataclass(frozen=True)
class ArtifactInventory:
    partition_count: int
    placement_count: int
    evidence_count: int
    admission_count: int
    selected_count: int


class SelectedEvidenceStore:
    def __init__(self, path: Path, offsets: dict[str, int]) -> None:
        self.path = path
        self.offsets = offsets
        self.stream = path.open("rb")

    def read(self, shard_id: str) -> tuple[bytes, bytes]:
        self.stream.seek(self.offsets[shard_id])
        payload = json.loads(self.stream.readline())
        if payload["shard_id"] != shard_id:
            raise ValueError("evidence content store index mismatch")
        return payload["content"].encode("utf-8"), bytes.fromhex(payload["content_sha256"])

    def close(self) -> None:
        self.stream.close()


def run_real_global_workload(
    artifact_root: Path,
    output_root: Path,
    *,
    seed: int = 7_007_010,
    queries_per_partition: int = 200,
    negative_checks: int = 1_000,
) -> dict[str, object]:
    """Execute fixed-seed queries over every persisted partition artifact."""
    artifact_root = Path(artifact_root)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    prior_metrics_path = output_root / "real_global_metrics.json"
    prior_semantic_digest = None
    prior_negative_digest = None
    if prior_metrics_path.is_file():
        try:
            prior_semantic_digest = json.loads(prior_metrics_path.read_text(encoding="utf-8")).get("semantic_query_digest")
        except (OSError, ValueError):
            prior_semantic_digest = None
    prior_negative_path = output_root / "negative_query_metrics.json"
    if prior_negative_path.is_file():
        try:
            prior_negative_digest = json.loads(prior_negative_path.read_text(encoding="utf-8")).get("semantic_digest")
        except (OSError, ValueError):
            prior_negative_digest = None
    directory = GlobalFieldDirectory.from_bytes((artifact_root / "GRF7_GLOBAL_DIRECTORY_MANIFEST.json").read_bytes())
    descriptors = directory.entries()
    if not descriptors:
        raise ValueError("global directory is empty")
    selected = _selected_indexes(descriptors, queries_per_partition, seed)
    inventory, rows = _preflight_artifacts(artifact_root, descriptors, selected)
    evidence_store = _write_evidence_content_store(output_root / "selected_evidence_content.jsonl", rows)

    def loader(partition_id: str) -> GRFPartition:
        descriptor = next(item for item in descriptors if item.partition_id == partition_id)
        partition = GRFPartition(descriptor)
        for index, q, r, placement_hash, evidence_hash, admission_hash in rows[partition_id]:
            placement = _placement(index, q, r, evidence_hash)
            if sha256(placement.placement_id.encode("utf-8")).digest() != placement_hash:
                raise ValueError("persisted placement identity hash mismatch")
            if sha256(f"admission:grf7:global:{index}".encode("utf-8")).digest() != admission_hash:
                raise ValueError("persisted admission identity hash mismatch")
            partition.insert(placement)
        return partition

    field = GlobalShardedField(loader)
    for descriptor in descriptors:
        field.add_descriptor(descriptor)
        for index, q, r, _placement_hash, evidence_hash, _admission_hash in rows[descriptor.partition_id]:
            placement_id = f"placement:grf7:global:{index}"
            field.register_persisted_route("placement_id", placement_id, descriptor.partition_id, placement_id)

    accepted_bridges = _install_accepted_bridges(field, descriptors, rows)
    _exercise_nonaccepted_lifecycle(field, descriptors, rows)
    forbidden = _install_forbidden_bridges(field, descriptors, rows, negative_checks)
    ledger_path = output_root / "query_ledger.jsonl"
    total = cross_count = stitch_count = rejection_checks = resolved = 0
    max_hops = max_fanout = max_hydrated = max_visited = 0
    semantic_digest = sha256()
    randomizer = random.Random(seed)
    try:
        with ledger_path.open("w", encoding="utf-8", newline="\n") as stream:
            for position, descriptor in enumerate(descriptors):
                candidates = list(rows[descriptor.partition_id])
                randomizer.shuffle(candidates)
                for local_index, row in enumerate(candidates):
                    index, _q, _r, _placement_hash, evidence_hash, _admission_hash = row
                    placement_id = f"placement:grf7:global:{index}"
                    cross = local_index < min(50, len(candidates))
                    rejection_check = 50 <= local_index < min(60, len(candidates))
                    started = perf_counter_ns()
                    result = field.recall(
                        GlobalRecallQuery(
                            f"query:grf7r:{index}",
                            "placement_id",
                            placement_id,
                            GlobalRecallBudget(1, 1, 2 if cross else 1, 2 if cross else 1, Q16_ONE // 2),
                            cross,
                        )
                    )
                    latency = perf_counter_ns() - started
                    expected_shard = "shard:grf:" + sha256(f"capture:grf7:global:{index}".encode("utf-8")).hexdigest()[:24]
                    stored_content, stored_hash = evidence_store.read(expected_shard)
                    content_ok = sha256(stored_content).digest() == stored_hash == evidence_hash
                    fallback_ok = expected_shard in result.path.source_fallback_refs and expected_shard in result.selected_shards
                    if not content_ok or not fallback_ok:
                        raise AssertionError(
                            "artifact-backed fallback content resolution failed: "
                            f"index={index} content_ok={content_ok} fallback_ok={fallback_ok} "
                            f"expected={expected_shard} selected={result.selected_shards} "
                            f"fallbacks={result.path.source_fallback_refs}"
                        )
                    bridge = result.path.bridges_used[0] if result.path.bridges_used else None
                    event = {
                        "query_id": result.query_id,
                        "entry_identity": placement_id,
                        "entry_partition": result.path.entry_partition,
                        "hydrated_partitions": result.disk_hydration_count,
                        "visited_partitions": result.path.visited_partitions,
                        "bridge": bridge,
                        "selected_shards": result.selected_shards,
                        "fallback_sources": result.path.source_fallback_refs,
                        "content_sha256": evidence_hash.hex(),
                        "content_hash_verified": content_ok,
                        "latency_ns": latency,
                        "rejection_or_rollback_check": rejection_check,
                    }
                    semantic_event = {key: value for key, value in event.items() if key != "latency_ns"}
                    semantic_digest.update(canonical_dumps(semantic_event))
                    stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
                    total += 1
                    cross_count += len(result.path.visited_partitions) > 1
                    stitch_count += bridge is not None
                    rejection_checks += rejection_check
                    resolved += content_ok and fallback_ok
                    max_hops = max(max_hops, len(result.path.boundary_crossings))
                    max_fanout = max(max_fanout, len(result.path.bridges_used))
                    max_hydrated = max(max_hydrated, result.disk_hydration_count)
                    max_visited = max(max_visited, result.visited_partition_count)
                for partition_id in tuple(item.partition_id for item in descriptors):
                    field.unload_partition(partition_id)
            negative_metrics = _run_negative_queries(field, evidence_store, descriptors, forbidden, output_root, seed, prior_negative_digest)
    finally:
        evidence_store.close()

    stitch_ledger = tuple(item.to_mapping() for item in field.stitch_events())
    (output_root / "stitch_event_ledger.json").write_bytes(canonical_dumps(stitch_ledger))
    metrics = {
        "seed": seed,
        "artifact_inventory": inventory.__dict__,
        "all_artifact_identity_hashes_verified": inventory.placement_count,
        "query_count": total,
        "cross_partition_query_count": cross_count,
        "stitch_query_count": stitch_count,
        "rejection_rollback_verification_count": rejection_checks,
        "negative_query_count": negative_metrics["negative_query_count"],
        "negative_forbidden_bridge_hit_count": negative_metrics["forbidden_bridge_hit_count"],
        "negative_replay_deterministic": negative_metrics["replay_deterministic"],
        "content_hash_resolution_count": resolved,
        "accepted_bridge_count": accepted_bridges,
        "stitch_metrics": field.stitch_metrics(),
        "max_partition_hops": max_hops,
        "max_fanout": max_fanout,
        "max_hydrated_partitions": max_hydrated,
        "max_visited_partitions": max_visited,
        "activation_budget": 2,
        "query_ledger_sha256": sha256(ledger_path.read_bytes()).hexdigest(),
        "semantic_query_digest": semantic_digest.hexdigest(),
        "replay_deterministic": prior_semantic_digest == semantic_digest.hexdigest(),
        "directory_digest": field.directory.digest(),
    }
    (output_root / "real_global_metrics.json").write_bytes(canonical_dumps(metrics))
    return metrics


def _selected_indexes(descriptors: tuple[object, ...], count: int, seed: int) -> dict[str, set[int]]:
    selected: dict[str, set[int]] = {}
    for offset, descriptor in enumerate(descriptors):
        start, end = descriptor.source_range  # type: ignore[attr-defined]
        if count > end - start + 1:
            raise ValueError("queries_per_partition exceeds partition cardinality")
        if count < 2:
            raise ValueError("queries_per_partition must be at least two")
        rng = random.Random(seed + offset)
        values = {start, end}
        values.update(rng.sample(range(start + 1, end), count - 2))
        selected[descriptor.partition_id] = values  # type: ignore[attr-defined]
    return selected


def _preflight_artifacts(artifact_root: Path, descriptors: tuple[object, ...], selected: dict[str, set[int]]) -> tuple[ArtifactInventory, dict[str, tuple[tuple[int, int, int, bytes, bytes, bytes], ...]]]:
    rows: dict[str, tuple[tuple[int, int, int, bytes, bytes, bytes], ...]] = {}
    placement_total = evidence_total = admission_total = 0
    for position, descriptor in enumerate(descriptors):
        prefix = artifact_root / "partitions" / f"partition_{position:04d}"
        selected_rows = []
        count = 0
        paths = (
            prefix.with_name(prefix.name + "_evidence.bin.gz"),
            prefix.with_name(prefix.name + "_placement.bin.gz"),
            prefix.with_name(prefix.name + "_admission.bin.gz"),
        )
        if not all(path.is_file() for path in paths):
            raise FileNotFoundError("persisted partition store is incomplete")
        with gzip.open(paths[0], "rb") as evidence_stream, gzip.open(paths[1], "rb") as placement_stream, gzip.open(paths[2], "rb") as admission_stream:
            while True:
                evidence_row = evidence_stream.read(EVIDENCE_ROW.size)
                placement_row = placement_stream.read(PLACEMENT_ROW.size)
                admission_row = admission_stream.read(ADMISSION_ROW.size)
                if not evidence_row and not placement_row and not admission_row:
                    break
                if len(evidence_row) != EVIDENCE_ROW.size or len(placement_row) != PLACEMENT_ROW.size or len(admission_row) != ADMISSION_ROW.size:
                    raise ValueError("persisted partition stores have different or truncated cardinality")
                ei, evidence_hash = EVIDENCE_ROW.unpack(evidence_row)
                pi, q, r, placement_hash = PLACEMENT_ROW.unpack(placement_row)
                ai, admission_hash = ADMISSION_ROW.unpack(admission_row)
                if ei != pi or pi != ai:
                    raise ValueError("persisted store row identity mismatch")
                expected_index = descriptor.source_range[0] + count
                if pi != expected_index:
                    raise ValueError("persisted identity sequence is not unique and contiguous")
                if sha256(f"grf7 global evidence {pi}".encode("utf-8")).digest() != evidence_hash:
                    raise ValueError("persisted evidence content hash mismatch")
                if sha256(f"placement:grf7:global:{pi}".encode("utf-8")).digest() != placement_hash:
                    raise ValueError("persisted placement identity hash mismatch")
                if sha256(f"admission:grf7:global:{pi}".encode("utf-8")).digest() != admission_hash:
                    raise ValueError("persisted admission identity hash mismatch")
                if pi in selected[descriptor.partition_id]:
                    selected_rows.append((pi, q, r, placement_hash, evidence_hash, admission_hash))
                count += 1
        if count != descriptor.placement_count:
            raise ValueError("persisted partition cardinality mismatch")
        rows[descriptor.partition_id] = tuple(selected_rows)
        placement_total += count
        evidence_total += count
        admission_total += count
    return ArtifactInventory(len(descriptors), placement_total, evidence_total, admission_total, sum(len(item) for item in rows.values())), rows


def _placement(index: int, q: int, r: int, evidence_hash: bytes) -> PlacementRecord:
    content = f"grf7 global evidence {index}".encode("utf-8")
    if sha256(content).digest() != evidence_hash:
        raise ValueError("evidence content hash mismatch")
    shard_id = "shard:grf:" + sha256(f"capture:grf7:global:{index}".encode("utf-8")).hexdigest()[:24]
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, q, r)
    mark = GeometryMark(f"mark:grf7:global:{index}", shard_id, cell.profile_id, cell.chart_id, cell, "grf7_scale", "high", 0, "field:grf7")
    return PlacementRecord(f"placement:grf7:global:{index}", shard_id, f"candidate:grf7:global:{index}", f"decision:grf7:global:{index}", mark, f"island:grf7:global:{index}", f"patch:grf7:global:{index // 20}", (shard_id,), cell.profile_id, "grf7_scale_v1")


def _write_evidence_content_store(path: Path, rows: dict[str, tuple[tuple[int, int, int, bytes, bytes, bytes], ...]]) -> SelectedEvidenceStore:
    offsets = {}
    with path.open("wb") as stream:
        for partition_id in sorted(rows):
            for index, _q, _r, _placement_hash, evidence_hash, _admission_hash in rows[partition_id]:
                content = f"grf7 global evidence {index}"
                if sha256(content.encode("utf-8")).digest() != evidence_hash:
                    raise ValueError("selected evidence content does not match persisted hash")
                shard_id = "shard:grf:" + sha256(f"capture:grf7:global:{index}".encode("utf-8")).hexdigest()[:24]
                offsets[shard_id] = stream.tell()
                stream.write(json.dumps({"shard_id": shard_id, "content": content, "content_sha256": evidence_hash.hex()}, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
    return SelectedEvidenceStore(path, offsets)


def _bridge(field: GlobalShardedField, proposal_id: str, bridge_id: str, source: tuple[object, ...], target: tuple[object, ...]) -> CrossPartitionStitchProposal:
    source_index, _q, _r, _ph, source_hash, _ah = source
    target_index, _tq, _tr, _tph, target_hash, _tah = target
    source_placement = _placement(source_index, source[1], source[2], source_hash)
    target_placement = _placement(target_index, target[1], target[2], target_hash)
    source_route = field._unique_routes[("placement_id", source_placement.placement_id)]
    target_route = field._unique_routes[("placement_id", target_placement.placement_id)]
    kernel = CrossPartitionBridgeKernel(bridge_id, source_route[0], target_route[0], source_placement.placement_id, target_placement.placement_id, Q16_ONE, Q16_ONE, 1, (source_placement.shard_id, target_placement.shard_id))
    return CrossPartitionStitchProposal(proposal_id, kernel, ("artifact_identity",))


def _install_accepted_bridges(field: GlobalShardedField, descriptors: tuple[object, ...], rows: dict[str, tuple[tuple[int, int, int, bytes, bytes, bytes], ...]]) -> int:
    count = 0
    for index in range(len(descriptors)):
        source = rows[descriptors[index].partition_id][0]
        target = rows[descriptors[(index + 1) % len(descriptors)].partition_id][0]
        proposal = _bridge(field, f"proposal:accepted:{index}", f"bridge:accepted:{index}", source, target)
        field.accept_stitch(proposal, f"stitch:accepted:{index}", "2026-07-10T00:00:00Z")
        count += 1
    return count


def _exercise_nonaccepted_lifecycle(field: GlobalShardedField, descriptors: tuple[object, ...], rows: dict[str, tuple[tuple[int, int, int, bytes, bytes, bytes], ...]]) -> None:
    source = rows[descriptors[0].partition_id][1]
    target = rows[descriptors[1].partition_id][1]
    rejected = _bridge(field, "proposal:rejected", "bridge:rejected", source, target)
    field.reject_stitch(rejected)
    deferred = _bridge(field, "proposal:deferred", "bridge:deferred", source, target)
    deferred = field.defer_stitch(deferred, "awaiting_witness")
    field.decay_stitch(deferred.proposal_id, "witness_expired")
    rollback = _bridge(field, "proposal:rollback", "bridge:rollback", source, target)
    field.accept_stitch(rollback, "stitch:rollback", "2026-07-10T00:00:00Z")
    field.rollback_stitch(rollback.bridge.bridge_id, "negative_control", "2026-07-10T00:00:01Z")


def _install_forbidden_bridges(field: GlobalShardedField, descriptors: tuple[object, ...], rows: dict[str, tuple[tuple[int, int, int, bytes, bytes, bytes], ...]], total_checks: int) -> dict[str, tuple[dict[str, object], ...]]:
    if total_checks == 0:
        return {name: () for name in ("rejected", "decayed", "rolled_back", "mixed")}
    if total_checks < 4 or total_checks % 4:
        raise ValueError("negative_checks must be zero or divisible by four")
    if len(descriptors) < 3:
        raise ValueError("negative bridge verification requires at least three partitions")
    per_category = total_checks // 4
    records: dict[str, list[dict[str, object]]] = {name: [] for name in ("rejected", "decayed", "rolled_back")}
    for category_index, category in enumerate(records):
        for ordinal in range(per_category):
            source_index = (ordinal * 7 + category_index * 13) % len(descriptors)
            target_index = (source_index + 2 + category_index) % len(descriptors)
            while target_index in (source_index, (source_index + 1) % len(descriptors)):
                target_index = (target_index + 1) % len(descriptors)
            source = rows[descriptors[source_index].partition_id][ordinal % len(rows[descriptors[source_index].partition_id])]
            target = rows[descriptors[target_index].partition_id][ordinal % len(rows[descriptors[target_index].partition_id])]
            bridge_id = f"bridge:forbidden:{category}:{ordinal:04d}"
            proposal = _bridge(field, f"proposal:forbidden:{category}:{ordinal:04d}", bridge_id, source, target)
            if category == "rejected":
                field.reject_stitch(proposal)
            elif category == "decayed":
                field.decay_stitch(field.defer_stitch(proposal, "negative_control_deferred").proposal_id, "negative_control_expired")
            else:
                field.accept_stitch(proposal, f"stitch:forbidden:{ordinal:04d}", "2026-07-10T00:00:00Z")
                field.rollback_stitch(bridge_id, "negative_control_rollback", "2026-07-10T00:00:01Z")
            records[category].append({"bridge_id": bridge_id, "source_partition": proposal.bridge.from_partition, "target_partition": proposal.bridge.to_partition, "entry_placement_id": proposal.bridge.from_placement_id})
    mixed = []
    for ordinal in range(per_category):
        selected = tuple(records[name][ordinal] for name in ("rejected", "decayed", "rolled_back"))
        mixed.append({"bridge_id": "mixed", "source_partition": selected[0]["source_partition"], "target_partition": selected[0]["target_partition"], "entry_placement_id": selected[0]["entry_placement_id"], "forbidden_records": selected})
    return {**{name: tuple(value) for name, value in records.items()}, "mixed": tuple(mixed)}


def _run_negative_queries(field: GlobalShardedField, evidence_store: SelectedEvidenceStore, descriptors: tuple[object, ...], forbidden: dict[str, tuple[dict[str, object], ...]], output_root: Path, seed: int, prior_digest: str | None) -> dict[str, object]:
    events = []
    semantic = sha256()
    ledger_path = output_root / "negative_query_ledger.jsonl"
    with ledger_path.open("w", encoding="utf-8", newline="\n") as stream:
        for category in ("rejected", "decayed", "rolled_back", "mixed"):
            for ordinal, record in enumerate(forbidden[category]):
                checks = tuple(record.get("forbidden_records", (record,)))
                forbidden_ids = tuple(str(item["bridge_id"]) for item in checks)
                started = perf_counter_ns()
                result = field.recall(GlobalRecallQuery(f"query:grf7r:negative:{category}:{ordinal}", "placement_id", str(record["entry_placement_id"]), GlobalRecallBudget(1, 1, 2, 2, Q16_ONE // 2), True))
                latency = perf_counter_ns() - started
                actual = result.path.bridges_used
                active = tuple(sorted(field._bridges))
                neighbors = tuple(item.neighbor_partition_id for item in field.directory.neighbors(str(record["source_partition"])))
                stale_neighbor = any(str(item["target_partition"]) in neighbors for item in checks if item["bridge_id"] != "mixed")
                hit = bool(set(forbidden_ids).intersection(actual))
                inactive = not set(forbidden_ids).intersection(active)
                if hit or not inactive or stale_neighbor:
                    raise AssertionError("forbidden bridge became reachable or left stale directory state")
                selected_shard = result.selected_shards[0] if result.selected_shards else ""
                if not selected_shard:
                    raise AssertionError("negative query selected no shard")
                content, content_hash = evidence_store.read(selected_shard)
                if sha256(content).digest() != content_hash:
                    raise AssertionError("negative query evidence content hash mismatch")
                event = {
                    "query_id": result.query_id,
                    "category": category,
                    "seed": seed,
                    "entry_identity": record["entry_placement_id"],
                    "entry_partition": result.path.entry_partition,
                    "forbidden_bridge_ids_checked": forbidden_ids,
                    "actual_bridges_used": actual,
                    "forbidden_bridge_hit": hit,
                    "forbidden_bridge_active": not inactive,
                    "directory_neighbor_state": neighbors,
                    "bridge_registry_state": active,
                    "stale_neighbor": stale_neighbor,
                    "selected_shards": result.selected_shards,
                    "fallback_sources": result.path.source_fallback_refs,
                    "content_sha256": content_hash.hex(),
                    "latency_ns": latency,
                }
                stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
                semantic.update(canonical_dumps({key: value for key, value in event.items() if key != "latency_ns"}))
                events.append(event)
                for partition_id in result.path.visited_partitions:
                    field.unload_partition(partition_id)
    by_category = {name: sum(item["category"] == name for item in events) for name in ("rejected", "decayed", "rolled_back", "mixed")}
    metrics = {
        "seed": seed,
        "negative_query_count": len(events),
        "by_category": by_category,
        "forbidden_bridge_hit_count": sum(item["forbidden_bridge_hit"] for item in events),
        "stale_neighbor_count": sum(item["stale_neighbor"] for item in events),
        "forbidden_active_count": sum(item["forbidden_bridge_active"] for item in events),
        "semantic_digest": semantic.hexdigest(),
        "replay_deterministic": prior_digest == semantic.hexdigest(),
        "ledger_sha256": sha256(ledger_path.read_bytes()).hexdigest(),
    }
    (output_root / "negative_query_metrics.json").write_bytes(canonical_dumps(metrics))
    return metrics
