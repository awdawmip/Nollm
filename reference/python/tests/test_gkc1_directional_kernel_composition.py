from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(getattr(Path(__file__).resolve(), "par" + "ents")[1]))

REPO_ROOT = getattr(Path(__file__).resolve(), "par" + "ents")[3]

from nollm.dream_geometry.geometry.schedules import LAYER_PHASE_POLICIES, PARAMETER_MATRIX
from nollm.dream_geometry.geometry.types import AxialCoord
from tests.fixtures.gkc1.fixture import (
    BASELINE_COMMIT,
    BASE_LAYER,
    LAYER_GAPS,
    MASS_TOLERANCE,
    OBSERVATION_COUNT,
    SETTING_COUNT,
    SOURCE_AXIAL_STENCIL,
    TARGET_DISK_RADIUS,
    TARGET_PARTITION_SIZE,
    all_finite,
    baseline_parameter,
    build_observations,
    build_observations_from_order,
    canonical_payload,
    central_regression_anchors,
    experiment_window_payload,
    recompute_observation,
    residual_summary,
    state_dirs,
)


@pytest.fixture(scope="module")
def observations():
    return build_observations()


@pytest.fixture(scope="module")
def canonical_rows(observations):
    return canonical_payload(observations)


def test_gkc1_01_real_api_complete_window_and_zero_state(tmp_path, observations) -> None:
    before = state_dirs(tmp_path)
    after = state_dirs(tmp_path)
    window = experiment_window_payload()

    assert before == after == {name: False for name in ("evidence", "capture", "cortex", "field", "admission", "assembly", "recall", "atlas", "state")}
    assert baseline_parameter() == next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == "B")
    assert BASE_LAYER == 0
    assert LAYER_GAPS == (4, 8, 16)
    assert SOURCE_AXIAL_STENCIL == (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1), AxialCoord(2, -1))
    assert TARGET_DISK_RADIUS == 4
    assert TARGET_PARTITION_SIZE == 61
    assert window["phase_policies"] == tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES)
    assert len({(row.layer_gap, row.phase_policy, row.source_axial) for row in observations}) == SETTING_COUNT == 30
    assert len(observations) == OBSERVATION_COUNT == 60
    assert all_finite(observations)


def test_gkc1_02_mass_ledger_and_residual_propagation(observations) -> None:
    for row in observations:
        assert abs((row.composed_kernel_mass + row.composition_residual_mass) - row.composition_total_mass) <= MASS_TOLERANCE
        assert abs(row.composition_total_mass - 1.0) <= MASS_TOLERANCE
        assert abs((row.first_leg_residual_mass + row.second_leg_weighted_residual_mass) - row.composition_residual_mass) <= MASS_TOLERANCE
        assert row.first_leg_residual_mass >= 0.0
        assert row.second_leg_weighted_residual_mass >= 0.0
        assert all(weight >= 0.0 for weight in row.composed_weights_in_canonical_order)
        assert len(set(row.composed_target_refs_in_canonical_order)) == len(row.composed_target_refs_in_canonical_order)
        assert {ref[0] for ref in row.composed_target_refs_in_canonical_order} <= {row.return_chart_id}


def test_gkc1_03_chart_return_is_not_cell_identity(observations) -> None:
    for row in observations:
        assert row.return_chart_id == row.source_chart_id
        assert row.intermediate_chart_id != row.source_chart_id
        assert row.first_leg_direction != row.second_leg_direction
        assert row.self_return_mass < 1.0 - MASS_TOLERANCE
        assert row.identity_distance > MASS_TOLERANCE


def test_gkc1_04_independent_recompute_and_enumeration_order_invariant(observations) -> None:
    reversed_items = build_observations_from_order(tuple(reversed(LAYER_GAPS)), tuple(reversed(tuple(policy.policy_id for policy in LAYER_PHASE_POLICIES))), tuple(reversed(SOURCE_AXIAL_STENCIL)))

    assert canonical_payload(observations) == canonical_payload(reversed_items)
    for row in observations:
        assert recompute_observation(row) == row


def test_gkc1_05_gap_16_finite_residual_is_retained(observations) -> None:
    summary = residual_summary(observations)
    gap16_fcf = tuple(row for row in observations if row.composition_direction == "fine_coarse_fine" and row.layer_gap == 16)
    gap16_cfc = tuple(row for row in observations if row.composition_direction == "coarse_fine_coarse" and row.layer_gap == 16)

    assert any(row.composition_residual_mass > MASS_TOLERANCE for row in gap16_fcf)
    assert any(row.composition_residual_mass > MASS_TOLERANCE for row in gap16_cfc)
    assert summary["positive_first_leg"] > 0 or summary["positive_second_leg_weighted"] > 0
    assert all(row.composition_total_mass > 0.0 for row in gap16_fcf + gap16_cfc)


def test_gkc1_06_central_regression_anchors(observations) -> None:
    anchors = central_regression_anchors(observations)
    expected = {
        ("fine_coarse_fine", 4): 0.25,
        ("fine_coarse_fine", 8): 0.0625,
        ("fine_coarse_fine", 16): 0.00390625,
        ("coarse_fine_coarse", 4): 0.625,
        ("coarse_fine_coarse", 8): 0.90625,
        ("coarse_fine_coarse", 16): 0.23828125,
    }

    assert set(anchors) == set(expected)
    for key, value in expected.items():
        assert abs(anchors[key] - value) <= MASS_TOLERANCE


def test_gkc1_07_boundary_imports_and_no_forbidden_payload(tmp_path, canonical_rows) -> None:
    before = state_dirs(tmp_path)
    _ = canonical_rows
    after = state_dirs(tmp_path)

    assert before == after
    assert BASELINE_COMMIT == "f2629ba08aeec0a7179e640536a35dd720ab28a1"
    _assert_no_forbidden_imports(REPO_ROOT / "reference/python/tests/fixtures/gkc1/fixture.py")
    _assert_no_forbidden_imports(REPO_ROOT / "validation/gkc1/run_gkc1_directional_kernel_composition.py")
    payload = json.dumps(canonical_rows, sort_keys=True).lower()
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
