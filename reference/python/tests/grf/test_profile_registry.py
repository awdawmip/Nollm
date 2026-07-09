from __future__ import annotations

import pytest

from nollm.grf.profiles import get_profile, performance_profile, profiles


def test_profile_roles_are_explicit() -> None:
    by_id = {profile.profile_id: profile for profile in profiles()}
    assert by_id["eisenstein_exact_v1"].role == "production_candidate"
    assert by_id["aligned_baseline_v1"].role == "baseline"
    assert by_id["dream_quasi_v1"].role == "research"
    assert performance_profile().profile_id == "eisenstein_exact_v1"
    assert performance_profile().profile_id != "dream_quasi_v1"


def test_exact_and_baseline_runtime_flags_disallow_float_and_polygon() -> None:
    for profile_id in ("eisenstein_exact_v1", "aligned_baseline_v1"):
        profile = get_profile(profile_id)
        assert profile.runtime_float_allowed is False
        assert profile.runtime_polygon is False


def test_unknown_profile_rejected() -> None:
    with pytest.raises(ValueError):
        get_profile("dream_quasi_default_performance")
