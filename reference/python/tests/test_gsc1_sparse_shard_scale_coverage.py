from __future__ import annotations

import ast
import json
import sys
from math import isfinite
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[3]

from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX
from nollm.dream_geometry.geometry.types import AxialCoord
from tests.fixtures.gsc1.fixture import (
    BASELINE_COMMIT,
    BASE_LAYERS,
    LAYER_GAPS,
    OCCUPANCY_PATTERNS,
    PHASES,
    SOURCE_DISTRIBUTION_CALL_COUNT,
    TARGET_RADIUS,
    THRESHOLD,
    TOLERANCE,
    all_finite,
    baseline_parameter,
    build_collision_summaries,
    build_observations,
    canonical_observation_payload,
    canonical_summary_payload,
    experiment_window_payload,
    observations_for_pattern,
    pattern_markers,
    render_report_metric,
    state_dirs,
    summaries_for_observations,
)


def test_gsc1_01_fixed_window_and_distribution_count() -> None:
    window = experiment_window_payload()
    observations = build_observations()

    assert baseline_parameter().parameter_id == "B"
    assert {parameter.parameter_id for parameter in PARAMETER_MATRIX if parameter.parameter_id == "B"} == {"B"}
    assert LAYER_GAPS == (1, 4, 8)
    assert BASE_LAYERS == (0, 8)
    assert PHASES == tuple(phase for phase in DEFAULT_PHASE_SAMPLES if (phase.phase_q, phase.phase_r) in {(0.0, 0.0), (0.5, 0.0)})
    assert window["layer_phase_policies"] == tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES)
    assert TARGET_RADIUS == 4
    assert THRESHOLD == 1e-9
    assert TOLERANCE.coordinate_abs_tol == 1e-12
    assert all(observation.source_layer <= 16 for observation in observations)
    assert len(observations) == SOURCE_DISTRIBUTION_CALL_COUNT == 144
    assert {pattern: sum(1 for observation in observations if observation.pattern_id == pattern) for pattern, _ in OCCUPANCY_PATTERNS} == {
        "singleton": 24,
        "local_fork": 72,
        "separated_pair": 48,
    }
    assert json.dumps(canonical_observation_payload(), sort_keys=True)


def test_gsc1_02_source_geometry_is_independent_from_occupancy_grouping() -> None:
    observations = build_observations()
    singleton_s0 = {
        (item.layer_gap, item.base_layer, item.phase_label, item.phase_policy): item
        for item in observations
        if item.pattern_id == "singleton" and item.marker_id == "s0"
    }
    fork_f0 = {
        (item.layer_gap, item.base_layer, item.phase_label, item.phase_policy): item
        for item in observations
        if item.pattern_id == "local_fork" and item.marker_id == "f0"
    }

    assert singleton_s0.keys() == fork_f0.keys()
    for key, left in singleton_s0.items():
        right = fork_f0[key]
        assert left.source_axial == right.source_axial == AxialCoord(0, 0)
        assert left.source_layer == right.source_layer
        assert left.target_chart_id == right.target_chart_id
        assert left.target_refs == right.target_refs
        assert left.kernel_weights == right.kernel_weights
        assert left.residual_mass == right.residual_mass
        assert left.residual_reasons == right.residual_reasons


def test_gsc1_03_support_collision_summaries_preserve_marker_identity() -> None:
    observations = build_observations()
    summaries = build_collision_summaries()
    payload = json.dumps(canonical_summary_payload(), sort_keys=True).lower()

    assert summaries
    assert any(summary.collision_target_count > 0 for summary in summaries)
    assert "parent" not in payload
    assert "child" not in payload
    assert "owner" not in payload
    assert "primary" not in payload
    for summary in summaries:
        grouped = [
            observation
            for observation in observations
            if (
                observation.pattern_id,
                observation.base_layer,
                observation.layer_gap,
                observation.phase_label,
                observation.phase_policy,
            )
            == (summary.pattern_id, summary.base_layer, summary.layer_gap, summary.phase_label, summary.phase_policy)
        ]
        assert summary.source_count == len({observation.marker_id for observation in grouped})
        assert summary.incidence_count == sum(len(observation.target_refs) for observation in grouped)
        assert summary.unique_target_count == len(summary.target_marker_ids)
        assert summary.collision_target_count == sum(1 for _, marker_ids in summary.target_marker_ids if len(marker_ids) > 1)
        assert all(tuple(sorted(marker_ids)) == marker_ids for _, marker_ids in summary.target_marker_ids)


def test_gsc1_04_input_order_does_not_affect_canonical_results() -> None:
    for pattern_id in ("local_fork", "separated_pair"):
        markers = pattern_markers(pattern_id)
        original = observations_for_pattern(pattern_id, markers)
        reversed_items = observations_for_pattern(pattern_id, tuple(reversed(markers)))

        assert canonical_observation_payload(original) == canonical_observation_payload(reversed_items)
        assert canonical_summary_payload(summaries_for_observations(original)) == canonical_summary_payload(summaries_for_observations(reversed_items))


def test_gsc1_05_finiteness_and_source_boundaries() -> None:
    observations = build_observations()
    declared_markers = {marker.marker_id for _, markers in OCCUPANCY_PATTERNS for marker in markers}

    assert all_finite(observations)
    for observation in observations:
        assert observation.marker_id in declared_markers
        assert 0.0 <= observation.residual_mass <= 1.0
        assert 0.0 <= observation.total_mass <= 1.0 + TOLERANCE.area_abs_tol + TOLERANCE.area_rel_tol
        assert observation.partition_size == 61
        assert observation.target_refs
        assert len(observation.target_refs) == len(observation.kernel_weights)
        assert all(isfinite(float(weight)) and float(weight) >= 0.0 for weight in observation.kernel_weights)


def test_gsc1_06_purity_and_no_runtime_state(tmp_path) -> None:
    before = state_dirs(tmp_path)
    _ = canonical_observation_payload()
    _ = canonical_summary_payload()
    after = state_dirs(tmp_path)

    assert before == after == {name: False for name in ("evidence", "capture", "cortex", "admission", "field", "assembly", "recall", "atlas")}
    assert BASELINE_COMMIT == "7c3ef9d3a83f87a0dccfa7e9018692be9cdc69af"
    _assert_no_forbidden_imports(REPO_ROOT / "reference/python/tests/fixtures/gsc1/fixture.py")
    _assert_no_forbidden_imports(REPO_ROOT / "validation/gsc1/run_gsc1_sparse_shard_scale_coverage.py")


def test_gsc1_07_reporting_noise_floor_uses_bound_not_zero() -> None:
    assert render_report_metric(1.1102230246251565e-16) == "\u22641.000000e-12"
    assert render_report_metric(-9.930136612989092e-16) == "\u22641.000000e-12"
    assert render_report_metric(1.1102230246251565e-16) != "0.000000e+00"
    assert render_report_metric(1.0001e-12) == "1.000100e-12"


def _assert_no_forbidden_imports(path: Path) -> None:
    forbidden = {
        "nollm.dream_geometry.evidence",
        "nollm.dream_geometry.capture",
        "nollm.dream_geometry.cortex",
        "nollm.dream_geometry.admission",
        "nollm.dream_geometry.assembly",
        "nollm.dream_geometry.recall",
        "nollm.dream_geometry.field",
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
