from __future__ import annotations

import os
from pathlib import Path

from nollm.dream_geometry.adapters.snapshot_compaction import (
    expand_snapshot_compaction_projection,
    project_snapshot_compaction,
    validate_snapshot_compaction_projection,
)
from tests.fixtures.dg6.fixture import empty_snapshot, isolated_duplicate_snapshot, isolated_stress_snapshot
from tests.fixtures.dx2.fixture import build_dx2_cycle


def test_dg6_01_empty_snapshot_projects_to_empty_view_and_expands() -> None:
    snapshot = empty_snapshot()
    projection = project_snapshot_compaction(snapshot)

    assert projection.mode == "view_only"
    assert projection.source_snapshot_id == snapshot.snapshot_id
    assert projection.source_trace_ids == ()
    assert projection.compression_plan.input_trace_count == 0
    assert projection.compacted_trace_view.entry_count == 0
    assert validate_snapshot_compaction_projection(snapshot, projection) == projection
    assert expand_snapshot_compaction_projection(snapshot, projection) == ()


def test_dg6_02_real_df1_single_admission_snapshot_projects_and_expands(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)
    admission_id = cycle.admission_ids[:1]
    single = __import__("tests.fixtures.dx2.fixture", fromlist=["assemble_dx2_set"]).assemble_dx2_set(
        cycle.evidence,
        cycle.cortex,
        cycle.admission,
        cycle.orchestrator,
        admission_id,
    ).snapshot

    projection = project_snapshot_compaction(single)

    assert projection.source_trace_ids == tuple(trace.trace_id for trace in single.replayed_traces)
    assert validate_snapshot_compaction_projection(single, projection) == projection
    assert expand_snapshot_compaction_projection(single, projection) == single.replayed_traces


def test_dg6_03_real_dx2_style_multi_admission_snapshot_expands_without_mutating_state(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)
    before = cycle.state_after_assembly

    projection = project_snapshot_compaction(cycle.assembly.snapshot)
    expanded = expand_snapshot_compaction_projection(cycle.assembly.snapshot, projection)

    assert expanded == cycle.assembly.snapshot.replayed_traces
    assert projection.compression_plan.input_trace_count == len(cycle.assembly.snapshot.replayed_traces)
    assert cycle.state_after_assembly == before
    assert cycle.reversed_assembly.snapshot.snapshot_id == cycle.assembly.snapshot.snapshot_id


def test_dg6_04_repeated_projection_is_deterministic() -> None:
    snapshot = isolated_duplicate_snapshot()

    first = project_snapshot_compaction(snapshot)
    second = project_snapshot_compaction(snapshot)

    assert first == second


def test_dg6_05_isolated_synthetic_duplicate_fixture_compacts_and_expands() -> None:
    snapshot = isolated_duplicate_snapshot()
    projection = project_snapshot_compaction(snapshot)

    assert projection.compression_plan.compacted_member_count == 2
    assert projection.compression_plan.output_view_entry_count == 1
    assert projection.compacted_trace_view.entry_count == 1
    assert expand_snapshot_compaction_projection(snapshot, projection) == snapshot.replayed_traces


def test_dg6_16_empty_temporary_cwd_has_no_side_effects(tmp_path) -> None:
    snapshot = isolated_duplicate_snapshot()
    before = _recursive_listing(tmp_path)
    original = Path.cwd()
    try:
        os.chdir(tmp_path)
        projection = project_snapshot_compaction(snapshot)
        validate_snapshot_compaction_projection(snapshot, projection)
        expand_snapshot_compaction_projection(snapshot, projection)
    finally:
        os.chdir(original)
    assert _recursive_listing(tmp_path) == before == ()


def test_dg6_18_stress_fixture_reports_counts_without_persistence_claims() -> None:
    snapshot = isolated_stress_snapshot(1000)
    projection = project_snapshot_compaction(snapshot)

    assert projection.compression_plan.input_trace_count == 1000
    assert projection.compression_plan.compacted_member_count == 400
    assert projection.compression_plan.output_view_entry_count == 800
    assert projection.compression_plan.estimated_view_entry_reduction == 200
    assert expand_snapshot_compaction_projection(snapshot, projection) == snapshot.replayed_traces


def _recursive_listing(root: Path) -> tuple[str, ...]:
    return tuple(sorted(str(path.relative_to(root)) for path in root.rglob("*")))
