from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BOOK = ROOT / "docs/project/NOLLM_ROUTE_BOOK_V3_7_ROTATED_PHYSICAL_FIELD_20260714.md"


def test_active_project_route_is_v37_and_role_correct() -> None:
    basis = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    book = BOOK.read_text(encoding="utf-8")
    assert BOOK.name in basis
    assert "adjacent-layer rotation `22.5 degrees`" in book
    assert "linear scale ratio `beta = 2^(1/4)`" in book
    assert "`GeometryAddress` identifies only a persistent physical memory cell" in book
    assert "single-entry" in book
