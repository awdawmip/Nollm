import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))

from validate_module_ownership_manifest import active_lab_contract_errors  # noqa: E402


def manifest_rows() -> list[dict[str, object]]:
    return json.loads((ROOT / "docs/architecture/module-ownership/MODULE_OWNERSHIP_MANIFEST.json").read_text(encoding="utf-8"))


def test_active_lab_public_imports_resolve() -> None:
    errors = [error for row in manifest_rows() for error in active_lab_contract_errors(row, ROOT)]
    assert errors == []


def test_missing_public_symbol_fails_contract_validation(tmp_path) -> None:
    package = tmp_path / "packages/nollm-core/src/nollm_core"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('__all__ = ["Present"]\n', encoding="utf-8")
    for name, relative in {
        "nollm_access": "packages/nollm-access/src/nollm_access",
        "nollm_snapshot": "packages/nollm-snapshot/src/nollm_snapshot",
        "nollm_trace": "packages/nollm-trace/src/nollm_trace",
    }.items():
        target = tmp_path / relative
        target.mkdir(parents=True)
        (target / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    script = tmp_path / "lab/nollm-lab/tool.py"
    script.parent.mkdir(parents=True)
    script.write_text("from nollm_core import Missing\n", encoding="utf-8")
    row = {"path": "lab/nollm-lab/tool.py", "owner": "LAB", "lifecycle_status": "ACTIVE", "file_type": "py"}
    assert "missing public symbol nollm_core.Missing" in active_lab_contract_errors(row, tmp_path)[0]


def test_dynamic_import_and_getattr_fail_contract_validation(tmp_path) -> None:
    for name, relative in {
        "nollm_core": "packages/nollm-core/src/nollm_core",
        "nollm_access": "packages/nollm-access/src/nollm_access",
        "nollm_snapshot": "packages/nollm-snapshot/src/nollm_snapshot",
        "nollm_trace": "packages/nollm-trace/src/nollm_trace",
    }.items():
        target = tmp_path / relative
        target.mkdir(parents=True)
        (target / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    script = tmp_path / "lab/nollm-lab/tool.py"
    script.parent.mkdir(parents=True)
    script.write_text("import importlib\nimport nollm_core\ngetattr(nollm_core, 'hidden')\nimportlib.import_module('nollm_core._state')\n", encoding="utf-8")
    row = {"path": "lab/nollm-lab/tool.py", "owner": "LAB", "lifecycle_status": "ACTIVE", "file_type": "py"}
    errors = active_lab_contract_errors(row, tmp_path)
    assert any("dynamic getattr" in error for error in errors)
    assert any("dynamic import_module" in error for error in errors)


def test_history_lab_scripts_are_not_active() -> None:
    rows = manifest_rows()
    history = [row for row in rows if str(row["path"]).startswith("lab/nollm-lab/history/")]
    assert history
    assert all(row["owner"] == "LAB" and row["lifecycle_status"] == "HISTORICAL" for row in history)


def test_lab_asset_classes_follow_stable_directories() -> None:
    rows = manifest_rows()
    for row in rows:
        path = str(row["path"])
        if path.startswith("lab/nollm-lab/openclaw/results/"):
            assert row["lifecycle_status"] == "HISTORICAL" and row["runtime_role"] == "historical result"
        elif path.startswith("lab/nollm-lab/openclaw/datasets/"):
            assert row["lifecycle_status"] == "ACTIVE" and row["runtime_role"] == "active fixture"
        elif path.startswith("lab/nollm-lab/m1/"):
            assert row["lifecycle_status"] == "ACTIVE" and row["runtime_role"] == "active tool"
        elif path.startswith("lab/nollm-lab/geometry/"):
            assert row["lifecycle_status"] == "ACTIVE" and row["runtime_role"] in {"active library", "active tool"}
