from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


SCHEMA = "nollm_aold_content_neutral_memory_validation_v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    evidence_bytes = args.evidence.read_bytes()
    events = [
        json.loads(line) for line in evidence_bytes.decode("utf-8").splitlines() if line
    ]
    summary = json.loads(args.summary.read_text("utf-8"))
    failures = []
    if (
        not events
        or any(event.get("schema_version") != SCHEMA for event in events)
        or summary.get("schema_version") != SCHEMA
    ):
        failures.append("schema")
    if summary.get("evidence_sha256") != sha256(evidence_bytes).hexdigest():
        failures.append("evidence_sha256")
    if any(summary.get(f"gate_{name}") is not True for name in "abcdef"):
        failures.append("offline_gates")
    if (
        summary.get("status") != "IN_PROGRESS"
        or summary.get("gate_g_provider_validated") is not False
    ):
        failures.append("provider_truth")
    scales = [
        event for event in events if event.get("event") == "progressive_routing_scale"
    ]
    if [event.get("statement_count") for event in scales] != [128, 300, 1000]:
        failures.append("scale_inventory")
    if any(
        event.get("selected_entry_count") != 1
        or event.get("uncovered_source_cell_count") != 0
        for event in scales
    ):
        failures.append("routing_certificate")
    print(
        json.dumps(
            {"status": "PASS" if not failures else "FAIL", "failures": failures},
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
