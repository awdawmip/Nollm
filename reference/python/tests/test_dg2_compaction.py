from dataclasses import replace

import pytest

from nollm.dream_geometry.field import compact_traces, expand_compaction
from nollm.dream_geometry.field.types import TraceCompaction
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


def test_dg2_1_t204_duplicate_trace_id_rejected_for_compaction() -> None:
    trace = _trace("same", "location", "s1")
    with pytest.raises(ValueError, match="duplicate trace_id"):
        compact_traces((trace, trace))
    forged = replace(trace, axis="phenomenon", support_key="s2")
    with pytest.raises(ValueError, match="duplicate trace_id"):
        compact_traces((trace, forged))


def test_dg2_1_t208_expand_rejects_bad_manifest() -> None:
    first = _trace("t1", "location", "s1")
    second = replace(first, trace_id="t2")
    duplicate_manifest = _forge_compaction(("t1", "t2"), ("t1", "t1"))
    missing_manifest = TraceCompaction("c2", ("missing", "t1"), "k", first.mass, ("missing", "t1"))
    with pytest.raises(ValueError, match="duplicate trace_id"):
        expand_compaction(duplicate_manifest, {"t1": first, "t2": second})
    with pytest.raises(ValueError, match="missing trace_id"):
        expand_compaction(missing_manifest, {"t1": first})


def test_dg2_2_t213_compaction_manifest_must_match_members() -> None:
    first = _trace("t1", "location", "s1")
    second = replace(first, trace_id="t2")
    trace_index = {"t1": first, "t2": second}
    with pytest.raises(ValueError, match="manifest"):
        TraceCompaction("missing-member", ("t1", "t2"), "k", first.mass + second.mass, ("t1",))
    with pytest.raises(ValueError, match="canonical"):
        TraceCompaction("bad-order", ("t2", "t1"), "k", first.mass + second.mass, ("t2", "t1"))
    with pytest.raises(ValueError, match="duplicate trace_id"):
        TraceCompaction("duplicate-member", ("t1", "t1"), "k", first.mass + second.mass, ("t1", "t1"))
    with pytest.raises(ValueError, match="manifest"):
        expand_compaction(_forge_compaction(("t1", "t2"), ("t1",)), trace_index)
    with pytest.raises(ValueError, match="canonical"):
        expand_compaction(_forge_compaction(("t1", "t2"), ("t2", "t1")), trace_index)
    with pytest.raises(ValueError, match="duplicate trace_id"):
        expand_compaction(_forge_compaction(("t1", "t2"), ("t1", "t1")), trace_index)


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


def _forge_compaction(member_trace_ids: tuple[str, ...], expansion_manifest: tuple[str, ...]) -> TraceCompaction:
    forged = object.__new__(TraceCompaction)
    object.__setattr__(forged, "compaction_id", "forged")
    object.__setattr__(forged, "member_trace_ids", member_trace_ids)
    object.__setattr__(forged, "canonical_key", "k")
    object.__setattr__(forged, "aggregate_mass", 0.6)
    object.__setattr__(forged, "expansion_manifest", expansion_manifest)
    return forged
