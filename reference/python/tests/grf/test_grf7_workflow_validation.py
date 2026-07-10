from __future__ import annotations

from nollm.grf.grf7_workflow_validation import run_workflow_validation


def test_workflow_validation_executes_all_baselines_without_core_adoption() -> None:
    result = run_workflow_validation(20)
    assert result.workflow_count == 4 and result.baseline_count == 4
    assert len(result.metrics) == 20
    assert result.grf_traceable is True
    assert result.grf_context_reduction_measured is True
    assert result.grf_pairwise_edge_maintenance is False
    assert result.false_relation_rollback_audited is True
    assert result.status == "GATE_I_PASS"
