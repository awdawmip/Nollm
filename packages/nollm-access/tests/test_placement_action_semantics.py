from nollm_access import (
    PLACEMENT_ACTION_SEMANTICS,
    PLACEMENT_ACTION_SEMANTICS_VERSION,
    placement_action_semantics_prompt,
)


def test_semantic_action_contract_is_explicit_without_content_classifier() -> None:
    assert PLACEMENT_ACTION_SEMANTICS_VERSION == "nollm_access_semantic_placement_actions_v1"
    assert tuple(action for action, _meaning in PLACEMENT_ACTION_SEMANTICS) == (
        "reuse", "revision_current", "new_local", "expand_surface", "defer",
    )
    prompt = placement_action_semantics_prompt()
    assert "materially the same current fact" in prompt
    assert "same subject or referent" in prompt
    assert "same proposition slot" in prompt
    assert "explicitly supersedes" in prompt
    assert "different subject with an analogous field" in prompt
    assert "additive fact about the same subject" in prompt
    assert "keywords" not in prompt
