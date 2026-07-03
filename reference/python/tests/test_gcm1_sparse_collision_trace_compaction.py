from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[3]

from tests.fixtures.gcm1.fixture import (
    BASELINE_COMMIT,
    SCENARIO_IDS,
    all_finite_scenarios,
    build_collision_witness,
    build_trace_scenarios,
    canonical_compaction_payload,
    evaluate_scenario,
    expand_scenario_compaction,
    scenario_payload,
    state_dirs,
    traces_equal,
    witness_payload,
)


def test_gcm1_01_witness_is_real_gsc1_local_fork_collision() -> None:
    witness = build_collision_witness()
    payload = witness_payload(witness)

    assert witness.pattern_id == "local_fork"
    assert witness.supporting_marker_ids in (("f0", "f1"), ("f0", "f2"), ("f1", "f2"), ("f0", "f1", "f2"))
    assert len(set(witness.supporting_marker_ids)) >= 2
    assert witness.hex_cell.cell_ref.chart_id == witness.target_ref[0]
    assert witness.hex_cell.cell_ref.axial.q == witness.target_ref[1]
    assert witness.hex_cell.cell_ref.axial.r == witness.target_ref[2]
    assert witness.hex_cell.chart_fingerprint is not None
    assert payload["hex_cell_ref"] == f"{witness.target_ref[0]}:{witness.target_ref[1]}:{witness.target_ref[2]}"
    assert json.dumps(payload, sort_keys=True)


def test_gcm1_02_shared_support_does_not_compact_distinct_origin_shards() -> None:
    scenario = _scenario("shared_support_distinct_shards")
    traces = scenario.input_traces

    assert traces[0].cell.cell_ref == traces[1].cell.cell_ref
    assert traces[0].support_key == traces[1].support_key
    assert traces[0].origin_shard_id != traces[1].origin_shard_id
    assert evaluate_scenario(scenario) == ()
    assert scenario_payload(scenario)["actual_uncompacted_trace_ids"] == scenario.expected_uncompacted_trace_ids


def test_gcm1_03_proposal_and_derivation_differences_do_not_compact() -> None:
    proposal = _scenario("shared_support_distinct_proposals")
    revision_proxy = _scenario("shared_support_distinct_revision_proxy")

    assert proposal.input_traces[0].proposal_id != proposal.input_traces[1].proposal_id
    assert evaluate_scenario(proposal) == ()
    assert revision_proxy.input_traces[0].parent_trace_id != revision_proxy.input_traces[1].parent_trace_id
    assert revision_proxy.input_traces[0].basis_refs != revision_proxy.input_traces[1].basis_refs
    assert evaluate_scenario(revision_proxy) == ()


def test_gcm1_04_exact_duplicate_transport_view_compacts_and_expands_losslessly() -> None:
    scenario = _scenario("exact_duplicate_transport_view")
    compactions = evaluate_scenario(scenario)

    assert len(compactions) == 1
    compaction = compactions[0]
    assert compaction.member_trace_ids == scenario.expected_compaction_member_ids == ("d0", "d1")
    assert compaction.expansion_manifest == compaction.member_trace_ids
    assert compaction.aggregate_mass == sum(trace.mass for trace in scenario.input_traces)
    expanded = expand_scenario_compaction(scenario, compaction)
    assert tuple(trace.trace_id for trace in expanded) == ("d0", "d1")
    trace_index = {trace.trace_id: trace for trace in scenario.input_traces}
    for expanded_trace in expanded:
        assert traces_equal(expanded_trace, trace_index[expanded_trace.trace_id])


def test_gcm1_05_mixed_group_only_compacts_exact_duplicate_group() -> None:
    scenario = _scenario("mixed_group")
    compactions = evaluate_scenario(scenario)

    assert len(compactions) == 1
    assert compactions[0].member_trace_ids == ("d0", "d1")
    assert scenario_payload(scenario)["actual_uncompacted_trace_ids"] == scenario.expected_uncompacted_trace_ids
    forbidden_member_ids = set(scenario.expected_uncompacted_trace_ids)
    assert forbidden_member_ids.isdisjoint(compactions[0].member_trace_ids)
    payload = json.dumps(scenario_payload(scenario), sort_keys=True).lower()
    for forbidden in ('"owner"', "parent_trace_ids", '"primary"', '"current"', '"retired"', '"merge"'):
        assert forbidden not in payload


def test_gcm1_06_order_invariance_and_no_mutation() -> None:
    for scenario in build_trace_scenarios():
        before = tuple(scenario.input_traces)
        first = canonical_compaction_payload(evaluate_scenario(scenario))
        reversed_scenario = type(scenario)(scenario.scenario_id, tuple(reversed(scenario.input_traces)), scenario.expected_compaction_member_ids, scenario.expected_uncompacted_trace_ids)
        second = canonical_compaction_payload(evaluate_scenario(reversed_scenario))
        assert first == second
        assert scenario.input_traces == before
        for compaction in evaluate_scenario(scenario):
            assert not hasattr(compaction, "delete_compacted_members")
            assert not hasattr(compaction, "apply")
            assert not hasattr(compaction, "replace")


def test_gcm1_07_no_persistence_memory_or_runtime_state(tmp_path) -> None:
    before = state_dirs(tmp_path)
    scenarios = build_trace_scenarios()
    _ = tuple(scenario_payload(scenario) for scenario in scenarios)
    after = state_dirs(tmp_path)

    assert before == after == {name: False for name in ("evidence", "capture", "cortex", "admission", "assembly", "recall", "atlas", "state")}
    assert BASELINE_COMMIT == "f850599995e75b0a5c74fa9267202958a6369bdd"
    assert tuple(scenario.scenario_id for scenario in scenarios) == SCENARIO_IDS
    assert all_finite_scenarios(scenarios)
    _assert_no_forbidden_imports(REPO_ROOT / "reference/python/tests/fixtures/gcm1/fixture.py")
    _assert_no_forbidden_imports(REPO_ROOT / "validation/gcm1/run_gcm1_sparse_collision_trace_compaction.py")


def test_gcm1_08_canonical_payload_has_no_recall_or_revision_conclusion() -> None:
    payload = json.dumps(tuple(scenario_payload(scenario) for scenario in build_trace_scenarios()), sort_keys=True).lower()
    for forbidden in ("dreamshard", "fieldsnapshot", "recalluniverse", "recalldigest", "revisionthread", '"current"', '"retired"', '"truth"', '"trust"'):
        assert forbidden not in payload


def _scenario(scenario_id: str):
    return next(scenario for scenario in build_trace_scenarios() if scenario.scenario_id == scenario_id)


def _assert_no_forbidden_imports(path: Path) -> None:
    forbidden = {
        "nollm.dream_geometry.evidence",
        "nollm.dream_geometry.capture",
        "nollm.dream_geometry.cortex",
        "nollm.dream_geometry.admission",
        "nollm.dream_geometry.assembly",
        "nollm.dream_geometry.recall",
        "nollm.dream_geometry.adapters",
        "nollm.dream_geometry.batch_admission",
        "socket",
        "requests",
        "urllib",
        "sqlite3",
    }
    allowed = {
        "nollm.dream_geometry.field.compaction",
        "nollm.dream_geometry.field.types",
        "nollm.dream_geometry.geometry.chart",
        "nollm.dream_geometry.geometry.schedules",
        "nollm.dream_geometry.geometry.types",
        "nollm.dream_geometry.protocol.contracts",
        "tests.fixtures.gsc1.fixture",
    }
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert not (imports & forbidden)
    assert all(not item.startswith("nollm.dream_geometry.field") or item in allowed for item in imports)
