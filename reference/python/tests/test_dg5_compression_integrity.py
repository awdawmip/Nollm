from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from nollm.dream_geometry.compression import CompressionPlanningError, plan_trace_compaction, validate_compression_plan
from nollm.dream_geometry.compression.types import CompressionPlan
from nollm.dream_geometry.compression.view import expand_compression_plan
from tests.fixtures.dg5.fixture import exact_duplicate_pair, mixed_fixture, trace_index

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_dg5_11_missing_trace_is_rejected() -> None:
    traces = mixed_fixture()
    plan = plan_trace_compaction(traces)
    index = trace_index(traces)
    index.pop("dup-a")
    with pytest.raises(CompressionPlanningError) as exc:
        expand_compression_plan(plan, index)
    assert exc.value.reason_code == "DG5_EXPANSION_TRACE_MISSING"


def test_dg5_12_trace_fingerprint_drift_is_rejected() -> None:
    traces = exact_duplicate_pair()
    plan = plan_trace_compaction(traces)
    index = trace_index(traces)
    index["dup-a"] = replace(index["dup-a"], mass=0.99)
    with pytest.raises(CompressionPlanningError) as exc:
        expand_compression_plan(plan, index)
    assert exc.value.reason_code == "DG5_EXPANSION_TRACE_FINGERPRINT_MISMATCH"


def test_dg5_13_tampered_plan_manifest_or_fingerprint_is_rejected() -> None:
    plan = plan_trace_compaction(mixed_fixture())
    bad_count = _copy_plan(plan, input_trace_count=99)
    with pytest.raises(CompressionPlanningError) as exc:
        validate_compression_plan(bad_count)
    assert exc.value.reason_code == "DG5_PLAN_MANIFEST_INVALID"
    bad_fingerprint = _copy_plan(plan, plan_fingerprint="bad")
    with pytest.raises(CompressionPlanningError) as exc:
        validate_compression_plan(bad_fingerprint)
    assert exc.value.reason_code == "DG5_PLAN_FINGERPRINT_MISMATCH"


def test_dg5_14_unexpected_trace_index_entry_is_rejected() -> None:
    traces = exact_duplicate_pair()
    plan = plan_trace_compaction(traces)
    index = trace_index(traces)
    index["extra"] = replace(traces[0], trace_id="extra")
    with pytest.raises(CompressionPlanningError) as exc:
        expand_compression_plan(plan, index)
    assert exc.value.reason_code == "DG5_UNEXPECTED_TRACE_INDEX_ENTRY"


def test_dg5_15_expansion_matches_original_canonical_manifest() -> None:
    traces = mixed_fixture()
    plan = plan_trace_compaction(traces)
    expanded = expand_compression_plan(plan, trace_index(traces))
    expected = tuple(trace_index(traces)[trace_id] for trace_id in plan.input_trace_ids)
    assert expanded == expected


def test_dg5_production_imports_stay_inside_allowed_boundary() -> None:
    forbidden = {
        "nollm.dream_geometry.evidence",
        "nollm.dream_geometry.capture",
        "nollm.dream_geometry.cortex",
        "nollm.dream_geometry.admission",
        "nollm.dream_geometry.assembly",
        "nollm.dream_geometry.recall",
        "nollm.dream_geometry.adapters",
        "nollm.dream_geometry.geometry",
        "sqlite3",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "openai",
        "transformers",
        "sentence_transformers",
        "langchain",
    }
    allowed_prefixes = (
        "nollm.dream_geometry.field.compaction",
        "nollm.dream_geometry.field.types",
        "nollm.dream_geometry.protocol.contracts",
        "nollm.dream_geometry.compression",
    )
    for path in (REPO_ROOT / "reference/python/nollm/dream_geometry/compression").glob("*.py"):
        imports = _imports(path)
        assert not (imports & forbidden)
        assert all(not item.startswith("nollm.dream_geometry.") or item.startswith(allowed_prefixes) for item in imports)


def _copy_plan(plan: CompressionPlan, **changes) -> CompressionPlan:
    values = {field: getattr(plan, field) for field in CompressionPlan.__dataclass_fields__}
    values.update(changes)
    return CompressionPlan(**values)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports
