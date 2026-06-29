import importlib
import pathlib
from unittest.mock import patch


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
V2_MODULES = [
    "nollm.dream_geometry",
    "nollm.dream_geometry.protocol",
    "nollm.dream_geometry.evidence",
    "nollm.dream_geometry.geometry",
    "nollm.dream_geometry.field",
    "nollm.dream_geometry.cortex",
    "nollm.dream_geometry.recall",
    "nollm.dream_geometry.adapters",
    "nollm.dream_geometry.validation",
]


def test_all_v2_packages_import_without_runtime_side_effects() -> None:
    with patch("pathlib.Path.read_text", side_effect=AssertionError("unexpected read_text")), patch(
        "pathlib.Path.write_text", side_effect=AssertionError("unexpected write_text")
    ), patch("builtins.open", side_effect=AssertionError("unexpected open")), patch(
        "subprocess.Popen", side_effect=AssertionError("unexpected subprocess")
    ):
        for module_name in V2_MODULES:
            module = importlib.import_module(module_name)
            assert module.__all__ is not None


def test_module_docstrings_state_allowed_and_forbidden_roles() -> None:
    for module_name in V2_MODULES:
        module = importlib.import_module(module_name)
        doc = module.__doc__ or ""
        assert "Allowed:" in doc
        assert "Forbidden:" in doc


def test_required_dg0_documents_exist_and_governance_mentions_v2_priority() -> None:
    required = [
        "docs/architecture/NOLLM_V2_MODULE_BOUNDARIES_DG0.md",
        "docs/architecture/NOLLM_V2_MIGRATION_BOUNDARY_DG0.md",
        "docs/architecture/NOLLM_GEOMETRY_ARCHITECTURE_AMENDMENT_V2_ATLAS_COVERAGE_KERNELS_20260629.md",
        "protocol/v2/CONSTITUTION.md",
        "protocol/v2/MODULE_DEPENDENCY_RULES.md",
        "protocol/v2/OBJECT_OWNERSHIP.md",
        "protocol/v2/INVARIANTS.md",
        "protocol/v2/LEGACY_BOUNDARY.md",
    ]
    for relative in required:
        assert (REPO_ROOT / relative).is_file(), relative

    governance = "\n".join(
        [
            (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8"),
        ]
    )
    assert "Dream Geometry V2 Route Lock" in governance
    assert "V2 amendment" in governance
    assert "parallel, not yet integrated" in governance
