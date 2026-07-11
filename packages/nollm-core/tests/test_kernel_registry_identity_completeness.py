from nollm_core import KernelRegistry


def test_fanout_changes_registry_identity() -> None:
    assert KernelRegistry(7).identity != KernelRegistry(8).identity
