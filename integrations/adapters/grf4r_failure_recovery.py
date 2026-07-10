"""Destructive failure fixtures scoped to a temporary GRF4R workspace."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from time import perf_counter_ns

from nollm.grf.admission_bridge import MissingSourceFallback, resolve_source_fallback
from nollm.grf.facade import GRFFacade

from .grf_file_adapter import GRFFileAdapter


@dataclass(frozen=True)
class FailureRecoveryResult:
    adapter_crash_classified: bool
    missing_evidence_detected: bool
    corrupted_object_detected: bool
    partial_write_detected: bool
    identity_attack_rejected: bool
    evidence_recovered: bool
    replay_preserved: bool
    recovery_time_ns: int

    @property
    def passed(self) -> bool:
        return all((self.adapter_crash_classified, self.missing_evidence_detected, self.corrupted_object_detected, self.partial_write_detected, self.identity_attack_rejected, self.evidence_recovered, self.replay_preserved))


def run_failure_recovery(workspace: Path) -> FailureRecoveryResult:
    root = Path(workspace)
    adapter = GRFFileAdapter(root)
    capture = adapter.capture(_request("capture", {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": "capture:grf4r:failure", "content": "recoverable evidence", "origin_kind": "validation_fixture", "source_window_refs": ("window:grf4r:failure",), "recorded_at": "2026-07-10T00:00:00Z"}))
    shard = str(capture["evidence_identity"])
    place = adapter.place(_request("place", {"kind": "nollm_grf_admit_request", "version": "1", "shard_id": shard, "source_window_id": "window:grf4r:failure", "policy_hint": {"policy_id": "validation_fixture_policy", "chart_id": "chart:failure"}, "recorded_at": "2026-07-10T00:00:01Z"}, evidence=shard))
    placement = str(place["placement_identity"])
    admit = adapter.admit(_request("admit", {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": shard, "placement_id": placement, "recorded_at": "2026-07-10T00:00:02Z", "admitted_by": "validation_fixture"}, evidence=shard, placement=placement))
    admission = str(admit["admission_identity"])
    replay_request = _request("replay", _query(admission), admission=admission)
    original_replay = adapter.handle_mapping(replay_request)

    facade = GRFFacade(root)
    evidence_path = facade.store.path_for("evidence_shard", shard, "grfs/evidence/shards")
    original_bytes = evidence_path.read_bytes()
    recovery_started = perf_counter_ns()

    evidence_path.unlink()
    missing = isinstance(resolve_source_fallback(shard, facade.store), MissingSourceFallback)
    evidence_path.write_bytes(original_bytes)

    evidence_path.write_bytes(b"{not-json")
    corrupted = _read_fails(shard, facade)
    evidence_path.write_bytes(original_bytes)

    evidence_path.write_bytes(original_bytes[: max(1, len(original_bytes) // 2)])
    partial = _read_fails(shard, facade)
    evidence_path.write_bytes(original_bytes)

    recovered = getattr(resolve_source_fallback(shard, facade.store), "content", None) == "recoverable evidence"
    identity_attack = adapter.recall(_request("recall", _query("shard:fake"), evidence="shard:wrong"))
    identity_rejected = identity_attack.get("ok") is False

    crashing = GRFFileAdapter(root)
    crashing._service.handle = lambda _request: (_ for _ in ()).throw(RuntimeError("fixture crash"))
    crash_response = crashing.validate(_request("validate", {}))
    adapter_crash = crash_response.get("error_code") == "adapter_failure"
    recovered_replay = GRFFileAdapter(root).handle_mapping(replay_request)
    recovery_ns = perf_counter_ns() - recovery_started
    return FailureRecoveryResult(adapter_crash, missing, corrupted, partial, identity_rejected, recovered, original_replay.get("result") == recovered_replay.get("result"), recovery_ns)


def _read_fails(shard_id: str, facade: GRFFacade) -> bool:
    try:
        facade.store.read_evidence_shard(shard_id)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return True
    return False


def _query(admission_id: str) -> dict[str, object]:
    return {"kind": "nollm_grf_recall_request", "version": "1", "query_id": "query:grf4r:failure", "entry_mode": "admission_id", "entry_ref": admission_id, "allowed_kernels": ("lateral",), "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1}}


def _request(capability: str, payload: dict[str, object], evidence: str | None = None, placement: str | None = None, admission: str | None = None) -> dict[str, object]:
    return {"contract_version": "grf_host_v1", "host_request_id": f"host:grf4r:failure:{capability}", "capability": capability, "payload": payload, "evidence_identity": evidence, "placement_identity": placement, "admission_identity": admission}
