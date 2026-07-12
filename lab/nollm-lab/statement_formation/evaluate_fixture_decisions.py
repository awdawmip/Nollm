from __future__ import annotations

import argparse
import json

from corpus_support import FIXTURES, METRICS, canonical_json, load_cases, materialize
from nollm_access import StatementFormationDecision, assemble_formed_statements


def _span_set(decision: StatementFormationDecision) -> set[tuple[str, int, int]]:
    return {selection.span.stable_key() for selection in decision.selections}


def evaluate() -> dict[str, object]:
    cases = {case["case_id"]: case for case in load_cases()}
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    if type(fixtures) is not list:
        raise TypeError("fixture proposals must be a list")
    results = {}
    for fixture in fixtures:
        if type(fixture) is not dict or set(fixture) != {"fixture_id", "case_id", "expectation", "proposal"}:
            raise ValueError("fixture proposal has unknown or missing fields")
        request, gold = materialize(cases[fixture["case_id"]])
        accepted = True
        try:
            proposal = StatementFormationDecision.from_mapping(fixture["proposal"])
            formed = assemble_formed_statements(request, proposal)
        except (TypeError, ValueError, KeyError):
            accepted = False
            proposal = None
            formed = ()
        gold_spans = _span_set(gold)
        proposed_spans = _span_set(proposal) if proposal is not None else set()
        matches = len(gold_spans & proposed_spans)
        precision = matches / len(proposed_spans) if proposed_spans else (1.0 if not gold_spans else 0.0)
        recall = matches / len(gold_spans) if gold_spans else (1.0 if not proposed_spans else 0.0)
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        gold_formed = assemble_formed_statements(request, gold)
        gold_text = [item.statement.content_utf8 for item in gold_formed]
        proposed_text = [item.statement.content_utf8 for item in formed]
        exact = accepted and proposed_text == gold_text
        metrics = {
            "schema_valid_rate": 1.0 if accepted else 0.0,
            "decision_state_accuracy": 1.0 if accepted and proposal.outcome == gold.outcome else 0.0,
            "exact_statement_count_accuracy": 1.0 if accepted and len(formed) == len(gold_formed) else 0.0,
            "exact_span_precision": precision,
            "exact_span_recall": recall,
            "exact_span_f1": f1,
            "text_faithfulness_rate": 1.0 if accepted else 0.0,
            "hallucinated_text_count": 0,
            "defer_accuracy": 1.0 if accepted and (proposal.outcome == "defer") == (gold.outcome == "defer") else 0.0,
            "source_inheritance_accuracy": 1.0 if accepted and all(item.statement.source_handle == request.evidence[0].source_handle for item in formed) else 0.0,
            "context_inheritance_accuracy": 1.0 if accepted and all(item.statement.context_refs == request.evidence[0].context_refs for item in formed) else 0.0,
            "exact_match": exact,
            "accepted": accepted,
        }
        expectation = fixture["expectation"]
        if expectation == "perfect" and (not all(metrics[key] == 1.0 for key in metrics if key not in {"hallucinated_text_count", "exact_match", "accepted"}) or not exact):
            raise ValueError("perfect fixture does not achieve perfect metrics")
        if expectation == "reject" and accepted:
            raise ValueError(f"fixture {fixture['fixture_id']} should be rejected")
        if expectation == "degraded" and (not accepted or exact):
            raise ValueError(f"fixture {fixture['fixture_id']} should be accepted with degraded metrics")
        results[fixture["fixture_id"]] = metrics
    return {"fixture_count": len(results), "fixtures": dict(sorted(results.items()))}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    metrics = evaluate()
    if args.write:
        from validate_corpus import validate
        METRICS.parent.mkdir(parents=True, exist_ok=True)
        METRICS.write_bytes(canonical_json({"corpus": validate(), "fixture_evaluation": metrics}))
    else:
        recorded = json.loads(METRICS.read_text(encoding="utf-8"))
        if recorded.get("fixture_evaluation") != metrics:
            raise ValueError("recorded fixture metrics are stale")
    print(json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
