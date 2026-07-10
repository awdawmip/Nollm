from __future__ import annotations

from nollm.grf.readiness_validation import core_readiness


def test_core_geometry_and_kernel_are_ready_without_terminal_dependencies() -> None:
    assert all(core_readiness().values())
