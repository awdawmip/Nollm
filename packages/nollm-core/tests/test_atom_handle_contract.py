from dataclasses import fields

from nollm_core import AtomHandle, GeometryAddress, MemoryAtom


def test_minimal_atom_and_addressed_handle_contracts() -> None:
    assert [field.name for field in fields(MemoryAtom)] == ["atom_id", "payload_utf8"]
    assert [field.name for field in fields(AtomHandle)] == ["geometry_address", "local_atom_id"]
    address = GeometryAddress("exact", "chart", 2, -17, 9)
    handle = AtomHandle(address, "local-a")
    assert handle.geometry_address.stable_key() == ("exact", "chart", 2, -17, 9, "")
    assert address.partition_id() == (-1, 0)
    assert GeometryAddress.from_mapping(address.to_mapping()) == address


def test_same_atom_id_is_valid_in_independent_core_instances(tmp_path) -> None:
    from nollm_core import CoreRuntime

    cell = GeometryAddress("exact", "chart", 0, 0, 0)
    first = CoreRuntime(tmp_path / "first")
    second = CoreRuntime(tmp_path / "second")
    assert first.put(MemoryAtom("same-id", "first"), cell) == second.put(MemoryAtom("same-id", "second"), cell)
    assert first.state_bytes() != second.state_bytes()
