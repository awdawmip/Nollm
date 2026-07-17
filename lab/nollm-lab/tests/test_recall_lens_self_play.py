from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/recall_lens/run_deterministic_self_play.py"


def _module():
    spec = importlib.util.spec_from_file_location("recall_lens_self_play", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_writer_reader_critic_matrix_has_100_real_handle_cycles(tmp_path):
    result = _module().validate(100, tmp_path)
    assert result["passed"]
    assert result["case_count"] == 100
    assert set(result["category_counts"].values()) == {10}
    assert result["statement_formation_rate"] == 1.0
    assert result["value_filter_error_rate"] == 0.0
    assert result["primary_lens_reach_rate"] == 1.0
    assert result["secondary_lens_reach_rate"] == 1.0
    assert result["single_entry_path_rate"] == 1.0
    assert result["duplicate_statement_count"] == 0
    assert result["orphan_statement_count"] == 0
    assert result["provider_case_count"] == 0
