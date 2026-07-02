from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path

import pytest

from nollm.dream_geometry.assembly import assemble_field_snapshot, recall_universe_from_snapshot
from nollm.dream_geometry.assembly.builder import _bind_recall_cover_cells
from nollm.dream_geometry.assembly.errors import DF1_UNIVERSE_CONSTRUCTION_FAILED, DF1AssemblyError
from nollm.dream_geometry.cortex import compile_query
from nollm.dream_geometry.geometry.types import CellRef, HexCell
from nollm.dream_geometry.recall import RecallDigestStatus, RecallPolicy, resolve_recall
from tests.fixtures.df1_assembly.fixture import build_df1_environment, finite_set, tree_manifest


def test_rc1_01_single_admission_df1_universe_executes_dr1_without_writes(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    before = _state_manifest(tmp_path)

    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))
    digest = resolve_recall(_kunming_rain_probe(), result.universe, evidence, policy=_policy())

    assert digest.status is RecallDigestStatus.resolved
    assert tuple(item.shard_id for item in digest.items) == ("shard:df1:alpha",)
    assert digest.traversal_records
    assert {record.phase for record in digest.traversal_records} >= {"up", "down"}
    assert _state_manifest(tmp_path) == before


def test_rc1_02_snapshot_local_cover_and_universe_executable_cover_are_separate_views(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))

    snapshot_cover = result.snapshot.coarse_covers[0]
    universe_cover = result.universe.covers[0]

    assert isinstance(snapshot_cover.support_cell, CellRef)
    assert isinstance(universe_cover.support_cell, HexCell)
    assert universe_cover.support_cell.cell_ref == snapshot_cover.support_cell
    assert universe_cover.support_cell.chart_fingerprint == snapshot_cover.chart_fingerprint
    assert result.universe.gravity_snapshot is not None
    assert result.universe.gravity_snapshot.snapshot_id == result.snapshot.gravity_snapshot.snapshot_id
    assert result.universe.gravity_snapshot.input_cover_ids == result.snapshot.gravity_snapshot.input_cover_ids
    assert result.universe.gravity_snapshot.chart_fingerprint == result.snapshot.gravity_snapshot.chart_fingerprint
    assert _cover_fields_without_support_cell(universe_cover) == _cover_fields_without_support_cell(snapshot_cover)


def test_rc1_03_multi_admission_input_order_is_deterministic_for_df1_and_dr1(tmp_path) -> None:
    specs = (
        ("adm_df1_alpha", "shard:df1:alpha", "gp_df1_alpha", "Kunming rain alpha."),
        ("adm_df1_beta", "shard:df1:beta", "gp_df1_beta", "Kunming rain beta."),
        ("adm_df1_gamma", "shard:df1:gamma", "gp_df1_gamma", "Kunming rain gamma."),
    )
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path, specs)

    first = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha", "adm_df1_beta", "adm_df1_gamma")))
    second = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_gamma", "adm_df1_alpha", "adm_df1_beta")))
    first_digest = resolve_recall(_kunming_rain_probe(), first.universe, evidence, policy=_policy())
    second_digest = resolve_recall(_kunming_rain_probe(), second.universe, evidence, policy=_policy())

    assert second.snapshot.snapshot_id == first.snapshot.snapshot_id
    assert second.snapshot.source_admission_ids == first.snapshot.source_admission_ids
    assert tuple(cover.cover_id for cover in second.snapshot.coarse_covers) == tuple(cover.cover_id for cover in first.snapshot.coarse_covers)
    assert second.snapshot.gravity_snapshot.snapshot_id == first.snapshot.gravity_snapshot.snapshot_id
    assert second.universe.universe_id == first.universe.universe_id
    assert _cover_identity(second.universe.covers) == _cover_identity(first.universe.covers)
    assert _digest_identity(second_digest) == _digest_identity(first_digest)


def test_rc1_04_public_reconstruction_path_returns_executable_universe(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))
    reconstructed = recall_universe_from_snapshot(result.snapshot, result.universe.proposal_records)
    digest = resolve_recall(_kunming_rain_probe(), reconstructed, evidence, policy=_policy())

    assert tuple(type(cover.support_cell) for cover in reconstructed.covers) == (HexCell,)
    assert _cover_identity(reconstructed.covers) == _cover_identity(result.universe.covers)
    assert digest.status is RecallDigestStatus.resolved
    assert tuple(item.shard_id for item in digest.items) == ("shard:df1:alpha",)


def test_rc1_05_cover_binding_inconsistency_fails_closed_without_writes(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))
    before = _state_manifest(tmp_path)
    raw_cover = result.snapshot.coarse_covers[0]
    incomplete_traces = tuple(trace for trace in result.universe.traces if trace.trace_id not in raw_cover.support_trace_ids)

    with pytest.raises(DF1AssemblyError) as error:
        _bind_recall_cover_cells((raw_cover,), incomplete_traces)

    assert error.value.reason_code == DF1_UNIVERSE_CONSTRUCTION_FAILED
    assert "cover_cell_binding_failed:" + raw_cover.cover_id == error.value.detail
    assert _state_manifest(tmp_path) == before


def _kunming_rain_probe():
    return compile_query(
        {
            "contract_version": "dc1.v1",
            "probe_id": "probe_rc1_kunming_rain",
            "query_text": "Kunming rain",
            "reference_instant": "2026-07-02T10:00:00+08:00",
            "requires_runtime_resolution": False,
            "ephemeral": True,
            "budget": {"max_axes": 4, "max_charts": 8, "max_layers": 4, "max_cells_per_layer": 32},
            "do_not_infer": ["rc1 synthetic fixture only"],
            "forbidden_inferences": ["no semantic fallback"],
            "axes": [
                {
                    "axis_id": "location",
                    "ray": [
                        {
                            "step_id": "step_q_location",
                            "expression": "Kunming",
                            "basis": "explicit_in_query",
                            "basis_refs": [{"ref_type": "text_span", "record_id": "probe_rc1_kunming_rain", "start_char": 0, "end_char": 7, "quoted_text": "Kunming"}],
                            "rationale": None,
                        }
                    ],
                },
                {
                    "axis_id": "phenomenon",
                    "ray": [
                        {
                            "step_id": "step_q_phenomenon",
                            "expression": "rain",
                            "basis": "explicit_in_query",
                            "basis_refs": [{"ref_type": "text_span", "record_id": "probe_rc1_kunming_rain", "start_char": 8, "end_char": 12, "quoted_text": "rain"}],
                            "rationale": None,
                        }
                    ],
                },
            ],
        }
    )


def _policy() -> RecallPolicy:
    return RecallPolicy(min_required_axis_matches=2, max_lateral_hops=2)


def _state_manifest(root: Path) -> dict[str, tuple[tuple[str, str], ...]]:
    return {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission")}


def _cover_fields_without_support_cell(cover) -> dict[str, object]:
    return {field.name: getattr(cover, field.name) for field in fields(cover) if field.name != "support_cell"}


def _cover_identity(covers) -> tuple[tuple[str, str, str], ...]:
    return tuple((cover.cover_id, cover.support_cell.cell_ref.chart_id, f"{cover.support_cell.cell_ref.axial.q}:{cover.support_cell.cell_ref.axial.r}") for cover in covers)


def _digest_identity(digest) -> tuple[object, ...]:
    return (
        digest.status,
        tuple(item.shard_id for item in digest.items),
        tuple((record.phase, record.cover_id, record.source_cell_ref, record.target_cell_ref, record.reason_code) for record in digest.traversal_records),
        digest.warnings,
        digest.discarded,
    )
