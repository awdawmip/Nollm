from __future__ import annotations

import ast
import json
import sys
from math import isclose, sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX, ScaleRotationSchedule
from tests.fixtures.gpr1.fixture import (
    BASELINE_COMMIT,
    LAYER_GAPS,
    all_finite,
    baseline_b_formula_payload,
    build_metric_rows,
    canonical_metric_payload,
    experiment_window_payload,
    parameter_by_id,
    parameter_payload,
    phase_score_for,
    state_dirs,
)


def test_gpr1_01_parameter_matrix_and_baseline_b_scale_formulas_are_stable() -> None:
    assert parameter_payload() == (
        {"parameter_id": "A", "beta": "1.189207115", "delta_theta_degrees": "15", "role": "slow densification engineering control"},
        {"parameter_id": "B", "beta": "1.189207115", "delta_theta_degrees": "22.5", "role": "current engineering baseline"},
        {"parameter_id": "C", "beta": "1.41421356237", "delta_theta_degrees": "15", "role": "medium-speed engineering control"},
        {"parameter_id": "D", "beta": "1.61803398875", "delta_theta_degrees": "15", "role": "research model"},
        {"parameter_id": "E", "beta": "1.73205080757", "delta_theta_degrees": "30", "role": "Eisenstein arithmetic benchmark"},
    )

    baseline = parameter_by_id("B")
    schedule = ScaleRotationSchedule(baseline)
    payload = baseline_b_formula_payload()

    assert isclose(baseline.beta, 2.0**0.25, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(baseline.beta**2, sqrt(2.0), rel_tol=0.0, abs_tol=1e-12)
    assert baseline.delta_theta_degrees == 22.5
    assert payload["density_growth_per_layer"] == payload["expected_density_growth_per_layer"]
    for layer_payload in payload["layers"]:
        layer = layer_payload["layer"]
        side_ratio = schedule.side_length(layer) / schedule.side_length(0)
        assert layer_payload["side_ratio"] == format(side_ratio, ".12g")
        assert layer_payload["area_ratio"] == format(baseline.beta ** (-2 * layer), ".12g")
        assert layer_payload["density_ratio"] == format(baseline.beta ** (2 * layer), ".12g")


def test_gpr1_02_finite_coverage_window_metrics_are_finite_and_reproducible() -> None:
    first = canonical_metric_payload()
    second = canonical_metric_payload()
    rows = build_metric_rows()

    assert first == second
    assert len(rows) == len(PARAMETER_MATRIX) * len(LAYER_GAPS) * len(DEFAULT_PHASE_SAMPLES) * len(LAYER_PHASE_POLICIES)
    assert all(row.distribution_count == 1 for row in rows)
    assert all(all_finite(row) for row in rows)
    assert all(row.branching_max >= 1 for row in rows)
    assert all(0.0 <= row.residual_mean <= 1.0 for row in rows)
    assert json.dumps(first, sort_keys=True)


def test_gpr1_03_baseline_b_rotation_phase_and_overlap_diagnostics_are_separated() -> None:
    baseline = parameter_by_id("B")
    schedule = ScaleRotationSchedule(baseline)
    rows = [row for row in build_metric_rows() if row.parameter_id == "B" and row.gap in (8, 16)]

    assert (baseline.delta_theta_degrees * 8) % 60.0 == 0.0
    assert (baseline.delta_theta_degrees * 16) % 60.0 == 0.0
    assert rows
    assert all(row.rotation_recurrence_mod60 for row in rows)
    assert {row.phase_policy for row in rows} == {"constant_local", "layer_drift_control"}
    assert len({(row.phase_label, row.phase_policy, row.overlap_entropy, row.phase_recurrence_score) for row in rows}) > 2
    constant = phase_score_for(schedule, 8, DEFAULT_PHASE_SAMPLES[0], LAYER_PHASE_POLICIES[0])
    drift = phase_score_for(schedule, 8, DEFAULT_PHASE_SAMPLES[0], LAYER_PHASE_POLICIES[1])
    assert constant != drift


def test_gpr1_04_control_matrix_reports_without_selecting_a_new_profile() -> None:
    rows = build_metric_rows()
    payload = experiment_window_payload()

    assert {parameter.parameter_id for parameter in PARAMETER_MATRIX} == {"A", "B", "C", "D", "E"}
    assert {row.parameter_id for row in rows} == {"A", "B", "C", "D", "E"}
    assert parameter_by_id("B").role == "current engineering baseline"
    assert "selected_profile" not in json.dumps(canonical_metric_payload(), sort_keys=True)
    assert payload["layer_phase_policies"] == ("constant_local", "layer_drift_control")


def test_gpr1_05_pure_geometry_runner_and_fixture_do_not_touch_memory_state(tmp_path) -> None:
    before = state_dirs(tmp_path)
    _ = canonical_metric_payload()
    after = state_dirs(tmp_path)

    assert before == after == {name: False for name in ("evidence", "capture", "cortex", "admission", "field", "assembly", "recall")}
    assert BASELINE_COMMIT == "5e5110a0b1c4f08e9b5cce1b4864f7d403a35cee"
    _assert_no_forbidden_imports(Path("validation/gpr1/run_gpr1_geometry_profile_regime.py"))
    _assert_no_forbidden_imports(Path("reference/python/tests/fixtures/gpr1/fixture.py"))


def _assert_no_forbidden_imports(path: Path) -> None:
    forbidden = {
        "nollm.dream_geometry.evidence",
        "nollm.dream_geometry.capture",
        "nollm.dream_geometry.cortex",
        "nollm.dream_geometry.admission",
        "nollm.dream_geometry.assembly",
        "nollm.dream_geometry.recall",
        "nollm.dream_geometry.adapters",
        "nollm.dream_geometry.batch_admission",
        "socket",
        "requests",
        "urllib",
    }
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert not (imports & forbidden)
