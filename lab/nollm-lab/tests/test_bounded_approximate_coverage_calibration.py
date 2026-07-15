from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/geometry/run_bounded_approximate_coverage_calibration.py"


def _module():
    spec = importlib.util.spec_from_file_location("bounded_coverage_calibration", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_calibration_selects_m4_and_keeps_hit_identity_diagnostic_only() -> None:
    result = _module().validate()
    assert result["passed"]
    assert result["selected_method"] == "m4"
    assert result["methods"]["m3"]["sample_count"] == 54
    assert result["methods"]["m4"]["sample_count"] == 96
    assert all(result["checks"].values())
    assert result["production"]["prototype_hit_identity_is_diagnostic_only"]
    assert 0 <= result["production"]["prototype_hit_match_rate"] <= 1
