from __future__ import annotations

import pytest

from nollm.grf.cell_address import CellAddress
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.local_patch import LocalPatch


def cell(profile_id: str = "eisenstein_exact_v1", chart_id: str = "chart_a", q: int = 0, r: int = 0) -> CellAddress:
    return CellAddress(profile_id, chart_id, 1, q, r)


def patch(**overrides) -> LocalPatch:
    values = {
        "patch_id": "patch_a",
        "island_id": "island_a",
        "chart_id": "chart_a",
        "profile_id": "eisenstein_exact_v1",
        "center_cell": cell(),
        "occupied_cells": (cell(q=0, r=0), cell(q=1, r=0)),
        "boundary_cells": (),
        "state": "floating",
        "density_pressure_q16": Q16_ONE // 2,
        "ambiguity_q16": Q16_ONE // 8,
    }
    values.update(overrides)
    return LocalPatch(**values)


def test_patch_rejects_mixed_profile_or_chart_cells() -> None:
    with pytest.raises(ValueError):
        patch(occupied_cells=(cell("aligned_baseline_v1"),))
    with pytest.raises(ValueError):
        patch(boundary_cells=(cell(chart_id="chart_b"),))
    with pytest.raises(ValueError):
        patch(center_cell=cell(q=5), occupied_cells=(cell(q=0),))


def test_patch_stable_serialization_and_boundary_empty() -> None:
    local = patch()
    rendered = local.to_mapping()
    assert rendered == local.to_mapping()
    assert rendered["boundary_cells"] == ()
    assert rendered["not_folder"] is True
    assert rendered["not_fact_merge"] is True
    assert "parent" not in rendered and "topic" not in rendered


def test_patch_state_transition_and_cell_float_rejection() -> None:
    assert patch().transition("placed").state == "placed"
    with pytest.raises(ValueError):
        patch().transition("stitched")
    with pytest.raises(TypeError):
        CellAddress("eisenstein_exact_v1", "chart_a", 1, 1.0, 0)  # type: ignore[arg-type]
