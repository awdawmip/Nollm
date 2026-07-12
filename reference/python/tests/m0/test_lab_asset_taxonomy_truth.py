import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MANIFEST = ROOT / "docs/architecture/module-ownership/MODULE_OWNERSHIP_MANIFEST.json"
ACTIVE_CLASSES = {
    "ACTIVE_LIBRARY", "ACTIVE_TOOL", "ACTIVE_FIXTURE", "ACTIVE_TEST",
    "ACTIVE_VALIDATION", "ACTIVE_REPOSITORY_TOOL",
}


def lab_rows() -> list[dict[str, object]]:
    return [row for row in json.loads(MANIFEST.read_text(encoding="utf-8")) if row["owner"] == "LAB"]


def test_all_lab_assets_have_a_valid_class_and_gate_coverage() -> None:
    rows = lab_rows()
    assert rows
    assert all(row["asset_class"] for row in rows)
    assert all(row["validation_gate"] for row in rows if row["asset_class"] in ACTIVE_CLASSES | {"LEGACY_REGRESSION"})
    assert all(not row["validation_gate"] for row in rows if row["asset_class"] in {"LEGACY_REFERENCE", "HISTORICAL_RESULT"})


def test_stable_suites_have_exact_classes() -> None:
    rows = lab_rows()
    assert all(row["asset_class"] == "ACTIVE_TEST" and row["validation_gate"].startswith("package:") for row in rows if row["path"].startswith("packages/") and "/tests/" in row["path"])
    assert all(row["asset_class"] == "ACTIVE_TEST" and row["validation_gate"] == "governance:m0" for row in rows if row["path"].startswith("reference/python/tests/m0/"))
    assert all(row["asset_class"] == "LEGACY_REGRESSION" and row["validation_gate"] == "compatibility:grf" for row in rows if row["path"].startswith("reference/python/tests/grf/"))


def test_broad_lab_roots_are_not_default_active() -> None:
    historical_roots = ("examples/", "experiments/", "validation/")
    assert all(row["asset_class"] not in ACTIVE_CLASSES for row in lab_rows() if row["path"].startswith(historical_roots))


def test_statement_formation_assets_have_explicit_gates() -> None:
    rows = [row for row in lab_rows() if row["path"].startswith("lab/nollm-lab/statement_formation/")]
    assert rows
    assert all(row["asset_class"] == "LEGACY_REGRESSION" for row in rows)
    assert all(row["lifecycle_status"] == "MIGRATION_ASSET" for row in rows)
    assert {row["validation_gate"] for row in rows} == {"lab:statement-formation-corpus", "lab:statement-formation-fixtures"}


def test_lab_charter_is_an_active_governance_fixture() -> None:
    charter = next(row for row in lab_rows() if row["path"] == "docs/architecture/modules/NOLLM_LAB_CHARTER.md")
    assert charter["asset_class"] == "ACTIVE_FIXTURE"
    assert charter["validation_gate"] == "repository:manifest"
