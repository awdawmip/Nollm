from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/recall_lens/run_synthetic_long_arm_conformance.py"


def _module():
    spec = importlib.util.spec_from_file_location("tokyo_time_weather_observation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_synthetic_long_arms_have_three_positive_and_one_negative_control(tmp_path):
    result = _module().validate(tmp_path)
    assert result["passed"]
    assert result["statement_count"] == 9
    assert result["independent_single_entry_count"] == 3
    assert result["same_target_handle"]
    assert all(len(item["path"]) >= 2 for item in result["recalls"].values())
    assert result["arm_lengths"] == {"tokyo": 2, "absolute_time": 2, "weather": 2, "unrelated": 2}
    assert not result["unrelated_target_reached"]
    assert not result["persistent_lens_text_found"]
    assert not result["provider_backed"]
