"""Compatibility entrypoint for the active bounded approximate Coverage kernel."""

from .approximate_coverage import clear_approximate_coverage_cache, expand_approximate_coverage
from .coverage_contract import (
    ACTIVE_APPROXIMATION_POLICY,
    AmbiguousPhysicalCoverage,
    ApproximateCoveragePolicy,
    PhysicalCoverageExpansion,
    PhysicalCoverageMember,
    UnsupportedPhysicalCoverage,
    UnsafeWritableAddress,
    validate_active_writable_address,
)


expand_physical_coverage = expand_approximate_coverage
clear_physical_coverage_cache = clear_approximate_coverage_cache


__all__ = [
    "ACTIVE_APPROXIMATION_POLICY",
    "AmbiguousPhysicalCoverage",
    "ApproximateCoveragePolicy",
    "PhysicalCoverageExpansion",
    "PhysicalCoverageMember",
    "UnsupportedPhysicalCoverage",
    "UnsafeWritableAddress",
    "clear_physical_coverage_cache",
    "expand_physical_coverage",
    "validate_active_writable_address",
]
