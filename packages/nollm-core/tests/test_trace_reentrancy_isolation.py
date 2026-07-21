import pytest

from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, PutCommand


def cell(q=0, r=0):
    return GeometryAddress("eisenstein_exact_v1", "c", 0, q, r)


class SingleFireSink:
    def __init__(self, action, *, raise_after=False):
        self.action = action
        self.raise_after = raise_after
        self.core = None
        self.calls = 0
        self.error = None

    def emit(self, event):
        if event.name != "core.batch.begin" or self.calls:
            return
        self.calls += 1
        try:
            self.action(self.core)
        except BaseException as error:
            self.error = error
        if self.raise_after:
            raise ValueError("optional Trace sink failed")


@pytest.mark.parametrize(
    "action",
    (
        lambda core: core.put(MemoryAtom("inner", "inner"), cell(1, 0)),
        lambda core: core.apply_batch((PutCommand(MemoryAtom("inner", "inner"), cell(1, 0)),)),
        lambda core: core.import_state_bytes(b"{}"),
    ),
)
def test_trace_callback_cannot_reenter_public_state_operations(tmp_path, action):
    sink = SingleFireSink(action)
    with CoreRuntime(tmp_path, trace_sink=sink) as core:
        sink.core = core
        outer = core.put(MemoryAtom("outer", "outer"), cell())
        assert core.contains(outer)
        assert core.placement_count() == 1

    assert sink.calls == 1
    assert isinstance(sink.error, RuntimeError)
    assert "reenter" in str(sink.error)


def test_trace_callback_cannot_close_or_release_workspace_owner(tmp_path):
    sink = SingleFireSink(lambda core: core.close())
    core = CoreRuntime(tmp_path, trace_sink=sink)
    sink.core = core

    outer = core.put(MemoryAtom("outer", "outer"), cell())

    assert core.contains(outer)
    assert core.is_open
    assert isinstance(sink.error, RuntimeError)
    with pytest.raises(RuntimeError, match="live mutable owner"):
        CoreRuntime(tmp_path)
    core.close()


def test_trace_exception_does_not_change_commit_result(tmp_path):
    sink = SingleFireSink(lambda _core: None, raise_after=True)
    with CoreRuntime(tmp_path, trace_sink=sink) as core:
        sink.core = core
        handle = core.put(MemoryAtom("outer", "outer"), cell())
        assert core.get(handle).payload_utf8 == "outer"


def test_outer_batch_rollback_survives_rejected_trace_reentry(tmp_path):
    sink = SingleFireSink(lambda core: core.put(MemoryAtom("inner", "inner"), cell(1, 0)))
    with CoreRuntime(tmp_path, trace_sink=sink) as core:
        sink.core = core
        before = core.export_state_bytes()
        duplicate = PutCommand(MemoryAtom("same", "same"), cell())
        with pytest.raises(FileExistsError):
            core.apply_batch((duplicate, duplicate))
        assert core.export_state_bytes() == before
        assert core.placement_count() == 0

    assert isinstance(sink.error, RuntimeError)
