from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.adapters import IntegrationShell
from nollm.dream_geometry.validation.dx1_synthetic_cycle_fixture import build_dx1_cycle, canonical_mapping, tree_manifest


def test_x013_s06_same_input_reopen_and_zero_persistence(tmp_path) -> None:
    fixture = build_dx1_cycle(tmp_path)
    shell = IntegrationShell()
    first = shell.handle(fixture.invocation, fixture.integration_context).to_mapping()
    second = shell.handle(replace(fixture.invocation, request_id=fixture.invocation.request_id), fixture.integration_context).to_mapping()
    assert canonical_mapping(first) == canonical_mapping(second)
    assert tree_manifest(tmp_path / "evidence") == fixture.before_recall_manifests["evidence"]
    assert tree_manifest(tmp_path / "cortex") == fixture.before_recall_manifests["cortex"]

    reopened = build_dx1_cycle(tmp_path)
    reopened_response = shell.handle(reopened.invocation, reopened.integration_context).to_mapping()
    assert canonical_mapping(first) == canonical_mapping(reopened_response)


def test_x014_s07_input_permutation_keeps_public_mapping(tmp_path) -> None:
    baseline = build_dx1_cycle(tmp_path / "baseline")
    permuted = build_dx1_cycle(tmp_path / "permuted", permuted=True)
    shell = IntegrationShell()
    first = shell.handle(baseline.invocation, baseline.integration_context).to_mapping()
    second = shell.handle(permuted.invocation, permuted.integration_context).to_mapping()
    assert canonical_mapping(first) == canonical_mapping(second)
    assert first["result"]["primary_evidence"][0]["shard_id"] == second["result"]["primary_evidence"][0]["shard_id"]
    assert first["result"]["primary_evidence"][0]["matched_axis_ids"] == second["result"]["primary_evidence"][0]["matched_axis_ids"]
