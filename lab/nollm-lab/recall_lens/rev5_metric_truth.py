from __future__ import annotations

from pathlib import Path


PROVIDER_PROHIBITION_TEXT = (
    "live openclaw/model calls are prohibited",
    "active repository instruction prohibits live",
    "do not run live openclaw",
)


def declared_target_metric_valid(event: object) -> bool:
    if type(event) is not dict:
        return False
    targets = event.get("declared_target_statement_ids")
    returned = event.get("returned_statement_ids")
    return (
        event.get("target_declared_before_recall") is True
        and type(targets) is list and bool(targets)
        and all(type(value) is str and value for value in targets)
        and type(returned) is list
        and all(type(value) is str and value for value in returned)
        and event.get("target_source") != "recall_result"
    )


def semantic_none_metric_valid(event: object) -> bool:
    return (
        type(event) is dict
        and event.get("main_agent_run_observed") is True
        and event.get("memory_operation_observed") is True
        and event.get("visible_answer_observed") is True
        and event.get("admitted_injection_count") == 0
    )


def leakage_metric_valid(event: object) -> bool:
    if type(event) is not dict:
        return False
    returned = event.get("returned_statement_ids")
    forbidden = event.get("forbidden_statement_ids")
    measured = event.get("unrelated_leakage_count")
    if type(returned) is not list or type(forbidden) is not list or type(measured) is not int:
        return False
    if any(type(value) is not str for value in [*returned, *forbidden]):
        return False
    return measured == len(set(returned).intersection(forbidden))


def active_authority_has_provider_prohibition(repo_root: Path) -> bool:
    paths = (
        repo_root / "AGENTS.md",
        repo_root / "docs/project/ACTIVE_PROJECT.md",
        repo_root / "docs/project/NOLLM_CURRENT_STATUS.md",
    )
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    return any(phrase in text for phrase in PROVIDER_PROHIBITION_TEXT)
