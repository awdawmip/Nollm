from __future__ import annotations

from pathlib import Path

from conftest import cleanup_generated_python_artifacts


ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FIXTURES = {
    "AGENTS.md",
    "docs/project/ACTIVE_PROJECT.md",
    "docs/project/NOLLM_ACTIVE_REPOSITORY_ASSET_POLICY.md",
    "docs/architecture/module-ownership/ACTIVE_ASSET_CURATION_PLAN.json",
    "protocol/v2/LAYER_CONSTITUTION.md",
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
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for command in (
        "python -m pytest -q packages/nollm-core/tests",
        "python -m pytest -q packages/nollm-access/tests",
        "python tools/generate_module_ownership_manifest.py --check",
        "python tools/check_active_tree_assets.py",
    ):
        assert command in readme
    assert "NOLLM_ACTIVE_REPOSITORY_ASSET_POLICY.md" in readme


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
