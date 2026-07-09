from __future__ import annotations

from nollm.grf.kernel_registry import KernelRegistry


def test_kernel_registry_compression_is_independent_from_shard_count() -> None:
    registry = KernelRegistry()
    registry.compile_profiles(("eisenstein_exact_v1", "dream_quasi_v1", "aligned_baseline_v1"))

    small = registry.compression_report(10_000)
    large = registry.compression_report(1_000_000)

    assert small.compressed_size == large.compressed_size
    assert small.raw_entries == large.raw_entries
    assert small.reconstruction_error == 0
    assert small.kernel_count == 15
    assert registry.digest() == registry.digest()
