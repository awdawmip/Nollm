from __future__ import annotations

import json

import pytest

from nollm_core import (
    ACTIVE_APPROXIMATION_POLICY,
    GeometryAddress,
    CoreRuntime,
    MemoryAtom,
    MoveCommand,
    PutCommand,
    UnsupportedPhysicalCoverage,
    UnsafeWritableAddress,
    validate_active_writable_address,
)


def _address(radius: int) -> GeometryAddress:
    return GeometryAddress("default_dream_v1", "default", 0, radius, 0)


def test_public_policy_separates_storage_and_writable_domains() -> None:
    policy = ACTIVE_APPROXIMATION_POLICY
    assert policy.storage_hex_radius == (1 << 31) - 1
    assert policy.active_writable_hex_radius == (1 << 30) - 1
    assert policy.max_coverage_down_steps == 2
    assert policy.writable_field_contract_id == "nollm_hex_storage_2p31_writable_2p30_depth2_v1"
    assert validate_active_writable_address(_address(policy.active_writable_hex_radius))
    with pytest.raises(UnsafeWritableAddress) as captured:
        validate_active_writable_address(_address(policy.active_writable_hex_radius + 1))
    assert captured.value.required_radius == policy.active_writable_hex_radius + 1


def test_batch_rejects_every_unsafe_target_before_any_write(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    safe = _address(0)
    unsafe = _address(ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius + 1)
    before = runtime.export_state_bytes()
    with pytest.raises(UnsafeWritableAddress):
        runtime.apply_batch((
            PutCommand(MemoryAtom("safe", "safe"), safe),
            PutCommand(MemoryAtom("unsafe", "unsafe"), unsafe),
        ))
    assert runtime.export_state_bytes() == before
    assert runtime.placement_count() == 0


def test_move_rejection_preserves_existing_handle(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    handle = runtime.put(MemoryAtom("existing", "payload"), _address(0))
    before = runtime.export_state_bytes()
    unsafe = _address(ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius + 1)
    with pytest.raises(UnsafeWritableAddress):
        runtime.apply_batch((MoveCommand(handle, unsafe),))
    assert runtime.export_state_bytes() == before
    assert runtime.get(handle).payload_utf8 == "payload"


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
