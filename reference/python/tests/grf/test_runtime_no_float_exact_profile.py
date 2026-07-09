from __future__ import annotations

import inspect

from nollm.grf.cell_address import CellAddress
from nollm.grf.coverage_template import COVERAGE_UP, CoverageTemplateCompiler, expand_template
import nollm.grf.coverage_template as coverage_template


def test_exact_profile_runtime_expands_without_float_source() -> None:
    source = inspect.getsource(coverage_template)
    assert "float(" not in source
    assert "math." not in source

    template = CoverageTemplateCompiler().compile("eisenstein_exact_v1", COVERAGE_UP)
    cell = CellAddress("eisenstein_exact_v1", "chart_a", 3, 4, -2, "phase_a")
    first = expand_template(cell, template)
    second = expand_template(cell, template)
    assert first == second
    assert all(type(weight) is int for _, weight in first)
    assert all(type(address.q) is int and type(address.r) is int for address, _ in first)
