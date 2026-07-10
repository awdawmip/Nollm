"""Recompute GRF7R2 Gates A-C from external Windows evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nollm.grf.gate_evidence import GateEvidence, GatePredicate


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _predicate(name: str, value: object, required: object, operator: str) -> GatePredicate:
    return GatePredicate(name, value, required, operator)


def _gate(gate: str, source: str, measurements: dict[str, object], event_count: int, checks: tuple[tuple[str, object, object, str], ...]) -> GateEvidence:
    return GateEvidence(gate, source, measurements, tuple(_predicate(*check) for check in checks), event_count)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.evidence_root
    registry = _read(root / "runtime" / "host_registry_replay_report.json")
    negative = _read(root / "real_global" / "negative_query_metrics.json")
    sustained = _read(root / "long_running" / "long_running_metrics.json")
    counts = dict(sustained["operation_counts"])
    gate_a = _gate("A", "runtime/host_registry_replay_report.json", registry, int(registry["registry_replay"]["entry_count"]), (
        ("same host restart retry", registry["same_host_restart_retry"], True, "eq"),
        ("cross host restart rejected", registry["cross_host_restart_rejected"], True, "eq"),
        ("mutated restart rejected", registry["mutated_restart_rejected"], True, "eq"),
        ("lost response identity", registry["lost_response_restart_identity"], True, "eq"),
        ("cache clear retains ownership", registry["cache_clear_durable_ownership"], True, "eq"),
        ("registry not evidence truth", registry["adapter_owns_evidence_truth"], False, "eq"),
        ("corruption rejected", registry["corruption_startup_rejected"], True, "eq"),
        ("truncated tail detected", registry["truncated_tail_detected"], True, "eq"),
    ))
    categories = dict(negative["by_category"])
    gate_b = _gate("B", "real_global/negative_query_metrics.json", negative, int(negative["negative_query_count"]), (
        ("negative query count", negative["negative_query_count"], 1000, "ge"),
        ("rejected coverage", categories["rejected"], 250, "ge"),
        ("decayed coverage", categories["decayed"], 250, "ge"),
        ("rolled back coverage", categories["rolled_back"], 250, "ge"),
        ("mixed coverage", categories["mixed"], 250, "ge"),
        ("forbidden hits", negative["forbidden_bridge_hit_count"], 0, "eq"),
        ("stale neighbors", negative["stale_neighbor_count"], 0, "eq"),
        ("active forbidden bridges", negative["forbidden_active_count"], 0, "eq"),
        ("negative replay", negative["replay_deterministic"], True, "eq"),
    ))
    minimums = {"capture": 1000, "place": 1000, "admit": 1000, "recall": 10000, "replay": 10000, "cross_partition_recall": 1000, "stitch": 500, "rollback": 500, "move": 500, "split_merge": 100, "restart": 100, "adapter_failure": 100, "real_post_commit_retry": 1000}
    checks = [(f"{name} actual events", counts.get(name, 0), required, "ge") for name, required in minimums.items()]
    checks.extend((
        ("one million events", sustained["operation_count"], 1_000_000, "ge"),
        ("recovery equals injected", sustained["recovery_count"], sustained["injected_failure_count"], "eq"),
        ("identity collisions", sustained["identity_collision_count"], 0, "eq"),
        ("duplicate evidence", sustained["duplicate_evidence_count"], 0, "eq"),
        ("duplicate placement", sustained["duplicate_placement_count"], 0, "eq"),
        ("duplicate admission", sustained["duplicate_admission_count"], 0, "eq"),
        ("orphans", sustained["orphan_count"], 0, "eq"),
        ("snapshot replay", sustained["snapshot_replay_equals_final_state"], True, "eq"),
        ("retained state is observable", int(sustained["ledger_bytes"]) + int(sustained["tracemalloc_current_bytes"]), 0, "gt"),
    ))
    gate_c = _gate("C", "long_running/long_running_metrics.json", sustained, int(sustained["operation_count"]), tuple(checks))
    payload = {"schema": "grf7r2_gate_evidence_v1", "gates": tuple(item.to_mapping() for item in (gate_a, gate_b, gate_c)), "status": "GRF7_ACCEPTED" if all(item.result.passed for item in (gate_a, gate_b, gate_c)) else "GRF7_NOT_ACCEPTED"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print(payload["status"])
    return 0 if payload["status"] == "GRF7_ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
