import importlib
import pathlib
import sys

from subprocess_harness import RunResult, run_subprocess


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = REPO_ROOT / "reference" / "python"
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


FRESH_IMPORT_BOOTSTRAP = r"""
import importlib
import io
import os
import pathlib
import socket
import subprocess
import sys
import urllib.request

reference_python = sys.argv[1]
module_name = sys.argv[2]
sys.path.insert(0, reference_python)

def fail(name):
    def _blocked(*args, **kwargs):
        raise RuntimeError(f"blocked import side effect: {name}")
    return _blocked

import builtins
builtins.open = fail("builtins.open")
io.open = fail("io.open")
pathlib.Path.open = fail("pathlib.Path.open")
pathlib.Path.read_text = fail("pathlib.Path.read_text")
pathlib.Path.read_bytes = fail("pathlib.Path.read_bytes")
pathlib.Path.write_text = fail("pathlib.Path.write_text")
pathlib.Path.write_bytes = fail("pathlib.Path.write_bytes")
os.open = fail("os.open")
os.read = fail("os.read")
os.write = fail("os.write")
os.remove = fail("os.remove")
os.rename = fail("os.rename")
os.replace = fail("os.replace")
socket.socket = fail("socket.socket")
socket.create_connection = fail("socket.create_connection")
subprocess.Popen = fail("subprocess.Popen")
subprocess.run = fail("subprocess.run")
subprocess.call = fail("subprocess.call")
subprocess.check_call = fail("subprocess.check_call")
subprocess.check_output = fail("subprocess.check_output")
urllib.request.urlopen = fail("urllib.request.urlopen")

module = importlib.import_module(module_name)
assert module.__all__ is not None
"""


def run_fresh_import(module_name: str, reference_python: pathlib.Path = REFERENCE_PYTHON) -> RunResult:
    return run_subprocess(
        [sys.executable, "-c", FRESH_IMPORT_BOOTSTRAP, str(reference_python), module_name],
        cwd=REPO_ROOT,
        timeout_seconds=30,
    )


def test_all_v2_packages_import_without_runtime_side_effects_in_fresh_processes() -> None:
    for module_name in V2_MODULES:
        result = run_fresh_import(module_name)
        assert result.returncode == 0, f"{module_name}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


def test_fresh_import_purity_catches_builtins_open_side_effect(tmp_path: pathlib.Path) -> None:
    package_root = tmp_path / "reference" / "python" / "nollm" / "dream_geometry" / "protocol"
    package_root.mkdir(parents=True)
    (tmp_path / "reference" / "python" / "nollm" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "reference" / "python" / "nollm" / "dream_geometry" / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    (package_root / "__init__.py").write_text("open('marker.txt', 'w')\n__all__ = []\n", encoding="utf-8")
    result = run_fresh_import("nollm.dream_geometry.protocol", tmp_path / "reference" / "python")
    assert result.returncode != 0
    assert "blocked import side effect: builtins.open" in result.stderr


def test_fresh_import_purity_catches_os_open_side_effect(tmp_path: pathlib.Path) -> None:
    package_root = tmp_path / "reference" / "python" / "nollm" / "dream_geometry" / "geometry"
    package_root.mkdir(parents=True)
    (tmp_path / "reference" / "python" / "nollm" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "reference" / "python" / "nollm" / "dream_geometry" / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    (package_root / "__init__.py").write_text("import os\nos.open('marker.txt', os.O_CREAT | os.O_WRONLY)\n__all__ = []\n", encoding="utf-8")
    result = run_fresh_import("nollm.dream_geometry.geometry", tmp_path / "reference" / "python")
    assert result.returncode != 0
    assert "blocked import side effect: os.open" in result.stderr


def test_module_docstrings_state_allowed_and_forbidden_roles() -> None:
    for module_name in V2_MODULES:
        module = importlib.import_module(module_name)
        doc = module.__doc__ or ""
        assert "Allowed:" in doc
        assert "Forbidden:" in doc


def test_required_v2_canonical_documents_exist_and_governance_prioritizes_v2() -> None:
    required = [
        "docs/architecture/NOLLM_V2_MODULE_BOUNDARIES_DG0.md",
        "docs/architecture/NOLLM_V2_MIGRATION_BOUNDARY_DG0.md",
        "docs/architecture/NOLLM_GEOMETRY_ARCHITECTURE_AMENDMENT_V2_ATLAS_COVERAGE_KERNELS_20260629.md",
        "protocol/v2/CONSTITUTION.md",
        "protocol/v2/LAYER_CONSTITUTION.md",
        "protocol/v2/MODULE_DEPENDENCY_RULES.md",
        "protocol/v2/OBJECT_OWNERSHIP.md",
        "protocol/v2/INVARIANTS.md",
        "protocol/v2/LEGACY_BOUNDARY.md",
    ]
    for relative in required:
        assert (REPO_ROOT / relative).is_file(), relative

    layer = (REPO_ROOT / "protocol" / "v2" / "LAYER_CONSTITUTION.md").read_text(encoding="utf-8")
    legacy = (REPO_ROOT / "protocol" / "v2" / "LEGACY_BOUNDARY.md").read_text(encoding="utf-8")
    root_governance = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8"),
        ]
    )
    assert "V2 is the only active architecture" in layer
    assert "L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0" in layer
    assert "Capture, Admission, and Assembly are business paths, not layers" in layer
    assert "V1, MT1, and pre-V2 prototype material is retired history" in legacy
    assert "Physical presence is not active status" in legacy
    assert "Core does not import adapters or terminals" in root_governance
    assert "Dream Geometry V2 Route Lock" not in root_governance
    assert "Nollm V1 Route Lock" not in root_governance
    assert "nollm.cli" not in root_governance
    assert "examples/openclaw" not in root_governance
