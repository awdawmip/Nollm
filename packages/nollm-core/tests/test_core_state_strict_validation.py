import json

import pytest

from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom


def test_runtime_bytes_equal_store_and_reject_noncanonical_or_duplicate_state(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    runtime.put(MemoryAtom("a", "payload"), GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0))
    assert runtime.state_bytes() == runtime.store.read_bytes()
    document = json.loads(runtime.state_bytes())
    document["cells"].append(document["cells"][0])
    duplicate = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    with pytest.raises(ValueError, match="duplicate cell"):
        runtime.import_state(duplicate)
    with pytest.raises(ValueError, match="canonical"):
        runtime.import_state(runtime.state_bytes().rstrip())
    document = json.loads(runtime.state_bytes())
    document["cells"][0]["address"]["layer"] = True
    invalid = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    with pytest.raises(TypeError, match="integer"):
        runtime.import_state(invalid)
