from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil

from integrations.adapters.grf7r_facade_runtime import FacadeRuntimeAdapter, HostRequestRegistryError, LostHostResponse


def _capture(content: str = "durable host evidence") -> dict[str, object]:
    return {"contract_version": "grf_host_v2", "host_request_id": "host:alpha:durable:capture", "capability": "capture", "payload": {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": "capture:grf7r2:durable", "content": content, "origin_kind": "validation_fixture", "source_window_refs": ("window:grf7r2:durable",), "recorded_at": "2026-07-10T00:00:00Z"}, "evidence_identity": None, "placement_identity": None, "admission_identity": None}


def run(root: Path) -> dict[str, object]:
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    workspace, registry, attacks = root / "workspace", root / "host_request_registry.jsonl", root / "runtime_attack_ledger.jsonl"
    request = _capture()
    alpha = FacadeRuntimeAdapter(workspace, attacks, registry_path=registry, compact_ledger=True)
    try:
        alpha.handle("alpha", request, lose_response_after_commit=True)
    except LostHostResponse:
        pass
    alpha.close()
    restarted = FacadeRuntimeAdapter(workspace, attacks, registry_path=registry, compact_ledger=True)
    same_host = restarted.handle("alpha", request)
    cross_host = restarted.handle("beta", request)
    mutated = restarted.handle("alpha", _capture("mutated payload"))
    restarted.clear_response_cache()
    cache_cleared = restarted.handle("alpha", request)
    report = {
        "same_host_restart_retry": same_host.get("ok") is True,
        "cross_host_restart_rejected": cross_host.get("error_code") == "cross_host_or_mutated_replay",
        "mutated_restart_rejected": mutated.get("error_code") == "cross_host_or_mutated_replay",
        "lost_response_restart_identity": same_host.get("evidence_identity") == cache_cleared.get("evidence_identity"),
        "cache_clear_durable_ownership": cache_cleared.get("ok") is True,
        "registry_replay": restarted.registry.snapshot(),
        "adapter_owns_evidence_truth": False,
        "registry_sha256": sha256(registry.read_bytes()).hexdigest(),
        "runtime_attack_ledger_sha256": sha256(attacks.read_bytes()).hexdigest(),
    }
    (root / "host_registry_replay_report.json").write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    # Complete corruption is fail-closed; an incomplete final line is detected and ignored.
    corrupt = root / "corrupt_registry.jsonl"
    corrupt.write_bytes(registry.read_bytes() + b"not-json\n")
    try:
        FacadeRuntimeAdapter(workspace, root / "corrupt_events.jsonl", registry_path=corrupt)
        report["corruption_startup_rejected"] = False
    except HostRequestRegistryError:
        report["corruption_startup_rejected"] = True
    tail = root / "truncated_tail_registry.jsonl"
    tail.write_bytes(registry.read_bytes() + b'{"truncated"')
    report["truncated_tail_detected"] = FacadeRuntimeAdapter(workspace, root / "tail_events.jsonl", registry_path=tail).registry.truncated_tail_detected
    (root / "host_registry_replay_report.json").write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    output = Path(os.environ.get("NOLLM_GRF7R2_OUTPUT_ROOT", r"C:\Users\chaos\nollm_grf7r2_external_evidence_20260710")) / "runtime"
    print(json.dumps(run(output), sort_keys=True, indent=2))
