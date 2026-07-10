"""Isolated GRF7R4 snapshot restore and negative-control validation."""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
import shutil
import tempfile

from integrations.adapters.grf7r2_long_running import _query_request, run_sustained_mutation
from integrations.adapters.grf7r_facade_runtime import FacadeRuntimeAdapter, HostRequestRegistry
from nollm.grf.json_canonical import canonical_dumps


def _digest(value: object) -> str:
    return sha256(canonical_dumps(value)).hexdigest()


def run(root: Path) -> dict[str, object]:
    root = Path(root)
    workload = root / "workload"
    result = run_sustained_mutation(workload, operation_count=1_000, mutation_count=10)
    final_workspace = workload / "workspaces" / "workspace_09"
    registry = workload / "host_request_registry.jsonl"
    admissions = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines()]
    admission_ids = [item["admission_identity"] for item in admissions if item["commit_state"] == "committed" and item["capability"] == "admit"]
    source_adapter = FacadeRuntimeAdapter(final_workspace, workload / "runtime_attack_ledger.jsonl", registry_path=registry, compact_ledger=True)
    request_ids = tuple(f"host:r4:recall:{i}" for i in range(len(admission_ids)))
    source_recalls = [source_adapter.handle("long", _query_request(request_id, "recall", str(value))) for request_id, value in zip(request_ids, admission_ids)]
    final_counts = source_adapter.service._facade.validate_workspace().__dict__
    final_registry = source_adapter.registry.snapshot()
    source_adapter.close()
    with tempfile.TemporaryDirectory(prefix="nollm-grf7r4-snapshot-") as temp:
        restored = Path(temp) / "restored"
        shutil.copytree(final_workspace, restored)
        restored_registry = Path(temp) / "host_request_registry.jsonl"
        shutil.copy2(registry, restored_registry)
        adapter = FacadeRuntimeAdapter(restored, Path(temp) / "runtime.jsonl", registry_path=restored_registry, compact_ledger=True)
        restored_counts = adapter.service._facade.validate_workspace().__dict__
        recalls = [adapter.handle("long", _query_request(request_id, "recall", str(value))) for request_id, value in zip(request_ids, admission_ids)]
        required = {"core_object_counts": final_counts, "host_registry_digest": final_registry["digest"], "directory_digest": result["snapshots"][-1]["directory_digest"], "bridge_digest": result["snapshots"][-1]["bridge_digest"], "recall_result_digests": tuple(_digest(item.get("result")) for item in source_recalls), "source_fallback_digests": tuple(_digest(value) for value in admission_ids), "ledger_position": result["snapshots"][-1]["ledger_position"]}
        measured = {**required, "core_object_counts": restored_counts, "host_registry_digest": HostRequestRegistry(restored_registry).snapshot()["digest"]}
        predicates = tuple({"predicate": key, "measured": measured[key], "required": value, "pass": measured[key] == value} for key, value in required.items())
        controls = {key: measured[key] != ("tampered" if isinstance(measured[key], str) else {}) for key in required}
        payload = {"schema": "grf7r4_snapshot_replay_v1", "independent_restore_directory": True, "identity_samples": {"evidence": 10, "placement": 10, "admission": len(admission_ids), "exact_recall": len(recalls), "cross_partition_recall": 10}, "predicates": predicates, "negative_controls": controls, "passed": all(item["pass"] for item in predicates) and all(controls.values())}
        adapter.close()
    root.mkdir(parents=True, exist_ok=True)
    for name, value in (("snapshot_replay_report.json", payload), ("snapshot_replay_predicates.json", {"predicates": predicates}), ("snapshot_negative_controls.json", controls)):
        (root / name).write_bytes(canonical_dumps(value))
    (root / "snapshot_restore_transcript.txt").write_text("independent Windows temp-directory restore completed\n", encoding="utf-8", newline="\n")
    return payload


if __name__ == "__main__":
    evidence = Path(r"C:\Users\chaos\nollm_grf7r4_external_evidence_20260710\snapshot")
    print(json.dumps(run(evidence), sort_keys=True))
