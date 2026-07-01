from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.adapters import IntegrationShell
from nollm.dream_geometry.field.types import cell_ref_key
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
    assert _canonical_distributions(baseline.recall_universe.coverage_up) == _canonical_distributions(permuted.recall_universe.coverage_up)
    assert _canonical_distributions(baseline.recall_universe.coverage_down) == _canonical_distributions(permuted.recall_universe.coverage_down)
    assert baseline.coverage_up_input_orders != permuted.coverage_up_input_orders
    assert baseline.coverage_down_input_orders != permuted.coverage_down_input_orders
    assert baseline.context_input_orders["interpretation_records"] == tuple(reversed(permuted.context_input_orders["interpretation_records"]))
    assert baseline.context_input_orders["revision_threads"] == tuple(reversed(permuted.context_input_orders["revision_threads"]))

    first_primary = first["result"]["primary_evidence"]
    second_primary = second["result"]["primary_evidence"]
    assert len(first_primary) == 1
    assert len(second_primary) == 1
    assert first_primary[0]["shard_id"] == second_primary[0]["shard_id"]
    assert first_primary[0]["matched_axis_ids"] == second_primary[0]["matched_axis_ids"]
    assert first_primary[0]["tier"] == second_primary[0]["tier"]
    assert first_primary[0]["interpretation_context"] == second_primary[0]["interpretation_context"]
    assert first_primary[0]["revision_context"] == second_primary[0]["revision_context"]
    assert _max_positive_kernel_count(baseline.recall_universe.coverage_up) >= 2
    assert _max_positive_kernel_count(baseline.recall_universe.coverage_down) >= 2
    assert first_primary[0]["shard_id"] not in [item["shard_id"] for item in first["result"]["contextual_evidence"]]


def _canonical_distributions(distributions):
    payload = []
    for distribution in distributions:
        payload.append(
            (
                cell_ref_key(distribution.source_cell),
                distribution.direction.value,
                tuple(sorted((cell_ref_key(kernel.target_cell), round(kernel.weight, 15)) for kernel in distribution.kernels if kernel.weight > 0.0)),
                round(distribution.residual.mass, 15),
                round(distribution.total_mass, 15),
            )
        )
    return tuple(sorted(payload))


def _max_positive_kernel_count(distributions) -> int:
    return max((sum(1 for kernel in distribution.kernels if kernel.weight > 0.0) for distribution in distributions), default=0)
