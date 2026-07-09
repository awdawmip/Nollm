from __future__ import annotations

import inspect

import nollm.grf.relation_field as relation_field_module
from grf_runtime_fixture import relation_field
from nollm.grf.coverage_template import COVERAGE_UP
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.propagation import SparseActivation


def test_relation_field_runtime_uses_template_lookup_without_polygon_or_float() -> None:
    source = inspect.getsource(relation_field_module).lower()
    for forbidden in ("shapely", "polygon", "sin(", "cos(", "float(", "embedding", "semantic search"):
        assert forbidden not in source
    field = relation_field()
    start = field.placements[0].geometry_mark.cell
    out = field.step(SparseActivation(start, Q16_ONE, "query"), (COVERAGE_UP,), 1, 0)
    assert out
    assert all(item[1].kernel_type == COVERAGE_UP for item in out)
