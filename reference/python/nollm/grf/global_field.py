"""Global sharded GRF directory, bounded recall, stitching, and repartition."""

from __future__ import annotations

from bisect import bisect_right
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
        self._cell_intervals: dict[tuple[str, str, int], tuple[tuple[int, int, int, int, str], ...]] = {}
        self._cell_prefix_max: dict[tuple[str, str, int], tuple[int, ...]] = {}
        self._source_intervals: tuple[tuple[int, int, str], ...] = ()
        self._source_prefix_max: tuple[int, ...] = ()
        self._last_descriptors_examined = 0

    def add(self, descriptor: GRFPartitionDescriptor) -> None:
        if descriptor.partition_id in self._descriptors:
            raise FileExistsError("partition already exists")
        self._descriptors[descriptor.partition_id] = descriptor
        self._rebuild_indexes()

    def add_many(self, descriptors: tuple[GRFPartitionDescriptor, ...]) -> None:
        incoming = tuple(descriptors)
        incoming_ids = tuple(item.partition_id for item in incoming)
        if len(set(incoming_ids)) != len(incoming_ids) or any(item in self._descriptors for item in incoming_ids):
            raise FileExistsError("partition already exists")
        self._descriptors.update((item.partition_id, item) for item in incoming)
        self._rebuild_indexes()

    def has_partition(self, partition_id: str) -> bool:
        return partition_id in self._descriptors

    def replace(self, descriptor: GRFPartitionDescriptor) -> None:
        if descriptor.partition_id not in self._descriptors:
            raise KeyError("partition does not exist")
        self._descriptors[descriptor.partition_id] = descriptor
        self._rebuild_indexes()

    def remove(self, partition_id: str) -> GRFPartitionDescriptor:
        descriptor = self._descriptors.pop(partition_id)
        self._neighbors = {key: value for key, value in self._neighbors.items() if partition_id not in key}
        for endpoint in self._descriptors:
            self._refresh_neighbor_refs(endpoint)
        self._rebuild_indexes()
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

    def disconnect(self, partition_id: str, neighbor_partition_id: str) -> None:
        self._neighbors.pop((partition_id, neighbor_partition_id), None)
        self._neighbors.pop((neighbor_partition_id, partition_id), None)
        if partition_id in self._descriptors:
            self._refresh_neighbor_refs(partition_id)
        if neighbor_partition_id in self._descriptors:
            self._refresh_neighbor_refs(neighbor_partition_id)

    def entries(self) -> tuple[GRFPartitionDescriptor, ...]:
        return tuple(self._descriptors[key] for key in sorted(self._descriptors))

    def neighbors(self, partition_id: str) -> tuple[GRFPartitionNeighbor, ...]:
        return tuple(value for key, value in sorted(self._neighbors.items()) if key[0] == partition_id)

    def locate_cell(self, cell: CellAddress) -> tuple[str, ...]:
        key = (cell.profile_id, cell.chart_id, cell.layer)
        intervals = self._cell_intervals.get(key, ())
        prefix = self._cell_prefix_max.get(key, ())
        starts = tuple(item[0] for item in intervals)
        index = bisect_right(starts, cell.q) - 1
        found = []
        examined = 0
        while index >= 0 and prefix[index] >= cell.q:
            q_min, q_max, r_min, r_max, partition_id = intervals[index]
            examined += 1
            if q_min <= cell.q <= q_max and r_min <= cell.r <= r_max:
                found.append(partition_id)
            index -= 1
        self._last_descriptors_examined = examined
        return tuple(sorted(found))

    def locate_source(self, source_position: int) -> tuple[str, ...]:
        if type(source_position) is not int:
            raise TypeError("source_position must be integer")
        starts = tuple(item[0] for item in self._source_intervals)
        index = bisect_right(starts, source_position) - 1
        found = []
        examined = 0
        while index >= 0 and self._source_prefix_max[index] >= source_position:
            start, end, partition_id = self._source_intervals[index]
            examined += 1
            if start <= source_position <= end:
                found.append(partition_id)
            index -= 1
        self._last_descriptors_examined = examined
        return tuple(sorted(found))

    @property
    def last_descriptors_examined(self) -> int:
        return self._last_descriptors_examined

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
        descriptors = []
        for item in mapping["partitions"]:
            boundary = GRFPartitionBoundary(**item["boundary"])
            snapshot = GRFPartitionSnapshotRef(**item["snapshot_ref"])
            descriptors.append(GRFPartitionDescriptor(item["partition_id"], item["profile_id"], item["chart_id"], tuple(item["layer_range"]), boundary, item["placement_count"], snapshot, tuple(item["neighbor_partition_refs"]), tuple(item["bridge_summary"])))
        directory.add_many(tuple(descriptors))
        for item in mapping["neighbors"]:
            neighbor = GRFPartitionNeighbor(**item)
            directory._neighbors[(neighbor.partition_id, neighbor.neighbor_partition_id)] = neighbor
        directory._rebuild_indexes()
        return directory

    def _refresh_neighbor_refs(self, partition_id: str) -> None:
        descriptor = self._descriptors[partition_id]
        refs = tuple(item.neighbor_partition_id for item in self.neighbors(partition_id))
        self._descriptors[partition_id] = replace(descriptor, neighbor_partition_refs=refs)

    def _rebuild_indexes(self) -> None:
        cells: dict[tuple[str, str, int], list[tuple[int, int, int, int, str]]] = {}
        sources = []
        for descriptor in self._descriptors.values():
            for layer in range(descriptor.layer_range[0], descriptor.layer_range[1] + 1):
                key = (descriptor.profile_id, descriptor.chart_id, layer)
                boundary = descriptor.boundary
                cells.setdefault(key, []).append((boundary.q_min, boundary.q_max, boundary.r_min, boundary.r_max, descriptor.partition_id))
            sources.append((descriptor.boundary.source_start, descriptor.boundary.source_end, descriptor.partition_id))
        self._cell_intervals = {key: tuple(sorted(values)) for key, values in cells.items()}
        self._cell_prefix_max = {key: _prefix_max(tuple(item[1] for item in values)) for key, values in self._cell_intervals.items()}
        self._source_intervals = tuple(sorted(sources))
        self._source_prefix_max = _prefix_max(tuple(item[1] for item in self._source_intervals))


class GRFPartition:
    def __init__(self, descriptor: GRFPartitionDescriptor, profiles: tuple[str, ...] = ("eisenstein_exact_v1",)) -> None:
        kernels = KernelRegistry()
        kernels.compile_profiles(profiles)
        self.descriptor = descriptor
        self.engine = FieldEngine(kernels, CellRegistry())
        self.ledger: list[tuple[str, str]] = []
        self.version = descriptor.snapshot_ref.version

    def insert(self, placement: PlacementRecord) -> None:
        self.validate_insert(placement)
        self.engine.insert(placement)
        self.ledger.append(("insert", placement.placement_id))
        self._refresh_count()

    def validate_insert(self, placement: PlacementRecord) -> None:
        if placement.geometry_mark.profile_id != self.descriptor.profile_id or placement.geometry_mark.chart_id != self.descriptor.chart_id:
            raise ValueError("placement profile/chart outside partition")
        if not self.descriptor.boundary.contains_cell(placement.geometry_mark.cell):
            raise ValueError("placement cell outside partition boundary")
        if placement.placement_id in self.engine.placements._placements:
            raise FileExistsError("placement already exists in partition")
        existing = self.engine.placements.placement_id_for_shard(placement.shard_id)
        if existing is not None and existing != placement.placement_id:
            raise FileExistsError("shard already has a placement in partition")

    def remove(self, placement_id: str) -> PlacementRecord:
        placement = self.engine.remove(placement_id)
        self.ledger.append(("remove", placement_id))
        self._refresh_count()
        return placement

    def move(self, placement: PlacementRecord) -> None:
        if placement.geometry_mark.profile_id != self.descriptor.profile_id or placement.geometry_mark.chart_id != self.descriptor.chart_id:
            raise ValueError("moved placement profile/chart outside partition")
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
class StitchEvent:
    sequence: int
    proposal_id: str
    bridge_id: str
    event: str
    state: str
    reason: str

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


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
    resident_partition_count: int
    cache_loaded_partition_count: int
    visited_partition_count: int
    disk_hydration_count: int
    exact_identity_match: bool
    budget_exhausted: bool


class GlobalShardedField:
    def __init__(self, loader: Callable[[str], GRFPartition] | None = None) -> None:
        self.directory = GlobalFieldDirectory()
        self._partitions: dict[str, GRFPartition] = {}
        self._loader = loader
        self._resident_partition_ids: set[str] = set()
        self._disk_hydrations = 0
        self._unique_routes: dict[tuple[str, str], tuple[str, str]] = {}
        self._shared_routes: dict[tuple[str, str], set[tuple[str, str]]] = {}
        self._bridges: dict[str, CrossPartitionStitchRecord] = {}
        self._rollbacks: list[BridgeRollbackRecord] = []
        self._stitch_ledger: list[StitchEvent] = []
        self._proposal_states: dict[str, str] = {}

    def add_partition(self, partition: GRFPartition) -> None:
        self.directory.add(partition.descriptor)
        self._partitions[partition.descriptor.partition_id] = partition
        self._resident_partition_ids.add(partition.descriptor.partition_id)

    def add_descriptor(self, descriptor: GRFPartitionDescriptor) -> None:
        self.directory.add(descriptor)

    def insert(self, partition_id: str, placement: PlacementRecord, admission_id: str | None = None) -> None:
        partition = self._load(partition_id)
        unique = [("shard_id", placement.shard_id), ("placement_id", placement.placement_id)]
        if admission_id is not None:
            unique.append(("admission_id", admission_id))
        for key in unique:
            if key in self._unique_routes:
                raise FileExistsError(f"duplicate unique identity: {key[0]}")
        partition.validate_insert(placement)
        partition.insert(placement)
        self.directory.replace(partition.descriptor)
        for key in unique:
            self._unique_routes[key] = (partition_id, placement.placement_id)
        shared = [("island_id", placement.island_id), ("patch_id", placement.patch_id)]
        shared.extend(("source_window", ref) for ref in placement.source_fallback_refs)
        for key in shared:
            self._shared_routes.setdefault(key, set()).add((partition_id, placement.placement_id))

    def bind_admission_identity(self, admission_id: str, placement_id: str) -> None:
        key = ("admission_id", admission_id)
        if key in self._unique_routes:
            raise FileExistsError("duplicate admission identity")
        placement_route = self._unique_routes.get(("placement_id", placement_id))
        if placement_route is None:
            raise FileNotFoundError("placement identity is not routed")
        self._unique_routes[key] = placement_route

    def register_persisted_route(self, mode: str, entry_ref: str, partition_id: str, placement_id: str) -> None:
        if not self.directory.has_partition(partition_id):
            raise FileNotFoundError("persisted route partition is not registered")
        key = (mode, entry_ref)
        if mode in ("shard_id", "placement_id", "admission_id"):
            if key in self._unique_routes:
                raise FileExistsError("duplicate persisted unique identity")
            self._unique_routes[key] = (partition_id, placement_id)
            return
        if mode not in ("source_window", "island_id", "patch_id"):
            raise ValueError("unsupported persisted route mode")
        self._shared_routes.setdefault(key, set()).add((partition_id, placement_id))

    def recall(self, query: GlobalRecallQuery) -> GlobalRecallResult:
        hydration_start = self._disk_hydrations
        entry_partitions = self._route(query.entry_mode, query.entry_ref)
        if not entry_partitions:
            return GlobalRecallResult(query.query_id, (), GlobalRecallPath("", (), (), (), (), 0, ()), len(self._partitions), len(self._resident_partition_ids), len(self._partitions), 0, 0, False, False)
        entry_partition = entry_partitions[0]
        queue: list[tuple[str, int, str | None]] = [(partition_id, 0, None) for partition_id in entry_partitions[: query.budget.max_partition_fanout]]
        visited: list[str] = []
        crossings: list[tuple[str, str]] = []
        bridges_used: list[str] = []
        selected: list[str] = []
        selected_set: set[str] = set()
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
            digest = resolve_grf_recall(QueryProbe(f"{query.query_id}:{partition_id}", mode, ref, ("lateral",), RecallBudget(0, 1, 0, 0, 0, 1)), partition.relation_field(), collect_rejected=False)
            for shard_id in digest.selected_shards:
                if shard_id not in selected_set:
                    selected.append(shard_id)
                    selected_set.add(shard_id)
            fallbacks.update(report.source_fallback_ref for report in digest.coverage_reports)
            if not query.cross_partition or hops >= query.budget.max_partition_hops:
                continue
            candidates = [record for record in self._bridges.values() if record.state == "accepted" and record.bridge.from_partition == partition_id and record.bridge.confidence_q16 >= query.budget.bridge_confidence_threshold_q16]
            for record in sorted(candidates, key=lambda item: item.bridge.bridge_id)[: query.budget.max_partition_fanout]:
                queue.append((record.bridge.to_partition, hops + 1, record.bridge.to_placement_id))
                crossings.append((partition_id, record.bridge.to_partition))
                bridges_used.append(record.bridge.bridge_id)
        result = tuple(selected[: query.budget.max_result_count])
        path = GlobalRecallPath(entry_partition, tuple(visited), tuple(crossings), ("local_relation_field",) + (("cross_partition_bridge",) if bridges_used else ()), tuple(bridges_used), activations, tuple(sorted(fallbacks)))
        identity_key = (query.entry_mode, str(query.entry_ref))
        unique_route = self._unique_routes.get(identity_key)
        expected_placement = None if unique_route is None else unique_route[1]
        expected_shard = None
        if expected_placement is not None:
            expected_shard = self._load(entry_partition).engine.placements._placements[expected_placement].shard_id
        return GlobalRecallResult(query.query_id, result, path, len(self._partitions), len(self._resident_partition_ids), len(self._partitions), len(visited), self._disk_hydrations - hydration_start, expected_shard in result if expected_shard else False, exhausted)

    def propose_stitch(self, proposal: CrossPartitionStitchProposal) -> CrossPartitionStitchProposal:
        if proposal.proposal_id in self._proposal_states:
            raise FileExistsError("stitch proposal already exists")
        self._proposal_states[proposal.proposal_id] = "proposed"
        self._append_stitch_event(proposal, "proposed", "proposed", "")
        return proposal

    def defer_stitch(self, proposal: CrossPartitionStitchProposal, reason: str) -> CrossPartitionStitchProposal:
        self._ensure_proposed(proposal)
        deferred = proposal.transition("deferred")
        self._proposal_states[proposal.proposal_id] = "deferred"
        self._append_stitch_event(proposal, "deferred", "deferred", reason)
        return deferred

    def accept_stitch(self, proposal: CrossPartitionStitchProposal, stitch_id: str, accepted_at: str) -> CrossPartitionStitchRecord:
        self._ensure_proposed(proposal)
        self._validate_bridge_endpoints(proposal.bridge)
        accepted = proposal.transition("accepted")
        record = CrossPartitionStitchRecord(stitch_id, accepted.proposal_id, accepted.bridge, "accepted", "validation_fixture", accepted_at)
        if record.bridge.bridge_id in self._bridges:
            raise FileExistsError("bridge already accepted")
        self._bridges[record.bridge.bridge_id] = record
        self._proposal_states[proposal.proposal_id] = "accepted"
        self._append_stitch_event(proposal, "accepted", "accepted", "")
        self.directory.connect(GRFPartitionNeighbor(record.bridge.from_partition, record.bridge.to_partition, "accepted_bridge", False))
        self._refresh_bridge_summary(record.bridge.from_partition)
        self._refresh_bridge_summary(record.bridge.to_partition)
        return record

    def reject_stitch(self, proposal: CrossPartitionStitchProposal) -> CrossPartitionStitchProposal:
        self._ensure_proposed(proposal)
        rejected = proposal.transition("rejected")
        self._proposal_states[proposal.proposal_id] = "rejected"
        self._append_stitch_event(proposal, "rejected", "rejected", "predicate_rejected")
        return rejected

    def decay_stitch(self, proposal_id: str, reason: str) -> None:
        state = self._proposal_states.get(proposal_id)
        if state not in ("deferred", "accepted"):
            raise ValueError("only deferred or accepted stitch can decay")
        record = next((item for item in self._bridges.values() if item.proposal_id == proposal_id), None)
        bridge_id = "" if record is None else record.bridge.bridge_id
        if record is not None:
            self._remove_active_bridge(record.bridge.bridge_id)
        self._proposal_states[proposal_id] = "decayed"
        self._stitch_ledger.append(StitchEvent(len(self._stitch_ledger) + 1, proposal_id, bridge_id, "decayed", "decayed", reason))

    def rollback_stitch(self, bridge_id: str, reason: str, rolled_back_at: str) -> BridgeRollbackRecord:
        record = self._remove_active_bridge(bridge_id)
        rollback = BridgeRollbackRecord(f"rollback:{bridge_id}", record.stitch_id, bridge_id, reason, rolled_back_at)
        self._rollbacks.append(rollback)
        self._proposal_states[record.proposal_id] = "rolled_back"
        self._stitch_ledger.append(StitchEvent(len(self._stitch_ledger) + 1, record.proposal_id, bridge_id, "rolled_back", "rolled_back", reason))
        return rollback

    def stitch_metrics(self) -> dict[str, int]:
        events = tuple(self._stitch_ledger)
        return {
            "proposal_count": sum(item.event == "proposed" for item in events),
            "accepted_count": sum(item.event == "accepted" for item in events),
            "rejected_count": sum(item.event == "rejected" for item in events),
            "deferred_count": sum(item.event == "deferred" for item in events),
            "decayed_count": sum(item.event == "decayed" for item in events),
            "rollback_count": sum(item.event == "rolled_back" for item in events),
        }

    def stitch_events(self) -> tuple[StitchEvent, ...]:
        return tuple(self._stitch_ledger)

    def move_across_partition(self, from_partition_id: str, to_partition_id: str, placement: PlacementRecord) -> None:
        source = self._load(from_partition_id)
        target = self._load(to_partition_id)
        prior = source.engine.placements._placements.get(placement.placement_id)
        if prior is None:
            raise FileNotFoundError("source placement does not exist")
        if prior.shard_id != placement.shard_id:
            raise ValueError("cross-partition move cannot change evidence identity")
        target.validate_insert(placement)
        source.remove(placement.placement_id)
        try:
            target.insert(placement)
        except Exception:
            source.insert(prior)
            self.directory.replace(source.descriptor)
            raise
        self.directory.replace(source.descriptor)
        self.directory.replace(target.descriptor)
        self._reroute_placement(placement.placement_id, to_partition_id)

    def split_partition(self, partition_id: str, left: GRFPartition, right: GRFPartition, split_q: int) -> None:
        original = self._load(partition_id)
        placements = original.engine.placements.placements()
        self._invalidate_bridges_for_partitions({partition_id}, "split_requires_reproposal")
        self.directory.remove(partition_id)
        self._partitions.pop(partition_id, None)
        self._resident_partition_ids.discard(partition_id)
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
        self._invalidate_bridges_for_partitions({left_id, right_id}, "merge_requires_reproposal")
        self.directory.remove(left_id)
        self.directory.remove(right_id)
        self._partitions.pop(left_id, None)
        self._partitions.pop(right_id, None)
        self._resident_partition_ids.difference_update((left_id, right_id))
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
        key = (mode, str(ref))
        unique = self._unique_routes.get(key)
        if unique is not None:
            return (unique[0],)
        return tuple(sorted({partition_id for partition_id, _placement_id in self._shared_routes.get(key, set())}))

    def _local_entry(self, query: GlobalRecallQuery, partition_id: str, via_placement: str | None) -> tuple[str, object]:
        if via_placement is not None:
            return "placement_id", via_placement
        if query.entry_mode == "explicit_cell":
            return query.entry_mode, query.entry_ref
        key = (query.entry_mode, str(query.entry_ref))
        unique = self._unique_routes.get(key)
        if unique is not None:
            return "placement_id", unique[1]
        shared = sorted(item for item in self._shared_routes.get(key, set()) if item[0] == partition_id)
        if not shared:
            raise FileNotFoundError("shared entry has no placement in routed partition")
        return query.entry_mode, query.entry_ref

    def _load(self, partition_id: str) -> GRFPartition:
        partition = self._partitions.get(partition_id)
        if partition is None and self._loader is not None:
            partition = self._loader(partition_id)
            self._partitions[partition_id] = partition
            self._disk_hydrations += 1
        if partition is None:
            raise FileNotFoundError(f"partition not loaded: {partition_id}")
        return partition

    def unload_partition(self, partition_id: str) -> None:
        if partition_id in self._resident_partition_ids:
            raise ValueError("cannot unload resident partition")
        self._partitions.pop(partition_id, None)

    def load_partition(self, partition_id: str) -> GRFPartition:
        """Load an explicitly registered partition through the configured loader."""
        if not self.directory.has_partition(partition_id):
            raise FileNotFoundError("partition is not registered")
        return self._load(partition_id)

    def snapshot_partition(self, partition_id: str) -> GRFPartitionSnapshotRef:
        return self._load(partition_id).snapshot()

    def retire_partition(self, partition_id: str) -> GRFPartitionDescriptor:
        """Retire only an empty partition so existing routes cannot orphan."""
        partition = self._load(partition_id)
        if partition.engine.placements.placement_count() != 0:
            raise ValueError("cannot retire a partition with placements")
        descriptor = self.directory.remove(partition_id)
        self._partitions.pop(partition_id, None)
        self._resident_partition_ids.discard(partition_id)
        return descriptor

    def rebuild_directory(self) -> str:
        """Recreate directory indexes from metadata without reading evidence content."""
        descriptors = self.directory.entries()
        neighbors = tuple(neighbor for descriptor in descriptors for neighbor in self.directory.neighbors(descriptor.partition_id))
        rebuilt = GlobalFieldDirectory()
        rebuilt.add_many(descriptors)
        for neighbor in neighbors:
            if rebuilt.has_partition(neighbor.partition_id) and rebuilt.has_partition(neighbor.neighbor_partition_id):
                rebuilt.connect(neighbor)
        self.directory = rebuilt
        return rebuilt.digest()

    def _reroute_placement(self, placement_id: str, partition_id: str) -> None:
        for key, value in tuple(self._unique_routes.items()):
            if value[1] == placement_id:
                self._unique_routes[key] = (partition_id, placement_id)
        for key, values in tuple(self._shared_routes.items()):
            matches = {item for item in values if item[1] == placement_id}
            if matches:
                values.difference_update(matches)
                values.add((partition_id, placement_id))

    def _refresh_bridge_summary(self, partition_id: str) -> None:
        descriptor = next(item for item in self.directory.entries() if item.partition_id == partition_id)
        bridges = tuple(sorted(record.bridge.bridge_id for record in self._bridges.values() if partition_id in (record.bridge.from_partition, record.bridge.to_partition)))
        self.directory.replace(replace(descriptor, bridge_summary=bridges))

    def _ensure_proposed(self, proposal: CrossPartitionStitchProposal) -> None:
        state = self._proposal_states.get(proposal.proposal_id)
        if state is None:
            self.propose_stitch(proposal)
        elif state != proposal.state:
            raise ValueError("proposal state does not match stitch ledger")

    def _append_stitch_event(self, proposal: CrossPartitionStitchProposal, event: str, state: str, reason: str) -> None:
        self._stitch_ledger.append(StitchEvent(len(self._stitch_ledger) + 1, proposal.proposal_id, proposal.bridge.bridge_id, event, state, reason))

    def _validate_bridge_endpoints(self, bridge: CrossPartitionBridgeKernel) -> None:
        if not self.directory.has_partition(bridge.from_partition) or not self.directory.has_partition(bridge.to_partition):
            raise FileNotFoundError("bridge partition endpoint does not exist")
        source = self._load(bridge.from_partition).engine.placements._placements.get(bridge.from_placement_id)
        target = self._load(bridge.to_partition).engine.placements._placements.get(bridge.to_placement_id)
        if source is None or target is None:
            raise FileNotFoundError("bridge placement endpoint does not exist")
        if not {source.shard_id, target.shard_id}.issubset(set(bridge.evidence_refs)):
            raise ValueError("bridge evidence refs do not cover endpoint evidence")

    def _remove_active_bridge(self, bridge_id: str) -> CrossPartitionStitchRecord:
        record = self._bridges.pop(bridge_id)
        source, target = record.bridge.from_partition, record.bridge.to_partition
        still_linked = any(item.bridge.from_partition == source and item.bridge.to_partition == target for item in self._bridges.values())
        if not still_linked:
            self.directory.disconnect(source, target)
        self._refresh_bridge_summary(source)
        self._refresh_bridge_summary(target)
        return record

    def _invalidate_bridges_for_partitions(self, partition_ids: set[str], reason: str) -> None:
        bridge_ids = [bridge_id for bridge_id, record in self._bridges.items() if partition_ids.intersection((record.bridge.from_partition, record.bridge.to_partition))]
        for bridge_id in bridge_ids:
            record = self._remove_active_bridge(bridge_id)
            self._proposal_states[record.proposal_id] = "rolled_back"
            self._stitch_ledger.append(StitchEvent(len(self._stitch_ledger) + 1, record.proposal_id, bridge_id, "invalidated_for_repartition", "rolled_back", reason))


def partition_descriptor(partition_id: str, q_min: int, q_max: int, source_start: int, source_end: int, strategy: str = "spatial_cell_range") -> GRFPartitionDescriptor:
    boundary = GRFPartitionBoundary(strategy, q_min, q_max, -1_000_000_000, 1_000_000_000, source_start, source_end)
    empty_digest = sha256(canonical_dumps(())).hexdigest()
    snapshot = GRFPartitionSnapshotRef(partition_id, f"snapshot:{partition_id}:v1", f"ledger:{partition_id}", 1, empty_digest)
    return GRFPartitionDescriptor(partition_id, "eisenstein_exact_v1", "chart:grf7", (0, 0), boundary, 0, snapshot)


def _text(value: str, label: str) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")


def _prefix_max(values: tuple[int, ...]) -> tuple[int, ...]:
    maximum = -2**63
    output = []
    for value in values:
        maximum = max(maximum, value)
        output.append(maximum)
    return tuple(output)
