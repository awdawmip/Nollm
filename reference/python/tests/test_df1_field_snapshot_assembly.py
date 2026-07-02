from __future__ import annotations

from dataclasses import replace

import pytest

from nollm.dream_geometry.assembly import AdmissionReplaySource, FieldAssemblyPolicy, FiniteAdmissionSet, assemble_field_snapshot
from nollm.dream_geometry.assembly.errors import (
    DF1_ADMISSION_FINGERPRINT_CONFLICT,
    DF1_DUPLICATE_ADMISSION_ID,
    DF1_FIELD_POLICY_MISMATCH,
    DF1_GEOMETRY_PROFILE_MISMATCH,
    DF1_PROJECTION_FINGERPRINT_MISMATCH,
    DF1_SHARD_NOT_FOUND,
    DF1_UNVERIFIED_CHART_LINK,
    DF1AssemblyError,
)
from nollm.dream_geometry.admission.types import fingerprint
from nollm.dream_geometry.recall import resolve_recall
from tests.fixtures.df1_assembly.fixture import build_df1_environment, finite_projected_set, finite_set, tree_manifest


def test_df1_a001_single_admission_builds_snapshot_and_dr1_universe(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))

    assert result.snapshot.snapshot_id.startswith("sha256:")
    assert result.snapshot.source_admission_ids == ("adm_df1_alpha",)
    assert result.snapshot.admission_manifest[0].shard_id == "shard:df1:alpha"
    assert result.universe.proposal_records[0].proposal.proposal_id == "gp_df1_alpha"
    assert result.audit_summary.validation_status == "pass"


def test_df1_a002_to_a004_permutation_stability_for_multiple_admissions(tmp_path) -> None:
    specs = (
        ("adm_df1_alpha", "shard:df1:alpha", "gp_df1_alpha", "Kunming rain alpha."),
        ("adm_df1_beta", "shard:df1:beta", "gp_df1_beta", "Kunming rain beta."),
        ("adm_df1_gamma", "shard:df1:gamma", "gp_df1_gamma", "Kunming rain gamma."),
    )
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path, specs)
    first = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha", "adm_df1_beta", "adm_df1_gamma")))
    second = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_gamma", "adm_df1_alpha", "adm_df1_beta")))

    assert second.snapshot.snapshot_id == first.snapshot.snapshot_id
    assert second.snapshot.admission_manifest == first.snapshot.admission_manifest
    assert tuple(cover.cover_id for cover in second.snapshot.coarse_covers) == tuple(cover.cover_id for cover in first.snapshot.coarse_covers)
    assert second.snapshot.gravity_snapshot.snapshot_id == first.snapshot.gravity_snapshot.snapshot_id


def test_df1_a005_e002_e003_assembly_is_zero_write(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    before = {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")}
    assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))
    assert {name: tree_manifest(tmp_path / name) for name in ("evidence", "cortex", "admission")} == before
    assert not tree_manifest(tmp_path / "snapshot")
    assert not tree_manifest(tmp_path / "cache")


def test_df1_b001_b002_duplicate_admission_identity_fail_closed(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    record = admission.get_admission_record("adm_df1_alpha")
    source = AdmissionReplaySource(record, evidence, cortex, orchestrator.replay_record)
    duplicate = FiniteAdmissionSet("df1_duplicate", (source, source))
    with pytest.raises(DF1AssemblyError) as duplicate_error:
        assemble_field_snapshot(duplicate)
    assert duplicate_error.value.reason_code == DF1_DUPLICATE_ADMISSION_ID

    conflict_record = replace(record, projection_fingerprint="sha256:" + "0" * 64)
    conflict = FiniteAdmissionSet("df1_conflict", (source, AdmissionReplaySource(conflict_record, evidence, cortex, orchestrator.replay_record)))
    with pytest.raises(DF1AssemblyError) as conflict_error:
        assemble_field_snapshot(conflict)
    assert conflict_error.value.reason_code == DF1_ADMISSION_FINGERPRINT_CONFLICT


def test_df1_b003_b004_projection_tamper_rejects_without_partial_snapshot(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    record = replace(admission.get_admission_record("adm_df1_alpha"), projection_fingerprint="sha256:" + "1" * 64)
    source = AdmissionReplaySource(record, evidence, cortex, orchestrator.replay_record)
    with pytest.raises(DF1AssemblyError) as error:
        assemble_field_snapshot(FiniteAdmissionSet("df1_tamper", (source,)))
    assert error.value.reason_code == DF1_PROJECTION_FINGERPRINT_MISMATCH


def test_df1_b005_missing_shard_rejects(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    record = replace(admission.get_admission_record("adm_df1_alpha"), subject_shard_id="shard:df1:missing")
    source = AdmissionReplaySource(record, evidence, cortex, orchestrator.replay_record)
    with pytest.raises(DF1AssemblyError) as error:
        assemble_field_snapshot(FiniteAdmissionSet("df1_missing_shard", (source,)))
    assert error.value.reason_code == DF1_SHARD_NOT_FOUND


def test_df1_c001_c002_profile_and_policy_mismatch_reject(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    with pytest.raises(DF1AssemblyError) as geometry_error:
        assemble_field_snapshot(replace(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)), geometry_profile_id="other"))
    assert geometry_error.value.reason_code == DF1_GEOMETRY_PROFILE_MISMATCH

    with pytest.raises(DF1AssemblyError) as policy_error:
        assemble_field_snapshot(replace(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)), field_policy_identity="dg2_cover_policy:other"))
    assert policy_error.value.reason_code == DF1_FIELD_POLICY_MISMATCH


def test_df1_c003_c005_verified_cross_chart_link_is_canonical(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(
        tmp_path,
        (("adm_df1_alpha", "shard:df1:alpha", "gp_df1_alpha", "Kunming rain alpha."),),
    )
    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))
    assert result.snapshot.verified_chart_links == ()

    cross_root = tmp_path / "cross"
    from tests.fixtures.df1_assembly.fixture import build_request

    ev, cx, adm = build_df1_environment(cross_root, ())[0:3]
    orch = __import__("nollm.dream_geometry.admission", fromlist=["MemoryAdmissionOrchestrator"]).MemoryAdmissionOrchestrator(ev, cx, adm)
    orch.admit(build_request("adm_df1_cross", "shard:df1:cross", "gp_df1_cross", "Kunming rain cross.", cross_chart=True))
    reopened = __import__("nollm.dream_geometry.admission", fromlist=["open_store"]).open_store(cross_root / "admission", ev, cx, orch.validate_replay_record)
    replay = __import__("nollm.dream_geometry.admission", fromlist=["MemoryAdmissionOrchestrator"]).MemoryAdmissionOrchestrator(ev, cx, reopened)
    cross = assemble_field_snapshot(finite_set(ev, cx, reopened, replay, ("adm_df1_cross",)))
    assert len(cross.snapshot.verified_chart_links) == 1
    assert len(cross.universe.verified_chart_links) == 1


def test_df1_c004_unverified_chart_link_manifest_rejects(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    record = admission.get_admission_record("adm_df1_alpha")
    payload = dict(record.placement_plan_payload)
    axes = [dict(item) for item in payload["axis_placements"]]
    axes[0]["verified_chart_link"] = {"verified": False}
    payload["axis_placements"] = tuple(axes)
    bad = replace(record, placement_plan_payload=payload, placement_plan_fingerprint=fingerprint(payload))
    source = AdmissionReplaySource(bad, evidence, cortex, orchestrator.replay_record)
    with pytest.raises(DF1AssemblyError) as error:
        assemble_field_snapshot(FiniteAdmissionSet("df1_bad_link", (source,)))
    assert error.value.reason_code == DF1_UNVERIFIED_CHART_LINK


def test_df1_e001_explicit_inputs_do_not_need_discovery(monkeypatch, tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    explicit = finite_projected_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",))

    def fail(*_args, **_kwargs):
        raise AssertionError("implicit discovery forbidden")

    monkeypatch.setattr("pathlib.Path.glob", fail)
    monkeypatch.setattr("pathlib.Path.rglob", fail)
    monkeypatch.setattr("pathlib.Path.iterdir", fail)
    result = assemble_field_snapshot(explicit)
    assert result.snapshot.source_admission_ids == ("adm_df1_alpha",)


def test_df1_f001_f002_universe_validates_without_resolve(monkeypatch, tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)

    def fail_resolve(*_args, **_kwargs):
        raise AssertionError("DF1 must not execute recall")

    monkeypatch.setattr("nollm.dream_geometry.recall.resolve_recall", fail_resolve)
    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))
    assert result.universe.traces
    assert resolve_recall is not fail_resolve


def test_df1_policy_rejects_mutable_output_mode(tmp_path) -> None:
    evidence, cortex, admission, orchestrator = build_df1_environment(tmp_path)
    with pytest.raises(DF1AssemblyError):
        assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)), FieldAssemblyPolicy(output_mode="persist"))
