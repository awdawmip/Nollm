from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/recall_lens/freeze_provider_long_arm_attempt.py"


def _module():
    spec = importlib.util.spec_from_file_location("provider_long_arm_attempt_freeze", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_capture_labels_require_exact_supplied_fact() -> None:
    module = _module()

    assert module._capture_label({"user_utf8": "前缀" + module.EXPECTED["target"]}) == "target"
    assert module._capture_label({"user_utf8": "无关事实"}) is None
    assert module._capture_label({"user_utf8": 3}) is None


def test_sha_uses_exact_bytes() -> None:
    module = _module()

    assert module._sha(b"a\r\n") != module._sha(b"a\n")
