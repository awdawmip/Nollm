from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/recall_lens/freeze_rev3_live_growth.py"


def _module():
    spec = importlib.util.spec_from_file_location("rev3_live_growth_freeze", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_event_key_matches_capture_store_current_state_order() -> None:
    module = _module()
    base = {"attempt": 2, "event_epoch_ms": 10}
    captured = {**base, "status": "captured", "event_id": "b"}
    processing = {**base, "status": "processing", "event_id": "a"}
    admitted = {**base, "status": "admitted", "event_id": "c"}

    assert sorted((admitted, processing, captured), key=module._event_key)[-1] == admitted


def test_sha_uses_exact_bytes() -> None:
    module = _module()

    assert module._sha(b"a\r\n") != module._sha(b"a\n")
