from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


SCHEMA = "nollm_aold_single_content_neutral_pipeline_validation_v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    evidence_bytes = args.evidence.read_bytes()
    events = [json.loads(line) for line in evidence_bytes.decode("utf-8").splitlines() if line]
    summary = json.loads(args.summary.read_text("utf-8"))
    failures = []
    if not events or summary.get("schema_version") != SCHEMA or any(event.get("schema_version") != SCHEMA for event in events):
        failures.append("schema")
    if summary.get("evidence_sha256") != sha256(evidence_bytes).hexdigest():
        failures.append("evidence_sha256")
    offline_gates = [key for key in summary if key.startswith("gate_") and key != "gate_g_provider_validated"]
    if any(summary.get(key) is not True for key in offline_gates):
        failures.append("offline_gates")
    if summary.get("status") != "IN_PROGRESS" or summary.get("gate_g_provider_validated") is not False or summary.get("provider_calls") != 0:
        failures.append("provider_truth")
    active = next((event for event in events if event.get("event") == "active_reachability"), {})
    if any(active.get(key) != 0 for key in ("legacy_reachable_count", "content_category_branch_count", "source_role_gate_count")):
        failures.append("active_reachability")
    capture = next((event for event in events if event.get("event") == "capture_pipeline"), {})
    if capture.get("tool_evidence_count") != 6 or capture.get("capture_a_statement_count") != 20 or capture.get("capture_b_statement_count") != 1 or capture.get("capture_b_contains_a_statement") is not False:
        failures.append("capture_pipeline")
    scales = [event for event in events if event.get("event") == "progressive_routing_scale"]
    if [event.get("statement_count") for event in scales] != [128, 300, 1000]:
        failures.append("scale_inventory")
    print(json.dumps({"status": "PASS" if not failures else "FAIL", "failures": failures}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
