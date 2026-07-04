from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from nollm.dream_geometry.adapters.snapshot_compaction import (
    DG6AdapterError,
    SnapshotCompactionAdapterPolicy,
    expand_snapshot_compaction_projection,
    project_snapshot_compaction,
    validate_snapshot_compaction_projection,
)
from nollm.dream_geometry.assembly.types import snapshot_fingerprint_payload, stable_fingerprint
from tests.fixtures.dg6.fixture import empty_snapshot, isolated_duplicate_snapshot, single_trace_snapshot


def test_dg6_06_snapshot_id_drift_is_rejected() -> None:
    snapshot = replace(empty_snapshot(), snapshot_id="sha256:bad")
    with pytest.raises(DG6AdapterError) as error:
        project_snapshot_compaction(snapshot)
    assert error.value.reason_code == "DG6_SNAPSHOT_FINGERPRINT_MISMATCH"


def test_dg6_07_duplicate_trace_id_is_rejected() -> None:
    snapshot = single_trace_snapshot()
    duplicate = replace(snapshot, replayed_traces=(snapshot.replayed_traces[0], snapshot.replayed_traces[0]))
    duplicate = replace(duplicate, snapshot_id=stable_fingerprint(snapshot_fingerprint_payload(duplicate)))
    with pytest.raises(DG6AdapterError) as error:
        project_snapshot_compaction(duplicate)
    assert error.value.reason_code in {"DG6_DUPLICATE_TRACE_ID", "DG6_DG5_PLAN_INVALID"}


def test_dg6_08_same_snapshot_id_trace_payload_replacement_rejects_projection_use() -> None:
    snapshot = single_trace_snapshot()
    projection = project_snapshot_compaction(snapshot)
    altered_trace = replace(snapshot.replayed_traces[0], mass=snapshot.replayed_traces[0].mass + 0.5)
    altered = replace(snapshot, replayed_traces=(altered_trace,))

    with pytest.raises(DG6AdapterError) as validate_error:
        validate_snapshot_compaction_projection(altered, projection)
    with pytest.raises(DG6AdapterError) as expand_error:
        expand_snapshot_compaction_projection(altered, projection)
    assert validate_error.value.reason_code in {"DG6_SOURCE_TRACE_MANIFEST_MISMATCH", "DG6_DG5_PLAN_INVALID"}
    assert expand_error.value.reason_code in {"DG6_SOURCE_TRACE_MANIFEST_MISMATCH", "DG6_DG5_PLAN_INVALID"}


@pytest.mark.parametrize(
    "field,value,reason",
    (
        ("source_snapshot_id", "other", "DG6_PROJECTION_MANIFEST_INVALID"),
        ("source_trace_ids", ("wrong",), "DG6_SOURCE_TRACE_MANIFEST_MISMATCH"),
        ("source_trace_fingerprints", (("wrong", "fp"),), "DG6_SOURCE_TRACE_MANIFEST_MISMATCH"),
        ("projection_id", "wrong", "DG6_PROJECTION_MANIFEST_INVALID"),
        ("projection_fingerprint", "wrong", "DG6_PROJECTION_FINGERPRINT_MISMATCH"),
    ),
)
def test_dg6_09_projection_field_tampering_rejects_validate_and_expand(field: str, value, reason: str) -> None:
    snapshot = isolated_duplicate_snapshot()
    projection = project_snapshot_compaction(snapshot)
    tampered = replace(projection, **{field: value})

    with pytest.raises(DG6AdapterError) as validate_error:
        validate_snapshot_compaction_projection(snapshot, tampered)
    with pytest.raises(DG6AdapterError) as expand_error:
        expand_snapshot_compaction_projection(snapshot, tampered)
    assert validate_error.value.reason_code == reason
    assert expand_error.value.reason_code == reason


def test_dg6_09_plan_and_view_tampering_rejects_validate_and_expand() -> None:
    snapshot = isolated_duplicate_snapshot()
    projection = project_snapshot_compaction(snapshot)
    plan_tampered = replace(projection, compression_plan=replace(projection.compression_plan, plan_id="wrong"))
    view_tampered = replace(projection, compacted_trace_view=replace(projection.compacted_trace_view, view_fingerprint="wrong"))

    for tampered, reason in ((plan_tampered, "DG6_DG5_PLAN_INVALID"), (view_tampered, "DG6_DG5_VIEW_INVALID")):
        with pytest.raises(DG6AdapterError) as validate_error:
            validate_snapshot_compaction_projection(snapshot, tampered)
        with pytest.raises(DG6AdapterError) as expand_error:
            expand_snapshot_compaction_projection(snapshot, tampered)
        assert validate_error.value.reason_code == reason
        assert expand_error.value.reason_code == reason


def test_dg6_10_projection_against_different_valid_snapshot_rejects() -> None:
    projection = project_snapshot_compaction(isolated_duplicate_snapshot())
    other = single_trace_snapshot()

    with pytest.raises(DG6AdapterError):
        validate_snapshot_compaction_projection(other, projection)
    with pytest.raises(DG6AdapterError):
        expand_snapshot_compaction_projection(other, projection)


def test_dg6_11_dg5_plan_view_mismatch_is_rejected() -> None:
    snapshot = isolated_duplicate_snapshot()
    projection = project_snapshot_compaction(snapshot)
    bad_plan = replace(projection.compression_plan, passthrough_trace_ids=projection.compression_plan.input_trace_ids, compactions=())
    tampered = replace(projection, compression_plan=bad_plan)

    with pytest.raises(DG6AdapterError) as error:
        validate_snapshot_compaction_projection(snapshot, tampered)
    assert error.value.reason_code == "DG6_DG5_PLAN_INVALID"


def test_dg6_12_expansion_mismatch_rejects() -> None:
    snapshot = single_trace_snapshot()
    projection = project_snapshot_compaction(snapshot)
    altered = replace(snapshot, replayed_traces=(replace(snapshot.replayed_traces[0], support_key="different"),))

    with pytest.raises(DG6AdapterError):
        expand_snapshot_compaction_projection(altered, projection)


def test_dg6_13_invalid_policy_downgrade_and_unknown_policy_reject() -> None:
    with pytest.raises(DG6AdapterError) as downgrade:
        SnapshotCompactionAdapterPolicy(require_dg5_bound_plan=False)
    assert downgrade.value.reason_code == "DG6_INVALID_POLICY"
    with pytest.raises(DG6AdapterError) as unknown:
        SnapshotCompactionAdapterPolicy(policy_id="other")
    assert unknown.value.reason_code == "DG6_INVALID_POLICY"


def test_dg6_14_public_failures_do_not_leak_attribute_or_key_errors() -> None:
    with pytest.raises(DG6AdapterError) as error:
        project_snapshot_compaction(object())  # type: ignore[arg-type]
    assert error.value.reason_code == "DG6_INVALID_SNAPSHOT"
    assert "AttributeError" not in str(error.value)
    assert "KeyError" not in str(error.value)


def test_dg6_15_adapter_import_boundary_excludes_forbidden_modules() -> None:
    root = Path("reference/python/nollm/dream_geometry/adapters/snapshot_compaction")
    forbidden = ("evidence", "capture", "cortex", "admission", "recall", "runtime", "openclaw", "database", "cache")
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        lowered = "\n".join(imports).lower()
        for token in forbidden:
            assert token not in lowered, (path, token, imports)


def test_dg6_17_projection_has_no_recall_storage_or_runtime_fields() -> None:
    projection = project_snapshot_compaction(isolated_duplicate_snapshot())
    forbidden = {"recall_universe", "recall_result", "rank", "priority", "truth", "trust", "semantic_score", "storage_path", "cache_key", "runtime_handle", "field_mutation", "apply_result"}
    assert forbidden.isdisjoint(projection.__dataclass_fields__)
