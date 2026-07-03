from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[3]

from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX
from nollm.dream_geometry.geometry.types import AxialCoord
from tests.fixtures.gra1.fixture import (
    ANGLE_TOLERANCE_DEGREES,
    AXIAL_CENTER_STENCIL,
    BASELINE_COMMIT,
    LATTICE_TOLERANCE,
    LAYER_GAPS,
    MAX_LAYER,
    OBSERVATION_COUNT,
    PARAMETER_ID,
    SCALE_TOLERANCE,
    all_finite,
    base_layers_for_gap,
    baseline_parameter,
    build_observations,
    build_observations_from_order,
    canonical_payload,
    classification_totals,
    experiment_window_payload,
    recompute_classification,
    state_dirs,
    summary_counts,
)


def test_gra1_01_real_schedule_and_complete_window() -> None:
    observations = build_observations()
    window = experiment_window_payload()

    assert baseline_parameter() == next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == "B")
    assert PARAMETER_ID == "B"
    assert LAYER_GAPS == (1, 2, 4, 8, 16)
    assert MAX_LAYER == 16
    assert AXIAL_CENTER_STENCIL == (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1), AxialCoord(2, -1))
    assert window["phase_samples"] == tuple((phase.phase_q, phase.phase_r) for phase in DEFAULT_PHASE_SAMPLES)
    assert window["phase_policies"] == tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES)
    assert {gap: len(base_layers_for_gap(gap)) for gap in LAYER_GAPS} == {1: 16, 2: 15, 4: 13, 8: 9, 16: 1}
    assert len(observations) == OBSERVATION_COUNT == (16 + 15 + 13 + 9 + 1) * 4 * 2
    assert all(len(observation.center_map_rows) == 5 for observation in observations)
    assert json.dumps(canonical_payload(), sort_keys=True)


def test_gra1_02_scale_rotation_candidate_recurrence_values() -> None:
    observations = build_observations()
    for gap, expected_scale in ((8, 4), (16, 16)):
        selected = tuple(observation for observation in observations if observation.layer_gap == gap)
        assert selected
        assert all(abs(observation.side_ratio - expected_scale) <= SCALE_TOLERANCE for observation in selected)
        assert all(observation.rotation_mod_hex_degrees <= ANGLE_TOLERANCE_DEGREES for observation in selected)
        assert all(observation.nearest_integer_scale == expected_scale for observation in selected)
        assert all(observation.scale_integer_error <= SCALE_TOLERANCE for observation in selected)
    for gap in (1, 2, 4):
        assert all(observation.classification == "noncommensurate" for observation in observations if observation.layer_gap == gap)


def test_gra1_03_constant_local_center_lattice_findings_are_computed() -> None:
    observations = build_observations()
    for gap in (8, 16):
        selected = tuple(
            observation
            for observation in observations
            if observation.layer_gap == gap and observation.phase_label == "(0,0)" and observation.phase_policy == "constant_local"
        )
        assert len(selected) == len(base_layers_for_gap(gap))
        assert all(observation.classification == recompute_classification(observation) for observation in selected)
        assert all(observation.classification == "exact_center_sublattice" for observation in selected)
        assert all(observation.max_center_map_residual <= LATTICE_TOLERANCE for observation in selected)


def test_gra1_04_layer_drift_records_phase_separation_without_erasing_recurrence() -> None:
    observations = build_observations()
    for gap in (8, 16):
        selected = tuple(
            observation
            for observation in observations
            if observation.layer_gap == gap and observation.phase_label == "(0,0)" and observation.phase_policy == "layer_drift_control"
        )
        assert len(selected) == len(base_layers_for_gap(gap))
        assert all(observation.rotation_mod_hex_degrees <= ANGLE_TOLERANCE_DEGREES for observation in selected)
        assert all(observation.scale_integer_error <= SCALE_TOLERANCE for observation in selected)
        assert all(observation.classification in {"exact_center_sublattice", "commensurate_phase_separated"} for observation in selected)
        assert any(observation.classification == "commensurate_phase_separated" for observation in selected)
        assert all(observation.relative_phase is not None for observation in selected)


def test_gra1_05_classification_recomputes_and_order_does_not_affect_payload() -> None:
    observations = build_observations()

    assert canonical_payload(observations) == canonical_payload(build_observations_from_order(tuple(reversed(LAYER_GAPS))))
    assert all(recompute_classification(observation) == observation.classification for observation in observations)
    assert sum(classification_totals(observations).values()) == len(observations)
    assert sum(summary_counts(observations).values()) == len(observations)
    assert all_finite(observations)


def test_gra1_06_no_production_memory_or_runtime_boundary(tmp_path) -> None:
    before = state_dirs(tmp_path)
    _ = canonical_payload()
    after = state_dirs(tmp_path)

    assert before == after == {name: False for name in ("evidence", "capture", "cortex", "field", "admission", "assembly", "recall", "atlas", "state")}
    assert BASELINE_COMMIT == "2ce5c13f48c2478010acb73c4a612678e7830b10"
    _assert_no_forbidden_imports(REPO_ROOT / "reference/python/tests/fixtures/gra1/fixture.py")
    _assert_no_forbidden_imports(REPO_ROOT / "validation/gra1/run_gra1_rotation_scale_resonance.py")


def test_gra1_07_payload_has_no_hierarchy_or_permission_conclusions() -> None:
    payload = json.dumps(canonical_payload(), sort_keys=True).lower()
    for forbidden in ("parent", "child", "cover", "admission", "recall", "compression", "dreamshard", "field"):
        assert forbidden not in payload


def _assert_no_forbidden_imports(path: Path) -> None:
    forbidden = {
        "nollm.dream_geometry.evidence",
        "nollm.dream_geometry.capture",
        "nollm.dream_geometry.cortex",
        "nollm.dream_geometry.field",
        "nollm.dream_geometry.admission",
        "nollm.dream_geometry.assembly",
        "nollm.dream_geometry.recall",
        "nollm.dream_geometry.adapters",
        "socket",
        "requests",
        "urllib",
        "sqlite3",
    }
    allowed = {
        "nollm.dream_geometry.geometry.chart",
        "nollm.dream_geometry.geometry.schedules",
        "nollm.dream_geometry.geometry.types",
    }
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert not (imports & forbidden)
    assert all(not item.startswith("nollm.dream_geometry") or item in allowed for item in imports)
