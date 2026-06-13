from __future__ import annotations

from pathlib import Path

from conftest import cleanup_generated_python_artifacts


ROOT = Path(__file__).resolve().parents[3]
ALLOWED_RECALL_FIXTURES = {
    "examples/openclaw/recalls/sample_recall_digest.json",
    "examples/openclaw/recalls/sample_recall_digest.md",
}
REQUIRED_FIXTURES = {
    "examples/audit_reports/openclaw_audit.json",
    *ALLOWED_RECALL_FIXTURES,
}


def test_repository_tree_has_no_generated_artifacts() -> None:
    cleanup_generated_python_artifacts()
    generated = []
    generated.extend(relative_paths(ROOT.rglob(".pytest_cache")))
    generated.extend(relative_paths(ROOT.rglob("__pycache__")))
    generated.extend(relative_paths(ROOT.rglob("*.pyc")))
    generated.extend(
        path
        for pattern in ("examples/openclaw/recalls/recall_*.json", "examples/openclaw/recalls/recall_*.md")
        for path in relative_paths(ROOT.glob(pattern))
        if path not in ALLOWED_RECALL_FIXTURES
    )

    assert sorted(generated) == []


def test_required_hygiene_fixtures_remain_present() -> None:
    missing = sorted(path for path in REQUIRED_FIXTURES if not (ROOT / path).exists())

    assert missing == []


def relative_paths(paths) -> list[str]:
    return sorted(path.relative_to(ROOT).as_posix() for path in paths)
