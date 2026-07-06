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

    assert checker.find_issues(tmp_path) == []


def test_package_hygiene_script_detects_generated_recall(tmp_path: Path) -> None:
    checker = load_checker()
    recalls = tmp_path / "examples" / "openclaw" / "recalls"
    recalls.mkdir(parents=True)
    (recalls / "recall_000001.json").write_text("{}", encoding="utf-8")

    assert checker.find_issues(tmp_path) == ["examples/openclaw/recalls/recall_000001.json"]


def test_package_hygiene_allows_runtime_release_archives_only(tmp_path: Path) -> None:
    checker = load_checker()
    runtime = tmp_path / "out" / "nollm_runtime" / "releases"
    runtime.mkdir(parents=True)
    (runtime / "local_rc.zip").write_bytes(b"zip")
    (tmp_path / "leaked.zip").write_bytes(b"zip")

    assert checker.find_issues(tmp_path) == ["leaked.zip"]


def test_v2_source_topology_and_retirement_records_exist() -> None:
    required = (
        ROOT / "docs" / "project" / "NOLLM_SOURCE_TOPOLOGY_V2.md",
        ROOT / "docs" / "history" / "V1_RETIREMENT_RECORD.md",
        ROOT / "docs" / "history" / "OPENCLAW_V2_MIGRATION_ASSET_BOUNDARY.md",
    )

    assert [path for path in required if not path.exists()] == []
