from __future__ import annotations

from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.replay import load_all_grf_objects
from nollm.grf.stitching import StitchProposal, StitchTransform, StitchWitness
from nollm.grf.storage import GRFFileStore


def test_rejected_stitch_survives_reload_as_anti_stitch_evidence(tmp_path) -> None:
    lexical = StitchWitness("lexical_hint", Q16_ONE // 2, ("Apple company", "apple fruit"))
    rejected = StitchProposal("proposal_false_friend", "patch_company", "patch_fruit", StitchTransform.translation(0, 0), (lexical,), Q16_ONE // 2, "proposed").accept(0)
    store = GRFFileStore(tmp_path)
    store.write_stitch_proposal(rejected)
    loaded = load_all_grf_objects(tmp_path)["rejected_stitch_proposals"]
    assert len(loaded) == 1
    assert loaded[0].state == "rejected"
    assert loaded[0].proposal_id == "proposal_false_friend"
