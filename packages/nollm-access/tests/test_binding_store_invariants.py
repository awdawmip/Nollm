import pytest

from nollm_access import FileBindingStore
from nollm_core import AtomHandle, GeometryAddress


def handle(name: str) -> AtomHandle:
    return AtomHandle(GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0), name)


def test_one_current_and_one_statement_per_binding(tmp_path) -> None:
    store = FileBindingStore(tmp_path)
    store.put("current", handle("a"))
    store.put("support", handle("a"))
    assert store.binding_for_handle(handle("a")).current_statement_id == "current"
    assert store.binding_for_handle(handle("a")).supporting_statement_ids == ("support",)
    with pytest.raises(ValueError, match="already bound"):
        store.put("support", handle("b"))
