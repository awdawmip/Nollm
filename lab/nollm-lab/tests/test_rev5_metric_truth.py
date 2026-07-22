import json
from pathlib import Path

from recall_lens.rev5_metric_truth import (
    active_authority_has_provider_prohibition,
    declared_target_metric_valid,
    leakage_metric_valid,
    semantic_none_metric_valid,
)


ROOT = Path(__file__).resolve().parents[3]


def _old_events() -> list[dict[str, object]]:
    path = ROOT / "validation/aold_llm_native_main_agent_recall_20260722.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_old_result_selected_targets_are_not_semantic_reach_evidence():
    event = next(item for item in _old_events() if item.get("kind") == "relevant")
    assert declared_target_metric_valid(event) is False
    assert declared_target_metric_valid({
        "target_declared_before_recall": True,
        "target_source": "query_registry",
        "declared_target_statement_ids": ["expected"],
        "returned_statement_ids": ["expected"],
    }) is True


def test_old_none_and_hard_coded_leakage_are_not_measured_results():
    event = next(item for item in _old_events() if item.get("kind") == "none-unrelated")
    assert semantic_none_metric_valid(event) is False
    assert leakage_metric_valid(event) is False
    assert leakage_metric_valid({
        "returned_statement_ids": ["allowed", "forbidden"],
        "forbidden_statement_ids": ["forbidden"],
        "unrelated_leakage_count": 1,
    }) is True


def test_active_repository_authority_does_not_claim_provider_prohibition():
    assert active_authority_has_provider_prohibition(ROOT) is False
