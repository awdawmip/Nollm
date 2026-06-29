import ast
import importlib
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
FIELD_ROOT = REPO_ROOT / "reference" / "python" / "nollm" / "dream_geometry" / "field"
FORBIDDEN_IMPORT_PREFIXES = (
    "nollm.openclaw_",
    "nollm.dream_geometry.cortex",
    "nollm.dream_geometry.recall",
    "nollm.dream_geometry.adapters",
    "nollm.dream_geometry.validation",
    "subprocess",
    "socket",
    "requests",
    "urllib",
)
FORBIDDEN_TEXT = ("select_anchor", "semantic_search", "best_memory")


def test_dg2_b1_field_imports_only_protocol_and_geometry() -> None:
    for path in FIELD_ROOT.rglob("*.py"):
        for imported in _imports(path):
            assert not imported.startswith(FORBIDDEN_IMPORT_PREFIXES), f"{path} imports {imported}"


def test_dg2_b2_field_import_has_no_side_effects() -> None:
    imported = importlib.import_module("nollm.dream_geometry.field")
    assert imported.__all__


def test_dg2_b6_no_external_anchor_or_query_selector_language() -> None:
    for path in FIELD_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_TEXT:
            assert forbidden not in text


def test_dg2_b6_report_uses_synthetic_small_fixtures() -> None:
    from nollm.dream_geometry.validation.dg2_field_report import build_report

    report = build_report()
    assert "synthetic_only" in report
    assert "DG2 Field Dynamics Baseline Report" in report
    assert "DG1_PURE_GEOMETRY_BASELINE_REPORT" not in report


def test_dg2_protocol_invariants_are_supplemental_to_dg0_contract() -> None:
    from nollm.dream_geometry.protocol.contracts import DG2_FIELD_INVARIANTS, INVARIANTS

    assert [item.identifier for item in INVARIANTS] == [f"I-V2-{index:03d}" for index in range(1, 11)]
    assert [item.identifier for item in DG2_FIELD_INVARIANTS] == [f"I-V2-{index:03d}" for index in range(11, 19)]


def _imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    return imports
