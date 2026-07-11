from nollm_access import AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress


def test_forget_succeeds_when_evidence_is_missing(tmp_path) -> None:
    evidence = FileEvidenceStore(tmp_path)
    core = CoreRuntime(tmp_path / "core")
    access = AccessRuntime(core, evidence, FileHandleStore(tmp_path))
    access.capture(MemoryStatement("s", "payload"))
    cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    handle = access.apply(AccessDecision("new", "s", "new", target_cell=cell, reason_text="fixture"))
    evidence._path("s").unlink()
    access.apply(AccessDecision("forget", "s", "forget", existing_handle=handle, reason_text="fixture"))
    assert not core.contains(handle)
    assert not access.handle_store.exists("s")
