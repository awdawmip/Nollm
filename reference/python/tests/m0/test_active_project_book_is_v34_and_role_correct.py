from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BOOK = ROOT / "docs/project/NOLLM_PROJECT_BOOK_V3_4_CORE_FUNCTION_PRIORITY_20260713.md"


def test_active_project_book_is_v34_and_role_correct() -> None:
    basis = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    book = BOOK.read_text(encoding="utf-8")
    assert BOOK.name in basis
    assert "Host LLM owns semantic" in book
    assert "Core owns deterministic validation, geometry" in book
    assert "bounded recall" in book
    assert "No external semantic index, vector, graph, or global" in book
