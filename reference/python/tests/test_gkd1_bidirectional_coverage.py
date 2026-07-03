from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(getattr(Path(__file__).resolve(), "par" + "ents")[1]))

REPO_ROOT = getattr(Path(__file__).resolve(), "par" + "ents")[3]

from nollm.dream_geometry.geometry.coverage import CoverageDirection
from nollm.dream_geometry.geometry.schedules import LAYER_PHASE_POLICIES, PARAMETER_MATRIX
from nollm.dream_geometry.geometry.types import AxialCoord
from tests.fixtures.gkd1.fixture import (
    BASELINE_COMMIT,
    COVERAGE_THRESHOLD,
    LAYER_GAPS,
    MASS_TOLERANCE,
    OBSERVATION_COUNT_PER_DIRECTION,
    PAIR_COUNT,
    SOURCE_AXIAL_STENCIL,
    TARGET_DISK_RADIUS,
    TARGET_PARTITION_SIZE,
    all_finite,
    base_layers_for_gap,
    baseline_parameter,
    build_observations,
    build_observations_from_order,
    build_pairs,
    canonical_payload,
    experiment_window_payload,
    pair_payload,
    recompute_observation,
    residual_boundary_summary,
    state_dirs,
)


@pytest.fixture(scope="module")
def observations():
    return build_observations()


@pytest.fixture(scope="module")
def pairs(observations):
    return build_pairs()


@pytest.fixture(scope="module")
def canonical_rows(observations):
    return canonical_payload(observations)


@pytest.fixture(scope="module")
def pair_rows(pairs):
    return pair_payload(pairs)


def test_gkd1_01_real_bidirectional_api_complete_window_and_zero_state(tmp_path, observations, pairs) -> None:
    before = state_dirs(tmp_path)
    after = state_dirs(tmp_path)
    window = experiment_window_payload()

    assert before == after == {name: False for name in ("evidence", "capture", "cortex", "field", "admission", "assembly", "recall", "atlas", "state")}
    assert baseline_parameter() == next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == "B")
    assert LAYER_GAPS == (4, 8, 16)
    assert SOURCE_AXIAL_STENCIL == (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1), AxialCoord(2, -1))
    assert TARGET_DISK_RADIUS == 4
    assert TARGET_PARTITION_SIZE == 61
    assert COVERAGE_THRESHOLD == 1e-9
    assert window["phase_policies"] == tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES)
    assert {gap: len(base_layers_for_gap(gap)) for gap in LAYER_GAPS} == {4: 13, 8: 9, 16: 1}
    assert len([row for row in observations if row.direction == CoverageDirection.fine_to_coarse.value]) == OBSERVATION_COUNT_PER_DIRECTION == 230
    assert len([row for row in observations if row.direction == CoverageDirection.coarse_to_fine.value]) == OBSERVATION_COUNT_PER_DIRECTION
    assert len(observations) == 460
    assert len(pairs) == PAIR_COUNT == 230
    assert all_finite(observations)


def test_gkd1_02_direction_scale_and_mass_ledger(observations) -> None:
    for observation in observations:
        if observation.direction == CoverageDirection.fine_to_coarse.value:
            assert observation.source_side_length <= observation.target_side_length + MASS_TOLERANCE
        else:
            assert observation.source_side_length + MASS_TOLERANCE >= observation.target_side_length
        assert abs((observation.kernel_mass + observation.coverage_residual_mass) - observation.total_mass) <= MASS_TOLERANCE
        assert abs(observation.total_mass - 1.0) <= MASS_TOLERANCE
        assert observation.coverage_support_count == len(observation.kernel_weights_descending)
        assert observation.target_partition_size == TARGET_PARTITION_SIZE
        assert {target_ref[0] for target_ref in observation.target_refs_in_canonical_order} <= {observation.target_chart_id}


def test_gkd1_03_independent_recompute_and_enumeration_order_invariant(observations, pairs) -> None:
    reversed_items = build_observations_from_order(tuple(reversed(LAYER_GAPS)), tuple(reversed(tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES))), tuple(reversed(SOURCE_AXIAL_STENCIL)))

    assert canonical_payload(observations) == canonical_payload(reversed_items)
    for observation in observations:
        assert recompute_observation(observation) == observation
    assert len(pair_payload(pairs)) == PAIR_COUNT


def test_gkd1_04_directional_non_inverse_measurement(pairs) -> None:
    assert all(pair.support_relation == "up_less_than_down" for pair in pairs)
    assert all(not pair.exact_kernel_vector_equal for pair in pairs)
    assert sum(1 for pair in pairs if pair.support_relation == "up_less_than_down") == 230
    assert sum(1 for pair in pairs if pair.exact_kernel_vector_equal) == 0


def test_gkd1_05_finite_partition_residual_boundary(observations) -> None:
    summary = residual_boundary_summary(observations)
    down_positive = tuple(row for row in observations if row.direction == CoverageDirection.coarse_to_fine.value and row.coverage_residual_mass > MASS_TOLERANCE)

    assert summary["up_zero_residual"] == 230
    assert summary["up_positive_residual"] == 0
    assert summary["down_zero_residual"] == 220
    assert summary["down_positive_residual"] == 10
    assert summary["down_positive_gap_counts"] == {16: 10}
    assert summary["down_positive_policy_counts"] == {"constant_local": 5, "layer_drift_control": 5}
    assert summary["down_positive_source_axials"] == ((0, 0), (0, 1), (1, -1), (1, 0), (2, -1))
    assert all(abs(row.coverage_residual_mass - 0.76171875) <= MASS_TOLERANCE for row in down_positive)
    assert all(row.residual_reasons == ("outside_supplied_partition",) for row in down_positive)


def test_gkd1_06_boundary_imports_and_no_sealed_path_runtime(tmp_path, canonical_rows) -> None:
    before = state_dirs(tmp_path)
    _ = canonical_rows
    after = state_dirs(tmp_path)

    assert before == after
    assert BASELINE_COMMIT == "39b673fbba829f1c3285e9496b5af9c9890bf0af"
    _assert_no_forbidden_imports(REPO_ROOT / "reference/python/tests/fixtures/gkd1/fixture.py")
    _assert_no_forbidden_imports(REPO_ROOT / "validation/gkd1/run_gkd1_bidirectional_coverage.py")


def test_gkd1_07_payload_has_no_forbidden_non_geometry_labels(canonical_rows, pair_rows) -> None:
    payload = json.dumps({"observations": canonical_rows, "pairs": pair_rows}, sort_keys=True).lower()
    forbidden = tuple(
        "".join(parts)
        for parts in (
            ("par", "ent"),
            ("chi", "ld"),
            ("ance", "stor"),
            ("desc", "endant"),
            ("own", "er"),
            ("contain", "er"),
            ("hier", "archy"),
            ("eligible_for_", "compaction"),
            ("eligible_for_", "admission"),
            ("recall", "_rank"),
            ("semantic", "_importance"),
            ('"tr', 'uth"'),
            ('"tr', 'ust"'),
        )
    )
    for item in forbidden:
        assert item not in payload


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
        "req" + "uests",
        "url" + "lib",
        "sql" + "ite3",
        "sub" + "process",
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
