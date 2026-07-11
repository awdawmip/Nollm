import pytest

from nollm_core import KernelRegistry, available_profile_ids, runtime_profile


def test_profile_and_kernel_registry_are_finite_and_stable() -> None:
    assert available_profile_ids() == ("aligned_baseline_v1", "dream_quasi_v1", "eisenstein_exact_v1")
    assert runtime_profile("dream_quasi_v1").runtime_float_allowed is False
    assert not hasattr(runtime_profile("dream_quasi_v1"), "role")
    assert KernelRegistry().identity == KernelRegistry().identity
    with pytest.raises(ValueError, match="unknown profile_id"):
        runtime_profile("unknown")


def test_compiled_artifact_digest_is_checked(monkeypatch) -> None:
    import nollm_core.kernel_registry as module

    monkeypatch.setattr(module, "COMPILED_TEMPLATES_JSON", b"{}\n")
    with pytest.raises(ValueError, match="artifact digest mismatch"):
        KernelRegistry()
