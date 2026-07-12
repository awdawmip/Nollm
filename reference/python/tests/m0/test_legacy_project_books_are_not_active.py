from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_legacy_project_books_are_not_active() -> None:
    basis = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    for relative in (
        "docs/project/NOLLM_PROJECT_BOOK_V3_0_MODULAR_GEOMETRY_INFRASTRUCTURE_M1_20260711.md",
        "docs/architecture/NOLLM_PROJECT_BOOK_V2_2_LAYERED_CORE_TO_TERMINAL.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert text.startswith("# LEGACY_REFERENCE / SUPERSEDED")
        assert Path(relative).name not in basis
