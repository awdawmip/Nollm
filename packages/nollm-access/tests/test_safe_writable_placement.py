from __future__ import annotations

import pytest

from nollm_access import AccessDecision
from nollm_core import ACTIVE_APPROXIMATION_POLICY, GeometryAddress, UnsafeWritableAddress


def test_access_rejects_unsafe_new_target_during_decision_preflight() -> None:
    target = GeometryAddress(
        "default_dream_v1",
        "default",
        0,
        ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius + 1,
        0,
    )
    with pytest.raises(UnsafeWritableAddress):
        AccessDecision("decision", "statement", "new", target, reason_text="host selected target")
