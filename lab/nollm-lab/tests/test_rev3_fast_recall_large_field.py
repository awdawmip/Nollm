from __future__ import annotations

import pytest

from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom
from nollm_openclaw_formation.memory_loop import build_fast_recall_prompt


@pytest.mark.parametrize("count,target_q", [(40, 39), (300, 299), (1027, 1026)])
def test_fast_recall_uses_complete_progressive_atlas_not_stable_prefix(tmp_path, count, target_q):
    with CoreRuntime(tmp_path) as core:
        for q in range(count):
            core.put(MemoryAtom(f"atom-{q}", str(q)), GeometryAddress("default_dream_v1", "default", 0, q, 0))
    built = build_fast_recall_prompt(f"Find target {target_q}", str(tmp_path), f"large-{count}")

    assert built["status"] == "entry_decision"
    assert built["hidden_call_count"] == 1
    assert built["prompt_utf8_bytes"] <= 65536
    assert built["atlas_page"]["coverage_certificate"]["occupied_field_cell_count"] == count
    assert built["atlas_page"]["coverage_certificate"]["uncovered_source_cell_count"] == 0
    assert len(built["atlas_page"]["regions"]) <= 32
    assert any(entry["entry_cell"]["q"] == target_q for entry in built["entries"])
