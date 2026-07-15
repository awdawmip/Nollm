from __future__ import annotations

import pytest

from nollm_access import (
    ACTIVE_SEMANTIC_WRITE_POLICY,
    AccessDecision,
    ActiveSemanticWritePolicyError,
)
from nollm_core import ACTIVE_APPROXIMATION_POLICY, AtomHandle, GeometryAddress


def test_access_rejects_unsafe_new_target_during_decision_preflight() -> None:
    target = GeometryAddress(
        "default_dream_v1",
        "default",
        0,
        ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius + 1,
        0,
    )
    with pytest.raises(ActiveSemanticWritePolicyError, match="hex_radius"):
        AccessDecision("decision", "statement", "new", target, reason_text="host selected target")


@pytest.mark.parametrize(
    "target,field",
    (
        (GeometryAddress("default_dream_v1", "default", 1, 0, 0), "layer"),
        (GeometryAddress("eisenstein_exact_v1", "research", 0, 0, 0), "profile_id"),
    ),
)
def test_access_policy_rejects_nonactive_semantic_planes(target: GeometryAddress, field: str) -> None:
    with pytest.raises(ActiveSemanticWritePolicyError) as captured:
        ACTIVE_SEMANTIC_WRITE_POLICY.validate(target)
    assert captured.value.field == field


def test_revision_current_rejects_handle_outside_active_semantic_plane() -> None:
    handle = AtomHandle(GeometryAddress("default_dream_v1", "default", 1, 0, 0), "atom")
    with pytest.raises(ActiveSemanticWritePolicyError, match="layer"):
        AccessDecision(
            "revision",
            "statement",
            "revision_current",
            existing_handle=handle,
            reason_text="host selected revision",
        )
