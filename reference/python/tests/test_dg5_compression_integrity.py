from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from nollm.dream_geometry.compression import CompressionPlanningError, plan_trace_compaction, validate_compression_plan
from nollm.dream_geometry.compression.fingerprint import compression_plan_fingerprint, planned_payload, plan_id_for
from nollm.dream_geometry.compression.types import CompressionPlan
from nollm.dream_geometry.compression.view import build_compacted_trace_view, expand_compression_plan
from nollm.dream_geometry.field.types import TraceCompaction, stable_id
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


def test_dg5_c1_01_rehashed_non_conflatable_compaction_is_bound_rejected() -> None:
    traces = mixed_fixture()
    plan = plan_trace_compaction(traces)
    forged = _compaction("forged-non-conflatable", ("collision-a", "same-cell-distinct"), 0.5)
    forged_plan = _rehash_plan(
        plan,
        compactions=(forged,),
        passthrough_trace_ids=("dup-a", "dup-b", "pass-a"),
        compacted_member_count=2,
        output_view_entry_count=4,
        estimated_view_entry_reduction=1,
    )
    _assert_build_and_expand_reject(forged_plan, trace_index(traces), "DG5_PLAN_MANIFEST_INVALID")


def test_dg5_c1_02_rehashed_compaction_field_tampering_is_rejected() -> None:
    traces = exact_duplicate_pair()
    plan = plan_trace_compaction(traces)
    compaction = plan.compactions[0]
    tampered_mass = _rehash_plan(plan, compactions=(replace(compaction, aggregate_mass=99.0),))
    _assert_build_and_expand_reject(tampered_mass, trace_index(traces), "DG5_PLAN_MANIFEST_INVALID")
    tampered_key = _rehash_plan(plan, compactions=(_compaction("other-key", compaction.member_trace_ids, compaction.aggregate_mass),))
    _assert_build_and_expand_reject(tampered_key, trace_index(traces), "DG5_PLAN_MANIFEST_INVALID")
    tampered_id = _copy_plan(plan, compactions=(replace(compaction, compaction_id="wrong"),))
    with pytest.raises(CompressionPlanningError) as exc:
        validate_compression_plan(tampered_id)
    assert exc.value.reason_code == "DG5_PLAN_MANIFEST_INVALID"


def test_dg5_c1_03_missing_expected_compaction_is_bound_rejected() -> None:
    traces = exact_duplicate_pair()
    plan = plan_trace_compaction(traces)
    forged_plan = _rehash_plan(
        plan,
        compactions=(),
        passthrough_trace_ids=plan.input_trace_ids,
        compacted_member_count=0,
        output_view_entry_count=2,
        estimated_view_entry_reduction=0,
    )
    _assert_build_and_expand_reject(forged_plan, trace_index(traces), "DG5_PLAN_MANIFEST_INVALID")


def test_dg5_c1_04_singleton_compaction_is_structurally_rejected() -> None:
    traces = exact_duplicate_pair()
    plan = plan_trace_compaction(traces)
    singleton = _compaction("singleton", ("dup-a",), 0.2)
    forged_plan = _copy_plan(
        plan,
        compactions=(singleton,),
        passthrough_trace_ids=("dup-b",),
        compacted_member_count=1,
        output_view_entry_count=2,
        estimated_view_entry_reduction=0,
    )
    with pytest.raises(CompressionPlanningError) as exc:
        validate_compression_plan(_rehash_plan(forged_plan))
    assert exc.value.reason_code == "DG5_PLAN_MANIFEST_INVALID"


def test_dg5_c1_05_noncanonical_plan_id_passthrough_and_compaction_order_are_rejected() -> None:
    traces = mixed_fixture()
    plan = plan_trace_compaction(traces)
    with pytest.raises(CompressionPlanningError) as exc:
        validate_compression_plan(_copy_plan(plan, plan_id="not-canonical", plan_fingerprint=compression_plan_fingerprint(_copy_plan(plan, plan_id="not-canonical"))))
    assert exc.value.reason_code == "DG5_PLAN_MANIFEST_INVALID"
    noncanonical_passthrough = _rehash_plan(plan, passthrough_trace_ids=tuple(reversed(plan.passthrough_trace_ids)))
    with pytest.raises(CompressionPlanningError) as exc:
        validate_compression_plan(noncanonical_passthrough)
    assert exc.value.reason_code == "DG5_PLAN_MANIFEST_INVALID"
    first = _compaction("b-key", ("collision-a", "pass-a"), 0.5)
    second = _compaction("a-key", ("dup-a", "dup-b"), 0.5)
    noncanonical_compactions = tuple(reversed(tuple(sorted((first, second), key=lambda item: item.compaction_id))))
    bad_order = _rehash_plan(
        plan,
        compactions=noncanonical_compactions,
        passthrough_trace_ids=("same-cell-distinct",),
        compacted_member_count=4,
        output_view_entry_count=3,
        estimated_view_entry_reduction=2,
    )
    with pytest.raises(CompressionPlanningError) as exc:
        validate_compression_plan(bad_order)
    assert exc.value.reason_code == "DG5_PLAN_MANIFEST_INVALID"


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


def _rehash_plan(plan: CompressionPlan, **changes) -> CompressionPlan:
    updated = _copy_plan(plan, **changes)
    from nollm.dream_geometry.compression.types import CompressionPolicy

    policy = CompressionPolicy(updated.policy_id, updated.policy_version, updated.mode, True)
    plan_id = plan_id_for(planned_payload(policy, updated.input_trace_ids, updated.input_trace_fingerprints, updated.compactions, updated.passthrough_trace_ids))
    updated = _copy_plan(updated, plan_id=plan_id, plan_fingerprint="")
    return _copy_plan(updated, plan_fingerprint=compression_plan_fingerprint(updated))


def _compaction(canonical_key: str, member_trace_ids: tuple[str, ...], aggregate_mass: float) -> TraceCompaction:
    member_trace_ids = tuple(sorted(member_trace_ids))
    return TraceCompaction(
        compaction_id=stable_id("trace_compaction:v2", {"canonical_key": canonical_key, "members": member_trace_ids}),
        member_trace_ids=member_trace_ids,
        canonical_key=canonical_key,
        aggregate_mass=aggregate_mass,
        expansion_manifest=member_trace_ids,
    )


def _assert_build_and_expand_reject(plan: CompressionPlan, index: dict, reason_code: str) -> None:
    with pytest.raises(CompressionPlanningError) as build_exc:
        build_compacted_trace_view(plan, index)
    assert build_exc.value.reason_code == reason_code
    with pytest.raises(CompressionPlanningError) as expand_exc:
        expand_compression_plan(plan, index)
    assert expand_exc.value.reason_code == reason_code


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
