import json

import pytest

from nollm_core import BridgeSpec, CoreRuntime, GeometryAddress, GeometryAnchor, MemoryAtom
from nollm_core.storage import canonical_state_bytes


def test_reversed_cells_atoms_and_empty_cells_are_rejected(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    for q in (0, 1):
        runtime.put(MemoryAtom(f"a{q}", f"p{q}"), GeometryAddress("eisenstein_exact_v1", "c", 0, q, 0))
    document = json.loads(runtime.state_bytes())
    document["cells"].reverse()
    with pytest.raises(ValueError, match="semantic order"):
        runtime.import_state(canonical_state_bytes(document))
    document = json.loads(runtime.state_bytes())
    document["cells"].append({"address": GeometryAddress("eisenstein_exact_v1", "c", 0, 2, 0).to_mapping(), "atoms": []})
    with pytest.raises(ValueError, match="empty cells"):
        runtime.import_state(canonical_state_bytes(document))


def test_reversed_atoms_rejected(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    runtime.put(MemoryAtom("a", "a"), cell)
    runtime.put(MemoryAtom("b", "b"), cell)
    document = json.loads(runtime.state_bytes())
    document["cells"][0]["atoms"].reverse()
    with pytest.raises(ValueError, match="semantic order"):
        runtime.import_state(canonical_state_bytes(document))


def test_reversed_bridges_and_store_bypass_are_rejected(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    anchor = GeometryAnchor("a", (cell,))
    runtime.bridge_add(BridgeSpec("a", anchor, anchor, 1, "normal", 1, 1))
    runtime.bridge_add(BridgeSpec("b", anchor, anchor, 1, "normal", 1, 1))
    document = json.loads(runtime.state_bytes())
    document["bridges"].reverse()
    payload = canonical_state_bytes(document)
    with pytest.raises(ValueError, match="semantic order"):
        runtime.import_state(payload)
    assert not hasattr(runtime, "store")
