from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nollm.dream_geometry.adapters import CapabilitiesInvocation, IntegrationShell
from nollm.dream_geometry.validation.di1_integration_fixture import build_deferred_context, build_di1_context


def test_t_720_relative_time_without_runtime_resolution_defers_without_clock(tmp_path) -> None:
    _, _, _, invocation, context = build_deferred_context(tmp_path)
    mapping = IntegrationShell().handle(invocation, context).to_mapping()
    assert mapping["ok"] is True
    assert mapping["result"]["status"] == "deferred"
    assert mapping["result"]["primary_evidence"] == []


def test_t_723_call_does_not_change_evidence_files_or_ledger(tmp_path) -> None:
    store, _, _, invocation, context = build_di1_context(tmp_path)
    before_hashes = _tree_hashes(tmp_path / "evidence")
    before_ledger = store.read_ledger()
    IntegrationShell().handle(invocation, context)
    assert _tree_hashes(tmp_path / "evidence") == before_hashes
    assert store.read_ledger() == before_ledger


def test_t_726_capabilities_does_not_touch_evidence_store() -> None:
    class ExplodingStore:
        def __getattr__(self, name):
            raise AssertionError(name)

    response = IntegrationShell().handle(CapabilitiesInvocation("req-cap-sentinel", "capabilities"), ExplodingStore())
    assert response.to_mapping()["ok"] is True


def test_error_messages_do_not_include_exception_text_or_paths(tmp_path, monkeypatch) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)

    def boom(*args, **kwargs):
        raise RuntimeError("C:/secret/path/internal detail")

    monkeypatch.setattr("nollm.dream_geometry.adapters.integration_shell.recall_facade.resolve_recall", boom)
    mapping = IntegrationShell().handle(invocation, context).to_mapping()
    rendered = json.dumps(mapping, sort_keys=True)
    assert mapping["error"]["code"] == "DI1_INTERNAL_ERROR"
    assert "secret" not in rendered
    assert "RuntimeError" not in rendered


def _tree_hashes(root: Path) -> dict[str, str]:
    hashes = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes
