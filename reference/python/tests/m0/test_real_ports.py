from __future__ import annotations

from pathlib import Path

import pytest

from nollm.grf import (
    BridgeKernel,
    CellAddress,
    FieldEngine,
    GeometryMark,
    GRFFacade,
    GRFWorkspaceConsistentStateAdapter,
    PlacementRecord,
    QueryProbe,
    RecallBudget,
    resolve_grf_recall,
)
from nollm.grf.fixed_point import Q16_ONE
from nollm_core import NullTraceSink, TraceEvent
from nollm_snapshot import SnapshotService
from nollm_trace import CompositeTraceSink, MemoryTraceSink


RECORDED_AT = "2026-07-11T00:00:00Z"


class FailingTraceSink:
    def emit(self, event: TraceEvent) -> None:
        raise RuntimeError(event.name)


class FailingExportAdapter(GRFWorkspaceConsistentStateAdapter):
    def export_state(self, token: object) -> bytes:
        super().export_state(token)
        raise RuntimeError("forced export failure")


def placement(
    placement_id: str,
    shard_id: str,
    patch_id: str,
    layer: int,
    q: int,
    r: int,
) -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart_m0c1", layer, q, r)
    mark = GeometryMark(
        "mark:" + placement_id,
        shard_id,
        "eisenstein_exact_v1",
        "chart_m0c1",
        cell,
        "host_explicit",
        "high",
        0,
        "m0c1:test",
    )
    return PlacementRecord(
        placement_id,
        shard_id,
        "candidate:" + placement_id,
        "decision:" + placement_id,
        mark,
        "island:" + shard_id,
        patch_id,
        ("source:" + shard_id,),
        "eisenstein_exact_v1",
        "m0c1_real_port_v1",
    )


def populated_workspace(path: Path) -> tuple[GRFFacade, str]:
    facade = GRFFacade(path)
    receipt = facade.capture_text(
        "capture:m0c1:utf8",
        "原始证据：negative coordinates stay reversible.",
        "window:m0c1:utf8",
        RECORDED_AT,
    )
    assert receipt.shard_id is not None
    cell = CellAddress("eisenstein_exact_v1", "chart_m0c1", 2, -17, 9)
    facade.store.write_placement_record(
        placement(
            "placement:m0c1:negative",
            receipt.shard_id,
            "patch:m0c1:negative",
            cell.layer,
            cell.q,
            cell.r,
        ),
        RECORDED_AT,
    )
    facade.admit_existing_placement(
        receipt.shard_id,
        cell,
        "placement:m0c1:negative",
        RECORDED_AT,
        "validation_fixture",
    )
    return facade, receipt.shard_id


def test_snapshot_port_round_trips_real_grf_workspace(tmp_path: Path) -> None:
    facade, shard_id = populated_workspace(tmp_path / "source")
    service = SnapshotService()
    source_port = GRFWorkspaceConsistentStateAdapter(facade.workspace)

    payload = service.create(source_port)
    restored_root = tmp_path / "restored"
    service.restore(GRFWorkspaceConsistentStateAdapter(restored_root), payload)
    restored = GRFFacade(restored_root)

    assert restored.validate_workspace() == facade.validate_workspace()
    assert restored.get_source(shard_id) == "原始证据：negative coordinates stay reversible."
    assert service.verify(GRFWorkspaceConsistentStateAdapter(restored_root), payload)
    assert not service.structural_diff(
        payload,
        service.create(GRFWorkspaceConsistentStateAdapter(restored_root)),
    )


def test_snapshot_clone_and_facade_snapshot_are_structurally_equivalent(tmp_path: Path) -> None:
    facade, _ = populated_workspace(tmp_path / "source")
    service = SnapshotService()
    payload = service.clone(
        GRFWorkspaceConsistentStateAdapter(facade.workspace),
        GRFWorkspaceConsistentStateAdapter(tmp_path / "clone"),
    )
    legacy_snapshot = facade.snapshot(tmp_path / "legacy-snapshot")
    legacy_restore = GRFFacade.restore(legacy_snapshot, tmp_path / "legacy-restore")

    assert service.create(GRFWorkspaceConsistentStateAdapter(tmp_path / "clone")) == payload
    assert service.create(GRFWorkspaceConsistentStateAdapter(legacy_snapshot)) == payload
    assert legacy_restore.validate_workspace() == facade.validate_workspace()


def test_snapshot_failures_release_read_and_preserve_workspace(tmp_path: Path) -> None:
    facade, shard_id = populated_workspace(tmp_path / "source")
    failing = FailingExportAdapter(facade.workspace)

    with pytest.raises(RuntimeError, match="forced export failure"):
        SnapshotService().create(failing)

    token = failing.begin_consistent_read()
    failing.end_consistent_read(token)
    with pytest.raises(ValueError, match="invalid GRF workspace snapshot"):
        SnapshotService().restore(
            GRFWorkspaceConsistentStateAdapter(facade.workspace),
            b"not-a-zip",
        )
    assert facade.get_source(shard_id) == "原始证据：negative coordinates stay reversible."


def run_real_trace_sequence(sink: object) -> tuple[object, ...]:
    engine = FieldEngine(trace_sink=sink)
    first = placement("placement:a", "shard:a", "patch:a", 1, -2, 3)
    second = placement("placement:b", "shard:b", "patch:b", 1, -1, 3)
    moved_second = placement("placement:b", "shard:b", "patch:b", 1, 0, 3)
    temporary = placement("placement:temporary", "shard:temporary", "patch:t", 1, 4, -5)
    bridge = BridgeKernel(
        "bridge:a-b",
        "patch:a",
        "patch:b",
        Q16_ONE // 2,
        "normal",
        1,
        2,
        ("shard:a", "shard:b"),
    )

    engine.insert(first)
    engine.insert(second)
    engine.insert(temporary)
    engine.move(moved_second)
    engine.add_bridge(bridge)
    field = engine.build_relation_field()
    query = QueryProbe(
        "query:m0c1",
        "explicit_cell",
        first.geometry_mark.cell,
        ("lateral", "bridge"),
        RecallBudget(2, 16, 2, 1, 2, 16),
    )
    digest = resolve_grf_recall(query, field)
    relation_output = field.step(
        _activation(first.geometry_mark.cell),
        ("lateral", "bridge"),
        1,
        2,
    )
    engine.remove("placement:temporary")
    engine.remove_bridge(bridge.bridge_id)
    final_field = engine.build_relation_field()
    return (
        engine.cells.all(),
        engine.cells.placement_count(),
        final_field.bridge_kernels,
        digest,
        relation_output,
    )


def _activation(cell: CellAddress):
    from nollm.grf.propagation import SparseActivation

    return SparseActivation(cell, Q16_ONE, "m0c1:entry")


def test_real_core_trace_is_optional_and_failure_isolated() -> None:
    null_result = run_real_trace_sequence(NullTraceSink())
    memory = MemoryTraceSink()
    memory_result = run_real_trace_sequence(memory)
    failing_result = run_real_trace_sequence(FailingTraceSink())
    composite_memory = MemoryTraceSink()
    composite_result = run_real_trace_sequence(
        CompositeTraceSink(FailingTraceSink(), composite_memory)
    )

    assert null_result == memory_result == failing_result == composite_result
    names = {event.name for event in memory.events}
    assert {
        "cell.insert",
        "cell.remove",
        "cell.move",
        "field.bridge.add",
        "field.bridge.remove",
        "relation.step",
    } <= names
    assert composite_memory.events
