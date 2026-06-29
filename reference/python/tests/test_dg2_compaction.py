from dataclasses import replace

from nollm.dream_geometry.field import compact_traces, expand_compaction
from nollm.dream_geometry.protocol.contracts import TraceState
from tests.test_dg2_cover_lifecycle import _trace


def test_dg2_p1_p2_compatible_traces_compact_and_expand_losslessly() -> None:
    first = _trace("t1", "location", "s1")
    second = replace(first, trace_id="t2")
    compacted = compact_traces((second, first))
    assert len(compacted) == 1
    assert compacted[0].member_trace_ids == ("t1", "t2")
    expanded = expand_compaction(compacted[0], {"t1": first, "t2": second})
    assert tuple(trace.trace_id for trace in expanded) == ("t1", "t2")
    assert compacted[0].aggregate_mass == first.mass + second.mass


def test_dg2_p3_different_boundaries_do_not_merge() -> None:
    base = _trace("t1", "location", "s1")
    variants = (
        replace(base, trace_id="shard", origin_shard_id="other"),
        replace(base, trace_id="proposal", proposal_id="other"),
        replace(base, trace_id="parent", parent_trace_id="other"),
        replace(base, trace_id="axis", axis="other"),
        replace(base, trace_id="support", support_key="other"),
    )
    for variant in variants:
        assert compact_traces((base, variant)) == ()


def test_dg2_p4_states_do_not_mix() -> None:
    base = _trace("t1", "location", "s1")
    proposed = replace(base, trace_id="t2", state=TraceState.proposed)
    archived = replace(base, trace_id="t3", state=TraceState.archived)
    assert compact_traces((base, proposed, archived)) == ()


def test_dg2_p6_order_invariance_and_no_mutation_api() -> None:
    first = _trace("t1", "location", "s1")
    second = replace(first, trace_id="t2")
    assert compact_traces((first, second))[0].compaction_id == compact_traces((second, first))[0].compaction_id
    assert not hasattr(compact_traces((first, second))[0], "delete_compacted_members")
