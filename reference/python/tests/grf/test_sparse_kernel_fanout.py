from __future__ import annotations

import pytest

from nollm.grf.cell_address import CellAddress
from nollm.grf.coverage_template import COVERAGE_UP, DEFAULT_FANOUT_LIMIT, CoverageTemplateCompiler, expand_lateral, expand_template


def test_template_and_runtime_fanout_have_hard_bound() -> None:
    template = CoverageTemplateCompiler(fanout_limit=DEFAULT_FANOUT_LIMIT).compile("eisenstein_exact_v1", COVERAGE_UP)
    assert len(template.entries) <= DEFAULT_FANOUT_LIMIT
    expanded = expand_template(CellAddress("eisenstein_exact_v1", "chart_a", 0, 0, 0), template)
    assert len(expanded) <= DEFAULT_FANOUT_LIMIT


def test_lateral_ring_two_exceeds_default_bound() -> None:
    cell = CellAddress("aligned_baseline_v1", "chart_a", 0, 0, 0)
    with pytest.raises(ValueError):
        expand_lateral(cell, ring=2, fanout_limit=DEFAULT_FANOUT_LIMIT)


def test_cell_address_rejects_float_coordinates_and_empty_chart() -> None:
    with pytest.raises(TypeError):
        CellAddress("aligned_baseline_v1", "chart_a", 0, 1.0, 0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        CellAddress("aligned_baseline_v1", "", 0, 1, 0)
