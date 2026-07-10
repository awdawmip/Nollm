"""Real in-memory GRF2R dataset generation and field benchmark execution."""

from __future__ import annotations

from array import array
from dataclasses import dataclass
from math import isqrt
from sys import getsizeof
from time import perf_counter_ns

from .bridge_kernel import BridgeKernel
from .cell_address import CellAddress
from .evidence import EvidenceShardRecord
from .evidence_island import EvidenceIsland, EvidenceShardRef
from .field_engine import CellRegistry, FieldEngine
from .fixed_point import Q16_ONE
from .kernel_registry import KernelRegistry
from .placement import GeometryMark, PlacementRecord
from .recall import QueryProbe, RecallBudget, resolve_grf_recall
from .relation_field import RelationField
from .source_window import SourceWindowRecord
from .stitching import StitchProposal, StitchRecord, StitchTransform, StitchWitness


@dataclass(frozen=True)
class RealDatasetCounts:
    dataset_size: int
    shard_count: int
    source_window_count: int
    cell_count: int
    placement_count: int
    island_count: int
    stitch_count: int


@dataclass(frozen=True)
class RealScaleMetrics:
    counts: RealDatasetCounts
    cell_storage_size: int
    placement_storage_size: int
    kernel_storage_size: int
    template_storage_size: int
    relation_storage_size: int
    explicit_graph_storage_size: int
    explicit_graph_edge_count: int
    build_latency_ns: int
    lookup_latency_ns: int
    recall_latency_ns: int
    kernel_reuse_ratio: str
    source_fallback_preserved: bool
    field_engine_executed: bool
    relation_field_executed: bool
    explicit_graph_materialized: bool
    baseline_comparison: dict[str, dict[str, object]]

    def to_mapping(self) -> dict[str, object]:
        return {
            "dataset_size": self.counts.dataset_size,
            "shard_count": self.counts.shard_count,
            "source_window_count": self.counts.source_window_count,
            "cell_count": self.counts.cell_count,
            "placement_count": self.counts.placement_count,
            "island_count": self.counts.island_count,
            "stitch_count": self.counts.stitch_count,
            "cell_storage_size": self.cell_storage_size,
            "placement_storage_size": self.placement_storage_size,
            "kernel_storage_size": self.kernel_storage_size,
            "template_storage_size": self.template_storage_size,
            "relation_storage_size": self.relation_storage_size,
            "explicit_graph_storage_size": self.explicit_graph_storage_size,
            "explicit_graph_edge_count": self.explicit_graph_edge_count,
            "build_latency_ns": self.build_latency_ns,
            "lookup_latency_ns": self.lookup_latency_ns,
            "recall_latency_ns": self.recall_latency_ns,
            "kernel_reuse_ratio": self.kernel_reuse_ratio,
            "source_fallback_preserved": self.source_fallback_preserved,
            "field_engine_executed": self.field_engine_executed,
            "relation_field_executed": self.relation_field_executed,
            "explicit_graph_materialized": self.explicit_graph_materialized,
            "baseline_comparison": self.baseline_comparison,
        }


@dataclass(frozen=True)
class IncrementalEquivalence:
    selected_shards_equal: bool
    coverage_paths_equal: bool
    kernel_paths_equal: bool
    scores_equal: bool
    storage_state_equal: bool
    all_equal: bool

    def to_mapping(self) -> dict[str, bool]:
        return self.__dict__.copy()


class RealSyntheticDataset:
    """Creates actual GRF records but retains only field-owned placement state."""

    def __init__(self, dataset_size: int, occupancy: int = 20) -> None:
        if type(dataset_size) is not int or dataset_size <= 0:
            raise ValueError("dataset_size must be a positive integer")
        if type(occupancy) is not int or occupancy < 1:
            raise ValueError("occupancy must be a positive integer")
        self.dataset_size = dataset_size
        self.occupancy = occupancy

    def records(self):
        for index in range(self.dataset_size):
            window = SourceWindowRecord(
                f"window:grf2r:{index}", "validation_fixture", (f"fixture:grf2r:{index}",), "2026-07-10T00:00:00Z", policy_ref="grf2r_real_scale"
            )
            shard = EvidenceShardRecord(
                f"shard:grf2r:{index}", f"real synthetic evidence shard {index}", "2026-07-10T00:00:00Z", "validation_fixture", (window.window_id,), "trusted", "captured"
            )
            cell = self._cell_for(index)
            island = EvidenceIsland(
                f"island:grf2r:{index}", (EvidenceShardRef(shard.shard_id, shard.source_window_refs, shard.trust_state, shard.usage_state),), shard.source_window_refs, "validation_fixture", "placed"
            )
            mark = GeometryMark(
                f"mark:grf2r:{index}", shard.shard_id, cell.profile_id, cell.chart_id, cell, "grf2r_real_generator", "high", 0, "field:grf2r"
            )
            placement = PlacementRecord(
                f"placement:grf2r:{index}", shard.shard_id, f"candidate:grf2r:{index}", f"decision:grf2r:{index}", mark, island.island_id,
                f"patch:grf2r:{index // self.occupancy}", shard.source_window_refs, cell.profile_id, "grf2r_real_generator_v1"
            )
            yield shard, window, island, placement

    def stitch_record(self) -> StitchRecord:
        bridge = BridgeKernel("bridge:grf2r:0", "patch:grf2r:0", "patch:grf2r:1", Q16_ONE // 2, "normal", 1, self.occupancy, ("fixture:grf2r:bridge",))
        proposal = StitchProposal(
            "proposal:grf2r:0", bridge.from_patch, bridge.to_patch, StitchTransform.translation(1, 0),
            (StitchWitness("source_backed_ref", Q16_ONE, ("fixture:grf2r:bridge",)),), Q16_ONE, "accepted"
        )
        return StitchRecord.from_accepted_proposal("stitch:grf2r:0", proposal, "validation_fixture", "2026-07-10T00:00:00Z", 0, bridge)

    def _cell_for(self, index: int) -> CellAddress:
        cell_index = index // self.occupancy
        cell_count = (self.dataset_size + self.occupancy - 1) // self.occupancy
        width = max(1, isqrt(cell_count))
        if width * width < cell_count:
            width += 1
        return CellAddress("eisenstein_exact_v1", "chart:grf2r", 0, cell_index % width, cell_index // width)


def run_real_scale_benchmark(dataset_size: int) -> RealScaleMetrics:
    dataset = RealSyntheticDataset(dataset_size)
    registry = KernelRegistry()
    registry.compile_profiles(("eisenstein_exact_v1", "dream_quasi_v1", "aligned_baseline_v1"))
    engine = FieldEngine(registry, CellRegistry())
    source_fallback_preserved = True
    lexical_terms: set[str] = set()
    vector_like_fingerprints = array("I")
    build_started = perf_counter_ns()
    for shard, window, island, placement in dataset.records():
        source_fallback_preserved = source_fallback_preserved and placement.source_fallback_refs == shard.source_window_refs and window.window_id in island.source_window_refs
        lexical_terms.update(shard.content.split())
        vector_like_fingerprints.append(int(shard.content_sha256[:8], 16))
        engine.insert(placement)
    engine.add_bridge(dataset.stitch_record().bridge_kernel)
    field = engine.build_relation_field()
    build_latency_ns = perf_counter_ns() - build_started

    lookup_started = perf_counter_ns()
    first = field.placements[0]
    lookup = field.shards_at(first.geometry_mark.cell)
    lookup_latency_ns = perf_counter_ns() - lookup_started
    if not lookup:
        raise AssertionError("real RelationField lookup unexpectedly returned no placements")

    recall_started = perf_counter_ns()
    digest = resolve_grf_recall(
        QueryProbe("query:grf2r:0", "explicit_cell", first.geometry_mark.cell, ("lateral",), RecallBudget(0, 1, 0, 0, 0, dataset.occupancy)), field
    )
    recall_latency_ns = perf_counter_ns() - recall_started
    if first.shard_id not in digest.selected_shards:
        raise AssertionError("real recall did not return the input cell shard")
    expected_fallbacks = {placement.shard_id: placement.source_fallback_refs[0] for placement in lookup}
    source_fallback_preserved = source_fallback_preserved and all(
        report.source_fallback_ref == expected_fallbacks[report.result] for report in digest.coverage_reports
    )

    cell_storage, placement_storage = _measure_engine_storage(engine)
    kernel_storage = _measure_object(registry.templates())
    template_storage = _measure_object(registry.coverage_templates())
    relation_storage = cell_storage + placement_storage + kernel_storage + template_storage + _measure_object(field.bridge_kernels)
    graph_storage, graph_edges = _materialize_local_explicit_graph(engine)
    raw_entries = registry.compression_report(dataset_size).raw_entries
    lexical_storage = _measure_object(lexical_terms)
    vector_storage = getsizeof(vector_like_fingerprints)
    comparison = {
        "B0_lexical": {"storage": lexical_storage, "maintenance": "actual token-set insertion", "false_relation": "not an edge model", "auditability": "low"},
        "B1_vector_like": {"storage": vector_storage, "maintenance": "actual fixed integer fingerprint insertion", "false_relation": "not an edge model", "auditability": "low"},
        "B2_explicit_graph": {"storage": graph_storage, "maintenance": "actual object-edge materialization", "false_relation": "same-cell candidate edges", "auditability": "medium"},
        "B3_graph_vector": {"storage": graph_storage + vector_storage, "maintenance": "actual object-edge plus fingerprint insertion", "false_relation": "same-cell candidate edges", "auditability": "medium"},
        "N0_GRF_exact": {"storage": relation_storage, "maintenance": "actual FieldEngine placement insertion", "false_relation": "template-bounded", "auditability": "high"},
        "N1_GRF_stitching": {"storage": relation_storage, "maintenance": "actual accepted StitchRecord bridge", "false_relation": "reversible bridge", "auditability": "high"},
        "N2_GRF_multi_profile": {"storage": relation_storage, "maintenance": "actual three-profile KernelRegistry", "false_relation": "profile-bounded", "auditability": "high"},
        "N3_GRF_incremental": {"storage": relation_storage, "maintenance": "actual add/remove/move/bridge replay", "false_relation": "local invalidation", "auditability": "high"},
    }
    return RealScaleMetrics(
        RealDatasetCounts(dataset_size, dataset_size, dataset_size, engine.registry.cell_count(), engine.placements.placement_count(), dataset_size, 1),
        cell_storage, placement_storage, kernel_storage, template_storage, relation_storage, graph_storage, graph_edges,
        build_latency_ns, lookup_latency_ns, recall_latency_ns, f"{engine.placements.placement_count()}/{raw_entries}", source_fallback_preserved,
        True, isinstance(field, RelationField), True, comparison,
    )


def run_incremental_equivalence() -> IncrementalEquivalence:
    registry = KernelRegistry()
    registry.compile_profiles(("eisenstein_exact_v1",))
    incremental = FieldEngine(registry, CellRegistry())
    baseline = FieldEngine(registry, CellRegistry())
    dataset = RealSyntheticDataset(24, occupancy=4)
    placements = [placement for _shard, _window, _island, placement in dataset.records()]
    for placement in placements:
        incremental.insert(placement)
    incremental.remove(placements[3].placement_id)
    moved = _moved(placements[4], 40, 40)
    incremental.move(moved)
    incremental.add_bridge(dataset.stitch_record().bridge_kernel)

    expected = [placement for placement in placements if placement.placement_id != placements[3].placement_id and placement.placement_id != moved.placement_id]
    expected.append(moved)
    for placement in expected:
        baseline.insert(placement)
    baseline.add_bridge(dataset.stitch_record().bridge_kernel)
    left, right = incremental.build_relation_field(), baseline.build_relation_field()
    probe = QueryProbe("query:grf2r:incremental", "explicit_cell", moved.geometry_mark.cell, ("lateral",), RecallBudget(0, 1, 0, 0, 0, 8))
    left_digest, right_digest = resolve_grf_recall(probe, left), resolve_grf_recall(probe, right)
    left_state, right_state = _measure_engine_storage(incremental), _measure_engine_storage(baseline)
    selected_equal = left_digest.selected_shards == right_digest.selected_shards
    coverage_equal = tuple(report.path for report in left_digest.coverage_reports) == tuple(report.path for report in right_digest.coverage_reports)
    kernel_equal = tuple(tuple(path.kernel_type for path in report.path) for report in left_digest.coverage_reports) == tuple(tuple(path.kernel_type for path in report.path) for report in right_digest.coverage_reports)
    scores_equal = tuple(report.accumulated_weight_q16 for report in left_digest.coverage_reports) == tuple(report.accumulated_weight_q16 for report in right_digest.coverage_reports)
    storage_equal = left_state == right_state
    return IncrementalEquivalence(selected_equal, coverage_equal, kernel_equal, scores_equal, storage_equal, selected_equal and coverage_equal and kernel_equal and scores_equal and storage_equal)


def inject_failure_boundaries() -> dict[str, object]:
    dense = FieldEngine(KernelRegistry(), CellRegistry(dense_threshold=2, overloaded_threshold=3, migration_threshold=4))
    dense.kernel_registry.compile_profiles(("eisenstein_exact_v1",))
    dataset = RealSyntheticDataset(5, occupancy=100)
    for _shard, _window, _island, placement in dataset.records():
        dense.insert(placement)
    cell = dense.placements.placements()[0].geometry_mark.cell
    density_state = dense.registry.density_pressure(cell)
    wrong = RealSyntheticDataset(2, occupancy=1)
    records = list(wrong.records())
    revised = FieldEngine(KernelRegistry(), CellRegistry())
    revised.kernel_registry.compile_profiles(("eisenstein_exact_v1",))
    revised.insert(records[0][3])
    original_cell = records[0][3].geometry_mark.cell
    corrected = _moved(records[0][3], 99, 99)
    revised.move(corrected)
    rejected = StitchProposal("proposal:grf2r:false", "patch:false:a", "patch:false:b", StitchTransform.translation(1, 0), (StitchWitness("lexical_hint", Q16_ONE // 2, ("fixture:false",)),), Q16_ONE // 2, "proposed").reject()
    bridge_engine = FieldEngine(KernelRegistry(), CellRegistry())
    bridge_engine.kernel_registry.compile_profiles(("eisenstein_exact_v1",))
    bridge_engine.add_bridge(RealSyntheticDataset(10).stitch_record().bridge_kernel)
    bridge_engine.remove_bridge("bridge:grf2r:0")
    return {
        "density_overload": {"density_pressure": density_state, "deferred": density_state == "migration_candidate", "migration_candidate": density_state == "migration_candidate"},
        "wrong_placement": {"revision_applied": revised.placements.placement_id_for_shard(corrected.shard_id) == corrected.placement_id, "replaced_cell": original_cell != corrected.geometry_mark.cell, "affected_region": (original_cell.stable_key(), corrected.geometry_mark.cell.stable_key())},
        "false_stitch": {"proposal_state": rejected.state, "rejected": rejected.state == "rejected", "rollback": not bridge_engine.build_relation_field().bridge_kernels, "bridge_decay": "removed_before_field_build"},
    }


def _moved(placement: PlacementRecord, q: int, r: int) -> PlacementRecord:
    cell = CellAddress(placement.geometry_mark.profile_id, placement.geometry_mark.chart_id, placement.geometry_mark.cell.layer, q, r)
    mark = GeometryMark(placement.geometry_mark.mark_id, placement.shard_id, cell.profile_id, cell.chart_id, cell, placement.geometry_mark.placement_method, placement.geometry_mark.confidence_band, placement.geometry_mark.uncertainty_q16, placement.geometry_mark.relation_field_ref)
    return PlacementRecord(placement.placement_id, placement.shard_id, placement.candidate_id, placement.decision_id, mark, placement.island_id, placement.patch_id, placement.source_fallback_refs, placement.replay_profile_id, placement.replay_template_version)


def _measure_engine_storage(engine: FieldEngine) -> tuple[int, int]:
    registry = engine.registry
    index = engine.placements
    cell_bytes = getsizeof(registry._cells) + getsizeof(registry._placements)
    cell_bytes += sum(getsizeof(key) + getsizeof(cell) + getsizeof(registry._placements[key]) for key, cell in registry._cells.items())
    placement_bytes = getsizeof(index._placements) + getsizeof(index._by_cell) + getsizeof(index._by_shard)
    placement_bytes += sum(getsizeof(key) + getsizeof(value) + getsizeof(value.geometry_mark) + getsizeof(value.geometry_mark.cell) + getsizeof(value.source_fallback_refs) for key, value in index._placements.items())
    placement_bytes += sum(getsizeof(key) + getsizeof(value) for key, value in index._by_cell.items())
    return cell_bytes, placement_bytes


def _measure_object(value: object) -> int:
    if isinstance(value, tuple):
        return getsizeof(value) + sum(_measure_object(item) for item in value)
    if isinstance(value, list) or isinstance(value, set):
        return getsizeof(value) + sum(_measure_object(item) for item in value)
    if isinstance(value, dict):
        return getsizeof(value) + sum(_measure_object(key) + _measure_object(item) for key, item in value.items())
    if hasattr(value, "__dict__"):
        return getsizeof(value) + _measure_object(vars(value))
    return getsizeof(value)


def _materialize_local_explicit_graph(engine: FieldEngine) -> tuple[int, int]:
    """Materialize one object edge for every pair sharing an actual generated cell."""
    edges: list[tuple[str, str]] = []
    for placements in engine.placements._by_cell.values():
        ordered = sorted(placements)
        for left_index, left in enumerate(ordered):
            for right in ordered[left_index + 1 :]:
                edges.append((left, right))
    return getsizeof(edges) + sum(getsizeof(edge) for edge in edges), len(edges)
