from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BOOK = ROOT / "docs/project/NOLLM_ROUTE_BOOK_V3_8_TRANSLATION_COVARIANT_COVERAGE_REUSE_20260714.md"


def test_active_project_route_is_v38_and_role_correct() -> None:
    basis = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    book = BOOK.read_text(encoding="utf-8")
    assert BOOK.name in basis
    assert "平移协变 Coverage" in book
    assert "两个 Oracle 先于 certification" in book
    assert "Surface 使用全部 overlap members" in book
    assert "实际 path 包含 coverage_up/down" in book
