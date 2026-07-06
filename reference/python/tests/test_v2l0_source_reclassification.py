from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DREAM_GEOMETRY = ROOT / "reference" / "python" / "nollm" / "dream_geometry"
DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "ROADMAP.md",
    ROOT / "AGENTS.md",
    ROOT / "protocol" / "v2" / "LEGACY_BOUNDARY.md",
    ROOT / "docs" / "history" / "V1_RETIREMENT_RECORD.md",
    ROOT / "docs" / "history" / "OPENCLAW_V2_MIGRATION_ASSET_BOUNDARY.md",
    ROOT / "docs" / "project" / "NOLLM_SOURCE_TOPOLOGY_V2.md",
]

FORBIDDEN_DREAM_GEOMETRY_IMPORT_PREFIXES = (
    "nollm.cli",
    "nollm.tool_api",
    "nollm.openclaw",
    "nollm.companion",
    "nollm.archive",
    "nollm.legacy",
    "nollm.native_field",
    "integrations.openclaw",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_legacy_and_openclaw_are_reclassified_as_inactive_material() -> None:
    corpus = "\n".join(read(path) for path in DOC_PATHS)

    for phrase in [
        "V1, MT1, and pre-V2 prototype",
        "retired history",
        "Physical presence is not active",
        "OpenClaw is a frozen migration asset",
        "not the current Nollm runtime",
        "HCG is an accepted L5 File Capture Adapter",
        "HAG1-C1R is accepted but unpromoted",
    ]:
        assert phrase in corpus


def test_root_docs_do_not_preserve_v1_current_navigation_phrases() -> None:
    corpus = "\n".join(read(path) for path in DOC_PATHS).lower()

    forbidden = [
        "stable v1",
        "v1 is the active",
        "v1 is active",
        "current architecture (v1 legacy state)",
        "dream geometry v2 (parallel, not yet integrated)",
        "not yet replacing v1",
        "openclaw provider is current nollm memory core",
    ]
    assert [phrase for phrase in forbidden if phrase in corpus] == []


def test_dream_geometry_source_has_no_outward_adapter_or_terminal_imports() -> None:
    offenders: list[str] = []
    for path in DREAM_GEOMETRY.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            imported_names = imported_module_names(node)
            for name in imported_names:
                if name.startswith(FORBIDDEN_DREAM_GEOMETRY_IMPORT_PREFIXES):
                    offenders.append(f"{path.relative_to(ROOT).as_posix()} imports {name}")

    assert offenders == []


def imported_module_names(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module:
        return (node.module,)
    return ()
