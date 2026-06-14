from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

MAJOR_DOCS = (
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "ROADMAP.md",
)

STABLE_ACTIONS = (
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
)

INTERNAL_ACTIONS = (
    "nollm.surface",
    "nollm.focus",
    "nollm.write_card",
    "nollm.update_status",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_major_docs_share_v1_route_lock_language() -> None:
    required = (
        "Nollm V1 Route Lock",
        "Nollm V1 Core exposes explicit filesystem-backed objects",
        "Nollm V1 Core does not compose context",
        "Cortex / LLM",
    )
    for path in MAJOR_DOCS:
        text = read(path)
        for phrase in required:
            assert phrase in text, f"{path}: missing {phrase!r}"


def test_readme_and_tool_surface_list_stable_v1_tool_actions() -> None:
    for path in (ROOT / "README.md", ROOT / "protocol" / "TOOL_SURFACE.md"):
        text = read(path)
        for action in STABLE_ACTIONS:
            assert action in text, f"{path}: missing stable action {action}"


def test_internal_actions_are_labeled_internal_or_experimental() -> None:
    for path in (ROOT / "README.md", ROOT / "protocol" / "TOOL_SURFACE.md"):
        text = read(path)
        for action in INTERNAL_ACTIONS:
            index = text.find(action)
            assert index >= 0, f"{path}: missing internal action {action}"
            context = text[max(0, index - 160) : index + 240].lower()
            assert "internal" in context or "experimental" in context, f"{path}: {action} is not labeled"


def test_known_limitations_file_exists_and_matches_roadmap() -> None:
    limitations = read(ROOT / "docs" / "V1_KNOWN_LIMITATIONS.md").replace("`", "")
    roadmap = read(ROOT / "ROADMAP.md").replace("`", "")
    required = (
        "Unicode/mojibake terminology guard remains deferred.",
        "No GitHub Actions yet.",
        "No formal CONTRIBUTING.md yet.",
        "No public AGENTS.example.md yet.",
        "Packaging remains simple.",
        "recall_scale_scan example requires care because it may generate digest files.",
        "SQLite audit projection remains future research, not V1 runtime.",
        "MCP remains future consideration, not V1.",
    )
    for phrase in required:
        assert phrase in limitations
        assert phrase in roadmap


def test_forbidden_context_surface_is_not_documented_as_available() -> None:
    docs = "\n".join(
        read(path)
        for path in (
            ROOT / "README.md",
            ROOT / "docs" / "integration" / "LLM_INTEGRATION.md",
            ROOT / "protocol" / "TOOL_SURFACE.md",
        )
    )
    assert "nollm.context" not in docs
    assert "deterministic context bundle is implemented" not in docs.lower()
    assert "orient -> surface -> focus -> recall" not in docs
