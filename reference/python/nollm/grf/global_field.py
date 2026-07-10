"""Global sharded GRF directory, bounded recall, stitching, and repartition."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Callable

from .cell_address import CellAddress
from .field_engine import CellRegistry, FieldEngine
from .fixed_point import Q16_ONE
from .json_canonical import canonical_dumps, canonical_loads
from .kernel_registry import KernelRegistry
from .placement import PlacementRecord
from .recall import QueryProbe, RecallBudget, resolve_grf_recall

PARTITION_STRATEGIES = frozenset({"spatial_cell_range", "source_range", "profile_partitioning"})
CROSS_STITCH_STATES = frozenset({"proposed", "deferred", "accepted", "rejected", "decayed", "rolled_back"})


@dataclass(frozen=True, order=True)
class GRFPartitionBoundary:
    strategy: str
    q_min: int
    q_max: int
    r_min: int
    r_max: int
    source_start: int
    source_end: int

    def __post_init__(self) -> None:
        if self.strategy not in PARTITION_STRATEGIES:
            raise ValueError("unknown partition strategy")
        if any(type(value) is not int for value in (self.q_min, self.q_max, self.r_min, self.r_max, self.source_start, self.source_end)):
            raise TypeError("partition boundary values must be integers")
        if self.q_min > self.q_max or self.r_min > self.r_max or self.source_start > self.source_end:
            raise ValueError("partition boundary range is reversed")

    def contains_cell(self, cell: CellAddress) -> bool:
        return self.q_min <= cell.q <= self.q_max and self.r_min <= cell.r <= self.r_max

    def contains_source(self, source_position: int) -> bool:
        return self.source_start <= source_position <= self.source_end

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True, order=True)
class GRFPartitionSnapshotRef:
    partition_id: str
    snapshot_ref: str
    ledger_ref: str
    version: int
    sha256: str

    def __post_init__(self) -> None:
        _text(self.partition_id, "partition_id")
        _text(self.snapshot_ref, "snapshot_ref")
        _text(self.ledger_ref, "ledger_ref")
        _text(self.sha256, "sha256")
        if type(self.version) is not int or self.version < 1:
            raise ValueError("snapshot version must be positive")

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True, order=True)
class GRFPartitionNeighbor:
    partition_id: str
    neighbor_partition_id: str
    reason: str
    bidirectional: bool = True

    def __post_init__(self) -> None:
        _text(self.partition_id, "partition_id")
        _text(self.neighbor_partition_id, "neighbor_partition_id")
        _text(self.reason, "reason")
        if self.partition_id == self.neighbor_partition_id:
            raise ValueError("partition cannot neighbor itself")

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True, order=True)
class GRFPartitionDescriptor:
    partition_id: str
    profile_id: str
    chart_id: str
    layer_range: tuple[int, int]
    boundary: GRFPartitionBoundary
    placement_count: int
    snapshot_ref: GRFPartitionSnapshotRef
    neighbor_partition_refs: tuple[str, ...] = ()
    bridge_summary: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for label, value in (("partition_id", self.partition_id), ("profile_id", self.profile_id), ("chart_id", self.chart_id)):
            _text(value, label)
        if len(self.layer_range) != 2 or self.layer_range[0] > self.layer_range[1]:
            raise ValueError("invalid layer_range")
        if not isinstance(self.boundary, GRFPartitionBoundary):
            raise TypeError("boundary must be GRFPartitionBoundary")
        if type(self.placement_count) is not int or self.placement_count < 0:
            raise ValueError("placement_count must be non-negative")
        if self.snapshot_ref.partition_id != self.partition_id:
            raise ValueError("snapshot partition mismatch")

    @property
    def source_range(self) -> tuple[int, int]:
        return (self.boundary.source_start, self.boundary.source_end)

    @property
    def cell_bounds(self) -> tuple[int, int, int, int]:
        return (self.boundary.q_min, self.boundary.q_max, self.boundary.r_min, self.boundary.r_max)

    @property
    def ledger_ref(self) -> str:
        return self.snapshot_ref.ledger_ref

    def to_mapping(self) -> dict[str, object]:
        return {
            "partition_id": self.partition_id,
            "profile_id": self.profile_id,
            "chart_id": self.chart_id,
            "layer_range": self.layer_range,
            "cell_bounds": self.cell_bounds,
            "source_range": self.source_range,
            "boundary": self.boundary.to_mapping(),
            "placement_count": self.placement_count,
            "snapshot_ref": self.snapshot_ref.to_mapping(),
            "ledger_ref": self.ledger_ref,
            "neighbor_partition_refs": self.neighbor_partition_refs,
            "bridge_summary": self.bridge_summary,
            "stores_evidence_content": False,
            "stores_semantic_edges": False,
        }


class GlobalFieldDirectory:
    """Deterministic metadata-only partition directory."""

    def __init__(self) -> None:
        self._descriptors: dict[str, GRFPartitionDescriptor] = {}
        self._neighbors: dict[tuple[str, str], GRFPartitionNeighbor] = {}

    def add(self, descriptor: GRFPartitionDescriptor) -> None:
        if descriptor.partition_id in self._descriptors:
            raise FileExistsError("partition already exists")
        self._descriptors[descriptor.partition_id] = descriptor

    def replace(self, descriptor: GRFPartitionDescriptor) -> None:
        if descriptor.partition_id not in self._descriptors:
            raise KeyError("partition does not exist")
        self._descriptors[descriptor.partition_id] = descriptor

    def remove(self, partition_id: str) -> GRFPartitionDescriptor:
        descriptor = self._descriptors.pop(partition_id)
        self._neighbors = {key: value for key, value in self._neighbors.items() if partition_id not in key}
        return descriptor

    def connect(self, neighbor: GRFPartitionNeighbor) -> None:
        if neighbor.partition_id not in self._descriptors or neighbor.neighbor_partition_id not in self._descriptors:
            raise KeyError("neighbor endpoint is not registered")
        self._neighbors[(neighbor.partition_id, neighbor.neighbor_partition_id)] = neighbor
        if neighbor.bidirectional:
            reverse = GRFPartitionNeighbor(neighbor.neighbor_partition_id, neighbor.partition_id, neighbor.reason, True)
            self._neighbors[(reverse.partition_id, reverse.neighbor_partition_id)] = reverse
        self._refresh_neighbor_refs(neighbor.partition_id)
        self._refresh_neighbor_refs(neighbor.neighbor_partition_id)

    def entries(self) -> tuple[GRFPartitionDescriptor, ...]:
        return tuple(self._descriptors[key] for key in sorted(self._descriptors))

    def neighbors(self, partition_id: str) -> tuple[GRFPartitionNeighbor, ...]:
        return tuple(value for key, value in sorted(self._neighbors.items()) if key[0] == partition_id)

    def locate_cell(self, cell: CellAddress) -> tuple[str, ...]:
        return tuple(
            item.partition_id for item in self.entries()
            if item.profile_id == cell.profile_id
            and item.chart_id == cell.chart_id
            and item.layer_range[0] <= cell.layer <= item.layer_range[1]
            and item.boundary.contains_cell(cell)
        )

    def locate_source(self, source_position: int) -> tuple[str, ...]:
        if type(source_position) is not int:
            raise TypeError("source_position must be integer")
        return tuple(item.partition_id for item in self.entries() if item.boundary.contains_source(source_position))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": "grf7_global_directory_v1",
            "partitions": tuple(item.to_mapping() for item in self.entries()),
            "neighbors": tuple(item.to_mapping() for item in sorted(self._neighbors.values())),
            "partition_count": len(self._descriptors),
            "directory_entry_count": len(self._descriptors),
            "neighbor_link_count": len(self._neighbors),
            "stores_evidence_content": False,
            "stores_semantic_edges": False,
        }

    def canonical_bytes(self) -> bytes:
        return canonical_dumps(self.to_mapping())

    def digest(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, payload: bytes) -> "GlobalFieldDirectory":
        mapping = canonical_loads(payload)
        if mapping.get("schema") != "grf7_global_directory_v1":
            raise ValueError("global directory schema mismatch")
        directory = cls()
        for item in mapping["partitions"]:
            boundary = GRFPartitionBoundary(**item["boundary"])
            snapshot = GRFPartitionSnapshotRef(**item["snapshot_ref"])
            directory.add(GRFPartitionDescriptor(item["partition_id"], item["profile_id"], item["chart_id"], tuple(item["layer_range"]), boundary, item["placement_count"], snapshot, tuple(item["neighbor_partition_refs"]), tuple(item["bridge_summary"])))
        for item in mapping["neighbors"]:
            neighbor = GRFPartitionNeighbor(**item)
            directory._neighbors[(neighbor.partition_id, neighbor.neighbor_partition_id)] = neighbor
        return directory

    def _refresh_neighbor_refs(self, partition_id: str) -> None:
        descriptor = self._descriptors[partition_id]
        refs = tuple(item.neighbor_partition_id for item in self.neighbors(partition_id))
        self._descriptors[partition_id] = replace(descriptor, neighbor_partition_refs=refs)


class GRFPartition:
    def __init__(self, descriptor: GRFPartitionDescriptor, profiles: tuple[str, ...] = ("eisenstein_exact_v1",)) -> None:
        kernels = KernelRegistry()
        kernels.compile_profiles(profiles)
        self.descriptor = descriptor
        self.engine = FieldEngine(kernels, CellRegistry())
        self.ledger: list[tuple[str, str]] = []
        self.version = descriptor.snapshot_ref.version

    def insert(self, placement: PlacementRecord) -> None:
        if placement.geometry_mark.profile_id != self.descriptor.profile_id or placement.geometry_mark.chart_id != self.descriptor.chart_id:
            raise ValueError("placement profile/chart outside partition")
        if not self.descriptor.boundary.contains_cell(placement.geometry_mark.cell):
            raise ValueError("placement cell outside partition boundary")
        self.engine.insert(placement)
        self.ledger.append(("insert", placement.placement_id))
        self._refresh_count()

    def remove(self, placement_id: str) -> PlacementRecord:
        placement = self.engine.remove(placement_id)
        self.ledger.append(("remove", placement_id))
        self._refresh_count()
        return placement

    def move(self, placement: PlacementRecord) -> None:
        if not self.descriptor.boundary.contains_cell(placement.geometry_mark.cell):
            raise ValueError("moved placement outside partition boundary")
        self.engine.move(placement)
        self.ledger.append(("move", placement.placement_id))

    def relation_field(self):
        return self.engine.build_relation_field()

    def snapshot(self) -> GRFPartitionSnapshotRef:
        payload = canonical_dumps(tuple(item.to_mapping() for item in self.engine.placements.placements()))
        digest = sha256(payload).hexdigest()
        return GRFPartitionSnapshotRef(self.descriptor.partition_id, f"snapshot:{self.descriptor.partition_id}:v{self.version}", f"ledger:{self.descriptor.partition_id}", self.version, digest)

    def _refresh_count(self) -> None:
        self.descriptor = replace(self.descriptor, placement_count=self.engine.placements.placement_count())


@dataclass(frozen=True)
class CrossPartitionBridgeKernel:
    bridge_id: str
    from_partition: str
    to_partition: str
    from_placement_id: str
    to_placement_id: str
    weight_q16: int
    confidence_q16: int
    max_fanout: int
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.bridge_id, self.from_partition, self.to_partition, self.from_placement_id, self.to_placement_id):
            _text(value, "bridge field")
        if self.from_partition == self.to_partition:
            raise ValueError("cross-partition bridge endpoints must differ")
        if any(type(value) is not int or value < 0 or value > Q16_ONE for value in (self.weight_q16, self.confidence_q16)):
            raise ValueError("bridge weights must be Q16")
        if type(self.max_fanout) is not int or self.max_fanout < 1:
            raise ValueError("max_fanout must be positive")

    def to_mapping(self) -> dict[str, object]:
        return {**self.__dict__, "not_fact_merge": True}


@dataclass(frozen=True)
class CrossPartitionStitchProposal:
    proposal_id: str
    bridge: CrossPartitionBridgeKernel
    witnesses: tuple[str, ...]
    state: str = "proposed"

    def __post_init__(self) -> None:
        _text(self.proposal_id, "proposal_id")
        if self.state not in CROSS_STITCH_STATES:
            raise ValueError("unknown cross-partition stitch state")
        if not self.witnesses:
            raise ValueError("stitch witnesses cannot be empty")

    def transition(self, state: str) -> "CrossPartitionStitchProposal":
        if state not in CROSS_STITCH_STATES:
            raise ValueError("unknown cross-partition stitch state")
        allowed = {
            "proposed": {"deferred", "accepted", "rejected"},
            "deferred": {"accepted", "rejected", "decayed"},
            "accepted": {"decayed", "rolled_back"},
            "rejected": set(), "decayed": set(), "rolled_back": set(),
        }
        if state not in allowed[self.state]:
            raise ValueError("invalid stitch state transition")
        return replace(self, state=state)


@dataclass(frozen=True)
class CrossPartitionStitchRecord:
    stitch_id: str
    proposal_id: str
    bridge: CrossPartitionBridgeKernel
    state: str
    accepted_by: str
    accepted_at: str


@dataclass(frozen=True)
class BridgeRollbackRecord:
    rollback_id: str
    stitch_id: str
    bridge_id: str
    reason: str
    rolled_back_at: str


@dataclass(frozen=True)
class GlobalRecallBudget:
    max_partition_hops: int
    max_partition_fanout: int
    max_activation_budget: int
    max_result_count: int
    bridge_confidence_threshold_q16: int

    def __post_init__(self) -> None:
        values = (self.max_partition_hops, self.max_partition_fanout, self.max_activation_budget, self.max_result_count)
        if any(type(value) is not int or value < 1 for value in values):
            raise ValueError("global recall budgets must be positive")
        if type(self.bridge_confidence_threshold_q16) is not int or not 0 <= self.bridge_confidence_threshold_q16 <= Q16_ONE:
            raise ValueError("bridge threshold must be Q16")


@dataclass(frozen=True)
class GlobalRecallQuery:
    query_id: str
    entry_mode: str
    entry_ref: object
    budget: GlobalRecallBudget
    cross_partition: bool = True


@dataclass(frozen=True)
class GlobalRecallPath:
    entry_partition: str
    visited_partitions: tuple[str, ...]
    boundary_crossings: tuple[tuple[str, str], ...]
    kernels_used: tuple[str, ...]
    bridges_used: tuple[str, ...]
    activation_budget_used: int
    source_fallback_refs: tuple[str, ...]


@dataclass(frozen=True)
class GlobalRecallResult:
    query_id: str
    selected_shards: tuple[str, ...]
    path: GlobalRecallPath
    loaded_partition_count: int
    exact_identity_match: bool
    budget_exhausted: bool


class GlobalShardedField:
    def __init__(self, loader: Callable[[str], GRFPartition] | None = None) -> None:
        self.directory = GlobalFieldDirectory()
        self._partitions: dict[str, GRFPartition] = {}
        self._loader = loader
        self._identity_routes: dict[tuple[str, str], str] = {}
        self._identity_placements: dict[tuple[str, str], str] = {}
        self._bridges: dict[str, CrossPartitionStitchRecord] = {}
        self._rollbacks: list[BridgeRollbackRecord] = []

    def add_partition(self, partition: GRFPartition) -> None:
        self.directory.add(partition.descriptor)
        self._partitions[partition.descriptor.partition_id] = partition

    def insert(self, partition_id: str, placement: PlacementRecord, admission_id: str | None = None) -> None:
        partition = self._load(partition_id)
        partition.insert(placement)
        self.directory.replace(partition.descriptor)
        identities = (("shard_id", placement.shard_id), ("placement_id", placement.placement_id), ("island_id", placement.island_id), ("patch_id", placement.patch_id))
        identities += tuple(("source_window", ref) for ref in placement.source_fallback_refs)
        if admission_id is not None:
            identities += (("admission_id", admission_id),)
        for key in identities:
            self._identity_routes[key] = partition_id
            self._identity_placements[key] = placement.placement_id

    def recall(self, query: GlobalRecallQuery) -> GlobalRecallResult:
        entry_partitions = self._route(query.entry_mode, query.entry_ref)
        if not entry_partitions:
            return GlobalRecallResult(query.query_id, (), GlobalRecallPath("", (), (), (), (), 0, ()), 0, False, False)
        entry_partition = entry_partitions[0]
        queue: list[tuple[str, int, str | None]] = [(entry_partition, 0, None)]
        visited: list[str] = []
        crossings: list[tuple[str, str]] = []
        bridges_used: list[str] = []
        selected: set[str] = set()
        fallbacks: set[str] = set()
        activations = 0
        exhausted = False
        while queue and len(selected) < query.budget.max_result_count:
            partition_id, hops, via_placement = queue.pop(0)
            if partition_id in visited:
                continue
            if activations >= query.budget.max_activation_budget:
                exhausted = True
                break
            partition = self._load(partition_id)
            visited.append(partition_id)
            activations += 1
            mode, ref = self._local_entry(query, partition_id, via_placement)
            digest = resolve_grf_recall(QueryProbe(f"{query.query_id}:{partition_id}", mode, ref, ("lateral",), RecallBudget(0, 1, 0, 0, 0, query.budget.max_result_count)), partition.relation_field())
            selected.update(digest.selected_shards)
            fallbacks.update(report.source_fallback_ref for report in digest.coverage_reports)
            if not query.cross_partition or hops >= query.budget.max_partition_hops:
                continue
            candidates = [record for record in self._bridges.values() if record.state == "accepted" and record.bridge.from_partition == partition_id and record.bridge.confidence_q16 >= query.budget.bridge_confidence_threshold_q16]
            for record in sorted(candidates, key=lambda item: item.bridge.bridge_id)[: query.budget.max_partition_fanout]:
                queue.append((record.bridge.to_partition, hops + 1, record.bridge.to_placement_id))
                crossings.append((partition_id, record.bridge.to_partition))
                bridges_used.append(record.bridge.bridge_id)
        result = tuple(sorted(selected))[: query.budget.max_result_count]
        path = GlobalRecallPath(entry_partition, tuple(visited), tuple(crossings), ("local_relation_field",) + (("cross_partition_bridge",) if bridges_used else ()), tuple(bridges_used), activations, tuple(sorted(fallbacks)))
        identity_key = (query.entry_mode, str(query.entry_ref))
        expected_placement = self._identity_placements.get(identity_key)
        expected_shard = None
        if expected_placement is not None:
            expected_shard = self._load(entry_partition).engine.placements._placements[expected_placement].shard_id
        return GlobalRecallResult(query.query_id, result, path, len(visited), expected_shard in result if expected_shard else False, exhausted)

    def accept_stitch(self, proposal: CrossPartitionStitchProposal, stitch_id: str, accepted_at: str) -> CrossPartitionStitchRecord:
        accepted = proposal.transition("accepted")
        record = CrossPartitionStitchRecord(stitch_id, accepted.proposal_id, accepted.bridge, "accepted", "validation_fixture", accepted_at)
        self._bridges[record.bridge.bridge_id] = record
        self.directory.connect(GRFPartitionNeighbor(record.bridge.from_partition, record.bridge.to_partition, "accepted_bridge", False))
        self._refresh_bridge_summary(record.bridge.from_partition)
        self._refresh_bridge_summary(record.bridge.to_partition)
        return record

    def reject_stitch(self, proposal: CrossPartitionStitchProposal) -> CrossPartitionStitchProposal:
        return proposal.transition("rejected")

    def rollback_stitch(self, bridge_id: str, reason: str, rolled_back_at: str) -> BridgeRollbackRecord:
        record = self._bridges.pop(bridge_id)
        rollback = BridgeRollbackRecord(f"rollback:{bridge_id}", record.stitch_id, bridge_id, reason, rolled_back_at)
        self._rollbacks.append(rollback)
        self._refresh_bridge_summary(record.bridge.from_partition)
        self._refresh_bridge_summary(record.bridge.to_partition)
        return rollback

    def split_partition(self, partition_id: str, left: GRFPartition, right: GRFPartition, split_q: int) -> None:
        original = self._load(partition_id)
        placements = original.engine.placements.placements()
        self.directory.remove(partition_id)
        self._partitions.pop(partition_id, None)
        self.add_partition(left)
        self.add_partition(right)
        for placement in placements:
            target = left.descriptor.partition_id if placement.geometry_mark.cell.q <= split_q else right.descriptor.partition_id
            self._partitions[target].insert(placement)
            self._reroute_placement(placement.placement_id, target)
        self.directory.replace(left.descriptor)
        self.directory.replace(right.descriptor)

    def merge_partitions(self, left_id: str, right_id: str, merged: GRFPartition) -> None:
        placements = (*self._load(left_id).engine.placements.placements(), *self._load(right_id).engine.placements.placements())
        self.directory.remove(left_id)
        self.directory.remove(right_id)
        self._partitions.pop(left_id, None)
        self._partitions.pop(right_id, None)
        self.add_partition(merged)
        for placement in placements:
            merged.insert(placement)
            self._reroute_placement(placement.placement_id, merged.descriptor.partition_id)
        self.directory.replace(merged.descriptor)

    def _route(self, mode: str, ref: object) -> tuple[str, ...]:
        if mode == "explicit_cell":
            if not isinstance(ref, CellAddress):
                raise TypeError("explicit_cell requires CellAddress")
            return self.directory.locate_cell(ref)
        route = self._identity_routes.get((mode, str(ref)))
        return () if route is None else (route,)

    def _local_entry(self, query: GlobalRecallQuery, partition_id: str, via_placement: str | None) -> tuple[str, object]:
        if via_placement is not None:
            return "placement_id", via_placement
        if query.entry_mode == "explicit_cell":
            return query.entry_mode, query.entry_ref
        key = (query.entry_mode, str(query.entry_ref))
        return "placement_id", self._identity_placements[key]

    def _load(self, partition_id: str) -> GRFPartition:
        partition = self._partitions.get(partition_id)
        if partition is None and self._loader is not None:
            partition = self._loader(partition_id)
            self._partitions[partition_id] = partition
        if partition is None:
            raise FileNotFoundError(f"partition not loaded: {partition_id}")
        return partition

    def _reroute_placement(self, placement_id: str, partition_id: str) -> None:
        for key, value in tuple(self._identity_placements.items()):
            if value == placement_id:
                self._identity_routes[key] = partition_id

    def _refresh_bridge_summary(self, partition_id: str) -> None:
        descriptor = next(item for item in self.directory.entries() if item.partition_id == partition_id)
        bridges = tuple(sorted(record.bridge.bridge_id for record in self._bridges.values() if partition_id in (record.bridge.from_partition, record.bridge.to_partition)))
        self.directory.replace(replace(descriptor, bridge_summary=bridges))


def partition_descriptor(partition_id: str, q_min: int, q_max: int, source_start: int, source_end: int, strategy: str = "spatial_cell_range") -> GRFPartitionDescriptor:
    boundary = GRFPartitionBoundary(strategy, q_min, q_max, -1_000_000_000, 1_000_000_000, source_start, source_end)
    empty_digest = sha256(canonical_dumps(())).hexdigest()
    snapshot = GRFPartitionSnapshotRef(partition_id, f"snapshot:{partition_id}:v1", f"ledger:{partition_id}", 1, empty_digest)
    return GRFPartitionDescriptor(partition_id, "eisenstein_exact_v1", "chart:grf7", (0, 0), boundary, 0, snapshot)


def _text(value: str, label: str) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")
