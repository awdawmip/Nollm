from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/geometry/run_dense_locality_surface_validation.py"


def _module():
    spec = importlib.util.spec_from_file_location("dense_locality_surface_validation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reduced_fixture_exercises_surface_and_truthful_counts() -> None:
    result = _module().validate(dense_cell_count=30, atom_count=60)
    assert result["dense_cells"]["occupied_cell_count"] == 30
    assert result["dense_atoms"]["atom_count"] == 60
    assert result["dense_atoms"]["reopen_identity"]
    assert result["dense_atoms"]["mutation_invalidated"]
    assert not result["checks"]["dense_cell_minimum"]
    assert not result["checks"]["dense_atom_minimum"]
