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
FIXTURE_EXTENSIONS = {".json", ".jsonl", ".md", ".yaml", ".yml"}


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


def test_committed_fixtures_do_not_contain_machine_local_absolute_paths() -> None:
    offenders = []
    for path in (ROOT / "examples").rglob("*"):
        if not path.is_file() or path.suffix.lower() not in FIXTURE_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8")
        if has_machine_local_absolute_path(text):
            offenders.append(path.relative_to(ROOT).as_posix())

    assert offenders == []


def test_canonical_test_command_is_documented() -> None:
    docs = [
        ROOT / "README.md",
        ROOT / "reference" / "python" / "PACKAGING.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "python3 run_tests.py" in text or "python run_tests.py" in text
        assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1" in text


def relative_paths(paths) -> list[str]:
    return sorted(path.relative_to(ROOT).as_posix() for path in paths)


def has_machine_local_absolute_path(text: str) -> bool:
    markers = (
        "C:\\",
        "C:/",
        "\\Users\\",
        "/Users/",
        "/home/",
    )
    return any(marker in text for marker in markers)
