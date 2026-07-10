from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf4_host_validation import run_multi_host_conformance
from nollm.grf.cell_address import CellAddress
from nollm.grf.field_engine import FieldEngine
from nollm.grf.kernel_registry import KernelRegistry
from nollm.grf.placement import GeometryMark, PlacementRecord
from nollm.grf.production_validation import run_production_like_benchmark


def _placement(shard_id: str, q: int) -> PlacementRecord:
    cell = CellAddress("eisenstein_exact_v1", "chart:grf4", 0, q, 0)
    mark = GeometryMark(f"mark:{shard_id}", shard_id, "eisenstein_exact_v1", "chart:grf4", cell, "test", "high", 0, "field:grf4")
    return PlacementRecord(f"placement:{shard_id}", shard_id, f"candidate:{shard_id}", f"decision:{shard_id}", mark, f"island:{shard_id}", f"patch:{shard_id}", (f"window:{shard_id}",), "eisenstein_exact_v1", "grf4")


def test_kernel_relation_and_field_caches_are_stable_and_invalidate_on_update() -> None:
    registry = KernelRegistry()
    registry.compile_profiles(("eisenstein_exact_v1",))
    assert registry.coverage_templates() is registry.coverage_templates()
    engine = FieldEngine(registry)
    engine.insert(_placement("shard:cache:a", 0))
    first = engine.build_relation_field()
    assert engine.build_relation_field() is first
    assert first.shards_at(first.placements[0].geometry_mark.cell) == first.shards_at(first.placements[0].geometry_mark.cell)
    engine.insert(_placement("shard:cache:b", 1))
    assert engine.build_relation_field() is not first


def test_declared_openclaw_and_codex_hosts_match_file_adapter(tmp_path: Path) -> None:
    result = run_multi_host_conformance(tmp_path)
    assert result["hosts"] == ("codex", "file", "openclaw_v2")
    assert result["same_core_result"] is True
    assert result["same_source_fallback"] is True


def test_production_like_runner_executes_mixed_profiles_incremental_updates_and_recovery() -> None:
    metrics = run_production_like_benchmark(1000)
    assert metrics.evidence_count == 1000
    assert metrics.placement_count == 1000
    assert metrics.profile_ids == ("eisenstein_exact_v1", "dream_quasi_v1", "aligned_baseline_v1")
    assert metrics.source_fallback_preserved is True
    assert metrics.incremental_update_preserved is True
    assert metrics.failure_recovery["density_overload"]["migration_candidate"] is True
