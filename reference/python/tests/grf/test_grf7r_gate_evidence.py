from __future__ import annotations

from copy import deepcopy

import pytest

from nollm.grf.gate_evidence import GateEvidence, GatePredicate
from experiments.grf.verify_grf7r_evidence import _read


def _evidence() -> GateEvidence:
    return GateEvidence(
        "A",
        "experiments/grf/results/GRF7R_GATE_A_RAW.json",
        {"query_count": 20_000},
        (
            GatePredicate("query count", 20_000, 20_000, "ge"),
            GatePredicate("hash verified", True, True, "eq"),
        ),
        20_000,
    )


def test_gate_status_is_computed_from_predicates() -> None:
    evidence = _evidence()
    assert evidence.result.status == "GATE_A_PASS"
    assert GateEvidence.from_mapping(evidence.to_mapping()) == evidence


def test_modified_count_cannot_retain_pass_status() -> None:
    payload = deepcopy(_evidence().to_mapping())
    payload["predicates"][0]["measured_value"] = 19_999
    with pytest.raises(ValueError, match="predicate pass"):
        GateEvidence.from_mapping(payload)


def test_forged_gate_pass_is_rejected() -> None:
    payload = deepcopy(_evidence().to_mapping())
    payload["predicates"][0]["measured_value"] = 0
    payload["predicates"][0]["pass"] = False
    payload["status"] = "GATE_A_PASS"
    with pytest.raises(ValueError, match="gate status"):
        GateEvidence.from_mapping(payload)


def test_missing_raw_evidence_is_rejected(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="required raw evidence"):
        _read(tmp_path / "missing.json")


def test_modified_hash_cannot_retain_pass_status() -> None:
    evidence = GateEvidence("J", "manifest.json", {"sha256": "expected"}, (GatePredicate("canonical hash", "expected", "expected", "eq"),), 1)
    payload = deepcopy(evidence.to_mapping())
    payload["predicates"][0]["measured_value"] = "modified"
    with pytest.raises(ValueError, match="predicate pass"):
        GateEvidence.from_mapping(payload)
