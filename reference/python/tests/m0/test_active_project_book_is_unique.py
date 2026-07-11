from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ACTIVE = ROOT / "docs/project/NOLLM_PROJECT_BOOK_V3_0_MODULAR_GEOMETRY_INFRASTRUCTURE_M1_20260711.md"


def test_active_project_book_is_unique() -> None:
    index = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    assert ACTIVE.name in index
    assert index.count("NOLLM_PROJECT_BOOK_") == 1
    legacy = (ROOT / "docs/architecture/NOLLM_PROJECT_BOOK_V2_2_LAYERED_CORE_TO_TERMINAL.md").read_text(encoding="utf-8")
    assert legacy.startswith("# LEGACY_REFERENCE / SUPERSEDED")
    assert ACTIVE.name in legacy
