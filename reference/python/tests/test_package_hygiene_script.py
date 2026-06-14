from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "reference" / "python" / "scripts" / "check_package_hygiene.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_package_hygiene", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_hygiene_script_passes_clean_temp_tree(tmp_path: Path) -> None:
    checker = load_checker()
    (tmp_path / "examples" / "openclaw" / "recalls").mkdir(parents=True)
    (tmp_path / "examples" / "openclaw" / "recalls" / "sample_recall_digest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "examples" / "audit_reports").mkdir(parents=True)
    (tmp_path / "examples" / "audit_reports" / "openclaw_audit.json").write_text("{}", encoding="utf-8")

    assert checker.find_issues(tmp_path) == []


def test_package_hygiene_script_detects_generated_recall(tmp_path: Path) -> None:
    checker = load_checker()
    recalls = tmp_path / "examples" / "openclaw" / "recalls"
    recalls.mkdir(parents=True)
    (recalls / "recall_000001.json").write_text("{}", encoding="utf-8")

    assert checker.find_issues(tmp_path) == ["examples/openclaw/recalls/recall_000001.json"]


def test_release_docs_exist() -> None:
    assert (ROOT / "docs" / "V1_RELEASE_CHECKLIST.md").exists()
    assert (ROOT / "docs" / "V1_RELEASE_NOTES_DRAFT.md").exists()
