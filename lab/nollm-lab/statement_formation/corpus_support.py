from __future__ import annotations

import json
from pathlib import Path

from nollm_access import (
    StatementFormationDecision,
    StatementFormationRequest,
    assemble_formed_statements,
)


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "datasets" / "statement_formation_v1.jsonl"
FIXTURES = ROOT / "fixtures" / "decision_proposals_v1.json"
METRICS = ROOT.parents[2] / "docs" / "validation" / "AL_STATEMENT_FORMATION_CORPUS_METRICS.json"
CASE_FIELDS = {"case_id", "split", "category", "language", "request", "gold_decision"}


def load_cases(path: Path = DATASET) -> list[dict[str, object]]:
    cases = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = json.loads(line)
        if type(value) is not dict or set(value) != CASE_FIELDS:
            raise ValueError(f"case line {line_number} has unknown or missing fields")
        if type(value["case_id"]) is not str or not value["case_id"]:
            raise TypeError("case_id must be a non-empty string")
        if value["split"] not in {"development", "held_out"}:
            raise ValueError("unknown corpus split")
        if type(value["category"]) is not str or not value["category"]:
            raise TypeError("category must be a non-empty string")
        if value["language"] not in {"zh", "en", "mixed"}:
            raise ValueError("unknown language label")
        cases.append(value)
    if len({case["case_id"] for case in cases}) != len(cases):
        raise ValueError("case_id values must be unique")
    return cases


def materialize(case: dict[str, object]) -> tuple[StatementFormationRequest, StatementFormationDecision]:
    request = StatementFormationRequest.from_mapping(case["request"])
    decision = StatementFormationDecision.from_mapping(case["gold_decision"])
    assemble_formed_statements(request, decision)
    return request, decision


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
