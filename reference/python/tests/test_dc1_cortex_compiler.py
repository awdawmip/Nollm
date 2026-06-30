from __future__ import annotations

import json
from pathlib import Path

import pytest

from nollm.dream_geometry.cortex import DC1Rejection, compile_query, payload_fingerprint
from nollm.dream_geometry.cortex.store import CortexStore, open_store as open_cortex_store
from nollm.dream_geometry.evidence import RevisionEdge, RevisionThread
from nollm.dream_geometry.protocol.contracts import RevisionRelation
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


def test_dc1_1_t401_to_t407_query_time_and_budget_contract(tmp_path) -> None:
    rule_only_relative = _query_payload()
    rule_only_relative["axes"][1]["ray"] = [
        {
            "step_id": "step_q_relative_rule",
            "expression": "相对时间",
            "basis": "source_backed_rule",
            "basis_refs": [{"ref_type": "rule", "rule_id": "rule_relative_marker", "rule_version": "v1", "rule_label": "relative marker", "source_ref": "project:dc1"}],
        }
    ]
    assert "DC1_QUERY_RELATIVE_EXPLICIT_SPAN_REQUIRED" in _codes(lambda: compile_query(rule_only_relative))

    accepted = compile_query(_query_payload())
    assert accepted.budget.max_charts == 64
    assert accepted.budget.max_layers == 64
    assert accepted.budget.max_cells_per_layer == 256

    non_relative = _query_payload()
    non_relative["axes"] = [axis for axis in non_relative["axes"] if axis["axis_id"] != "relative_time"]
    assert "DC1_QUERY_RESOLVED_TIME_FORBIDDEN" in _codes(lambda: compile_query(non_relative))

    old_budget = _query_payload()
    old_budget["budget"] = {"max_axes": 3, "max_total_steps": 3, "max_ray_steps": 1}
    assert "DC1_UNKNOWN_FIELD" in _codes(lambda: compile_query(old_budget))

    excessive_query = _query_payload()
    excessive_query["budget"]["max_charts"] = 65
    assert "DC1_BUDGET_EXCEEDED" in _codes(lambda: compile_query(excessive_query))

    evidence = _fixture_store(tmp_path / "evidence")
    cortex = open_cortex_store(tmp_path / "cortex", evidence)
    excessive_total = _growth_payload()
    excessive_total["proposal_id"] = "gp_excess_total"
    excessive_total["budget"]["max_total_steps"] = 49
    assert "DC1_BUDGET_EXCEEDED" in _codes(lambda: cortex.compile_growth(excessive_total))
    excessive_ray = _growth_payload()
    excessive_ray["proposal_id"] = "gp_excess_ray"
    excessive_ray["budget"]["max_ray_steps"] = 17
    assert "DC1_BUDGET_EXCEEDED" in _codes(lambda: cortex.compile_growth(excessive_ray))


def test_dc1_1_t410_to_t414_conflict_refs_and_rule_identity(tmp_path) -> None:
    evidence = _fixture_store(tmp_path / "evidence")
    evidence.put_revision_thread(RevisionThread("revision:weather", ("shard:rain", "shard:city"), (RevisionEdge("shard:city", "shard:rain", RevisionRelation.clarifies, ()),), ()))
    cortex = open_cortex_store(tmp_path / "cortex", evidence)

    shard_conflict = _growth_payload()
    shard_conflict["proposal_id"] = "gp_conflict_shard"
    shard_conflict["possible_conflict_refs"] = ["shard:city"]
    assert cortex.compile_growth(shard_conflict).proposal.possible_conflict_refs == ("shard:city",)

    interpretation_conflict = _growth_payload()
    interpretation_conflict["proposal_id"] = "gp_conflict_interpretation"
    interpretation_conflict["possible_conflict_refs"] = ["interpretation:city-note"]
    assert cortex.compile_growth(interpretation_conflict).proposal.possible_conflict_refs == ("interpretation:city-note",)

    duplicate = _growth_payload()
    duplicate["proposal_id"] = "gp_conflict_duplicate"
    duplicate["possible_conflict_refs"] = ["shard:city", "shard:city"]
    assert "DC1_DUPLICATE_CONFLICT_REFERENCE" in _codes(lambda: cortex.compile_growth(duplicate))

    revision_ref = _growth_payload()
    revision_ref["proposal_id"] = "gp_conflict_revision"
    revision_ref["possible_conflict_refs"] = ["revision:weather"]
    assert "DC1_CONFLICT_REFERENCE_NOT_EPISTEMIC_RECORD" in _codes(lambda: cortex.compile_growth(revision_ref))

    same_rule = _growth_payload()
    same_rule["proposal_id"] = "gp_same_rule_ok"
    same_rule["axes"][3]["ray"][2]["basis_refs"].append({"ref_type": "rule", "rule_id": "rule_weather_vocab", "rule_version": "v1", "rule_label": "weather vocabulary mapping", "source_ref": "project:weather"})
    assert cortex.compile_growth(same_rule).proposal.proposal_id == "gp_same_rule_ok"

    inconsistent = _growth_payload()
    inconsistent["proposal_id"] = "gp_rule_inconsistent"
    inconsistent["axes"][2]["ray"][2]["basis_refs"][0]["rule_version"] = "v2"
    assert "DC1_RULE_IDENTITY_INCONSISTENT" in _codes(lambda: cortex.compile_growth(inconsistent))


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


def test_dc1_1_t420_to_t428_reopen_semantic_and_receipt_closure(tmp_path) -> None:
    def prepared_store(name: str):
        evidence = _fixture_store(tmp_path / name / "evidence")
        cortex_root = tmp_path / name / "cortex"
        cortex = open_cortex_store(cortex_root, evidence)
        cortex.compile_growth(_growth_payload())
        proposal_path = next((cortex_root / "compiled_growth_proposals").glob("*.json"))
        receipt_path = next((cortex_root / "compilation_receipts").glob("*.json"))
        return evidence, cortex_root, proposal_path, receipt_path

    evidence, cortex_root, proposal_path, receipt_path = prepared_store("t420")
    proposal = _read_json(proposal_path)
    proposal["axes"][0]["ray"][0]["expression"] = "城市"
    proposal["axes"][0]["ray"][0]["basis_refs"][0]["quoted_text"] = "城市"
    _write_json(proposal_path, proposal)
    _sync_receipt_normalized_fingerprint(receipt_path, proposal)
    assert "DC1_INVALID_TEXT_SPAN" in _codes(lambda: open_cortex_store(cortex_root, evidence))

    evidence, cortex_root, proposal_path, receipt_path = prepared_store("t421")
    proposal = _read_json(proposal_path)
    proposal["axes"][1]["ray"][0]["basis_refs"][0]["record_id"] = "shard:rain"
    proposal["axes"][1]["ray"][0]["basis_refs"][0]["start_char"] = 0
    proposal["axes"][1]["ray"][0]["basis_refs"][0]["end_char"] = 2
    proposal["axes"][1]["ray"][0]["basis_refs"][0]["quoted_text"] = "昆明"
    proposal["axes"][1]["ray"][0]["expression"] = "昆明"
    _write_json(proposal_path, proposal)
    _sync_receipt_normalized_fingerprint(receipt_path, proposal)
    assert "DC1_BACKING_SHARD_SELF_REFERENCE" in _codes(lambda: open_cortex_store(cortex_root, evidence))

    evidence, cortex_root, proposal_path, receipt_path = prepared_store("t422")
    proposal = _read_json(proposal_path)
    proposal["axes"][0]["axis_id"] = "relative_time"
    _write_json(proposal_path, proposal)
    _sync_receipt_normalized_fingerprint(receipt_path, proposal)
    assert "DC1_GROWTH_RELATIVE_TIME_FORBIDDEN" in _codes(lambda: open_cortex_store(cortex_root, evidence))

    evidence, cortex_root, proposal_path, receipt_path = prepared_store("t423")
    proposal = _read_json(proposal_path)
    proposal["axes"][2]["ray"][1]["basis_refs"][1]["input_step_id"] = "step_kunming"
    _write_json(proposal_path, proposal)
    _sync_receipt_normalized_fingerprint(receipt_path, proposal)
    assert "DC1_INVALID_PREDECESSOR" in _codes(lambda: open_cortex_store(cortex_root, evidence))

    evidence, cortex_root, proposal_path, receipt_path = prepared_store("t424")
    proposal = _read_json(proposal_path)
    proposal["axes"][3]["ray"][2]["rationale"] = None
    _write_json(proposal_path, proposal)
    _sync_receipt_normalized_fingerprint(receipt_path, proposal)
    assert "DC1_PROVISIONAL_RATIONALE_REQUIRED" in _codes(lambda: open_cortex_store(cortex_root, evidence))

    evidence, cortex_root, proposal_path, receipt_path = prepared_store("t425")
    proposal = _read_json(proposal_path)
    proposal["budget"]["max_total_steps"] = 49
    _write_json(proposal_path, proposal)
    _sync_receipt_normalized_fingerprint(receipt_path, proposal)
    assert "DC1_BUDGET_EXCEEDED" in _codes(lambda: open_cortex_store(cortex_root, evidence))

    evidence, cortex_root, proposal_path, receipt_path = prepared_store("t426")
    receipt = _read_json(receipt_path)
    receipt["input_snapshot"]["forbidden_inferences"] = ["changed"]
    _write_json(receipt_path, receipt)
    assert "DC1_RECEIPT_INPUT_SNAPSHOT_MISMATCH" in _codes(lambda: open_cortex_store(cortex_root, evidence))

    evidence, cortex_root, proposal_path, receipt_path = prepared_store("t427")
    receipt = _read_json(receipt_path)
    receipt["kind"] = "query"
    _write_json(receipt_path, receipt)
    assert "DC1_RECEIPT_KIND_INVALID" in _codes(lambda: open_cortex_store(cortex_root, evidence))

    evidence, cortex_root, proposal_path, receipt_path = prepared_store("t428")
    receipt = _read_json(receipt_path)
    receipt["input_snapshot"]["forbidden_inferences"] = ["different but valid"]
    receipt["submitted_payload_fingerprint"] = payload_fingerprint(receipt["input_snapshot"])
    _write_json(receipt_path, receipt)
    assert "DC1_RECEIPT_PROPOSAL_MISMATCH" in _codes(lambda: open_cortex_store(cortex_root, evidence))


def test_dc1_evidence_root_unchanged_by_growth_write(tmp_path) -> None:
    evidence_root = tmp_path / "evidence"
    evidence = _fixture_store(evidence_root)
    before = _tree_digest(evidence_root)
    cortex = open_cortex_store(tmp_path / "cortex", evidence)
    cortex.compile_growth(_growth_payload())
    assert _tree_digest(evidence_root) == before


def _tree_digest(root: Path) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(path.relative_to(root)), path.read_text(encoding="utf-8")) for path in root.rglob("*") if path.is_file()))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")


def _sync_receipt_normalized_fingerprint(receipt_path: Path, proposal_payload: dict) -> None:
    receipt = _read_json(receipt_path)
    receipt["normalized_payload_fingerprint"] = payload_fingerprint(proposal_payload)
    _write_json(receipt_path, receipt)
