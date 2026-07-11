from nollm_core import KernelRegistry
from nollm_core.profiles import profile_registry_digest


def test_profile_and_kernel_identities_are_deterministic() -> None:
    assert profile_registry_digest() == profile_registry_digest()
    assert KernelRegistry().state_identity["profile_registry_id"] == profile_registry_digest()
