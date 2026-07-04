from __future__ import annotations

from dataclasses import replace

import pytest

from nollm.dream_geometry.compression import CompressionPlanningError, CompressionPolicy, plan_trace_compaction
from nollm.dream_geometry.compression.view import build_compacted_trace_view, expand_compression_plan
from tests.fixtures.dg5.fixture import exact_duplicate_pair, mixed_fixture, trace, trace_index


def test_dg5_01_empty_input_is_stable_noop() -> None:
    plan = plan_trace_compaction(())
    view = build_compacted_trace_view(plan, {})
    assert plan.input_trace_count == 0
    assert plan.output_view_entry_count == 0
    assert plan.estimated_view_entry_reduction == 0
    assert view.entry_count == 0
    assert expand_compression_plan(plan, {}) == ()


def test_dg5_02_exact_duplicate_transport_views_compact_and_expand_losslessly() -> None:
    traces = exact_duplicate_pair()
    plan = plan_trace_compaction(tuple(reversed(traces)))
    view = build_compacted_trace_view(plan, trace_index(traces))
    expanded = expand_compression_plan(plan, trace_index(traces))
    assert plan.compacted_member_count == 2
    assert plan.output_view_entry_count == 1
    assert view.entries[0].entry_kind == "compacted_transport_view"
    assert view.entries[0].member_trace_ids == ("dup-a", "dup-b")
    assert tuple(trace.trace_id for trace in expanded) == ("dup-a", "dup-b")
    assert expanded == traces


def test_dg5_03_passthrough_trace_remains_independent() -> None:
    single = (trace("solo"),)
    plan = plan_trace_compaction(single)
    view = build_compacted_trace_view(plan, trace_index(single))
    assert plan.compactions == ()
    assert plan.passthrough_trace_ids == ("solo",)
    assert view.entries[0].entry_kind == "passthrough_trace_view"


def test_dg5_04_mixed_fixture_compacts_only_exact_duplicate_group() -> None:
    traces = mixed_fixture()
    plan = plan_trace_compaction(traces)
    view = build_compacted_trace_view(plan, trace_index(traces))
    assert tuple(compaction.member_trace_ids for compaction in plan.compactions) == (("dup-a", "dup-b"),)
    assert set(plan.passthrough_trace_ids) == {"collision-a", "pass-a", "same-cell-distinct"}
    assert view.source_trace_count == 5
    assert view.entry_count == 4


def test_dg5_05_input_permutation_is_deterministic() -> None:
    traces = mixed_fixture()
    first = plan_trace_compaction(traces)
    second = plan_trace_compaction(tuple(reversed(traces)))
    assert first.plan_fingerprint == second.plan_fingerprint
    assert first.input_trace_ids == second.input_trace_ids
    first_view = build_compacted_trace_view(first, trace_index(traces))
    second_view = build_compacted_trace_view(second, trace_index(traces))
    assert first_view.view_fingerprint == second_view.view_fingerprint
    assert first_view.entries == second_view.entries


def test_dg5_06_repeated_planning_is_deterministic() -> None:
    traces = mixed_fixture()
    assert plan_trace_compaction(traces) == plan_trace_compaction(traces)


def test_dg5_07_shared_support_distinct_identity_does_not_compact() -> None:
    base = trace("base", support_key="same")
    distinct = replace(base, trace_id="distinct", origin_shard_id="other")
    assert plan_trace_compaction((base, distinct)).compactions == ()


def test_dg5_08_same_cell_different_payload_does_not_compact() -> None:
    base = trace("base")
    distinct = replace(base, trace_id="distinct", proposal_id="other")
    assert plan_trace_compaction((base, distinct)).compactions == ()


def test_dg5_08b_derivation_kind_difference_does_not_compact() -> None:
    base = trace("base")
    distinct = replace(base, trace_id="distinct", derivation_kind="other-derivation")
    assert plan_trace_compaction((base, distinct)).compactions == ()


def test_dg5_09_duplicate_trace_id_is_structured_error() -> None:
    base = trace("same")
    with pytest.raises(CompressionPlanningError) as exc:
        plan_trace_compaction((base, replace(base, origin_shard_id="other")))
    assert exc.value.reason_code == "DG5_DUPLICATE_TRACE_ID"


def test_dg5_10_invalid_policy_is_rejected() -> None:
    with pytest.raises(CompressionPlanningError) as exc:
        CompressionPolicy(mode="persistent")
    assert exc.value.reason_code == "DG5_INVALID_POLICY"
    with pytest.raises(CompressionPlanningError):
        CompressionPolicy(require_exact_transport_identity=False)
