from __future__ import annotations

from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.stitching import StitchProposal, StitchTransform, StitchWitness


FALSE_FRIENDS = {
    "A": "Apple company released an update",
    "B": "apple fruit storage temperature",
    "C": "Apple company privacy policy",
}


def test_false_friend_lexical_hint_is_preserved_as_rejected_anti_stitch() -> None:
    assert "apple" in FALSE_FRIENDS["A"].lower()
    assert "apple" in FALSE_FRIENDS["B"].lower()
    lexical = StitchWitness("lexical_hint", Q16_ONE // 2, ("A", "B"))
    proposal = StitchProposal("proposal_ab", "patch_a", "patch_b", StitchTransform.translation(0, 0), (lexical,), Q16_ONE // 2, "proposed")
    rejected = proposal.accept(0)
    assert rejected.state == "rejected"
    assert rejected.to_mapping()["witnesses"][0]["refs"] == ("A", "B")


def test_company_fixture_can_accept_with_source_backed_or_manual_witness() -> None:
    source = StitchWitness("source_backed_ref", Q16_ONE, ("A", "C"))
    proposal = StitchProposal("proposal_ac", "patch_a", "patch_c", StitchTransform.translation(1, 0), (source,), Q16_ONE, "proposed")
    assert proposal.accept(0).state == "accepted"
