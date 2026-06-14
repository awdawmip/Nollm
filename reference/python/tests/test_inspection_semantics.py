from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DISCOURAGED_PHRASES = (
    "human review workflow",
    "human approval workflow",
    "review queue for human approval",
    "cards needing human attention",
    "humans must review",
    "review inbox",
    "assigns semantic risk",
    "calculates semantic risk",
    "confirmed fact",
)
DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "protocol" / "REVIEW.md",
    ROOT / "protocol" / "ANNOTATION.md",
    ROOT / "protocol" / "HISTORY.md",
    ROOT / "protocol" / "TOOL_SURFACE.md",
    ROOT / "protocol" / "STATUS.md",
    ROOT / "protocol" / "TRUST.md",
    ROOT / "protocol" / "VALIDATION.md",
    ROOT / "protocol" / "SOURCE.md",
    ROOT / "docs" / "integration" / "LLM_INTEGRATION.md",
    ROOT / "cortex" / "NOLLM_EXTERNAL_AGENT_INSTRUCTIONS.md",
    ROOT / "tools" / "nollm_tool_manifest.json",
]


def test_review_docs_do_not_frame_inspection_as_passive_human_queue() -> None:
    offenders = []
    for path in DOC_PATHS:
        text = normalized_text(path)
        for phrase in DISCOURAGED_PHRASES:
            if phrase in text:
                offenders.append(f"{path.relative_to(ROOT).as_posix()}: {phrase}")

    assert offenders == []


def test_review_manifest_uses_active_inspection_semantics() -> None:
    manifest = json.loads((ROOT / "tools" / "nollm_tool_manifest.json").read_text(encoding="utf-8"))
    review = next(action for action in manifest["actions"] if action["name"] == "nollm.review")
    combined = f"{review['description']} {review['returns']}".lower()

    for required in (
        "active inspection surface",
        "metadata-derived",
        "not approval",
        "not truth assessment",
        "not semantic scoring",
        "not memory recall",
        "does not change status",
        "does not append ledger events",
    ):
        assert required in combined


def test_inspect_manifest_uses_active_inspection_semantics() -> None:
    manifest = json.loads((ROOT / "tools" / "nollm_tool_manifest.json").read_text(encoding="utf-8"))
    inspect = next(action for action in manifest["actions"] if action["name"] == "nollm.inspect")
    combined = f"{inspect['description']} {inspect['returns']}".lower()

    for required in (
        "active inspection surface",
        "metadata-derived",
        "not approval",
        "not truth assessment",
        "not semantic scoring",
        "not memory recall",
        "does not change status",
        "does not append ledger events",
    ):
        assert required in combined


def test_annotation_docs_preserve_operator_action_boundaries() -> None:
    combined = "\n".join(
        normalized_text(path)
        for path in (
            ROOT / "README.md",
            ROOT / "protocol" / "ANNOTATION.md",
            ROOT / "docs" / "integration" / "LLM_INTEGRATION.md",
        )
    )
    for required in (
        "annotations are operator notes",
        "annotations are ledgered",
        "annotations do not modify card content",
        "annotations do not change status",
        "annotations do not change trust",
        "annotations do not prove truth",
        "annotations do not approve memory",
        "annotations do not block llm usage",
        "annotations are not passive human review",
        "annotations are active operator actions",
        "audit may count annotations",
        "inspect/review may show `annotation_count`",
        "annotation text is not recall content",
        "annotation text does not change status or trust",
        "annotation text does not prove truth",
        "annotation counts are not semantic risk scores",
        "annotation_count means there are operator notes, not that a card is more or less reliable",
    ):
        assert required in combined


def test_ledger_history_docs_preserve_audit_trail_boundaries() -> None:
    combined = "\n".join(
        normalized_text(path)
        for path in (
            ROOT / "README.md",
            ROOT / "protocol" / "LEDGER.md",
            ROOT / "protocol" / "HISTORY.md",
            ROOT / "docs" / "integration" / "LLM_INTEGRATION.md",
        )
    )
    for required in (
        "ledger is an audit trail, not memory recall",
        "history is object-level ledger inspection",
        "ledger/history do not prove truth",
        "ledger/history do not approve memory",
        "ledger/history do not change status or trust",
        "ledger/history are read-only unless an explicit write action such as annotate/status is used",
        "annotation text may appear in history because history is explicit audit inspection, but annotation text is still not recall content",
    ):
        assert required in combined


def normalized_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()
