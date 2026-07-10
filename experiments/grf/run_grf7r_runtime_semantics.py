from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil

from integrations.adapters.grf7r_facade_runtime import FacadeRuntimeAdapter, LostHostResponse


def request(request_id: str, capability: str, payload: dict[str, object], evidence: str | None = None, placement: str | None = None, admission: str | None = None, version: str = "grf_host_v2") -> dict[str, object]:
    return {"contract_version": version, "host_request_id": request_id, "capability": capability, "payload": payload, "evidence_identity": evidence, "placement_identity": placement, "admission_identity": admission}


def run(root: Path) -> dict[str, object]:
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    adapter = FacadeRuntimeAdapter(root / "workspace", root / "runtime_events.jsonl")
    capture_payload = {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": "capture:grf7r:post-commit", "content": "durable runtime evidence", "origin_kind": "validation_fixture", "source_window_refs": ("window:grf7r:runtime",), "recorded_at": "2026-07-10T00:00:00Z"}
    capture = request("host:alpha:capture", "capture", capture_payload)
    try:
        adapter.handle("alpha", capture, lose_response_after_commit=True)
    except LostHostResponse:
        pass
    capture_retry = adapter.handle("alpha", capture)
    shard_id = str(capture_retry["evidence_identity"])
    place_payload = {"kind": "nollm_grf_admit_request", "version": "1", "shard_id": shard_id, "source_window_id": "window:grf7r:runtime", "policy_hint": {"policy_id": "grf_deterministic_policy_v1", "chart_id": "chart:runtime"}, "recorded_at": "2026-07-10T00:00:01Z"}
    place = request("host:alpha:place", "place", place_payload, shard_id)
    try:
        adapter.handle("alpha", place, lose_response_after_commit=True)
    except LostHostResponse:
        pass
    place_retry = adapter.handle("alpha", place)
    placement_id = str(place_retry["placement_identity"])
    admit_payload = {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": shard_id, "placement_id": placement_id, "recorded_at": "2026-07-10T00:00:02Z", "admitted_by": "host_rule"}
    admit = request("host:alpha:admit", "admit", admit_payload, shard_id, placement_id)
    try:
        adapter.handle("alpha", admit, lose_response_after_commit=True)
    except LostHostResponse:
        pass
    admit_retry = adapter.handle("alpha", admit)
    admission_id = str(admit_retry["admission_identity"])
    report_before = adapter.service._facade.validate_workspace()
    adapter.clear_response_cache()
    recovered = tuple(adapter.handle("alpha", item) for item in (capture, place, admit))
    report_after = adapter.service._facade.validate_workspace()
    query_payload = {"kind": "nollm_grf_recall_request", "version": "1", "query_id": "query:grf7r:runtime", "entry_mode": "admission_id", "entry_ref": admission_id, "allowed_kernels": ("lateral",), "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1}}
    replay_request = request("host:alpha:replay", "replay", query_payload, admission=admission_id)
    replay_first = adapter.handle("alpha", replay_request)
    restarted = FacadeRuntimeAdapter(root / "workspace", root / "runtime_events.jsonl")
    replay_second = restarted.handle("alpha", replay_request)
    replay_equal = replay_first["result"] == replay_second["result"]
    attacks = {}
    attacks["cross_host_duplicate_request"] = adapter.handle("beta", capture).get("ok") is False
    mutated = dict(capture)
    mutated["payload"] = {**capture_payload, "content": "mutated"}
    attacks["cross_host_replay"] = adapter.handle("beta", mutated).get("ok") is False
    attacks["wrong_evidence_identity"] = adapter.handle("alpha", request("host:attack:evidence", "place", place_payload, "shard:wrong")).get("ok") is False
    attacks["wrong_placement_identity"] = adapter.handle("alpha", request("host:attack:placement", "admit", admit_payload, shard_id, "placement:wrong")).get("ok") is False
    bad_query = {**query_payload, "entry_ref": "admission:wrong"}
    attacks["wrong_admission_identity"] = adapter.handle("alpha", request("host:attack:admission", "recall", bad_query, admission=admission_id)).get("ok") is False
    attacks["mixed_namespace_identity"] = adapter.handle("alpha", request("host:attack:mixed", "recall", query_payload, evidence=shard_id, admission=admission_id)).get("ok") is False
    try:
        adapter.handle("alpha", request("host:attack:stale", "validate", {}, version="grf_host_v0"))
        attacks["stale_protocol_version"] = False
    except ValueError:
        attacks["stale_protocol_version"] = True
    attacks["unsupported_capability"] = adapter.handle("alpha", request("host:attack:unsupported", "unknown", {})).get("ok") is False
    adapter.partial_after_dispatch = True
    attacks["partial_response"] = adapter.handle("alpha", request("host:attack:partial", "validate", {})).get("ok") is False
    adapter.fail_before_dispatch = True
    try:
        adapter.handle("alpha", request("host:attack:crash", "validate", {}))
        attacks["adapter_crash"] = False
    except RuntimeError:
        attacks["adapter_crash"] = True
    counts_unchanged = report_before == report_after
    identities_stable = tuple((item["evidence_identity"], item["placement_identity"], item["admission_identity"]) for item in recovered) == ((shard_id, None, None), (shard_id, placement_id, None), (shard_id, placement_id, admission_id))
    result = {
        "post_commit_retry_count": 3,
        "retry_identities_stable": identities_stable,
        "durable_counts_unchanged_after_cache_delete": counts_unchanged,
        "adapter_owns_durable_truth": False,
        "replay_deterministic_before_after_restart": replay_equal,
        "attacks": attacks,
        "attack_rejection_count": sum(attacks.values()),
        "attack_count": len(attacks),
    }
    adapter.flush_events()
    restarted.flush_events()
    result["runtime_event_ledger_sha256"] = sha256((root / "runtime_events.jsonl").read_bytes()).hexdigest()
    (root / "runtime_semantics_metrics.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    output = Path(os.environ.get("NOLLM_GRF7R_OUTPUT_ROOT", r"C:\Users\chaos\nollm_grf7_external_evidence_20260710\grf7r_closure")) / "runtime"
    print(json.dumps(run(output), sort_keys=True, indent=2))
