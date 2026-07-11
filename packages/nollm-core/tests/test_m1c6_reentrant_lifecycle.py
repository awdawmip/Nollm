from pathlib import Path

import pytest

from nollm_core import CoreRecallRequest, CoreRuntime, FileCoreStateStore, GeometryAddress, MemoryAtom, RecallBudget


CELL = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)


def request() -> CoreRecallRequest:
    return CoreRecallRequest("r", (CELL,), (), RecallBudget(1, 1, 0, 0, 0, 10))


class ReentrantSink:
    def __init__(self, event_name: str, action) -> None:
        self.event_name = event_name
        self.action = action
        self.rejected = False

    def emit(self, event) -> None:
        if event.name == self.event_name:
            try:
                self.action()
            except RuntimeError:
                self.rejected = True


@pytest.mark.parametrize("event_name,operation", [
    ("core.recall.begin", "recall"),
    ("core.snapshot.release", "snapshot"),
    ("core.batch.begin", "batch"),
])
def test_trace_cannot_mutate_or_close_active_core(tmp_path: Path, event_name: str, operation: str) -> None:
    core = None

    def reenter() -> None:
        if operation == "batch":
            core.close()
        else:
            core.put(MemoryAtom("trace-added", "x"), CELL)

    sink = ReentrantSink(event_name, reenter)
    core = CoreRuntime(tmp_path, trace_sink=sink)
    if operation == "recall":
        result = core.recall(request())
        assert all(item.atom.atom_id != "trace-added" for item in result.items)
    elif operation == "snapshot":
        token = core.begin_consistent_read()
        core.export_state(token)
        core.end_consistent_read(token)
    else:
        core.put(MemoryAtom("outer", "x"), CELL)
        assert core.is_open
    assert sink.rejected
    assert core.placement_count() == (1 if operation == "batch" else 0)
    core.close()


def test_same_thread_close_rejected_inside_transaction_lease(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path)
    with core.transaction_lease():
        with pytest.raises(RuntimeError, match="active Core operation"):
            core.close()
        with pytest.raises(RuntimeError, match="live mutable owner"):
            CoreRuntime(tmp_path)
    core.close()


def test_store_callback_cannot_close_active_core(tmp_path: Path) -> None:
    core = None
    rejected = False

    def hook(_path: Path) -> None:
        nonlocal rejected
        try:
            core.close()
        except RuntimeError:
            rejected = True

    CoreRuntime(tmp_path).close()
    store = FileCoreStateStore(tmp_path, hook)
    core = CoreRuntime(tmp_path, store=store)
    core.put(MemoryAtom("outer", "x"), CELL)
    assert rejected and core.is_open and core.placement_count() == 1
    core.close()
