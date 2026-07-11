import pytest

from nollm_access import AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress


def test_binding_failure_rolls_back_core(tmp_path) -> None:
    fail = False
    def before_replace(_path):
        nonlocal fail
        if fail:
            fail = False
            raise OSError("binding failure")
    core = CoreRuntime(tmp_path / "core")
    store = FileHandleStore(tmp_path, before_replace)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    access.capture(MemoryStatement("s", "payload"))
    core_before, binding_before = core.state_bytes(), store.state_bytes()
    fail = True
    decision = AccessDecision("d", "s", "new", target_cell=GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0), reason_text="fixture", decided_by="fixture")
    with pytest.raises(OSError, match="binding failure"):
        access.apply(decision)
    assert core.state_bytes() == core_before
    assert store.state_bytes() == binding_before
