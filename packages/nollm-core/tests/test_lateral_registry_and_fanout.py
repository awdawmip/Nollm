import pytest

from nollm_core import KernelRegistry, validate_lateral_ring


def test_lateral_is_registered_and_ring_two_rejected() -> None:
    registry = KernelRegistry()
    assert len(registry.templates()) == 33
    assert len(registry.coverage_template("eisenstein_exact_v1", "lateral").entries) == 6
    validate_lateral_ring(1)
    with pytest.raises(ValueError, match="fanout"):
        validate_lateral_ring(2)
