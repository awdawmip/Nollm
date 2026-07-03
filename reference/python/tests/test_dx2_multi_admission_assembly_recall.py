from __future__ import annotations

import json

import pytest

from nollm.dream_geometry.adapters import IntegrationReadContext, IntegrationShell
from nollm.dream_geometry.admission import AdmissionOutcome
from nollm.dream_geometry.assembly import FiniteAdmissionSet, assemble_field_snapshot
from nollm.dream_geometry.assembly.errors import DF1_EMPTY_ADMISSION_SET, DF1AssemblyError
from nollm.dream_geometry.batch_admission import BatchWindowStatus
from nollm.dream_geometry.capture import CaptureStatus, CandidateStatus, VisibilityScope
from nollm.dream_geometry.geometry.types import CellRef, HexCell
from nollm.dream_geometry.recall import RecallDigestStatus, resolve_recall
from tests.fixtures.dx2.fixture import (
    DX2_MISS_MESSAGE,
    admission_sources,
    build_dx2_cycle,
    kunming_rain_probe,
    oslo_snow_probe,
    state_manifest,
)


def test_dx2_01_capture_ba1_da1_commits_a_b_without_mutating_capture_or_admitting_c(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)

    assert tuple(item.member_id for item in cycle.ba1_receipt.member_receipts) == ("bam_dx2_01", "bam_dx2_02")
    assert cycle.ba1_receipt.final_window_status is BatchWindowStatus.closed
    assert all(item.admission_receipt.outcome is AdmissionOutcome.committed for item in cycle.ba1_receipt.member_receipts)
    assert {cycle.receipts[label].status for label in ("a", "b", "c", "d")} == {CaptureStatus.deferred}
    assert {cycle.receipts[label].visibility_scope for label in ("a", "b", "c", "d")} == {VisibilityScope.source_window}

    candidate_ids = {cycle.candidate_ids["a"], cycle.candidate_ids["b"]}
    assert len(candidate_ids) == 2
    assert cycle.capture.state_store.get_candidate(cycle.candidate_ids["a"]).status is CandidateStatus.deferred
    assert cycle.capture.state_store.get_candidate(cycle.candidate_ids["b"]).status is CandidateStatus.deferred

    admission_ids = [item.admission_receipt.admission_id for item in cycle.ba1_receipt.member_receipts]
    proposal_ids = [item.admission_receipt.proposal_id for item in cycle.ba1_receipt.member_receipts]
    projection_fingerprints = [item.admission_receipt.projection_fingerprint for item in cycle.ba1_receipt.member_receipts]
    placement_fingerprints = [cycle.admission.get_admission_record(admission_id).placement_plan_fingerprint for admission_id in admission_ids]
    assert len(set(admission_ids)) == 2
    assert len(set(proposal_ids)) == 2
    assert len(set(projection_fingerprints)) == 2
    assert len(set(placement_fingerprints)) == 2

    with pytest.raises(Exception):
        cycle.admission.get_admission_record("adm_dx2_c")
    assert state_manifest(tmp_path)["capture"] == cycle.state_after_capture["capture"]


def test_dx2_02_each_admission_record_replays_to_its_own_shard_without_batch_record(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)

    replayed = []
    for label, admission_id in zip(("a", "b"), cycle.admission_ids, strict=True):
        record = cycle.admission.get_admission_record(admission_id)
        projection = cycle.orchestrator.replay_record(record)
        replayed.append((record, projection))

        assert record.subject_shard_id == cycle.shards[label].shard_id
        assert projection.proposal.subject_shard_id == cycle.shards[label].shard_id
        assert projection.proposal.proposal_id == record.proposal_id
        assert projection.projection_fingerprint == record.projection_fingerprint
        assert {trace.origin_shard_id for trace in projection.source_traces + projection.derived_traces} == {cycle.shards[label].shard_id}
        assert {placement["axis_id"] for placement in record.placement_plan_payload["axis_placements"]} == {"location", "phenomenon"}
        assert all(placement["verified_chart_link"] is None for placement in record.placement_plan_payload["axis_placements"])

    assert {record.subject_shard_id for record, _projection in replayed} == {cycle.shards["a"].shard_id, cycle.shards["b"].shard_id}
    assert all("batch" not in record.record_type for record, _projection in replayed)


def test_dx2_03_df1_explicit_ba1_receipt_set_is_deterministic_read_only_and_excludes_c_d(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)
    a_b = {cycle.shards["a"].shard_id, cycle.shards["b"].shard_id}
    c_d = {cycle.shards["c"].shard_id, cycle.shards["d"].shard_id}

    assert set(cycle.assembly.snapshot.source_admission_ids) == set(cycle.admission_ids)
    assert set(entry.shard_id for entry in cycle.assembly.snapshot.admission_manifest) == a_b
    assert cycle.reversed_assembly.snapshot.snapshot_id == cycle.assembly.snapshot.snapshot_id
    assert cycle.reversed_assembly.snapshot.source_admission_ids == cycle.assembly.snapshot.source_admission_ids
    assert cycle.reversed_assembly.universe.universe_id == cycle.assembly.universe.universe_id
    assert tuple(cover.cover_id for cover in cycle.reversed_assembly.universe.covers) == tuple(cover.cover_id for cover in cycle.assembly.universe.covers)

    assert cycle.assembly.snapshot.coarse_covers
    assert cycle.assembly.universe.covers
    assert all(isinstance(cover.support_cell, CellRef) for cover in cycle.assembly.snapshot.coarse_covers)
    assert all(isinstance(cover.support_cell, HexCell) for cover in cycle.assembly.universe.covers)
    assert cycle.assembly.snapshot.verified_chart_links == ()

    assert c_d.isdisjoint(entry.shard_id for entry in cycle.assembly.snapshot.admission_manifest)
    assert c_d.isdisjoint(record.proposal.subject_shard_id for record in cycle.assembly.universe.proposal_records)
    assert c_d.isdisjoint(trace.origin_shard_id for trace in cycle.assembly.universe.traces)
    assert c_d.isdisjoint(_cover_shard_ids(cycle.assembly.universe.covers))
    assert cycle.state_after_assembly == cycle.state_before_assembly
    assert not (tmp_path / "field").exists()
    assert not (tmp_path / "assembly").exists()
    assert not (tmp_path / "recall").exists()


def test_dx2_04_dr1_recall_returns_only_original_a_b_dream_shards_without_writes(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)
    before = state_manifest(tmp_path)

    rerun = resolve_recall(kunming_rain_probe(), cycle.assembly.universe, cycle.evidence, policy=cycle.policy)
    allowed = {cycle.shards["a"].shard_id, cycle.shards["b"].shard_id}
    excluded = {cycle.shards["c"].shard_id, cycle.shards["d"].shard_id}

    assert cycle.recall_digest.status is RecallDigestStatus.resolved
    assert tuple(item.shard_id for item in rerun.items) == tuple(item.shard_id for item in cycle.recall_digest.items)
    assert set(item.shard_id for item in cycle.recall_digest.items).issubset(allowed)
    assert excluded.isdisjoint(item.shard_id for item in cycle.recall_digest.items)
    for item in cycle.recall_digest.items:
        shard = cycle.evidence.get_dream_shard(item.shard_id)
        assert shard.content.startswith("Kunming rain dx2")
        assert "trace" not in shard.content.lower()
        assert "cover" not in shard.content.lower()
    assert state_manifest(tmp_path) == before


def test_dx2_05_di1_public_envelope_is_read_only_and_omits_internal_geometry_details(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)
    before = state_manifest(tmp_path)

    mapping = IntegrationShell().handle(cycle.invocation, cycle.context).to_mapping()
    rendered_without_content = json.dumps(_without_content(mapping), sort_keys=True, ensure_ascii=False).lower()

    assert mapping["ok"] is True
    assert mapping["request_id"] == "req_dx2_kunming_rain"
    evidence = mapping["result"]["primary_evidence"]
    assert evidence
    assert {item["shard_id"] for item in evidence}.issubset({cycle.shards["a"].shard_id, cycle.shards["b"].shard_id})
    assert cycle.shards["c"].shard_id not in json.dumps(mapping, ensure_ascii=False)
    assert cycle.shards["d"].shard_id not in json.dumps(mapping, ensure_ascii=False)
    for forbidden in ("field", "cover_id", "gravity", "chart", "placement", "source_trace", "debug"):
        assert forbidden not in rendered_without_content
    assert state_manifest(tmp_path) == before


def test_dx2_06_captured_but_unadmitted_c_has_precise_miss_semantics(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)
    mapping = IntegrationShell().handle(cycle.invocation.__class__("req_dx2_oslo_snow", "recall", oslo_snow_probe()), cycle.context).to_mapping()

    assert cycle.c_miss_digest.status is RecallDigestStatus.insufficient_evidence
    assert cycle.c_miss_digest.items == ()
    assert mapping["ok"] is True
    assert mapping["result"]["primary_evidence"] == []
    assert cycle.shards["c"].shard_id not in json.dumps(mapping, ensure_ascii=False)
    assert DX2_MISS_MESSAGE == "当前显式 AdmissionRecord / FieldSnapshot 范围内，没有满足条件的正式几何证据。"


def test_dx2_07_admitted_d_is_not_discovered_outside_the_explicit_finite_set(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)
    d_record = cycle.admission.get_admission_record(cycle.d_admission_id)
    assert d_record.subject_shard_id == cycle.shards["d"].shard_id
    assert all(placement["verified_chart_link"] is not None for placement in d_record.placement_plan_payload["axis_placements"])

    rendered = json.dumps(IntegrationShell().handle(cycle.invocation, cycle.context).to_mapping(), ensure_ascii=False)
    assert cycle.shards["d"].shard_id not in {entry.shard_id for entry in cycle.assembly.snapshot.admission_manifest}
    assert cycle.shards["d"].shard_id not in {record.proposal.subject_shard_id for record in cycle.assembly.universe.proposal_records}
    assert cycle.shards["d"].shard_id not in {item.shard_id for item in cycle.recall_digest.items}
    assert cycle.shards["d"].shard_id not in rendered


def test_dx2_08_missing_record_and_bad_df1_input_fail_without_snapshot_or_writes(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)
    before = state_manifest(tmp_path)

    with pytest.raises(Exception):
        cycle.admission.get_admission_record("adm_dx2_missing_from_receipt")
    with pytest.raises(DF1AssemblyError) as error:
        assemble_field_snapshot(FiniteAdmissionSet("dx2_empty_explicit_set", ()))

    assert error.value.reason_code == DF1_EMPTY_ADMISSION_SET
    assert cycle.shards["c"].shard_id not in {entry.shard_id for entry in cycle.assembly.snapshot.admission_manifest}
    assert cycle.shards["d"].shard_id not in {entry.shard_id for entry in cycle.assembly.snapshot.admission_manifest}
    assert state_manifest(tmp_path) == before


def test_dx2_09_incomplete_di1_context_returns_public_error_without_writes(tmp_path) -> None:
    cycle = build_dx2_cycle(tmp_path)
    before = state_manifest(tmp_path)
    bad_context = IntegrationReadContext("not-store", cycle.assembly.universe, None, cycle.policy)

    mapping = IntegrationShell().handle(cycle.invocation, bad_context).to_mapping()

    assert mapping["ok"] is False
    assert mapping["error"]["code"] == "DI1_INVALID_READ_CONTEXT"
    assert state_manifest(tmp_path) == before


def _cover_shard_ids(covers) -> set[str]:
    shard_ids: set[str] = set()
    for cover in covers:
        for trace_id in cover.support_trace_ids:
            if ":shard:" in trace_id:
                shard_ids.add(trace_id.split(":shard:", 1)[1])
    return shard_ids


def _without_content(value):
    if isinstance(value, dict):
        return {key: _without_content(item) for key, item in value.items() if key != "content"}
    if isinstance(value, list):
        return [_without_content(item) for item in value]
    return value
