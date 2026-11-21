import json

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
    assert service.structural_diff(payload, service.create(clone)).equal
    clone.put(MemoryAtom("other", "different"), cell(0, 0))
    assert not service.structural_diff(payload, service.create(clone)).equal


def test_snapshot_create_is_atomic_core_state_export(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    runtime.put(MemoryAtom("stable", "payload"), cell(0, 0))
    assert SnapshotService().create(runtime) == runtime.export_state_bytes()


def test_failed_restore_preserves_current_state(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    handle = runtime.put(MemoryAtom("stable", "before"), cell(0, 0))
    before = runtime.export_state_bytes()
    with pytest.raises((ValueError, UnicodeDecodeError)):
        SnapshotService().restore(runtime, b"not canonical state")
    assert runtime.export_state_bytes() == before
    runtime.close()
    assert CoreRuntime(tmp_path).get(handle).payload_utf8 == "before"


def test_restore_normalizes_json_but_verify_still_compares_snapshot_bytes(tmp_path) -> None:
    service = SnapshotService()
    with CoreRuntime(tmp_path / "source") as source:
        handle = source.put(MemoryAtom("a", "原文"), cell(-3, 2))
        canonical = service.create(source)
    presentation = json.dumps(json.loads(canonical), ensure_ascii=False, indent=2).encode("utf-8")
    with CoreRuntime(tmp_path / "target") as target:
        service.restore(target, presentation)
        assert target.get(handle).payload_utf8 == "原文"
        assert service.verify(target, canonical)
        assert not service.verify(target, presentation)
        assert target.state_path.read_bytes() == canonical
    with CoreRuntime(tmp_path / "target") as reopened:
        assert service.verify(reopened, canonical)
