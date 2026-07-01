from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.adapters import IntegrationShell
from nollm.dream_geometry.protocol.contracts import CoverState
from nollm.dream_geometry.recall import RecallDigestStatus, resolve_recall, validate_recall_universe
from nollm.dream_geometry.validation.dx1_synthetic_cycle_fixture import (
    DISTRACTOR_IDS,
    TARGET_SHARD_ID,
    build_dx1_cycle,
    build_dx1_deferred_cycle,
    build_dx1_retired_cycle,
    tree_manifest,
)


def test_x001_to_x007_real_public_api_chain_and_s01_success(tmp_path) -> None:
    fixture = build_dx1_cycle(tmp_path)
    assert fixture.evidence_store.get_dream_shard(TARGET_SHARD_ID).content == "Kunming had rain on 2026-06-29."
    assert fixture.cortex_store.get_growth_proposal(fixture.target_proposal.proposal_id) == fixture.target_proposal
    assert fixture.compiled_query_probe.ephemeral is True
    assert fixture.exact_mismatch_probe.ephemeral is True
    assert fixture.recall_universe.coverage_up and fixture.recall_universe.coverage_down
    assert any(cover.state is CoverState.stable for cover in fixture.recall_universe.covers)
    assert fixture.gravity_snapshot.contributions
    validate_recall_universe(fixture.recall_universe, fixture.evidence_store)
    digest = resolve_recall(
        fixture.compiled_query_probe,
        fixture.recall_universe,
        fixture.evidence_store,
        runtime_time=fixture.runtime_time_resolution,
        policy=fixture.policy,
    )
    assert digest.status is RecallDigestStatus.resolved
    assert digest.traversal_records

    response = IntegrationShell().handle(fixture.invocation, fixture.integration_context).to_mapping()
    assert response["ok"] is True
    assert response["operation"] == "recall"
    result = response["result"]
    assert result["kind"] == "nollm_recall_digest"
    assert result["status"] == "resolved"
    assert result["ephemeral"] is True
    assert [item["shard_id"] for item in result["primary_evidence"]] == [TARGET_SHARD_ID]
    assert all(item["shard_id"] not in DISTRACTOR_IDS for item in result["primary_evidence"])
    target = result["primary_evidence"][0]
    assert target["matched_axis_ids"] == ["absolute_time", "location", "phenomenon"]
    assert target["content"] == "Kunming had rain on 2026-06-29."
    assert target["usage_state"] == "active"
    assert target["selection_basis"] == ["exact_structural_projection", "eligible_stable_cover", "final_multi_axis_evidence_gate"]
    assert target["interpretation_context"][0]["statement"] == "Synthetic weather-observation classification."
    assert target["interpretation_context"][0]["tier"] == "contextual"
    assert target["revision_context"][0]["record_kind"] == "revision_thread"


def test_x009_s02_missing_runtime_resolution_defers_without_evidence(tmp_path) -> None:
    fixture = build_dx1_deferred_cycle(tmp_path)
    response = IntegrationShell().handle(fixture.invocation, fixture.integration_context).to_mapping()
    assert response["ok"] is True
    assert response["result"]["status"] == "deferred"
    assert response["result"]["primary_evidence"] == []
    assert response["result"]["contextual_evidence"] == []
    assert "runtime_time_resolution_required" in response["result"]["warnings"]


def test_x010_s03_exact_mismatch_does_not_recall_rain(tmp_path) -> None:
    fixture = build_dx1_cycle(tmp_path)
    response = IntegrationShell().handle(fixture.mismatch_invocation, fixture.integration_context).to_mapping()
    assert response["ok"] is True
    assert response["result"]["status"] in {"insufficient_evidence", "budget_exhausted"}
    assert all(item["shard_id"] != TARGET_SHARD_ID for item in response["result"]["primary_evidence"])
    assert all("rain" not in item["content"].lower() for item in response["result"]["primary_evidence"])


def test_x011_s04_retired_usage_is_context_not_active_primary(tmp_path) -> None:
    fixture = build_dx1_retired_cycle(tmp_path)
    response = IntegrationShell().handle(fixture.invocation, fixture.integration_context).to_mapping()
    assert response["ok"] is True
    assert fixture.evidence_store.get_dream_shard(TARGET_SHARD_ID).content == "Kunming had rain on 2026-06-29."
    assert response["result"]["primary_evidence"] == []
    contextual_ids = [item["shard_id"] for item in response["result"]["contextual_evidence"]]
    assert TARGET_SHARD_ID in contextual_ids
    retired = next(item for item in response["result"]["contextual_evidence"] if item["shard_id"] == TARGET_SHARD_ID)
    assert retired["tier"] == "contextual"
    assert retired["usage_state"] == "retired"


def test_s01_s02_s03_s04_s06_do_not_change_manifests(tmp_path) -> None:
    shell = IntegrationShell()
    scenarios = (
        ("S01", build_dx1_cycle(tmp_path / "s01"), lambda fixture: (fixture.invocation, fixture.integration_context)),
        ("S02", build_dx1_deferred_cycle(tmp_path / "s02"), lambda fixture: (fixture.invocation, fixture.integration_context)),
        ("S03", build_dx1_cycle(tmp_path / "s03"), lambda fixture: (fixture.mismatch_invocation, fixture.integration_context)),
        ("S04", build_dx1_retired_cycle(tmp_path / "s04"), lambda fixture: (fixture.invocation, fixture.integration_context)),
    )
    for scenario, fixture, select_call in scenarios:
        invocation, context = select_call(fixture)
        shell.handle(invocation, context)
        _assert_manifest_unchanged(scenario, fixture)

    fixture = build_dx1_cycle(tmp_path / "s06")
    shell.handle(replace(fixture.invocation, request_id="req_dx1_s06_a"), fixture.integration_context)
    shell.handle(replace(fixture.invocation, request_id="req_dx1_s06_b"), fixture.integration_context)
    _assert_manifest_unchanged("S06", fixture)


def _assert_manifest_unchanged(scenario: str, fixture) -> None:
    assert tree_manifest(fixture.root / "evidence") == fixture.before_recall_manifests["evidence"], scenario + " evidence"
    assert tree_manifest(fixture.root / "cortex") == fixture.before_recall_manifests["cortex"], scenario + " cortex"
