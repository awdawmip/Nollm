from pathlib import Path

import pytest

from nollm_access import (
    AccessDecision,
    AccessRecallRequest,
    AccessRuntime,
    FileEvidenceStore,
    FileHandleStore,
    MemoryStatement,
)
from nollm_access.workspace_lock import BindingWriterCapability
from nollm_core import AtomHandle, CoreRuntime, GeometryAddress, RecallBudget


CELL = GeometryAddress("eisenstein_exact_v1", "m1c8", 0, 0, 0)
BUDGET = RecallBudget(0, 8, 0, 0, 0, 8)


def decision(statement_id: str) -> AccessDecision:
    return AccessDecision(
        f"d:{statement_id}",
        statement_id,
        "new",
        target_cell=CELL,
        reason_text="fixture",
        decided_by="fixture",
    )


def test_pair_callback_blocks_every_same_pair_access_entry(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    backing = FileEvidenceStore(tmp_path)
    first = None
    second = None
    rejected = []
    callback_count = 0

    class CallbackEvidence:
        workspace = backing.workspace

        def put_original(self, statement) -> None:
            nonlocal callback_count
            callback_count += 1
            if callback_count == 1:
                operations = {
                    "capture": lambda: second.capture(MemoryStatement("nested", "nested")),
                    "apply": lambda: second.apply(decision("nested")),
                    "recall": lambda: second.recall(AccessRecallRequest("nested", entry_cells=(CELL,), budget=BUDGET)),
                    "saved_handle": lambda: second.saved_handle("nested"),
                    "close": second.close,
                    "constructor": lambda: AccessRuntime(core, backing, FileHandleStore(tmp_path)),
                    "direct_store": lambda: second.handle_store.put("nested", AtomHandle(CELL, "ghost")),
                }
                for name, operation in operations.items():
                    with pytest.raises(RuntimeError, match="pair callback|writer capability"):
                        operation()
                    rejected.append(name)
            backing.put_original(statement)

        def get_original(self, statement_id):
            return backing.get_original(statement_id)

        def exists(self, statement_id):
            return backing.exists(statement_id)

    first = AccessRuntime(core, CallbackEvidence(), FileHandleStore(tmp_path))
    second = AccessRuntime(core, backing, FileHandleStore(tmp_path))
    first.capture(MemoryStatement("outer", "outer"))
    assert set(rejected) == {"capture", "apply", "recall", "saved_handle", "close", "constructor", "direct_store"}
    assert second.lifecycle_state == "OPEN"
    assert not backing.exists("nested")
    assert first._active_operations == second._active_operations == 0
    assert not hasattr(first._coordinator._local, "callback_depth")
    second.capture(MemoryStatement("after", "after"))
    second.close()
    assert second.lifecycle_state == "CLOSED"
    first.close()
    core.close()


def test_pair_callback_exception_cleans_shared_fence(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    backing = FileEvidenceStore(tmp_path)

    class FailingEvidence:
        workspace = backing.workspace

        def put_original(self, statement) -> None:
            raise OSError("capture fault")

        def get_original(self, statement_id):
            return backing.get_original(statement_id)

        def exists(self, statement_id):
            return backing.exists(statement_id)

    first = AccessRuntime(core, FailingEvidence(), FileHandleStore(tmp_path))
    second = AccessRuntime(core, backing, FileHandleStore(tmp_path))
    with pytest.raises(OSError, match="capture fault"):
        first.capture(MemoryStatement("failed", "failed"))
    assert not hasattr(first._coordinator._local, "callback_depth")
    assert first._active_operations == second._active_operations == 0
    second.capture(MemoryStatement("safe", "safe"))
    first.close()
    second.close()
    core.close()


def test_handle_store_mutation_requires_live_pair_capability(tmp_path: Path) -> None:
    store = FileHandleStore(tmp_path)
    handle = AtomHandle(CELL, "ghost")
    empty = store.state_bytes()
    for operation in (
        lambda: store.put("ghost", handle),
        lambda: store.revise_current(handle, "new", handle),
        lambda: store.remove_handle(handle),
        lambda: store.import_state(empty),
    ):
        with pytest.raises(RuntimeError, match="writer capability"):
            operation()
    assert store.state_bytes() == empty and not store.path.exists()

    core = CoreRuntime(tmp_path / "core")
    evidence = FileEvidenceStore(tmp_path)
    access = AccessRuntime(core, evidence, store)
    capability = access._binding_capability
    forged = BindingWriterCapability(access._coordinator)
    for candidate in (None, object(), forged):
        with pytest.raises(RuntimeError, match="writer capability"):
            store.import_state(empty, capability=candidate)
    access.capture(MemoryStatement("real", "real"))
    handle = access.apply(decision("real"))
    bound = store.state_bytes()
    assert access.saved_handle("real") == handle
    access.close()
    assert not capability.active
    with pytest.raises(RuntimeError, match="writer capability"):
        store.import_state(empty, capability=capability)
    assert store.state_bytes() == bound
    core.close()


def test_same_pair_store_configuration_is_frozen_and_compatible(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    evidence = FileEvidenceStore(tmp_path)
    store = FileHandleStore(tmp_path)
    first = AccessRuntime(core, evidence, store)
    with pytest.raises(RuntimeError, match="frozen"):
        store.before_replace = lambda _path: None
    for name, value in (("path", tmp_path / "other.json"), ("workspace", tmp_path / "other")):
        with pytest.raises(AttributeError):
            setattr(store, name, value)
    with pytest.raises(ValueError, match="compatible"):
        AccessRuntime(core, evidence, FileHandleStore(tmp_path, lambda _path: None))
    second = AccessRuntime(core, evidence, FileHandleStore(tmp_path))
    first.close()
    second.close()
    core.close()


def test_access_dependencies_and_store_identities_are_read_only(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    other = CoreRuntime(tmp_path / "other-core")
    evidence = FileEvidenceStore(tmp_path)
    handles = FileHandleStore(tmp_path)
    access = AccessRuntime(core, evidence, handles)
    original = {
        "core": access.core,
        "evidence_store": access.evidence_store,
        "handle_store": access.handle_store,
        "canonical_access_root": access.canonical_access_root,
        "canonical_core_state_path": access.canonical_core_state_path,
    }
    replacements = {
        "core": other,
        "evidence_store": FileEvidenceStore(tmp_path / "replacement"),
        "handle_store": FileHandleStore(tmp_path / "replacement"),
        "canonical_access_root": tmp_path / "replacement",
        "canonical_core_state_path": tmp_path / "replacement.json",
    }
    for name, value in replacements.items():
        with pytest.raises(AttributeError):
            setattr(access, name, value)
    for target, name, value in (
        (evidence, "workspace", tmp_path / "replacement"),
        (evidence, "root", tmp_path / "replacement"),
        (handles, "workspace", tmp_path / "replacement"),
        (handles, "path", tmp_path / "replacement.json"),
    ):
        with pytest.raises(AttributeError):
            setattr(target, name, value)
    assert all(getattr(access, name) == value for name, value in original.items())
    access.capture(MemoryStatement("safe", "safe"))
    access.apply(decision("safe"))
    assert core.placement_count() == 1 and other.placement_count() == 0
    access.close()
    core.close()
    other.close()


def test_trace_cannot_rebind_access_or_retained_store_configuration(tmp_path: Path) -> None:
    access = None
    core = None
    evidence = FileEvidenceStore(tmp_path)
    handles = FileHandleStore(tmp_path)
    other = CoreRuntime(tmp_path / "other-core")
    attempts = []

    class Sink:
        def emit(self, event) -> None:
            if event.name != "core.recall.begin":
                return
            attacks = (
                (access, "core", other),
                (access, "evidence_store", FileEvidenceStore(tmp_path / "redirect")),
                (access, "handle_store", FileHandleStore(tmp_path / "redirect")),
                (handles, "path", tmp_path / "redirect" / "bindings.json"),
                (handles, "workspace", tmp_path / "redirect"),
                (handles, "before_replace", lambda _path: None),
                (evidence, "workspace", tmp_path / "redirect"),
                (evidence, "root", tmp_path / "redirect"),
            )
            for target, name, value in attacks:
                try:
                    setattr(target, name, value)
                except (AttributeError, RuntimeError):
                    attempts.append(name)

    core = CoreRuntime(tmp_path / "core", trace_sink=Sink())
    access = AccessRuntime(core, evidence, handles)
    access.recall(AccessRecallRequest("attack", entry_cells=(CELL,), budget=BUDGET))
    assert len(attempts) == 8
    access.capture(MemoryStatement("safe", "safe"))
    handle = access.apply(decision("safe"))
    assert core.contains(handle) and other.placement_count() == 0
    assert not (tmp_path / "redirect").exists()
    access.close()
    core.close()
    other.close()
