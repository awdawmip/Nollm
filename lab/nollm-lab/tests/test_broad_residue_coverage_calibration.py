from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/geometry/run_broad_residue_coverage_calibration.py"


def _module():
    spec = importlib.util.spec_from_file_location("broad_residue_coverage_calibration", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixture_matrix_is_balanced_and_repeatable() -> None:
    module = _module()
    first = module.broad_exact_fixtures(4)
    assert first == module.broad_exact_fixtures(4)
    assert len(first) == 8 * 2 * 4
    assert {(fixture.phase, fixture.direction) for fixture in first} == {
        (phase, direction)
        for phase in range(8)
        for direction in ("coverage_up", "coverage_down")
    }


def test_quick_matrix_scores_both_kernels_and_policies() -> None:
    result = _module().validate(exact_per_phase_direction=2, diagnostic_count=32)
    assert not result["checks"]["full_exact_fixture_count"]
    assert result["selected_policy"] == "min_hit_1"
    assert set(result["methods"]) == {"production", "prototype"}
    assert set(result["methods"]["production"]) == {"min_hit_1", "min_hit_2"}
    assert result["exact_fixture_count"] == 32
    assert result["diagnostic_fixture_count"] == 32
