import pytest

from nollm_access import AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress


def test_binding_failure_rolls_back_core(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    store = FileHandleStore(tmp_path)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    access.capture(MemoryStatement("s", "payload"))
    core_before, binding_before = core.export_state_bytes(), store.state_bytes()
    original_write = store._write_bytes
    failed = False
    def fail_once(payload):
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("binding failure")
        original_write(payload)
    store._write_bytes = fail_once
    decision = AccessDecision("d", "s", "new", target_cell=GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0), reason_text="fixture", decided_by="fixture")
    with pytest.raises(OSError, match="binding failure"):
        access.apply(decision)
    assert core.export_state_bytes() == core_before
    assert store.state_bytes() == binding_before
