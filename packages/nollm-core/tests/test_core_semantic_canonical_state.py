import json

import pytest

from nollm_core import BridgeSpec, CoreRuntime, GeometryAddress, GeometryAnchor, MemoryAtom
from nollm_core.storage import canonical_state_bytes


@pytest.mark.parametrize("record_order", ["cells", "atoms", "bridges"])
def test_input_record_order_is_normalized_on_import(tmp_path, record_order) -> None:
    runtime = CoreRuntime(tmp_path)
    cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    runtime.put(MemoryAtom("a", "a"), cell)
    runtime.put(MemoryAtom("b", "b"), cell)
    runtime.put(MemoryAtom("c", "c"), GeometryAddress("eisenstein_exact_v1", "c", 0, 1, 0))
    anchor = GeometryAnchor("a", (cell,))
    runtime.bridge_add(BridgeSpec("a", anchor, anchor, 1, "normal", 1, 1))
    runtime.bridge_add(BridgeSpec("b", anchor, anchor, 1, "normal", 1, 1))
    canonical = runtime.export_state_bytes()
    document = json.loads(canonical)
    records = document["cells"][0]["atoms"] if record_order == "atoms" else document[record_order]
    records.reverse()
    runtime.import_state_bytes(json.dumps(document, indent=2).encode("utf-8"))
    assert runtime.export_state_bytes() == runtime.state_path.read_bytes() == canonical
    runtime.close()
    with CoreRuntime(tmp_path) as reopened:
        assert reopened.export_state_bytes() == canonical


def test_empty_cells_are_rejected(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        before = runtime.export_state_bytes()
        document = json.loads(before)
        document["cells"].append({"address": GeometryAddress("eisenstein_exact_v1", "c", 0, 2, 0).to_mapping(), "atoms": []})
        with pytest.raises(ValueError, match="empty cells"):
            runtime.import_state_bytes(canonical_state_bytes(document))
        assert runtime.export_state_bytes() == runtime.state_path.read_bytes() == before


def test_reopen_accepts_formatting_without_rewriting_the_source_file(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        cell = GeometryAddress("default_dream_v1", "default", 0, -2, 3)
        handle = runtime.put(MemoryAtom("a", "原文"), cell)
        canonical = runtime.export_state_bytes()
        path = runtime.state_path
    presentation = json.dumps(json.loads(canonical), ensure_ascii=False, indent=2).encode("utf-8")
    path.write_bytes(presentation)
    with CoreRuntime(tmp_path) as reopened:
        assert reopened.get(handle).payload_utf8 == "原文"
        assert reopened.export_state_bytes() == canonical
        assert path.read_bytes() == presentation
        reopened.put(MemoryAtom("b", "新表达"), cell)
        assert path.read_bytes() == reopened.export_state_bytes()
