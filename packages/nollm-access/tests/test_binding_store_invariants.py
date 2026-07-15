import pytest

from nollm_access import AccessDecision, AccessRuntime, FileBindingStore, FileEvidenceStore, MemoryStatement
from nollm_core import AtomHandle, CoreRuntime, GeometryAddress


CELL = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)


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
    missing = AtomHandle(GeometryAddress("eisenstein_exact_v1", "c", 0, 1, 0), "missing")
    assert store.bindings_for_handles((current, missing)) == (binding,)
    access.close()
    core.close()
