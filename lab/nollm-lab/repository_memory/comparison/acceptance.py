"""Held-out checks. Run from the evaluator, outside participant directories."""
from hashlib import sha256
import json

import pytest

from nollm_access import (AccessDecision, AccessRecallRequest, AccessRuntime, FileHandleStore,
                          FileStatementStore, MemoryStatement)
from nollm_core import AtomHandle, CoreRuntime, GeometryAddress


def test_binding_order_lookup_and_immutable_state(tmp_path):
    cell = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    store = FileHandleStore(tmp_path)
    with CoreRuntime(tmp_path) as core, AccessRuntime(core, FileStatementStore(tmp_path), store) as access:
        access.capture(MemoryStatement("z-current", "payload"))
        handle = access.apply(AccessDecision("new", "z-current", "new", target_cell=cell, reason_text="fixture"))
        for name in ("b-support", "a-support"):
            access.capture(MemoryStatement(name, "payload"))
            access.apply(AccessDecision(name, name, "reuse", existing_handle=handle, reason_text="fixture"))
        before = store.state_bytes()
        for lookup in (store.statement_ids_for_handle, access.statement_ids_for_handle):
            assert lookup(handle) == ("z-current", "a-support", "b-support")
            with pytest.raises(KeyError):
                lookup(AtomHandle(cell, "missing"))
        assert store.state_bytes() == before
        recalled = access.recall(AccessRecallRequest("read", entry_handles=(handle,)))
        assert [(item.statement_id, item.evidence_utf8) for item in recalled.items] == [("z-current", "payload")]


def test_binding_single_and_closed(tmp_path):
    cell = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    store = FileHandleStore(tmp_path)
    with CoreRuntime(tmp_path) as core, AccessRuntime(core, FileStatementStore(tmp_path), store) as access:
        access.capture(MemoryStatement("one", "payload"))
        handle = access.apply(AccessDecision("new", "one", "new", target_cell=cell, reason_text="fixture"))
        assert access.statement_ids_for_handle(handle) == ("one",)
        core.close()
        with pytest.raises(RuntimeError):
            access.statement_ids_for_handle(handle)
    with pytest.raises(RuntimeError):
        access.statement_ids_for_handle(handle)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def test_statement_bytes_and_modern_roundtrip(tmp_path):
    value = MemoryStatement("键", "é\n文本", "档", ("β", "a"))
    expected = '{"content_utf8":"é\\n文本","context_refs":["β","a"],"source_handle":"档","statement_id":"键"}\n'.encode()
    store = FileStatementStore(tmp_path)
    store.put(value)
    path, = store.root.rglob("*.json")
    before = path.read_bytes()
    assert value.canonical_bytes() == expected
    assert FileStatementStore(tmp_path).canonical_bytes("键") == expected
    assert before == encode({"schema_version": "nollm_access_statement_v1", "statement": value.to_mapping()})
    assert path.read_bytes() == before
    path.write_bytes(before + b" ")
    with pytest.raises(ValueError):
        store.canonical_bytes("键")


def test_statement_legacy_missing_and_identity(tmp_path):
    value = MemoryStatement("old", "legacy")
    store = FileStatementStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        store.canonical_bytes("none")
    digest = sha256(b"old").hexdigest()
    path = tmp_path / "access" / "evidence" / digest[:2] / (digest + ".json")
    path.parent.mkdir(parents=True)
    doc = {"schema_version": "nollm_access_evidence_v1", "statement": value.to_mapping()}
    path.write_bytes(encode(doc))
    assert store.canonical_bytes("old") == encode(value.to_mapping())
    assert not store.root.exists()
    assert path.read_bytes() == encode(doc)
    doc["statement"]["statement_id"] = "other"
    path.write_bytes(encode(doc))
    with pytest.raises(ValueError):
        store.canonical_bytes("old")


def test_digest_tracks_snapshot_bytes_across_restore_and_reopen(tmp_path):
    from nollm_core import MemoryAtom
    from nollm_snapshot import SnapshotService

    snapshots = SnapshotService()
    cell = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    with CoreRuntime(tmp_path) as core:
        empty = snapshots.create(core)
        expected_empty = sha256(empty).hexdigest()
        assert core.state_sha256() == expected_empty
        core.put(MemoryAtom("例", "café"), cell)
        updated = snapshots.create(core)
        assert updated != empty
        assert core.state_sha256() == sha256(updated).hexdigest()
        snapshots.restore(core, empty)
        assert core.state_sha256() == expected_empty
        assert snapshots.verify(core, empty)
    with pytest.raises(RuntimeError):
        core.state_sha256()
    with CoreRuntime(tmp_path) as reopened:
        assert reopened.state_sha256() == expected_empty


def test_digest_conditional_write_uses_core_observation(tmp_path, monkeypatch):
    cell = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    value = MemoryStatement("trial", "recorded")
    decision = AccessDecision("write", "trial", "new", target_cell=cell, reason_text="fixture")
    store = FileStatementStore(tmp_path)
    with CoreRuntime(tmp_path) as core, AccessRuntime(core, store, FileHandleStore(tmp_path)) as access:
        calls = []
        digest = core.state_sha256

        def observe():
            calls.append(True)
            return digest()

        monkeypatch.setattr(core, "state_sha256", observe)
        before = core.export_state_bytes()
        expected = sha256(before).hexdigest()
        stale = access.apply_if_state("0" * 64, value, decision)
        assert (stale.commit_state, stale.observed_core_state_sha256) == ("stale_zero_write", expected)
        assert core.export_state_bytes() == before
        assert not store.exists(value.statement_id)
        assert calls
        calls.clear()
        saved = access.apply_if_state(expected, value, decision)
        assert (saved.commit_state, saved.observed_core_state_sha256) == ("committed", expected)
        assert calls and saved.statement_created and store.get(value.statement_id) == value
        access.close()
        calls.clear()
        with pytest.raises(RuntimeError):
            access.apply_if_state(expected, value, decision)
        assert not calls
