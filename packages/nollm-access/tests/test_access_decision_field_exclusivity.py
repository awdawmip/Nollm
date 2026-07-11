import pytest

from nollm_access import AccessDecision
from nollm_core import AtomHandle, GeometryAddress


def test_unrelated_decision_fields_are_rejected() -> None:
    cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    with pytest.raises(ValueError, match="conflicting"):
        AccessDecision("d", "s", "new", target_cell=cell, existing_handle=AtomHandle(cell, "a"), reason_text="fixture")
