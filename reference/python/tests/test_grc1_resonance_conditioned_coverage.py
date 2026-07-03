from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[3]

from nollm.dream_geometry.geometry.schedules import LAYER_PHASE_POLICIES, PARAMETER_MATRIX
from nollm.dream_geometry.geometry.types import AxialCoord
from tests.fixtures.grc1.fixture import (
    BASELINE_COMMIT,
    COVERAGE_THRESHOLD,
    LAYER_GAPS,
    LATTICE_TOLERANCE,
    OBSERVATION_COUNT,
    PARAMETER_ID,
    SOURCE_AXIAL_STENCIL,
    TARGET_DISK_RADIUS,
    all_finite,
    base_layers_for_gap,
    baseline_parameter,
    build_observations,
    build_observations_from_order,
    canonical_payload,
    classification_counts,
    conditional_counts,
    coverage_summary,
    experiment_window_payload,
    recompute_alignment_class,
    recompute_coverage_metrics,
    state_dirs,
)


def test_grc1_01_real_api_complete_window_and_zero_state(tmp_path) -> None:
    before = state_dirs(tmp_path)
    observations = build_observations()
    after = state_dirs(tmp_path)
    window = experiment_window_payload()

    assert before == after == {name: False for name in ("evidence", "capture", "cortex", "field", "admission", "assembly", "recall", "atlas", "state")}
    assert baseline_parameter() == next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == "B")
    assert PARAMETER_ID == "B"
    assert LAYER_GAPS == (4, 8, 16)
    assert SOURCE_AXIAL_STENCIL == (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1), AxialCoord(2, -1))
    assert TARGET_DISK_RADIUS == 4
    assert COVERAGE_THRESHOLD == 1e-9
    assert window["phase_policies"] == tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES)
    assert {gap: len(base_layers_for_gap(gap)) for gap in LAYER_GAPS} == {4: 13, 8: 9, 16: 1}
    assert len(observations) == OBSERVATION_COUNT == 230
    assert all(observation.coverage_support_count == len(observation.kernel_weights_descending) for observation in observations)
    assert all_finite(observations)


def test_grc1_02_alignment_and_coverage_metrics_recompute_and_order_invariant() -> None:
    observations = build_observations()
    reversed_items = build_observations_from_order(tuple(reversed(LAYER_GAPS)), tuple(reversed(tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES))), tuple(reversed(SOURCE_AXIAL_STENCIL)))

    assert canonical_payload(observations) == canonical_payload(reversed_items)
    assert all(recompute_alignment_class(observation) == observation.alignment_class for observation in observations)
    for observation in observations:
        metrics = recompute_coverage_metrics(observation)
        assert metrics.branching_factor == observation.coverage_support_count
        assert metrics.effective_parent_count == observation.effective_support_count
        assert metrics.max_coverage_mass == observation.max_coverage_mass
        assert metrics.residual_mass == observation.coverage_residual_mass
    assert sum(classification_counts(observations).values()) == len(observations)
    assert sum(coverage_summary(observations).values()) == len(observations)
    assert sum(conditional_counts(observations).values()) == len(observations)


def test_grc1_03_candidate_recurrence_center_results_match_fixed_window() -> None:
    observations = build_observations()

    assert sum(1 for observation in observations if observation.layer_gap == 8 and observation.phase_policy == "constant_local" and observation.alignment_class == "exact_center_sublattice") == 45
    assert sum(1 for observation in observations if observation.layer_gap == 8 and observation.phase_policy == "layer_drift_control" and observation.alignment_class == "commensurate_phase_separated") == 45
    assert sum(1 for observation in observations if observation.layer_gap == 16 and observation.phase_policy == "constant_local" and observation.alignment_class == "exact_center_sublattice") == 5
    assert sum(1 for observation in observations if observation.layer_gap == 16 and observation.phase_policy == "layer_drift_control" and observation.alignment_class == "commensurate_phase_separated") == 5
    assert sum(1 for observation in observations if observation.layer_gap == 4 and observation.alignment_class == "noncommensurate") == 130


def test_grc1_04_exact_center_singleton_coverage_does_not_create_hierarchy_claim() -> None:
    exact = tuple(observation for observation in build_observations() if observation.alignment_class == "exact_center_sublattice")

    assert len(exact) == 50
    assert all(observation.coverage_singleton for observation in exact)
    assert all(observation.coverage_support_count == 1 for observation in exact)
    assert all(abs(observation.max_coverage_mass - 1.0) <= LATTICE_TOLERANCE for observation in exact)
    assert all(observation.coverage_residual_mass == 0.0 for observation in exact)


def test_grc1_05_phase_separation_is_not_equivalent_to_multi_support() -> None:
    observations = build_observations()
    gap8_drift = tuple(observation for observation in observations if observation.layer_gap == 8 and observation.phase_policy == "layer_drift_control")
    gap16_drift = tuple(observation for observation in observations if observation.layer_gap == 16 and observation.phase_policy == "layer_drift_control")

    assert len(gap8_drift) == 45
    assert any(observation.coverage_singleton for observation in gap8_drift)
    assert any(observation.coverage_multisupport for observation in gap8_drift)
    assert len(gap16_drift) == 5
    assert all(observation.coverage_singleton for observation in gap16_drift)
    assert not any(observation.coverage_multisupport for observation in gap16_drift)
    assert all(observation.alignment_class == "commensurate_phase_separated" for observation in gap8_drift + gap16_drift)


def test_grc1_06_boundary_imports_and_no_sealed_path_runtime(tmp_path) -> None:
    before = state_dirs(tmp_path)
    _ = canonical_payload()
    after = state_dirs(tmp_path)

    assert before == after
    assert BASELINE_COMMIT == "1c9b1f0498051cd62b66cfad2fa05a6071778ab3"
    _assert_no_forbidden_imports(REPO_ROOT / "reference/python/tests/fixtures/grc1/fixture.py")
    _assert_no_forbidden_imports(REPO_ROOT / "validation/grc1/run_grc1_resonance_conditioned_coverage.py")


def test_grc1_07_payload_has_no_forbidden_non_hierarchy_labels() -> None:
    payload = json.dumps(canonical_payload(), sort_keys=True).lower()
    for forbidden in (
        "parent",
        "child",
        "ancestor",
        "descendant",
        "eligible_for_compaction",
        "eligible_for_admission",
        "recall_rank",
        "semantic_importance",
        '"truth"',
        '"trust"',
    ):
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
        "subprocess",
    }
    allowed_prefixes = (
        "nollm.dream_geometry.geometry.chart",
        "nollm.dream_geometry.geometry.coverage",
        "nollm.dream_geometry.geometry.hexgrid",
        "nollm.dream_geometry.geometry.metrics",
        "nollm.dream_geometry.geometry.schedules",
        "nollm.dream_geometry.geometry.types",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert not (imports & forbidden)
    assert all(not item.startswith("nollm.dream_geometry") or item.startswith(allowed_prefixes) for item in imports)
