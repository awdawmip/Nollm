import pytest

from nollm_core import (
    AtomHandle,
    BridgeAddCommand,
    BridgeSpec,
    CoreRuntime,
    FileCoreStateStore,
    GeometryAddress,
    GeometryAnchor,
    MemoryAtom,
    MoveCommand,
    PutCommand,
    ReplaceCommand,
)


def cell(q: int, r: int) -> GeometryAddress:
    return GeometryAddress("exact", "chart", 1, q, r)


def test_put_replace_move_remove_and_reopen(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    handle = runtime.put(MemoryAtom("atom-a", "原始 payload"), cell(-3, 5))
    assert runtime.get(handle).payload_utf8 == "原始 payload"
    assert runtime.replace(handle, "replacement") == handle
    moved = runtime.move(handle, cell(8, -13))
    assert not runtime.contains(handle)
    assert runtime.get(moved).payload_utf8 == "replacement"
    assert CoreRuntime(tmp_path).get(moved).payload_utf8 == "replacement"
    assert runtime.remove(moved).atom_id == "atom-a"
    assert runtime.placement_count() == 0


def test_batch_is_atomic_and_commits_once(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    existing = runtime.put(MemoryAtom("existing", "old"), cell(0, 0))
    bridge = BridgeSpec(
        "bridge-a",
        GeometryAnchor("from", (cell(0, 0),)),
        GeometryAnchor("to", (cell(1, 0),)),
        1 << 15,
        "normal",
        1,
        2,
    )
    results = runtime.apply_batch(
        (
            PutCommand(MemoryAtom("new", "new payload"), cell(1, 0)),
            ReplaceCommand(existing, "updated"),
            MoveCommand(existing, cell(0, 1)),
            BridgeAddCommand(bridge),
        )
    )
    assert len(results) == 4
    assert runtime.get(AtomHandle(cell(0, 1), "existing")).payload_utf8 == "updated"
    before = runtime.state_bytes()
    with pytest.raises(KeyError):
        runtime.apply_batch(
            (
                PutCommand(MemoryAtom("rolled-back", "payload"), cell(2, 0)),
                MoveCommand(AtomHandle(cell(99, 99), "missing"), cell(3, 0)),
            )
        )
    assert runtime.state_bytes() == before
    assert not runtime.contains(AtomHandle(cell(2, 0), "rolled-back"))


def test_disk_failure_preserves_memory_and_reopen_state(tmp_path) -> None:
    fail = False

    def before_replace(_path) -> None:
        if fail:
            raise OSError("simulated disk failure")

    store = FileCoreStateStore(tmp_path, before_replace)
    runtime = CoreRuntime(tmp_path, store=store)
    original = runtime.put(MemoryAtom("stable", "before"), cell(0, 0))
    stable_bytes = runtime.state_bytes()
    fail = True
    with pytest.raises(OSError, match="simulated disk failure"):
        runtime.put(MemoryAtom("failed", "after"), cell(1, 0))
    assert runtime.state_bytes() == stable_bytes
    reopened = CoreRuntime(tmp_path)
    assert reopened.get(original).payload_utf8 == "before"
    assert reopened.placement_count() == 1
