from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROOT_DOCS = (
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "ROADMAP.md",
    ROOT / "AGENTS.md",
)
BOUNDARY_DOCS = (
    ROOT / "protocol" / "v2" / "LAYER_CONSTITUTION.md",
    ROOT / "protocol" / "v2" / "LEGACY_BOUNDARY.md",
    ROOT / "docs" / "history" / "V1_RETIREMENT_RECORD.md",
    ROOT / "docs" / "history" / "OPENCLAW_V2_MIGRATION_ASSET_BOUNDARY.md",
)
ACTIVE_NAVIGATION_FORBIDDEN = (
    "Nollm V1 Route Lock",
    "Stable historical V1 tool actions",
    "nollm.validate",
    "nollm.orient",
    "nollm.surface",
    "nollm.focus",
    "nollm.cli",
    "examples/openclaw",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_boundary_documents_exist_for_v2_retirement_classification() -> None:
    missing = [path.relative_to(ROOT).as_posix() for path in BOUNDARY_DOCS if not path.is_file()]

    assert missing == []


def test_root_and_boundary_docs_agree_on_v2_active_protocol() -> None:
    for path in (*ROOT_DOCS, *BOUNDARY_DOCS[:2]):
        text = read(path)

        assert "V2 is the only active architecture" in text
        assert "protocol/v2" in text or path.name == "LAYER_CONSTITUTION.md"
        assert "L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0" in text


def test_openclaw_is_classified_as_migration_asset_not_runtime() -> None:
    corpus = "\n".join(read(path) for path in (*ROOT_DOCS, *BOUNDARY_DOCS))

    assert "OpenClaw legacy is a frozen L5/L6 migration asset" in corpus
    assert "not current runtime" in corpus
    assert "not the current Nollm runtime path" in corpus
    assert "not a Core dependency" in corpus
    assert "L5 Host Adapter or L6 Terminal" in corpus


def test_root_docs_do_not_depend_on_v1_cli_tool_actions_or_openclaw_fixtures() -> None:
    for path in ROOT_DOCS:
        text = read(path)
        offenders = [phrase for phrase in ACTIVE_NAVIGATION_FORBIDDEN if phrase in text]

        assert offenders == [], f"{path} uses retired V1 material as active navigation: {offenders}"


def test_legacy_presence_is_not_current_stable_or_parallel_active_status() -> None:
    corpus = "\n".join(read(path) for path in (*ROOT_DOCS, *BOUNDARY_DOCS)).lower()
    forbidden = (
        "v1 is active runtime",
        "v1 is the active runtime",
        "stable v1",
        "current v1",
        "parallel active",
        "openclaw is integrated",
        "openclaw runtime is active",
    )

    assert [phrase for phrase in forbidden if phrase in corpus] == []
