from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/geometry/run_dense_single_entry_recall_validation.py"


def _module():
    spec = importlib.util.spec_from_file_location("dense_single_entry_recall_validation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reduced_dense_recall_is_single_entry_and_kernel_dependent() -> None:
    result = _module().validate(cell_count=30, atom_count=100)
    assert result["enabled"]["entry_count"] == 1
    assert result["enabled"]["target_path"] == ["coverage_down"]
    assert not result["disabled"]["target_reached"]
    assert not result["natural_multi_entry_observation"]["combined_request_used"]
    assert not result["checks"]["full_dense_cell_minimum"]
    assert not result["checks"]["full_dense_atom_minimum"]
