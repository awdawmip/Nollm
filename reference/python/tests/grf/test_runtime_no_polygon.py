from __future__ import annotations

import inspect

import nollm.grf.coverage_template as coverage_template


def test_runtime_source_does_not_import_or_call_polygon_geometry() -> None:
    source = inspect.getsource(coverage_template).lower()
    for forbidden in ("shapely", "polygon", "overlap", "clip", "sin(", "cos("):
        assert forbidden not in source


def test_runtime_source_has_no_object_semantic_terms() -> None:
    source = inspect.getsource(coverage_template).lower()
    for forbidden in ("stitch", "parent", "semantic edge"):
        assert forbidden not in source
