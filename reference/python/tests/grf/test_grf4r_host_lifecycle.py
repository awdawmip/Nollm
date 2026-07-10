from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf4r_host_lifecycle import run_all_host_lifecycles


def test_all_hosts_execute_contract_lifecycle_retry_and_replay(tmp_path: Path) -> None:
    results = run_all_host_lifecycles(tmp_path)
    assert tuple(item.host_name for item in results) == ("file", "openclaw_like", "codex_like")
    assert len({item.evidence_identity for item in results}) == 1
    for item in results:
        assert item.negotiated_capabilities == ("capture", "place", "admit", "recall", "replay", "validate")
        assert item.duplicate_evidence_count == 1
        assert item.retry_idempotent is True
        assert item.replay_deterministic is True
        assert item.timeout_recovered is True
        assert item.invalid_capability_rejected is True
