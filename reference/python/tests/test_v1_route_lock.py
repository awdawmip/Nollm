from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
V1_CLI_COMMANDS = {
    "validate",
    "orient",
    "recall",
    "read",
    "inspect",
    "review",
    "annotate",
    "annotations",
    "ledger",
    "history",
    "audit",
    "audit-check",
    "tool",
}
V1_TOOL_ACTIONS = {
    "nollm.validate",
    "nollm.orient",
    "nollm.recall",
    "nollm.read_card",
    "nollm.inspect",
    "nollm.review",
    "nollm.annotate",
    "nollm.annotations",
    "nollm.ledger",
    "nollm.history",
    "nollm.audit",
}
INTERNAL_ACTIONS = {
    "nollm.surface",
    "nollm.focus",
    "nollm.write_card",
    "nollm.update_status",
}


def test_v1_route_lock_docs_are_present() -> None:
    docs = [
        ROOT / "README.md",
        ROOT / "ROADMAP.md",
        ROOT / "ARCHITECTURE.md",
    ]
    required = (
        "Nollm V1 Route Lock",
        "Nollm V1 Core exposes explicit filesystem-backed objects, deterministic validation, audit projections, and tool surfaces.",
        "Nollm V1 Core does not compose context, rank semantics, infer truth, or perform autonomous memory management.",
        "context composition",
        "ledger/history inspection",
    )
    for path in docs:
        text = path.read_text(encoding="utf-8")
        for phrase in required:
            assert phrase in text, f"{path}: {phrase}"


def test_v1_non_goals_are_documented() -> None:
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in ("ROADMAP.md", "ARCHITECTURE.md")
    )
    for phrase in (
        "No SQLite runtime.",
        "No database-backed recall.",
        "No embedding/vector search.",
        "No graph database.",
        "No MCP server.",
        "No external LLM calls.",
        "No geometry recall.",
        "No polygon overlap.",
        "No automatic card placement.",
        "No automatic anchor creation.",
        "No automatic status approval.",
        "No autonomous memory rewriting.",
        "No semantic completeness scoring.",
        "No truth scoring.",
        "No passive human review inbox.",
        "No mandatory human approval gate.",
        "No tree descent.",
        "No parent/children hierarchy.",
        "No automatic context composition.",
        "No deterministic context bundle.",
        "No neighbor/related-card ranking.",
    ):
        assert phrase in combined


def test_manifest_marks_v1_stable_and_internal_actions() -> None:
    manifest = json.loads((ROOT / "tools" / "nollm_tool_manifest.json").read_text(encoding="utf-8-sig"))
    actions = {entry["name"]: entry for entry in manifest["actions"]}
    assert V1_TOOL_ACTIONS.issubset(actions)
    assert INTERNAL_ACTIONS.issubset(actions)
    for name in V1_TOOL_ACTIONS:
        entry = actions[name]
        assert entry["v1_surface"] == "stable"
        assert "kind" in entry
        assert "writes_ledger" in entry
        assert "mutates_cards" in entry
        assert "boundaries" in entry
        combined = f"{entry['description']} {entry['returns']} {' '.join(entry['boundaries'])}".lower()
        assert "truth" in combined
        assert "semantic" in combined
    for name in INTERNAL_ACTIONS:
        assert actions[name]["v1_surface"] == "internal-experimental"


def test_no_new_runtime_route_expansion() -> None:
    cli_text = (ROOT / "reference" / "python" / "nollm" / "cli.py").read_text(encoding="utf-8")
    for forbidden in ('add_parser("context"', "add_parser('context'"):
        assert forbidden not in cli_text
    manifest = json.loads((ROOT / "tools" / "nollm_tool_manifest.json").read_text(encoding="utf-8-sig"))
    action_names = {entry["name"] for entry in manifest["actions"]}
    assert "nollm.context" not in action_names


def test_known_limitations_are_documented() -> None:
    text = (ROOT / "docs" / "V1_KNOWN_LIMITATIONS.md").read_text(encoding="utf-8").replace("`", "")
    for phrase in (
        "Unicode/mojibake terminology guard remains deferred.",
        "No GitHub Actions yet.",
        "No formal CONTRIBUTING.md yet.",
        "No public AGENTS.example.md yet.",
        "Packaging remains simple.",
        "Generated-output recall examples are isolated and should be run against temp notebooks.",
        "SQLite audit projection remains future research, not V1 runtime.",
        "MCP remains future consideration, not V1.",
    ):
        assert phrase in text
