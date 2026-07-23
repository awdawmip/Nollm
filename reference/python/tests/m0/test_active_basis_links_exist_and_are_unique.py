from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[4]


def test_active_basis_links_exist_and_are_unique() -> None:
    basis_path = ROOT / "docs/project/ACTIVE_PROJECT.md"
    links = re.findall(r"\[[^]]+\]\(([^)]+)\)", basis_path.read_text(encoding="utf-8"))
    assert len(links) == 8
    assert len(set(links)) == len(links)
    assert all((basis_path.parent / link).is_file() for link in links)
