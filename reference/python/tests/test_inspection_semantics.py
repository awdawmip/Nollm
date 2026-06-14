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
    "semantic risk score",
    "semantic risk scoring",
    "confirmed fact",
)
DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "protocol" / "REVIEW.md",
    ROOT / "protocol" / "ANNOTATION.md",
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
    ):
        assert required in combined


def normalized_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()
