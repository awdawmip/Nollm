from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BOOK = ROOT / "docs/project/NOLLM_ROUTE_BOOK_V3_6_ADAPTIVE_MULTI_SCALE_SURFACE_20260714.md"


def test_active_project_route_is_v36_and_role_correct() -> None:
    basis = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    book = BOOK.read_text(encoding="utf-8")
    assert BOOK.name in basis
    assert "Surface完全由Core canonical geometry确定性派生" in book
    assert "k*`由几何规模和预算确定，不由语义查询确定" in book
    assert "真实LLM负责语义" in book
    assert "无graph/vector/embedding主路径" in book
