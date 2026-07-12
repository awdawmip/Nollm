from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import generate_module_ownership_manifest as manifest  # noqa: E402


def rows_by_path() -> dict[str, dict[str, object]]:
    rows, _ = manifest.build_rows(manifest.tracked_files())
    return {str(row["path"]): row for row in rows}


def test_manifest_classifies_linked_governance_as_active() -> None:
    rows = rows_by_path()
    for path in manifest.active_governance_paths():
        assert rows[path]["lifecycle_status"] == "ACTIVE"
        assert rows[path]["public_api"] == "governance"
        assert rows[path]["review_status"] == "CODE_REVIEWED"


def test_manifest_classifies_unlinked_tasks_as_historical() -> None:
    rows = rows_by_path()
    active = manifest.active_governance_paths()
    for path, row in rows.items():
        if path.startswith("docs/project/tasks/") and path not in active:
            assert row["lifecycle_status"] == "HISTORICAL"


def test_manifest_has_no_m0c1_filename_heuristic() -> None:
    source = (TOOLS / "generate_module_ownership_manifest.py").read_text(encoding="utf-8")
    assert '"M0C1" in name' not in source
    assert '"M1_" in name' not in source


def test_active_basis_change_requires_manifest_refresh(tmp_path) -> None:
    project = tmp_path / "docs/project"
    project.mkdir(parents=True)
    current = project / "current.md"
    previous = project / "previous.md"
    current.write_text("current", encoding="utf-8")
    previous.write_text("previous", encoding="utf-8")
    basis = project / "ACTIVE_PROJECT.md"
    basis.write_text("[Current](current.md)\n", encoding="utf-8")
    before = manifest.active_governance_paths(tmp_path)
    basis.write_text("[Previous](previous.md)\n", encoding="utf-8")
    after = manifest.active_governance_paths(tmp_path)
    assert before != after
    assert manifest.classify("docs/project/current.md", [], before).lifecycle == "ACTIVE"
    assert manifest.classify("docs/project/current.md", [], after).lifecycle == "HISTORICAL"
