import pytest

from nollm_core import KernelRegistry, available_profile_ids, runtime_profile


def test_profile_and_kernel_registry_are_finite_and_stable() -> None:
    assert available_profile_ids() == ("aligned_baseline_v1", "default_dream_v1", "dream_quasi_v1", "eisenstein_exact_v1")
    assert runtime_profile("dream_quasi_v1").runtime_float_allowed is False
    assert not hasattr(runtime_profile("dream_quasi_v1"), "role")
    assert KernelRegistry().identity == KernelRegistry().identity
    with pytest.raises(ValueError, match="unknown profile_id"):
        runtime_profile("unknown")


def test_packaged_registry_preserves_existing_state_identity() -> None:
    # Existing saved fields use these v5/v6 identities. Reusing parsed templates
    # must leave their storage interpretation unchanged.
    identity = KernelRegistry().state_identity
    assert identity["kernel_registry_version"] == "nollm_geometry_kernels_v5"
    assert identity["kernel_registry_id"] == "34d7d98c53d1bea0f1f2ac4f879a571183bf60b2ae7ae1fa1fbe44841940928f"
    assert identity["profile_registry_version"] == "nollm_geometry_profiles_v6"
    assert identity["profile_registry_id"] == "0041efb20e892978f4d57cbc396df8d6a3cd652987b6f4a77417b44580333d74"
