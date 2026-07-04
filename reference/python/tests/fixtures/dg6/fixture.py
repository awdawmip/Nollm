from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.assembly.types import FieldAssemblyPolicy, FiniteFieldSnapshot, policy_identity, snapshot_fingerprint_payload, stable_fingerprint
from nollm.dream_geometry.field.gravity import calculate_gravity_snapshot
from nollm.dream_geometry.field.types import GravityPolicy
from tests.fixtures.dg5.fixture import exact_duplicate_pair, stress_fixture, trace


def empty_snapshot() -> FiniteFieldSnapshot:
    snapshot = FiniteFieldSnapshot(
        snapshot_id="",
        assembly_id="dg6_empty_snapshot",
        policy_identity=policy_identity(FieldAssemblyPolicy()),
        geometry_profile_id="da1_sealed_default_v1",
        field_policy_identity="da1_sealed_default_v1|dg2_cover_policy:cover_policy:v2:a2d647c2e140e8629ddf4fa1352e8bda|dg2_gravity_policy:1",
        admission_manifest=(),
        replayed_traces=(),
        trace_residuals=(),
        coarse_covers=(),
        coverage_up=(),
        coverage_down=(),
        verified_chart_links=(),
        gravity_snapshot=calculate_gravity_snapshot((), GravityPolicy()),
        source_admission_ids=(),
    )
    return _seal_snapshot(snapshot)


def isolated_duplicate_snapshot() -> FiniteFieldSnapshot:
    first, second = exact_duplicate_pair()
    snapshot = replace(
        empty_snapshot(),
        assembly_id="dg6_isolated_duplicate_fixture",
        replayed_traces=tuple(sorted((first, second), key=lambda item: item.trace_id)),
    )
    return _seal_snapshot(snapshot)


def isolated_stress_snapshot(count: int = 1000) -> FiniteFieldSnapshot:
    snapshot = replace(
        empty_snapshot(),
        assembly_id="dg6_isolated_stress_fixture",
        replayed_traces=tuple(sorted(stress_fixture(count), key=lambda item: item.trace_id)),
    )
    return _seal_snapshot(snapshot)


def single_trace_snapshot() -> FiniteFieldSnapshot:
    snapshot = replace(
        empty_snapshot(),
        assembly_id="dg6_single_trace_fixture",
        replayed_traces=(trace("dg6-single", support_key="single"),),
    )
    return _seal_snapshot(snapshot)


def _seal_snapshot(snapshot: FiniteFieldSnapshot) -> FiniteFieldSnapshot:
    return replace(snapshot, snapshot_id=stable_fingerprint(snapshot_fingerprint_payload(snapshot)))
