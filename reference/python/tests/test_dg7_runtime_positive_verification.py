from __future__ import annotations

from dataclasses import replace
import json

import pytest

from nollm.dream_geometry.validation.dg7 import build_reference_scenario
from nollm.dream_geometry.validation.dg7 import run_reference_runtime
from nollm.dream_geometry.validation.dg7.runner import DG7RuntimeVerificationError, receipt_to_mapping


def test_dg7_01_reference_runtime_positive_chain(tmp_path) -> None:
    scenario = build_reference_scenario()
    receipt = run_reference_runtime(tmp_path / "work")
    mapping = receipt_to_mapping(receipt)

    assert scenario.explicit_assembly_admission_ids == ("adm_dg7_a", "adm_dg7_b")
    assert mapping["status"] == "completed"
    assert mapping["receipt_kind"] == "nollm_dg7_reference_runtime_receipt"
    assert mapping["scenario_id"] == "fixed-dg7-v1"
    assert [item["label"] for item in mapping["capture_receipts"]] == ["a", "b", "c", "d"]
    assert {item["status"] for item in mapping["capture_receipts"]} == {"deferred"}
    assert mapping["admission_receipt_ids"] == ["adm_dg7_a", "adm_dg7_b"]
    assert tuple(mapping["admission_receipt_ids"]) == scenario.explicit_assembly_admission_ids
    assert mapping["admitted_unassembled_d_admission_id"] == "adm_dg7_d"
    assert mapping["snapshot_source_admission_ids"] == ["adm_dg7_a", "adm_dg7_b"]
    assert tuple(mapping["snapshot_source_admission_ids"]) == scenario.explicit_assembly_admission_ids
    assert mapping["dg6_input_trace_count"] == len(mapping["dg6_expansion_trace_ids"])
    assert mapping["isolation"]["snapshot_replayed_trace_manifest_matches_dg6_expansion"] is True
    assert mapping["isolation"]["recall_is_independent_of_dg6_view"] is True


def test_dg7_c1_02_d_only_assembly_declaration_rejects_before_receipt_cache(tmp_path, monkeypatch) -> None:
    _patch_declared_ids(monkeypatch, ("adm_dg7_d",))
    work = tmp_path / "work"

    with pytest.raises(DG7RuntimeVerificationError) as error:
        run_reference_runtime(work)

    assert error.value.reason_code == "DG7_ASSEMBLY_REJECTED"
    assert not (work / ".dg7_reference_runtime_receipt.json").exists()
    _assert_no_forbidden_work_dirs(work)
    assert not any(token in str(error.value) for token in ("Traceback", "AttributeError", "KeyError", "TypeError", "ValueError", "nollm.dream_geometry"))


@pytest.mark.parametrize(
    "declared_ids",
    (
        ("adm_dg7_a", "adm_dg7_a"),
        ("adm_dg7_a",),
        ("adm_dg7_b", "adm_dg7_a"),
        ("adm_dg7_a", "adm_dg7_b", "adm_dg7_d"),
        ("", "adm_dg7_b"),
    ),
)
def test_dg7_c1_03_duplicate_missing_reordered_and_invalid_declarations_reject(tmp_path, monkeypatch, declared_ids) -> None:
    _patch_declared_ids(monkeypatch, declared_ids)
    with pytest.raises(DG7RuntimeVerificationError) as error:
        run_reference_runtime(tmp_path / "work")

    assert error.value.reason_code == "DG7_ASSEMBLY_REJECTED"
    assert not any(token in str(error.value) for token in ("Traceback", "AttributeError", "KeyError", "TypeError", "ValueError", "nollm.dream_geometry"))


def test_dg7_03_04_c_and_d_are_excluded_from_snapshot_projection_recall_and_envelope(tmp_path) -> None:
    mapping = receipt_to_mapping(run_reference_runtime(tmp_path / "work"))
    labels = {item["label"]: item for item in mapping["capture_receipts"]}
    excluded = {labels["c"]["shard_id"], labels["d"]["shard_id"]}
    rendered = json.dumps(mapping, sort_keys=True, ensure_ascii=False)

    assert mapping["isolation"]["captured_unadmitted_c_excluded"] is True
    assert mapping["isolation"]["admitted_unassembled_d_excluded"] is True
    assert excluded.isdisjoint(mapping["snapshot_source_shard_ids"])
    assert excluded.isdisjoint(item["shard_id"] for item in mapping["recall_envelope"]["primary_evidence"])
    assert mapping["c_miss_envelope"]["primary_evidence"] == []
    assert labels["c"]["shard_id"] not in json.dumps(mapping["recall_envelope"], ensure_ascii=False)
    assert labels["d"]["shard_id"] not in json.dumps(mapping["recall_envelope"], ensure_ascii=False)
    assert "dg7 captured control" not in rendered
    assert "admitted but excluded" not in rendered


def test_dg7_05_06_di1_public_envelope_contains_only_a_b_evidence_without_internal_payloads(tmp_path) -> None:
    mapping = receipt_to_mapping(run_reference_runtime(tmp_path / "work"))
    labels = {item["label"]: item for item in mapping["capture_receipts"]}
    allowed = {labels["a"]["shard_id"], labels["b"]["shard_id"]}
    envelope = mapping["recall_envelope"]
    rendered_without_content = json.dumps(_without_content(envelope), sort_keys=True, ensure_ascii=False).lower()

    assert envelope["status"] == "resolved"
    assert {item["shard_id"] for item in envelope["primary_evidence"]}.issubset(allowed)
    assert all(item["content"].startswith("Kunming rain dg7") for item in envelope["primary_evidence"])
    for forbidden in ("cover_id", "gravity", "chart", "placement", "source_trace", "debug", "compacted"):
        assert forbidden not in rendered_without_content


def _without_content(value):
    if isinstance(value, dict):
        return {key: _without_content(item) for key, item in value.items() if key != "content"}
    if isinstance(value, list):
        return [_without_content(item) for item in value]
    return value


def _patch_declared_ids(monkeypatch, declared_ids: tuple[str, ...]) -> None:
    from nollm.dream_geometry.validation.dg7 import runner

    original = runner.build_reference_scenario

    def replacement(scenario_id: str = "fixed-dg7-v1"):
        return replace(original(scenario_id), explicit_assembly_admission_ids=declared_ids)

    monkeypatch.setattr(runner, "build_reference_scenario", replacement)


def _assert_no_forbidden_work_dirs(work) -> None:
    for forbidden in ("field", "assembly", "recall", "cache", "database", "global-field"):
        assert not (work / forbidden).exists()
