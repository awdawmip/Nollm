from __future__ import annotations

import pytest

from nollm.grf.bridge_kernel import BridgeKernel
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.stitching import StitchProposal, StitchRecord, StitchTransform, StitchWitness, can_accept


def witness(kind: str, strength: int = Q16_ONE // 2, refs: tuple[str, ...] = ("shard:a",)) -> StitchWitness:
    return StitchWitness(kind, strength, refs)


def proposal(*witnesses: StitchWitness, confidence: int = Q16_ONE // 2) -> StitchProposal:
    return StitchProposal("proposal_a", "patch_a", "patch_b", StitchTransform.translation(1, 0), witnesses, confidence, "proposed")


def bridge() -> BridgeKernel:
    return BridgeKernel("bridge_a", "patch_a", "patch_b", Q16_ONE // 2, "normal", 2, 3, ("shard:a",))


def test_weak_signals_alone_never_accept() -> None:
    lexical = proposal(witness("lexical_hint"))
    llm = proposal(witness("llm_semantic_suggestion"))
    assert can_accept(lexical) is False
    assert lexical.accept(0).state == "rejected"
    assert can_accept(llm) is False
    assert llm.accept(0).state == "rejected"


def test_strong_and_medium_witnesses_accept_deterministically() -> None:
    strong = proposal(witness("manual_bridge"))
    assert strong.accept(0).state == "accepted"
    medium = proposal(witness("coverage_resonance"), witness("boundary_overlap"), confidence=(Q16_ONE * 3) // 4)
    assert medium.accept(Q16_ONE // 32).state == "accepted"


def test_source_backed_plus_coverage_can_create_stitch_record() -> None:
    accepted = proposal(witness("source_backed_ref"), witness("coverage_resonance")).accept(0)
    record = StitchRecord.from_accepted_proposal("stitch_a", accepted, "validation_fixture", "2026-07-09T10:00:00+08:00", 0, bridge())
    rendered = record.to_mapping()
    assert rendered["reversible"] is True
    assert rendered["not_fact_merge"] is True
    assert rendered["not_parent_child"] is True
    assert rendered["evidence_refs"] == ("shard:a",)


def test_stitch_record_requires_accepted_proposal() -> None:
    with pytest.raises(ValueError):
        StitchRecord.from_accepted_proposal("stitch_bad", proposal(witness("lexical_hint")), "human", "2026-07-09T10:00:00+08:00", 0, bridge())


def test_transform_schema_rejects_unknown_float_and_bridge_mismatch() -> None:
    with pytest.raises(ValueError):
        StitchTransform("unknown", (1,))
    with pytest.raises(TypeError):
        StitchTransform.translation(1.0, 0)  # type: ignore[arg-type]
    accepted = proposal(witness("manual_bridge")).accept(0)
    wrong_bridge = BridgeKernel("bridge_wrong", "patch_x", "patch_b", Q16_ONE // 2, "normal", 2, 3, ("shard:a",))
    with pytest.raises(ValueError):
        StitchRecord.from_accepted_proposal("stitch_wrong", accepted, "human", "2026-07-09T10:00:00+08:00", 0, wrong_bridge)
