from dataclasses import replace

import pytest

from nollm.dream_geometry.cortex.types import CompilationReceipt, QueryBudget
from nollm.dream_geometry.field.types import CoarseCover, CoverPolicy
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2
from nollm.dream_geometry.protocol.contracts import CoverState, UsageState
from nollm.dream_geometry.recall import RecallDigestStatus, RecallPolicy, ResolvedRelativeSpan, RuntimeTimeResolution, resolve_recall, validate_recall_universe
from nollm.dream_geometry.recall.types import RecallValidationError

from fixtures.dr1_recall.fixture import build_fixture, query_probe, relative_time_resolution, with_legacy_proposal_only, with_wrong_down_direction


def test_t_dr1_101_wrong_k_down_direction_rejected(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), with_wrong_down_direction(universe), store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.rejected
    assert "DR1_COVERAGE_DOWN_DIRECTION_MISMATCH" in digest.warnings
    assert digest.primary_evidence == ()


def test_t_dr1_102_removed_k_down_changes_outcome(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), replace(universe, coverage_down=()), store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.insufficient_evidence
    assert digest.primary_evidence == ()
    assert "DR1_K_DOWN_REQUIRED" in digest.discarded


def test_t_dr1_103_executed_residual_only_and_mass_accounting(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    extra_source = make_hex_cell(LocalChart("unused", 0, 1.0, 0.0, Vec2(20, 0)), AxialCoord(0, 0))
    extra_target = make_hex_cell(LocalChart("unused:fine", 1, 0.5, 0.0, Vec2(20, 0)), AxialCoord(0, 0))
    extra = compute_distribution(extra_source, (extra_target,), CoverageDirection.coarse_to_fine)
    normal = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    with_extra = resolve_recall(query_probe(), replace(universe, coverage_down=universe.coverage_down + (extra,)), store, runtime_time=relative_time_resolution())
    assert with_extra.unresolved_residual_mass == normal.unresolved_residual_mass
    for record in with_extra.traversal_records:
        if record.phase == "up":
            assert abs((record.mass_out + record.residual_mass) - record.mass_in) <= 1e-9


def test_t_dr1_104_budget_exhaustion_is_explicit(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    probe = replace(query_probe(), budget=QueryBudget(4, 8, 4, 1))
    digest = resolve_recall(probe, universe, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=1))
    assert digest.status is RecallDigestStatus.budget_exhausted
    assert "DR1_BUDGET_MAX_CELLS_PER_LAYER" in digest.discarded


def test_t_dr1_105_106_107_relative_time_strict_binding(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    fabricated = RuntimeTimeResolution((ResolvedRelativeSpan("not_relative_time", "not_in_query", "absolute_time", "2026-06-29", "2026-06-30T08:00:00+08:00", "caller", "bad", 0, 3, "bad"),), True)
    assert resolve_recall(query_probe(), universe, store, runtime_time=fabricated).status is RecallDigestStatus.rejected
    assert resolve_recall(query_probe(relative_time=False), universe, store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected
    duplicate = RuntimeTimeResolution(relative_time_resolution().spans * 2, True)
    assert resolve_recall(query_probe(), universe, store, runtime_time=duplicate).status is RecallDigestStatus.rejected
    partial = RuntimeTimeResolution((), False)
    deferred = resolve_recall(query_probe(), universe, store, runtime_time=partial)
    assert deferred.status is RecallDigestStatus.deferred


def test_t_dr1_108_duplicate_and_bad_receipt_rejected(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    with pytest.raises(RecallValidationError, match="DR1_DUPLICATE_PROPOSAL_ID"):
        validate_recall_universe(replace(universe, proposal_records=universe.proposal_records * 2), store)
    record = universe.proposal_records[0]
    bad_receipt = replace(record.receipt, normalized_payload_fingerprint="sha256:bad")
    bad = replace(universe, proposal_records=(replace(record, receipt=bad_receipt),))
    assert resolve_recall(query_probe(), bad, store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected
    missing = replace(universe, proposal_records=(replace(record, receipt=None),))
    assert resolve_recall(query_probe(), missing, store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected


def test_t_dr1_109_cover_policy_and_support_inconsistency_rejected(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    assert resolve_recall(query_probe(), replace(universe, cover_policy_records=()), store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected
    bad_cover = replace(universe.covers[0], support_keys=("support:absolute_time", "support:location", "support:wrong"))
    assert resolve_recall(query_probe(), replace(universe, covers=(bad_cover,)), store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected


def test_t_dr1_111_gravity_only_breaks_true_ties(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    base = universe.covers[0]
    low = replace(base, cover_id="cover:low")
    high = replace(base, cover_id="cover:high", mass=base.mass + 0.01)
    non_tie = resolve_recall(query_probe(), replace(universe, covers=(low, high)), store, runtime_time=relative_time_resolution())
    assert [item.cover_id for item in non_tie.primary_evidence][:2] == ["cover:high", "cover:low"]
    tie_a = replace(base, cover_id="cover:a")
    tie_b = replace(base, cover_id="cover:b")
    gravity = replace(universe.gravity_snapshot, contributions=(replace(universe.gravity_snapshot.contributions[0], cover_id="cover:b", potential=1000.0),))
    tied = resolve_recall(query_probe(), replace(universe, covers=(tie_a, tie_b), gravity_snapshot=gravity), store, runtime_time=relative_time_resolution())
    assert [item.cover_id for item in tied.primary_evidence][:2] == ["cover:b", "cover:a"]
    assert tied.gravity_guidance_applied is True


def test_t_dr1_112_primary_context_evidence_partition(tmp_path) -> None:
    tentative_store, _, tentative_universe = build_fixture(tmp_path / "tentative", usage_state=UsageState.tentative)
    tentative = resolve_recall(query_probe(), tentative_universe, tentative_store, runtime_time=relative_time_resolution())
    assert tentative.primary_evidence[0].qualification.tier == "primary_tentative"
    closed = resolve_recall(query_probe(), tentative_universe, tentative_store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_tentative_primary=False))
    assert closed.primary_evidence == ()
    retired_store, _, retired_universe = build_fixture(tmp_path / "retired", usage_state=UsageState.retired)
    retired = resolve_recall(query_probe(), retired_universe, retired_store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_retired_context=True))
    assert retired.contextual_evidence[0].qualification.tier == "context_retired"
    rejected_store, _, rejected_universe = build_fixture(tmp_path / "rejected", usage_state=UsageState.rejected)
    rejected = resolve_recall(query_probe(), rejected_universe, rejected_store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_rejected_context=True))
    assert rejected.contextual_evidence[0].qualification.tier == "context_rejected"


def test_t_dr1_113_missing_shard_no_ghost_evidence(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    bad_trace = replace(universe.traces[0], trace_id="trace:missing", origin_shard_id="shard:missing")
    bad_universe = replace(universe, traces=(bad_trace,) + universe.traces[1:], covers=(replace(universe.covers[0], support_trace_ids=(bad_trace.trace_id,) + universe.covers[0].support_trace_ids[1:]),))
    digest = resolve_recall(query_probe(), bad_universe, store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.rejected
    assert digest.primary_evidence == ()


def test_t_dr1_116_current_and_legacy_mixed_legacy_does_not_seed(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    legacy = with_legacy_proposal_only(universe).proposal_records[0]
    legacy = replace(legacy, proposal=replace(legacy.proposal, proposal_id="proposal:legacy"), source_ref="legacy")
    mixed = replace(universe, proposal_records=universe.proposal_records + (legacy,))
    digest = resolve_recall(query_probe(), mixed, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_legacy_context=True))
    assert digest.primary_evidence
    assert all(item.cover_id == "cover:rain" for item in digest.primary_evidence)
    assert "DR1_LEGACY_PROPOSALS_CONTEXT_ONLY" in digest.warnings


def test_t_dr1_115_117_deterministic_and_no_write_api(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    permuted = replace(universe, traces=tuple(reversed(universe.traces)), covers=tuple(reversed(universe.covers)), coverage_up=tuple(reversed(universe.coverage_up)))
    again = resolve_recall(query_probe(), permuted, store, runtime_time=relative_time_resolution())
    assert digest.primary_evidence == again.primary_evidence
    import nollm.dream_geometry.recall as recall

    assert not any(name.startswith(("write", "cache")) for name in dir(recall))
