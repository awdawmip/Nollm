from __future__ import annotations

import json

import pytest

from nollm_core import (
    ACTIVE_APPROXIMATION_POLICY,
    GeometryAddress,
    CoreRuntime,
    MemoryAtom,
    UnsupportedPhysicalCoverage,
)


def _address(radius: int) -> GeometryAddress:
    return GeometryAddress("default_dream_v1", "default", 0, radius, 0)


def test_public_coverage_policy_describes_storage_and_proven_safe_domains() -> None:
    policy = ACTIVE_APPROXIMATION_POLICY
    assert policy.storage_hex_radius == (1 << 31) - 1
    assert policy.active_writable_hex_radius == (1 << 30) - 1
    assert policy.max_coverage_down_steps == 2
    assert policy.writable_field_contract_id == "nollm_hex_storage_2p31_writable_2p30_depth2_v1"


def test_generic_core_mutation_accepts_storage_valid_research_addresses(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    storage_only = GeometryAddress("default_dream_v1", "default", 7, ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius + 1, 0)
    handle = runtime.put(MemoryAtom("research", "research"), storage_only)
    assert runtime.get(handle).payload_utf8 == "research"


def test_generic_core_move_accepts_storage_valid_target(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    handle = runtime.put(MemoryAtom("existing", "payload"), _address(0))
    storage_only = _address(ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius + 1)
    moved = runtime.move(handle, storage_only)
    assert moved.geometry_address == storage_only
    assert runtime.get(moved).payload_utf8 == "payload"


def test_storage_only_legacy_state_reopens_without_deletion(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    payload = json.loads(runtime.export_state_bytes())
    address = _address(ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius + 1)
    payload["cells"] = [{
        "address": address.to_mapping(),
        "atoms": [{"local_atom_id": "legacy", "atom": {"atom_id": "legacy", "payload_utf8": "preserved"}}],
    }]
    legacy_bytes = (json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    runtime.import_state_bytes(legacy_bytes)
    runtime.close()
    with CoreRuntime(tmp_path) as reopened:
        assert reopened.atoms_at(address)[0][1].payload_utf8 == "preserved"


def test_storage_boundary_coverage_failure_reports_atomic_context() -> None:
    source = _address(ACTIVE_APPROXIMATION_POLICY.storage_hex_radius)
    from nollm_core import expand_physical_coverage

    with pytest.raises(UnsupportedPhysicalCoverage) as captured:
        expand_physical_coverage(source, "coverage_down")
    message = str(captured.value)
    assert "source=" in message
    assert "direction=coverage_down" in message
    assert "required_radius=" in message
    assert "contract_id=nollm_hex_radius_2p31_default_chart_null_phase_v1" in message


@pytest.mark.parametrize(("layer", "direction"), ((-64, "coverage_up"), (64, "coverage_down")))
def test_physical_layer_boundary_reports_unsupported_direction(layer: int, direction: str) -> None:
    from nollm_core import expand_physical_coverage

    with pytest.raises(UnsupportedPhysicalCoverage):
        expand_physical_coverage(GeometryAddress("default_dream_v1", "default", layer, 0, 0), direction)
