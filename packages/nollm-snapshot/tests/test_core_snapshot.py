from threading import Event, Thread

import pytest

from nollm_core import AtomHandle, CoreRuntime, GeometryAddress, MemoryAtom
from nollm_snapshot import SnapshotService


def cell(q: int, r: int) -> GeometryAddress:
    return GeometryAddress("eisenstein_exact_v1", "chart", 1, q, r)


def test_snapshot_create_restore_clone_verify_and_diff_new_core(tmp_path) -> None:
    source = CoreRuntime(tmp_path / "source")
    handle = source.put(MemoryAtom("atom", "原始 UTF-8"), cell(-7, 11))
    service = SnapshotService()
    payload = service.create(source)

    restored = CoreRuntime(tmp_path / "restored")
    service.restore(restored, payload)
    assert restored.get(handle).payload_utf8 == "原始 UTF-8"
    assert service.verify(restored, payload)

    clone = CoreRuntime(tmp_path / "clone")
    assert service.clone(source, clone) == payload
    assert not service.structural_diff(payload, service.create(clone))
    clone.put(MemoryAtom("other", "different"), cell(0, 0))
    assert service.structural_diff(payload, service.create(clone))


def test_snapshot_freeze_uses_same_lock_as_mutation(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    token = runtime.begin_consistent_read()
    started = Event()
    finished = Event()

    def mutate() -> None:
        started.set()
        runtime.put(MemoryAtom("blocked", "payload"), cell(0, 0))
        finished.set()

    thread = Thread(target=mutate)
    thread.start()
    assert started.wait(1)
    assert not finished.wait(0.05)
    runtime.end_consistent_read(token)
    thread.join(1)
    assert finished.is_set()


def test_failed_restore_preserves_current_state(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    handle = runtime.put(MemoryAtom("stable", "before"), cell(0, 0))
    before = runtime.state_bytes()
    with pytest.raises((ValueError, UnicodeDecodeError)):
        SnapshotService().restore(runtime, b"not canonical state")
    assert runtime.state_bytes() == before
    assert CoreRuntime(tmp_path).get(handle).payload_utf8 == "before"
