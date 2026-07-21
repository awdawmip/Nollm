import pytest

from nollm_access import AccessDecision, AccessRuntime, FileBindingStore, FileEvidenceStore, MemoryStatement
from nollm_core import AtomHandle, CoreRuntime, GeometryAddress


CELL = GeometryAddress("default_dream_v1", "default", 0, 0, 0)


def test_one_current_and_one_statement_per_binding(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    store = FileBindingStore(tmp_path)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    access.capture(MemoryStatement("current", "payload"))
    current = access.apply(AccessDecision("d-current", "current", "new", target_cell=CELL, reason_text="fixture"))
    access.capture(MemoryStatement("support", "payload"))
    access.apply(AccessDecision("d-support", "support", "reuse", existing_handle=current, reason_text="fixture"))
    binding = store.binding_for_handle(current)
    assert binding.current_statement_id == "current"
    assert binding.supporting_statement_ids == ("support",)
    missing = AtomHandle(GeometryAddress("default_dream_v1", "default", 0, 1, 0), "missing")
    assert store.bindings_for_handles((current, missing)) == (binding,)
    access.close()
    core.close()


def test_confirmed_revision_retires_current_aliases_but_preserves_statements(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    store = FileBindingStore(tmp_path)
    evidence = FileEvidenceStore(tmp_path)
    access = AccessRuntime(core, evidence, store)
    for statement in (
        MemoryStatement("current", "version one"),
        MemoryStatement("alias", "version one"),
        MemoryStatement("revised", "version two"),
    ):
        access.capture(statement)
    handle = access.apply(AccessDecision("new", "current", "new", target_cell=CELL, reason_text="fixture"))
    access.apply(AccessDecision("reuse", "alias", "reuse", existing_handle=handle, reason_text="fixture"))
    revised = access.apply(AccessDecision("revision", "revised", "revision_current", existing_handle=handle, reason_text="fixture"))

    binding = store.binding_for_handle(revised)
    assert binding.current_statement_id == "revised"
    assert binding.supporting_statement_ids == ()
    with pytest.raises(KeyError):
        store.get("current")
    with pytest.raises(KeyError):
        store.get("alias")
    assert evidence.get("current").content_utf8 == "version one"
    assert evidence.get("alias").content_utf8 == "version one"
