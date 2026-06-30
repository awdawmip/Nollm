from __future__ import annotations

import json
from pathlib import Path

import pytest

from nollm.dream_geometry.cortex import DC1Rejection, compile_query
from nollm.dream_geometry.cortex.store import CortexStore, open_store as open_cortex_store
from nollm.dream_geometry.validation.dc1_cortex_report import _bad_explicit_payload, _fixture_store, _growth_payload, _query_payload


def _codes(callback) -> tuple[str, ...]:
    with pytest.raises(DC1Rejection) as raised:
        callback()
    return raised.value.reason_codes


def test_dc1_c001_to_c007_growth_acceptance_idempotency_and_reopen(tmp_path) -> None:
    evidence = _fixture_store(tmp_path / "evidence")
    cortex = open_cortex_store(tmp_path / "cortex", evidence)
    first = cortex.compile_growth(_growth_payload())
    retry = cortex.compile_growth(_growth_payload())
    reopened = open_cortex_store(tmp_path / "cortex", evidence)
    proposal = reopened.get_growth_proposal("gp_kunming_growth_v1")
    assert first.created is True
    assert retry.idempotent is True
    assert first.receipt.receipt_id == retry.receipt.receipt_id
    assert proposal.subject_shard_id == "shard:rain"
    assert any(step.provisional_only for axis in proposal.axes for step in axis.ray)


def test_dc1_c020_c030_growth_rejection_codes_and_conflict(tmp_path) -> None:
    evidence = _fixture_store(tmp_path / "evidence")
    cortex = open_cortex_store(tmp_path / "cortex", evidence)
    assert "DC1_INVALID_TEXT_SPAN" in _codes(lambda: cortex.compile_growth(_bad_explicit_payload()))

    backing_interpretation = _growth_payload()
    backing_interpretation["proposal_id"] = "gp_bad_backing"
    backing_interpretation["axes"] = [
        {
            "axis_id": "relation",
            "ray": [
                {
                    "step_id": "step_bad_backing",
                    "expression": "城市",
                    "basis": "backed_by_other_shard",
                    "basis_refs": [{"ref_type": "text_span", "record_id": "interpretation:city-note", "start_char": 0, "end_char": 2, "quoted_text": "城市"}],
                }
            ],
        }
    ]
    assert "DC1_BACKING_SUBJECT_NOT_DREAM_SHARD" in _codes(lambda: cortex.compile_growth(backing_interpretation))

    self_backing = _growth_payload()
    self_backing["proposal_id"] = "gp_bad_self_backing"
    self_backing["axes"] = [
        {
            "axis_id": "relation",
            "ray": [
                {
                    "step_id": "step_bad_self",
                    "expression": "昆明",
                    "basis": "backed_by_other_shard",
                    "basis_refs": [{"ref_type": "text_span", "record_id": "shard:rain", "start_char": 0, "end_char": 2, "quoted_text": "昆明"}],
                }
            ],
        }
    ]
    assert "DC1_BACKING_SHARD_SELF_REFERENCE" in _codes(lambda: cortex.compile_growth(self_backing))

    relative = _growth_payload()
    relative["proposal_id"] = "gp_bad_relative"
    relative["axes"][0]["axis_id"] = "relative_time"
    assert "DC1_GROWTH_RELATIVE_TIME_FORBIDDEN" in _codes(lambda: cortex.compile_growth(relative))

    legacy = _growth_payload()
    legacy["proposal_id"] = "gp_bad_anchor"
    legacy["anchor_name"] = "old-anchor"
    assert "DC1_LEGACY_ANCHOR_FIELD_FORBIDDEN" in _codes(lambda: cortex.compile_growth(legacy))

    first = cortex.compile_growth(_growth_payload())
    conflict = _growth_payload()
    conflict["forbidden_inferences"] = ["different but valid payload"]
    assert first.created
    assert "DC1_PROPOSAL_ID_PAYLOAD_CONFLICT" in _codes(lambda: cortex.compile_growth(conflict))


def test_dc1_growth_projection_and_provisional_predecessors(tmp_path) -> None:
    evidence = _fixture_store(tmp_path / "evidence")
    cortex = open_cortex_store(tmp_path / "cortex", evidence)
    bad_projection = _growth_payload()
    bad_projection["proposal_id"] = "gp_bad_projection"
    bad_projection["axes"][2]["ray"][1]["basis_refs"][1]["input_step_id"] = "step_kunming"
    assert "DC1_INVALID_PREDECESSOR" in _codes(lambda: cortex.compile_growth(bad_projection))

    first_provisional = _growth_payload()
    first_provisional["proposal_id"] = "gp_bad_provisional_first"
    first_provisional["axes"] = [
        {
            "axis_id": "custom/test",
            "ray": [
                {
                    "step_id": "step_first_provisional",
                    "expression": "泛化",
                    "basis": "provisional_llm_generalization",
                    "basis_refs": [{"ref_type": "step", "input_step_id": "step_missing"}],
                    "rationale": "candidate",
                }
            ],
        }
    ]
    assert "DC1_PROVISIONAL_FIRST_STEP_FORBIDDEN" in _codes(lambda: cortex.compile_growth(first_provisional))

    no_rationale = _growth_payload()
    no_rationale["proposal_id"] = "gp_bad_provisional_rationale"
    del no_rationale["axes"][3]["ray"][2]["rationale"]
    assert "DC1_PROVISIONAL_RATIONALE_REQUIRED" in _codes(lambda: cortex.compile_growth(no_rationale))


def test_dc1_q001_to_q024_query_ephemeral_and_rejections(tmp_path) -> None:
    before = tuple(tmp_path.rglob("*"))
    query = compile_query(_query_payload())
    after = tuple(tmp_path.rglob("*"))
    assert query.ephemeral is True
    assert query.requires_runtime_resolution is True
    assert query.reference_instant == "2026-06-30T09:00:00+08:00"
    assert before == after

    memory_basis = _query_payload()
    memory_basis["axes"][0]["ray"][0]["basis"] = "backed_by_other_shard"
    assert "DC1_QUERY_MEMORY_BASIS_FORBIDDEN" in _codes(lambda: compile_query(memory_basis))

    resolved = _query_payload()
    resolved["resolved_absolute_time"] = "2026-06-29"
    assert "DC1_QUERY_RESOLVED_TIME_FORBIDDEN" in _codes(lambda: compile_query(resolved))

    persistent = _query_payload()
    persistent["ephemeral"] = False
    assert "DC1_QUERY_NOT_EPHEMERAL" in _codes(lambda: compile_query(persistent))

    retry = compile_query(_query_payload())
    assert retry == query


def test_dc1_store_reopen_rejects_contract_violations(tmp_path) -> None:
    evidence = _fixture_store(tmp_path / "evidence")
    cortex_root = tmp_path / "cortex"
    cortex = open_cortex_store(cortex_root, evidence)
    cortex.compile_growth(_growth_payload())

    assert "DC1_CORTEX_ROOT_EQUALS_EVIDENCE_ROOT" in _codes(lambda: CortexStore(tmp_path / "evidence", evidence))

    proposal_path = next((cortex_root / "compiled_growth_proposals").glob("*.json"))
    receipt_path = next((cortex_root / "compilation_receipts").glob("*.json"))
    saved_receipt = receipt_path.read_text(encoding="utf-8")
    receipt_path.unlink()
    assert "DC1_RECEIPT_PROPOSAL_MISMATCH" in _codes(lambda: open_cortex_store(cortex_root, evidence))
    receipt_path.write_text(saved_receipt, encoding="utf-8")

    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    payload["unknown"] = "bad"
    proposal_path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    assert "DC1_ON_DISK_CONTRACT_VIOLATION" in _codes(lambda: open_cortex_store(cortex_root, evidence))


def test_dc1_evidence_root_unchanged_by_growth_write(tmp_path) -> None:
    evidence_root = tmp_path / "evidence"
    evidence = _fixture_store(evidence_root)
    before = _tree_digest(evidence_root)
    cortex = open_cortex_store(tmp_path / "cortex", evidence)
    cortex.compile_growth(_growth_payload())
    assert _tree_digest(evidence_root) == before


def _tree_digest(root: Path) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(path.relative_to(root)), path.read_text(encoding="utf-8")) for path in root.rglob("*") if path.is_file()))
