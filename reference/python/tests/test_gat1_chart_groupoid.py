from __future__ import annotations

import ast
import json
import sys
from math import isclose
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX, ScaleRotationSchedule
from nollm.dream_geometry.geometry.transform import SimilarityTransform, TransformWitness, cycle_residual, validate_transform
from nollm.dream_geometry.geometry.types import AxialCoord, Vec2
from tests.fixtures.gat1.fixture import (
    BASELINE_COMMIT,
    CHART_LAYER_TRIPLES,
    TOLERANCE,
    WITNESS_AXIALS,
    all_finite,
    baseline_parameter,
    build_cycle_checks,
    canonical_payload,
    chart_for,
    experiment_window_payload,
    fit_pair,
    negative_control_payload,
    render_report_metric,
    state_dirs,
    witness_points,
    witnesses_for,
)


def test_gat1_01_window_triples_and_witnesses_are_fixed() -> None:
    window = experiment_window_payload()
    checks = build_cycle_checks()

    assert baseline_parameter().parameter_id == "B"
    assert {parameter.parameter_id for parameter in PARAMETER_MATRIX if parameter.parameter_id == "B"} == {"B"}
    assert CHART_LAYER_TRIPLES == ((0, 1, 2), (0, 4, 8), (1, 5, 13), (0, 8, 16))
    assert WITNESS_AXIALS == (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1))
    assert len(set(WITNESS_AXIALS)) == 4
    assert window["phase_samples"] == tuple((phase.phase_q, phase.phase_r) for phase in DEFAULT_PHASE_SAMPLES)
    assert window["layer_phase_policies"] == tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES)
    assert len(checks) == 32
    assert window["cycle_count"] == 32
    assert all(check.triple in CHART_LAYER_TRIPLES for check in checks)
    assert json.dumps(canonical_payload(), sort_keys=True)


def test_gat1_02_pair_fit_validate_inverse_and_composition_are_real() -> None:
    checks = build_cycle_checks()
    limit = TOLERANCE.coordinate_abs_tol + TOLERANCE.coordinate_rel_tol

    for check in checks:
        assert len(check.pair_checks) == 3
        assert all(all_finite(item) for item in (check,))
        for pair in check.pair_checks:
            assert pair.transform.orientation == "orientation_preserving"
            assert pair.validation.state_recommendation == "verified"
            assert pair.validation.residual.witness_count == 4
            assert pair.validation.residual.witness_geometry_status == "nondegenerate"
            assert pair.validation.residual.max_residual <= 10.0 * limit
            assert pair.scale_error <= 10.0 * limit
            assert pair.rotation_error <= 10.0 * limit
            assert pair.inverse_point_error <= 10.0 * limit
            assert pair.composition_point_error <= 10.0 * limit


def test_gat1_03_all_triangle_cycles_are_verified_and_non_degenerate() -> None:
    seen = set()
    limit = TOLERANCE.coordinate_abs_tol + TOLERANCE.coordinate_rel_tol
    for check in build_cycle_checks():
        key = (check.triple, check.phase_label, check.phase_policy)
        seen.add(key)
        assert check.cycle.state_recommendation == "verified"
        assert check.cycle.witness_geometry_status == "nondegenerate"
        assert check.cycle.witness_count == 4
        assert check.cycle.max_residual <= 10.0 * limit
        assert check.cycle.rms_residual <= 10.0 * limit
        assert check.cycle.linear_identity_error <= 10.0 * limit
        assert check.cycle.translation_identity_error <= 10.0 * limit
    assert len(seen) == 32


def test_gat1_04_negative_controls_do_not_verify() -> None:
    states = negative_control_payload()
    assert states["shifted_target"] != "verified"
    assert states["duplicate_witness"] != "verified"
    assert states["tampered_cycle"] != "verified"
    assert states["orientation_reversing"] == "rejected"

    schedule = ScaleRotationSchedule(baseline_parameter())
    source = chart_for(schedule, 0, DEFAULT_PHASE_SAMPLES[0], LAYER_PHASE_POLICIES[0])
    target = chart_for(schedule, 1, DEFAULT_PHASE_SAMPLES[0], LAYER_PHASE_POLICIES[0])
    validation = fit_pair(source, target)
    collinear_points = (Vec2(0, 0), Vec2(1, 0), Vec2(2, 0))
    collinear = tuple(TransformWitness(point, point) for point in collinear_points)
    assert validate_transform(SimilarityTransform(1.0, 0.0, Vec2(0, 0)), collinear, 1.0).state_recommendation != "verified"
    assert cycle_residual((validation.transform,), witness_points(source), source.side_length, TOLERANCE).state_recommendation != "verified"


def test_gat1_05_purity_and_sealed_boundary(tmp_path) -> None:
    before = state_dirs(tmp_path)
    _ = canonical_payload()
    after = state_dirs(tmp_path)

    assert before == after == {name: False for name in ("evidence", "capture", "cortex", "admission", "field", "assembly", "recall", "atlas")}
    assert BASELINE_COMMIT == "ffe76e4ed574209e05ef3f8e35440aa50c0cd234"
    _assert_no_forbidden_imports(Path("validation/gat1/run_gat1_chart_groupoid.py"))
    _assert_no_forbidden_imports(Path("reference/python/tests/fixtures/gat1/fixture.py"))


def test_gat1_06_same_axial_label_fixture_is_not_overlap_or_atlas_state() -> None:
    schedule = ScaleRotationSchedule(baseline_parameter())
    source = chart_for(schedule, 0, DEFAULT_PHASE_SAMPLES[0], LAYER_PHASE_POLICIES[0])
    target = chart_for(schedule, 1, DEFAULT_PHASE_SAMPLES[0], LAYER_PHASE_POLICIES[0])
    witnesses = witnesses_for(source, target)

    assert len(witnesses) == 4
    assert "overlap" not in json.dumps(canonical_payload(), sort_keys=True).lower()
    assert "atlas merge" not in json.dumps(canonical_payload(), sort_keys=True).lower()


def test_gat1_c1_01_reporting_noise_floor_uses_bound_not_zero() -> None:
    assert render_report_metric(1.1102230246251565e-16) == "\u22641.000000e-12"
    assert render_report_metric(9.930136612989092e-16) == "\u22641.000000e-12"
    assert render_report_metric(-9.930136612989092e-16) == "\u22641.000000e-12"
    assert render_report_metric(1.1102230246251565e-16) != "0.000000e+00"


def test_gat1_c1_02_report_renderer_preserves_values_above_floor() -> None:
    assert render_report_metric(1.0001e-12) == "1.000100e-12"
    assert render_report_metric(-1.0001e-12) == "-1.000100e-12"


def test_gat1_c1_03_raw_validation_values_and_states_remain_separate_from_reporting() -> None:
    checks = build_cycle_checks()
    assert checks
    assert any(0.0 < check.cycle.max_residual <= 1e-12 for check in checks)
    assert all(check.cycle.state_recommendation == "verified" for check in checks)
    assert all(pair.validation.state_recommendation == "verified" for check in checks for pair in check.pair_checks)
    assert any(render_report_metric(check.cycle.max_residual) == "\u22641.000000e-12" for check in checks)
    assert all(isinstance(check.cycle.max_residual, float) for check in checks)


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
        "sqlite3",
    }
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert not (imports & forbidden)
