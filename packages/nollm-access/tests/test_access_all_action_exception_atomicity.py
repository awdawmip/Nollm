import pytest

from nollm_access import AccessConsistencyError, AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, FileCoreStateStore, GeometryAddress


def cell(q):
    return GeometryAddress("eisenstein_exact_v1", "fault", 0, q, 0)


def decision(statement, action, **kwargs):
    return AccessDecision(statement + action, statement, action, reason_text="fixture", **kwargs)


@pytest.mark.parametrize("action", ["new", "revision_current", "revision_keep_history", "forget", "reuse"])
def test_all_binding_failures_preserve_prestate(tmp_path, action) -> None:
    core = CoreRuntime(tmp_path / "core")
    store = FileHandleStore(tmp_path)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    access.capture(MemoryStatement("old", "old"))
    old = access.apply(decision("old", "new", target_cell=cell(0)))
    access.capture(MemoryStatement("next", "next"))
    before = core.state_bytes(), store.state_bytes()
    fail = True
    def once(_path):
        nonlocal fail
        if fail:
            fail = False
            raise OSError("binding failure")
    store.before_replace = once
    statement = "old" if action == "forget" else "next"
    kwargs = {"target_cell": cell(1)} if action in {"new", "revision_keep_history"} else {"existing_handle": old}
    with pytest.raises(OSError, match="binding failure"):
        access.apply(decision(statement, action, **kwargs))
    assert (core.state_bytes(), store.state_bytes()) == before
    CoreRuntime(tmp_path / "core")


def test_core_failure_does_not_change_binding(tmp_path) -> None:
    fail = False
    def core_fault(_path):
        nonlocal fail
        if fail:
            fail = False
            raise OSError("core failure")
    core = CoreRuntime(tmp_path / "core", store=FileCoreStateStore(tmp_path / "core", core_fault))
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))
    access.capture(MemoryStatement("s", "s"))
    before = core.state_bytes(), access.handle_store.state_bytes()
    fail = True
    with pytest.raises(OSError, match="core failure"):
        access.apply(decision("s", "new", target_cell=cell(0)))
    assert (core.state_bytes(), access.handle_store.state_bytes()) == before


def test_rollback_failure_is_fatal_consistency_error(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    store = FileHandleStore(tmp_path)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    access.capture(MemoryStatement("s", "s"))
    store.before_replace = lambda _path: (_ for _ in ()).throw(OSError("persistent failure"))
    with pytest.raises(AccessConsistencyError) as caught:
        access.apply(decision("s", "new", target_cell=cell(0)))
    assert isinstance(caught.value.__cause__, OSError)
