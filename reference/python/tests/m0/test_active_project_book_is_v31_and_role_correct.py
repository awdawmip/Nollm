from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BOOK = ROOT / "docs/project/NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md"


def test_active_project_book_is_v31_and_role_correct() -> None:
    basis = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    book = BOOK.read_text(encoding="utf-8")
    assert BOOK.name in basis
    assert "Active architecture and baseline-governance authority" in book
    for stable_role in ("Module Ownership", "Dependency Direction", "Public Contract Governance", "Evolving Baseline Governance"):
        assert stable_role in book
