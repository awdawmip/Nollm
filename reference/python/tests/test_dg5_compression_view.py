from __future__ import annotations

from pathlib import Path

from nollm.dream_geometry.compression import plan_trace_compaction
from nollm.dream_geometry.compression.fingerprint import trace_fingerprint
from nollm.dream_geometry.compression.view import build_compacted_trace_view, expand_compression_plan
from tests.fixtures.dg5.fixture import state_dirs, stress_fixture, trace_index


def test_dg5_16_finite_stress_fixture_reports_real_counts() -> None:
    traces = stress_fixture(1000)
    plan = plan_trace_compaction(traces)
    view = build_compacted_trace_view(plan, trace_index(traces))
    assert plan.input_trace_count == 1000
    assert plan.compacted_member_count == 400
    assert len(plan.compactions) == 200
    assert len(plan.passthrough_trace_ids) == 600
    assert view.entry_count == 800
    assert plan.estimated_view_entry_reduction == 200


def test_dg5_17_stress_expansion_preserves_each_trace_fingerprint() -> None:
    traces = stress_fixture(1000)
    plan = plan_trace_compaction(traces)
    expanded = expand_compression_plan(plan, trace_index(traces))
    assert tuple(trace.trace_id for trace in expanded) == plan.input_trace_ids
    original = trace_index(traces)
    for trace in expanded:
        assert trace_fingerprint(trace) == trace_fingerprint(original[trace.trace_id])


def test_dg5_18_no_durable_state_dirs_created(tmp_path: Path) -> None:
    before = state_dirs(tmp_path)
    traces = stress_fixture(20)
    plan = plan_trace_compaction(traces)
    _ = build_compacted_trace_view(plan, trace_index(traces))
    _ = expand_compression_plan(plan, trace_index(traces))
    after = state_dirs(tmp_path)
    assert before == after == {name: False for name in ("evidence", "capture", "field", "admission", "assembly", "recall", "atlas", "state")}

