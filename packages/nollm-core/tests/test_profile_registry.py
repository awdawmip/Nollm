import pytest

from nollm_core import KernelRegistry, get_profile, profiles


def test_profile_and_kernel_registry_are_finite_and_stable() -> None:
    assert tuple(profile.profile_id for profile in profiles()) == ("aligned_baseline_v1", "dream_quasi_v1", "eisenstein_exact_v1")
    assert KernelRegistry().identity == KernelRegistry().identity
    with pytest.raises(ValueError, match="unknown profile_id"):
        get_profile("unknown")
