import pytest

from nollm_core import KernelRegistry


def test_runtime_registry_rejects_noncanonical_fanout() -> None:
    with pytest.raises(ValueError, match="canonical compiled"):
        KernelRegistry(8)
