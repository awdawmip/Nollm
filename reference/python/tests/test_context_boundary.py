from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNTIME_PATHS = [
    ROOT / "reference" / "python" / "nollm",
    ROOT / "tools" / "nollm_tool_manifest.json",
]


def test_no_context_command_or_tool_is_registered() -> None:
    manifest = json.loads((ROOT / "tools" / "nollm_tool_manifest.json").read_text(encoding="utf-8"))
    action_names = {action["name"] for action in manifest["actions"]}

    assert "nollm.context" not in action_names

    cli_text = (ROOT / "reference" / "python" / "nollm" / "cli.py").read_text(encoding="utf-8")
    assert 'add_parser("context"' not in cli_text
    assert "add_parser('context'" not in cli_text


def test_no_context_example_or_runtime_context_builder_exists() -> None:
    top_level_examples = {path.name for path in (ROOT / "examples" / "tool_requests").glob("*.json")}
    assert "context_openclaw_card.json" not in top_level_examples

    forbidden_tokens = (
        "def build_context",
        "class Context",
        "neighbor_limit",
        "shared_anchor_card_count",
        "related_cards",
        "semantic_matches",
        "ranked_cards",
    )
    offenders = []
    for base in RUNTIME_PATHS:
        paths = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in forbidden_tokens:
                if token in text:
                    offenders.append(f"{path.relative_to(ROOT).as_posix()}: {token}")

    assert offenders == []


def test_docs_assign_context_composition_to_cortex_or_llm() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (
            ROOT / "README.md",
            ROOT / "protocol" / "READ.md",
            ROOT / "protocol" / "TOOL_SURFACE.md",
            ROOT / "docs" / "integration" / "LLM_INTEGRATION.md",
        )
    ).replace("`", "")
    for required in (
        "read_card reads exactly one explicit card",
        "read_card is not recall",
        "read_card is not context composition",
        "read_card does not return neighbors",
        "read_card does not rank related cards",
        "core does not assemble deterministic context",
        "context composition belongs to cortex / llm using explicit calls",
        "if an llm needs context, it should make explicit read/inspect/history/ledger/recall calls and compose outside core",
        "read / read_card = explicit object read",
        "context composition = cortex-side, not core",
    ):
        assert required in combined
