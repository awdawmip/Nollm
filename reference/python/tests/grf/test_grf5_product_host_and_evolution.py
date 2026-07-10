from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf5_operational_validation import run_operational_validation
from integrations.adapters.grf_declared_host_adapter import GRFDeclaredHostAdapter
from integrations.adapters.grf_product_host import GRFProductHost
from nollm.grf.contract_evolution import ContractVersionRegistry, migrate_host_request


def test_product_host_runs_file_backed_lifecycle_and_survives_restart(tmp_path: Path) -> None:
    host = GRFProductHost(tmp_path, "test")
    capture = host.capture("capture:product:test", "real product content", "window:product:test", "2026-07-10T00:00:00Z")
    shard = capture["evidence_identity"]
    place = host.place(shard, "window:product:test", "2026-07-10T00:00:01Z")
    admit = host.admit(shard, place["placement_identity"], "2026-07-10T00:00:02Z")
    recalled = host.recall("admission_id", admit["admission_identity"], admit["admission_identity"])
    replayed = host.restart().replay("admission_id", admit["admission_identity"], admit["admission_identity"])
    assert recalled["result"] == replayed["result"]
    assert recalled["contract_version"] == "grf_host_v2"


def test_contract_v1_migrates_to_v2_without_identity_or_payload_change() -> None:
    request = {"contract_version": "grf_host_v1", "host_request_id": "host:migrate:1", "capability": "recall", "payload": {"kind": "nollm_grf_recall_request", "version": "1", "query_id": "query:migrate", "entry_mode": "shard_id", "entry_ref": "shard:migrate", "allowed_kernels": ("lateral",), "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1}}, "evidence_identity": "shard:migrate", "placement_identity": None, "admission_identity": None}
    migrated = migrate_host_request(request)
    assert migrated["contract_version"] == "grf_host_v2"
    assert migrated["payload"] == request["payload"]
    assert migrated["evidence_identity"] == request["evidence_identity"]
    registry = ContractVersionRegistry()
    assert registry.get("grf_host_v1").status == "supported_deprecated"
    assert registry.current().version == "grf_host_v2"


def test_operational_cycles_preserve_counts_replay_and_fallback(tmp_path: Path) -> None:
    result = run_operational_validation(tmp_path, cycles=30, restart_interval=7)
    assert result.evidence_count == result.placement_count == result.admission_count == 30
    assert result.restart_count == 5
    assert result.replay_deterministic is True
    assert result.source_fallback_preserved is True


def test_product_host_accepts_openclaw_and_codex_declared_adapters(tmp_path: Path) -> None:
    integrations = ROOT / "integrations"
    adapters = (
        ("openclaw", integrations / "openclaw" / "v2-adapter" / "capabilities.json"),
        ("codex", integrations / "codex" / "adapter" / "capabilities.json"),
    )
    identities = []
    for name, declaration in adapters:
        workspace = tmp_path / name
        host = GRFProductHost(workspace, name, adapter=GRFDeclaredHostAdapter(workspace, declaration))
        capture = host.capture("capture:product:shared", "shared", "window:product:shared", "2026-07-10T00:00:00Z")
        identities.append(capture["evidence_identity"])
    assert len(set(identities)) == 1


def test_v1_and_v2_product_hosts_produce_equivalent_core_results(tmp_path: Path) -> None:
    results = []
    for version in ("grf_host_v1", "grf_host_v2"):
        host = GRFProductHost(tmp_path / version, "compatibility", contract_version=version)
        capture = host.capture("capture:compatibility", "compatibility", "window:compatibility", "2026-07-10T00:00:00Z")
        shard = capture["evidence_identity"]
        placement = host.place(shard, "window:compatibility", "2026-07-10T00:00:01Z")["placement_identity"]
        admission = host.admit(shard, placement, "2026-07-10T00:00:02Z")["admission_identity"]
        results.append(host.recall("admission_id", admission, admission)["result"])
    assert results[0] == results[1]
