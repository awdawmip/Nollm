from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/recall_lens/run_synthetic_lens_contract_conformance.py"


def _module():
    spec = importlib.util.spec_from_file_location("recall_lens_self_play", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_synthetic_lens_contract_matrix_does_not_claim_llm_self_play(tmp_path):
    result = _module().validate(100, tmp_path)
    assert result["passed"]
    assert result["case_count"] == 100
    assert set(result["category_counts"].values()) == {10}
    assert result["schema_version"] == "nollm_lab_synthetic_lens_contract_conformance_v2"
    assert result["schema_valid_count"] == 100
    assert result["exact_basis_valid_count"] == 100
    assert result["atlas_path_valid_count"] == 100
    assert result["relation_group_compiled_count"] == 90
    assert result["durable_applied_count"] == 90
    assert result["honest_unresolved_defer_count"] == 10
    assert result["duplicate_statement_count"] == 0
    assert result["provider_case_count"] == 0
    assert not result["persistent_lens_text_found"]
