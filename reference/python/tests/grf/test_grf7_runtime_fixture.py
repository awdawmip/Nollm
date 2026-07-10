from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf7_runtime_fixture import run_runtime_validation


def test_runtime_fixture_uses_queue_contract_adapter_and_restart(tmp_path) -> None:
    result = run_runtime_validation(tmp_path, request_count=1_000, retry_target=10, restart_target=10, failure_target=5)
    assert result.runtime_count == 3
    assert result.request_count == 1_000
    assert result.retry_count >= 10
    assert result.restart_count == 10
    assert result.injected_adapter_failure_count >= 5
    assert result.duplicate_evidence_count == 0
    assert result.identity_collision_count == 0
    assert result.adapter_owns_durable_truth is False
    assert result.status == "GATE_G_PASS"
