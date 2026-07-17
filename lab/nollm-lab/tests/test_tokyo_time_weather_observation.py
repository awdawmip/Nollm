from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/recall_lens/run_tokyo_time_weather_observation.py"


def _module():
    spec = importlib.util.spec_from_file_location("tokyo_time_weather_observation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_three_independent_single_entries_reach_one_tokyo_rain_handle(tmp_path):
    result = _module().validate(tmp_path)
    assert result["passed_deterministic_observation"]
    assert result["statement_count"] == 6
    assert result["target_atom_count"] == 1
    assert result["independent_single_entry_count"] == 3
    assert result["same_target_handle"]
    assert {tuple(item["path"]) for item in result["recalls"].values()} == {("lateral",)}
    assert result["none_result_count"] == 0
    assert not result["persistent_lens_text_found"]
    assert not result["provider_backed"]
