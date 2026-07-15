from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BOOK = ROOT / "docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md"


def test_active_project_route_is_v39_and_role_correct() -> None:
    basis = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    book = BOOK.read_text(encoding="utf-8")
    assert BOOK.name in basis
    assert "当前活动路线；替代 V3.8" in book
    assert "生产几何使用有界近似稀疏核" in book
    assert "Surface 惰性构建" in book
    assert "P1 Formation→Placement→restart Recall" in book
